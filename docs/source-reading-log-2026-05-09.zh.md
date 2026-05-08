# QwenPaw 源码阅读记录 2026-05-09

## 今日目标

今天主要阅读昨天实现的“云端意图下发到边侧 QwenPaw 执行”这条代码链路。

重点不是继续开发新功能，而是理解以下几个问题：

1. ClawHub 下发的意图是如何进入边侧 QwenPaw 的。
2. `cloud.py` 和 `CloudChannel` 是如何关联起来的。
3. `CloudChannel.stream_one()` 里的 `self._process(request)` 到底是谁。
4. `runner.stream_query()` 和 `AgentRunner.query_handler()` 是什么关系。
5. 用 Java 后端开发者熟悉的对象引用、方法引用、模板方法模式来理解这段 Python 代码。

## 今日读到的核心链路

本次重点确认的完整调用链如下：

```text
ClawHub 管理页面
  -> ClawHub 后端 dispatch 接口
  -> HTTP POST 边侧 QwenPaw /api/cloud/chat
  -> QwenPaw cloud.py
  -> workspace.channel_manager.get_channel("cloud")
  -> CloudChannel.stream_one(payload)
  -> CloudChannel.build_agent_request_from_native(payload)
  -> self._process(request)
  -> runner.stream_query(request)
  -> Runner.stream_query()
  -> self.query_handler(...)
  -> AgentRunner.query_handler(...)
  -> QwenPawAgent(...)
  -> agent(msgs)
  -> 大模型调用 / 工具调用 / 流式事件返回
```

一句话总结：

```text
cloud.py 是 HTTP 入口，CloudChannel 是消息适配器，runner.stream_query 是 Agent 执行入口，AgentRunner.query_handler 是 QwenPaw 的业务实现。
```

## cloud.py 的职责

文件：

```text
src/qwenpaw/app/routers/cloud.py
```

关键代码：

```python
router = APIRouter(prefix="/cloud", tags=["cloud"])
```

该 router 被主应用挂载到 `/api` 下，所以最终接口是：

```text
POST /api/cloud/chat
```

这个接口是 ClawHub 下发意图时调用的边侧入口。

核心方法：

```python
async def post_cloud_chat(request: Request) -> StreamingResponse:
```

它主要做这些事：

1. 读取 ClawHub 发来的 JSON body。
2. 通过 `get_agent_for_request(request)` 找到当前请求对应的 workspace。
3. 通过 `workspace.channel_manager.get_channel("cloud")` 找到 cloud channel。
4. 把普通 JSON 转换成 channel 原生 payload。
5. 创建或复用 chat 会话。
6. 通过 `workspace.task_tracker.attach_or_start(...)` 启动流式任务。
7. 返回 `StreamingResponse`，用 SSE 把边侧执行结果流式返回给 ClawHub。

关键代码：

```python
workspace = await get_agent_for_request(request)
cloud_channel = await workspace.channel_manager.get_channel("cloud")
```

这里的重点是：`cloud.py` 不直接创建 `CloudChannel`，而是从当前 workspace 的 `channel_manager` 里取已经初始化好的 `cloud` channel。

Java 类比：

```java
Workspace workspace = agentContext.getWorkspace(request);
BaseChannel cloudChannel = workspace.getChannelManager().getChannel("cloud");
```

## workspace.channel_manager 是什么

文件：

```text
src/qwenpaw/app/workspace/workspace.py
```

关键代码：

```python
@property
def channel_manager(self):
    return self._service_manager.services.get("channel_manager")
```

`workspace.channel_manager` 不是一个显式声明类型的字段，而是一个 `@property`，它从 service 字典里动态取对象。

这也是 VSCode/Pylance 有时无法直接跳到 `get_channel()` 源码的原因：Python 动态语言里，IDE 不一定能从 `services.get("channel_manager")` 推断出真实类型。

真实对象的创建位置：

```text
src/qwenpaw/app/workspace/service_factories.py
```

关键代码：

```python
cm = ChannelManager.from_config(
    process=make_process_from_runner(runner),
    config=temp_config,
    on_last_dispatch=on_last_dispatch,
    workspace_dir=ws.workspace_dir,
)
ws._service_manager.services["channel_manager"] = cm
```

