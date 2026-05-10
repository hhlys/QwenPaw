# 云地通信 custom channel 方案

## 目标

本方案目标是把云地通信能力做成一整块可复制的 custom channel，不修改 QwenPaw 主工程源码。

边侧部署时，只需要：

1. 安装 QwenPaw。
2. 复制 `cloud_edge` custom channel 目录。
3. 修改 `agent.json` 启用 `channels.cloud_edge`。
4. 启动 `qwenpaw app`。

## 代码位置

源码模板位于：

```text
examples/custom_channels/cloud_edge/
```

运行时安装到：

```text
~/.qwenpaw/custom_channels/cloud_edge/
```

## 为什么选择 custom_channels

QwenPaw 已经支持扫描：

```text
~/.qwenpaw/custom_channels/
```

只要目录中存在继承 `BaseChannel` 的类，并声明：

```python
channel = "cloud_edge"
```

QwenPaw 启动时就能自动发现它。因此 `cloud_edge` 不需要写进内置 channel registry，也不需要新增内置配置类。

## 运行流程

```text
qwenpaw app
  -> ChannelManager.from_config
  -> get_channel_registry()
  -> 加载内置 channels
  -> 扫描 ~/.qwenpaw/custom_channels
  -> 发现 cloud_edge.CloudEdgeChannel
  -> 读取 agent.json 中的 channels.cloud_edge
  -> 启动 cloud_edge
```

`cloud_edge` 启动后：

```text
边侧 QwenPaw -> ClawHub 注册节点
边侧 QwenPaw -> ClawHub 心跳
边侧 QwenPaw -> ClawHub 轮询任务
边侧 QwenPaw 本地执行任务
边侧 QwenPaw -> ClawHub 上报过程事件和最终结果
```

所有网络请求都是边侧主动访问云端，不要求云端访问边侧。

## agent.json 配置示例

```json
{
  "channels": {
    "console": {
      "enabled": true
    },
    "cloud_edge": {
      "enabled": true,
      "hub_url": "http://127.0.0.1:8080",
      "node_id": "edge-linux-001",
      "tenant_id": "tenant-a",
      "group_name": "default",
      "username": "edge-operator",
      "token": "",
      "heartbeat_interval": 30,
      "poll_interval": 2
    }
  }
}
```

## 意图下发

ClawHub 创建云端任务后，边侧 `cloud_edge` 轮询到任务，并把任务转换为 QwenPaw channel request：

```text
ClawHub task
  -> cloud_edge._execute_task()
  -> build_agent_request_from_native()
  -> self._process(request)
  -> QwenPaw AgentRunner
  -> LLM / tools / skills
```

执行过程中产生的事件会实时回传到 ClawHub：

```text
async for event in self._process(request)
  -> /api/edge/tasks/{taskId}/events
```

最终结果回传到：

```text
/api/edge/tasks/{taskId}/complete
```

## 定时任务要求

定时任务必须进入 QwenPaw 原生 cron 体系，而不是由模型自己创建脚本。

正确路径：

```text
云端下发意图
  -> 边侧 Agent 判断需要周期执行
  -> 调用 qwenpaw cron create 或 /cron/jobs
  -> 写入边侧 workspace/jobs.json
  -> CronManager 注册 APScheduler job
  -> QwenPaw 控制台“定时任务”页面可见
  -> CronExecutor 定时执行
  -> dispatch.channel = cloud_edge
  -> cloud_edge.send()
  -> ClawHub 同一个云端会话显示结果
```

推荐命令：

```bash
qwenpaw cron create \
  --base-url http://127.0.0.1:8088 \
  --agent-id default \
  --type agent \
  --name "每 5 分钟巡检" \
  --cron "*/5 * * * *" \
  --channel cloud_edge \
  --target-user "clawhub" \
  --target-session "云端 conversation_id" \
  --text "执行一次边侧巡检，并总结结果"
```

关键约束：

- `--channel` 必须是 `cloud_edge`。
- `--target-session` 必须是云端下发任务携带的 `conversation_id`。
- 不允许创建外部 Python 脚本、后台 while 循环、Linux crontab 或 systemd timer 来代替 QwenPaw cron。

## 验证方式

启动边侧：

```bash
python -m qwenpaw app --host 127.0.0.1 --port 8088
```

观察日志：

```text
custom channel registered: cloud_edge
cloud_edge custom channel started: node_id=edge-linux-001
cloud_edge registered: node_id=edge-linux-001 status=online
```

然后在 ClawHub 下发意图：

```text
创建一个每 5 分钟执行一次的边侧巡检定时任务，执行结果回传到当前云端会话。
```

预期：

- 边侧日志出现 `cloud_edge task received`。
- 边侧 QwenPaw 控制台“定时任务”页面出现新任务。
- cron 到点执行后，ClawHub 当前会话收到执行结果。

## 当前边界

当前能够做到：

- 云端纳管边侧节点。
- 边侧主动注册、心跳、轮询任务。
- 云端下发意图到边侧执行。
- 执行过程事件流式回传。
- 任务最终结果回传。
- 云端意图创建 QwenPaw 原生定时任务。
- 原生定时任务结果通过 `cloud_edge` 回传。

当前不做：

- 边侧本地任意 session 自动扫描上报。
- QwenPaw 插件管理页面里的启停与配置。
- 云端主动直连边侧。
- 外部脚本式定时任务。