因此：

```text
workspace.channel_manager
  -> self._service_manager.services["channel_manager"]
  -> ChannelManager 实例
```

## ChannelManager.get_channel("cloud")

文件：

```text
src/qwenpaw/app/channels/manager.py
```

关键代码：

```python
async def get_channel(self, channel: str) -> Optional[BaseChannel]:
    async with self._lock:
        for ch in self.channels:
            if ch.channel == channel:
                return ch
        return None
```

它的逻辑很简单：

```text
遍历 ChannelManager.channels
  -> 找到 ch.channel == "cloud" 的 channel
  -> 返回 CloudChannel 实例
```

`CloudChannel` 自己定义：

```python
channel = "cloud"
```

所以 `get_channel("cloud")` 找到的就是 `CloudChannel`。

## CloudChannel 是怎么被创建的

Cloud channel 的注册表在：

```text
src/qwenpaw/app/channels/registry.py
```

关键配置：

```python
_BUILTIN_SPECS = {
    ...
    "cloud": (".cloud", "CloudChannel"),
}
```

这表示：

```text
channel 名称 cloud
  -> 对应模块 src/qwenpaw/app/channels/cloud
  -> 对应类 CloudChannel
```

`ChannelManager.from_config()` 会遍历 channel registry：

```python
for key, ch_cls in get_channel_registry().items():
```

如果当前 agent 的 channel 配置里启用了 cloud，就执行：

```python
channels.append(ch_cls.from_config(**filtered_kwargs))
```

对于 cloud 来说，就是调用：

```python
CloudChannel.from_config(...)
```

最后创建出：

```python
CloudChannel(process=runner.stream_query, enabled=True, ...)
```

## Channel 配置从哪里读

workspace 启动时：

```text
src/qwenpaw/app/workspace/workspace.py
```

关键代码：

```python
self._config = load_agent_config(self.agent_id)
```

配置加载函数：

```text
src/qwenpaw/config/config.py
```

关键逻辑：

```python
agent_ref = config.agents.profiles[agent_id]
workspace_dir = Path(agent_ref.workspace_dir).expanduser()
agent_config_path = workspace_dir / "agent.json"
```

结论：

```text
优先读取当前 agent workspace 下的 agent.json。
如果 agent.json 不存在，则从全局 config.json 生成 fallback agent 配置并保存。
```

因此 `ChannelManager.from_config()` 使用的是：

```python
ws._config.channels
```

也就是当前 agent 自己的 `agent.json` 里的 channels 配置。

不是直接使用全局 `config.json` 的 channels，除非当前 workspace 的 `agent.json` 还不存在，需要从全局配置生成默认 agent 配置。

## make_process_from_runner 传了什么

文件：

```text
src/qwenpaw/app/channels/utils.py
```

关键代码：

```python
def make_process_from_runner(runner: Any):
    return runner.stream_query
```

所以：

```python
process=make_process_from_runner(runner)
```

实际等价于：

```python
process=runner.stream_query
```

注意这里不是调用方法：

```python
runner.stream_query()
```

而是传递方法引用：

```python
runner.stream_query
```

Java 类比：

```java
process = runner::streamQuery;
```

这是一个绑定方法引用。Python 中的 `runner.stream_query` 已经记住了 `self = runner`，后续调用 `process(request)` 时，不需要再额外传 runner。

## CloudChannel 如何持有 runner.stream_query

文件：

```text
src/qwenpaw/app/channels/cloud/channel.py
```

`CloudChannel.from_config()`：

```python
return cls(
    process=process,
    enabled=enabled,
    on_reply_sent=on_reply_sent,
)
```

`CloudChannel.__init__()`：

```python
def __init__(self, process, enabled, on_reply_sent=None):
    super().__init__(process, on_reply_sent=on_reply_sent)
    self.enabled = enabled
```

父类 `BaseChannel.__init__()`：

```text
src/qwenpaw/app/channels/base.py
```

关键代码：

```python
def __init__(self, process: ProcessHandler, ...):
    self._process = process
```

所以最终对象关系是：

```text
CloudChannel
  -> BaseChannel._process
    -> runner.stream_query
```

用 Java 对象引用方式理解：

```java
class CloudChannel extends BaseChannel {
}

class BaseChannel {
    private ProcessHandler process;

    BaseChannel(ProcessHandler process) {
        this.process = process;
    }
}
```

创建时相当于：

```java
new CloudChannel(runner::streamQuery);
```

因此 `CloudChannel` 并不是直接持有整个 runner 对象，而是持有 runner 的 `stream_query` 方法引用。

对象图：

```text
Workspace
  ├─ ServiceManager
  │    ├─ services["runner"] = AgentRunner
  │    └─ services["channel_manager"] = ChannelManager
  │
  └─ ChannelManager
       └─ channels: List[BaseChannel]
            └─ CloudChannel
                 └─ _process -> AgentRunner.stream_query
```

## CloudChannel.stream_one 执行流程

文件：

```text
src/qwenpaw/app/channels/cloud/channel.py
```

核心方法：

```python
async def stream_one(self, payload: Any) -> AsyncGenerator[str, None]:
```

它主要做两件事：

1. 把 cloud 原生 payload 转成 `AgentRequest`。
2. 调用 `self._process(request)`，也就是调用 `runner.stream_query(request)`。

关键代码：

```python
request = self.build_agent_request_from_native(payload)
```

然后：

```python
async for event in self._process(request):
    data = self._serialize_event_for_sse(event)
    yield f"data: {data}\n\n"
```

这里等价于：

```python
async for event in runner.stream_query(request):
    ...
```

`async for` 表示消费异步事件流。模型执行过程中产生一个 event，就处理一个 event，再转成 SSE 返回给 ClawHub。

## runner.stream_query 在哪里

`runner.stream_query()` 不在 QwenPaw 自己的 `AgentRunner` 里重写，而是在依赖包：

```text
myvenv/Lib/site-packages/agentscope_runtime/engine/runner.py
```

类：

```python
class Runner
```

方法：

```python
async def stream_query(self, request, **kwargs)
```

QwenPaw 的 `AgentRunner` 在：

```text
src/qwenpaw/app/runner/runner.py
```

定义：

```python
class AgentRunner(Runner):
```

所以：

```text
AgentRunner 继承 Runner
```

调用 `runner.stream_query(request)` 时，实际执行父类 `Runner.stream_query()`。

## Runner.stream_query 和 AgentRunner.query_handler 的关系

父类 `Runner.stream_query()` 是模板方法。

它负责通用流程：

1. 检查 runner 是否启动。
2. 补齐 `session_id` 和 `user_id`。
3. 创建初始 `AgentResponse`。
4. 根据 `framework_type` 选择消息适配器。
5. 把 `AgentRequest.input` 转成 AgentScope 的 `msgs`。
6. 调用 `self.query_handler(...)`。
7. 把子类 yield 出来的消息转换成标准 Event。
8. 最后 yield completed 或 failed response。

QwenPaw 的 `AgentRunner` 设置：

```python
self.framework_type = "agentscope"
```

因此父类会选择 AgentScope 适配器，把 `AgentRequest.input` 转成 `msgs`。

重点在：

```python
self.query_handler(...)
```

由于当前对象实际是 `AgentRunner`，所以这里动态分派到：

```python
AgentRunner.query_handler(...)
```

Java 类比：

```java
Runner runner = new AgentRunner();
runner.streamQuery();
```

父类 `streamQuery()` 内部调用：

```java
this.queryHandler();
```

最终执行的是子类：

```java
AgentRunner.queryHandler();
```

这是典型的模板方法模式。

## AgentRunner.query_handler 做什么

文件：

```text
src/qwenpaw/app/runner/runner.py
```

方法：

```python
async def query_handler(self, msgs, request: AgentRequest = None, **kwargs):
```

它是 QwenPaw 真正的业务处理入口。

今天已经梳理出它的大概职责：

1. 从 `msgs` 中提取用户最后一句话。
2. 判断是否是 `/command` 命令。
3. 设置当前 agent、session、root session 上下文。
4. 构造 `env_context`。
5. 加载 agent 配置。
6. 初始化 MCP clients。
7. 创建 `QwenPawAgent`。
8. 加载历史 session state。
9. 调用 `agent(msgs)`。
10. 流式 yield `msg, last`。
11. 保存 session state。
12. 更新 chat 活跃时间。

核心创建 agent 的位置：

```python
agent = QwenPawAgent(...)
```

真正开始执行的位置：

```python
async for msg, last in _stream_printing_messages_interruptible(
    agents=[agent],
    coroutine_task=agent(msgs),
):
    yield msg, last
```

这里之后才进入真正的大模型调用、工具调用、Agent 循环。

## 今日形成的关键理解

今天最终确认的个人理解如下：

```text
1. 创建 cloud channel 时，会把当前 workspace 的 runner.stream_query 方法引用传给 BaseChannel。

2. BaseChannel 把这个方法引用保存到 self._process。

3. ClawHub 调用 /api/cloud/chat 后，cloud.py 找到 CloudChannel，并启动 CloudChannel.stream_one(payload)。

4. stream_one 把 payload 转成 AgentRequest。

5. stream_one 执行 self._process(request)，本质就是执行 runner.stream_query(request)。

6. stream_query 是父类 Runner 的模板方法。

7. 父类 Runner.stream_query 内部调用 self.query_handler(...)。

8. 由于实际对象是 AgentRunner，所以 query_handler 最终执行 AgentRunner.query_handler。

9. AgentRunner.query_handler 创建 QwenPawAgent，并调用 agent(msgs)，开始真正的大模型和工具执行。
```

## 用 Java 思维重新表述

如果用 Java 伪代码理解，大概是：

```java
class Workspace {
    ServiceManager serviceManager;
}

class ServiceManager {
    Map<String, Object> services;
}

class AgentRunner extends Runner {
    @Override
    queryHandler(...) {
        QwenPawAgent agent = new QwenPawAgent(...);
        agent.call(msgs);
    }
}

class ChannelManager {
    List<BaseChannel> channels;
}

class BaseChannel {
    ProcessHandler process;

    BaseChannel(ProcessHandler process) {
        this.process = process;
    }
}

class CloudChannel extends BaseChannel {
    streamOne(payload) {
        AgentRequest request = buildAgentRequest(payload);
        process.apply(request);
    }
}
```

创建时：

```java
AgentRunner runner = serviceManager.get("runner");
CloudChannel cloudChannel = new CloudChannel(runner::streamQuery);
```

执行时：

```java
cloudChannel.streamOne(payload);
  -> process.apply(request);
  -> runner.streamQuery(request);
  -> Runner.streamQuery();
  -> this.queryHandler(...);
  -> AgentRunner.queryHandler(...);
```

## 今天没有继续深入的部分

今天先读到 `AgentRunner.query_handler()` 创建 `QwenPawAgent` 并调用 `agent(msgs)` 为止。

还没有详细展开：

1. `QwenPawAgent` 内部如何组织 prompt。
2. 模型 provider 是如何创建和调用的。
3. 工具调用是如何进入 tool guard / approval 的。
4. `agent(msgs)` 内部的 ReAct 执行循环。
5. `adapt_agentscope_message_stream` 如何把 AgentScope 消息转成 runtime Event。
6. SSE event 最终在 ClawHub 前端如何展示。

## 明天建议继续阅读

建议下一步从这里继续：

```text
src/qwenpaw/app/runner/runner.py
  -> AgentRunner.query_handler()
  -> QwenPawAgent(...)
  -> agent(msgs)
```

推荐阅读顺序：

1. 先看 `AgentRunner.query_handler()` 中创建 `QwenPawAgent` 前后 150 行，理解配置、上下文、session 是如何准备的。
2. 再进入 `src/qwenpaw/agents/react_agent.py`，看 `QwenPawAgent` 的构造函数。
3. 然后找 `QwenPawAgent.__call__` 或相关执行入口，理解 `agent(msgs)` 实际进入哪里。
4. 最后再看模型调用和工具调用部分。

明天的核心问题可以定为：

```text
CloudChannel 已经把请求送进 runner 了，那么 AgentRunner 如何创建 QwenPawAgent，QwenPawAgent 又如何真正调用大模型和工具？
```

