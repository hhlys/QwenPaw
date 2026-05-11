# 云端龙虾对话框与终端能力洞察

日期：2026-05-11

## 1. 背景

ClawHub 后续要做云端龙虾产品。除了实例管理、文件管理、升级和备份，还必须认真设计“对话框”和“终端”之间的关系。

表面上看：

- 对话框是用户和龙虾聊天。
- 终端是用户进入运行环境执行命令。

但在 Agent 产品里，它们不是两个孤立 UI，而是同一个智能体工作空间的两种控制平面：

```text
对话框：意图控制平面
终端：执行控制平面
文件管理：资产控制平面
```

如果这三者设计割裂，用户会遇到几个典型问题：

- 对话里说“帮我安装 pandas”，但不知道实际是否安装成功。
- 终端里执行了脚本，但对话里不知道结果。
- Agent 生成了文件，但用户不知道在哪下载。
- 任务失败了，只能在日志里排查，对话窗口看不到过程。
- 高级用户需要终端，普通用户又害怕终端。

因此，ClawHub 的关键设计不是“要不要做终端”，而是：

```text
如何让对话框、终端、文件管理共享同一个工作空间和事件流。
```

## 2. 基本定义

### 2.1 对话框是什么

对话框是用户表达意图、获取解释、确认动作和接收结果的入口。

它适合：

- 普通用户。
- 自然语言任务。
- 多轮对话。
- 结果解释。
- 任务确认。
- 安全审批。
- 任务进度摘要。

典型表达：

```text
帮我分析这个 Excel。
每天下午 5 点生成日报。
把今天生成的报告发给我。
修复一下这个龙虾。
升级到最新版本。
```

对话框不是简单聊天工具，而是 Agent 的“意图入口”。

### 2.2 终端是什么

终端是运行环境的命令行入口。

它适合：

- 开发者。
- 运维人员。
- 高级用户。
- 调试。
- 安装依赖。
- 查看日志。
- 执行脚本。
- 紧急修复。
- 环境诊断。

典型命令：

```bash
ls
python main.py
pip install pandas
tail -f app.log
openclaw doctor --fix
qwenpaw --version
```

终端不是普通用户的主入口，而是运行环境的“控制台入口”。

## 3. 不是同一个东西，但必须共享上下文

对话框和终端不是同一个东西。

区别如下：

| 维度 | 对话框 | 终端 |
|---|---|---|
| 用户心智 | 我让龙虾做事 | 我直接操作环境 |
| 输入形式 | 自然语言 | 命令 |
| 输出形式 | 解释、结果、进度 | stdout、stderr、退出码 |
| 用户类型 | 普通用户为主 | 高级用户/运维为主 |
| 风险 | 意图误解 | 直接破坏环境 |
| 权限 | 应该受 Agent 策略约束 | 应该受命令策略约束 |

但它们必须共享：

```text
同一个龙虾实例
同一个工作目录
同一个文件空间
同一个会话或任务上下文
同一套权限策略
同一套审计日志
同一条事件流
```

否则产品会割裂。

## 4. 竞品洞察

### 4.1 JVS Claw

公开资料显示，JVS Claw 的 CloudSpace 是一个独立云端运行环境，预装 Python、Node.js 等环境，可以打开软件、浏览网页、处理 Excel、写代码。

在机器人离线修复文档中，JVS 建议用户进入 CloudSpace 的 terminal，执行：

```bash
openclaw doctor --fix
```

然后重启 CloudSpace。

来源：[JVS Claw 机器人离线修复](https://docs-jvs.wuying.com/zh/docs/handbook/offline/)

#### 洞察

JVS 的终端不是普通用户每天使用的主入口，而是“云环境维修入口”。

其产品语义大概是：

```text
普通任务走对话；
环境出问题进 CloudSpace；
排障和修复用 terminal。
```

这给 ClawHub 的启发是：

- 对话框要覆盖大部分日常任务。
- 终端要保留给诊断、修复、开发、依赖安装。
- 修复功能可以先由平台自动执行 terminal 命令，而不是让用户手动输入。

换句话说，用户点“修复”，后台可以执行：

```bash
qwenpaw doctor --fix
```

但不一定让用户直接看到终端。

### 4.2 Kimi Claw

Kimi Claw 帮助中心提到：

- 用户可以直接和 Kimi Claw 对话。
- 可以使用 `/help`、`/status`、`/cron`、`/new`、`/reset`、`/compact`、`/skills`、`/memory`、`/logs`、`/debug` 等命令。
- 可以查看日志、管理定时任务、管理记忆和技能。
- 文件可以通过对话、工作空间、飞书机器人流转。

来源：

- [Kimi Claw 产品介绍](https://www.kimi.com/help/kimi-claw/overview)
- [Kimi Claw 文件收发](https://www.kimi.com/zh-cn/help/kimi-claw/file-transfer)

#### 洞察

Kimi 最值得学习的是“命令嵌入对话框”。

也就是说，它不一定要求用户打开一个传统终端，而是在对话输入框中引入 slash command：

```text
/status
/logs
/cron
/memory
/skills
/debug
```

这是一种中间形态：

```text
不是纯自然语言；
也不是完整 shell；
而是产品化命令。
```

这种设计很适合普通用户和高级用户之间的过渡层。

对 ClawHub 来说，可以设计三层入口：

```text
自然语言对话
  “帮我看看龙虾为什么离线”

产品化命令
  /status
  /logs
  /repair

完整终端
  tail -f logs/app.log
  pip install xxx
```

### 4.3 ArkClaw

ArkClaw 公开资料更强调 SaaS 托管、飞书/钉钉入口、企业安全和免运维。它的产品方向不像是鼓励普通用户进入终端，而是把终端能力隐藏在平台运维和 Agent 工具执行后面。

#### 洞察

ArkClaw 类型产品的核心思路是：

```text
企业用户不应该直接碰终端；
平台要把终端动作封装成安全可审计的操作。
```

例如：

- 重启。
- 修复。
- 查看日志。
- 安装插件。
- 执行任务。
- 导出结果。

这些都可以由按钮、命令或对话触发，但后台可以调用终端或容器命令。

这对 ClawHub 的企业化很关键。终端能力不能完全开放给所有用户，否则会带来：

- 数据泄露。
- 误删文件。
- 逃逸风险。
- 安装恶意依赖。
- 越权访问。

### 4.4 MaxClaw

MaxClaw 公开资料强调：

- 无服务器。
- 无 Docker。
- 无 API Key。
- 50GB 云工作空间。
- 文件管理。
- 长期记忆。
- 多工具执行。
- 多 IM 入口。

它的产品语义更像“托管 Agent Runtime”，不是“给用户一个终端自己维护”。

#### 洞察

MaxClaw 给 ClawHub 的启发是：

```text
普通用户不想学习终端；
他们只想让龙虾完成任务。
```

终端能力必须存在，但应该大多数时候隐身。

产品上应该强调：

```text
龙虾能运行代码
龙虾能处理文件
龙虾能安装工具
龙虾能生成结果
```

而不是：

```text
你可以打开 terminal 执行命令
```

## 5. 对话框与终端的三种关系模型

### 5.1 模型一：完全分离

```text
对话框只聊天
终端只执行命令
```

优点：

- 实现简单。
- 边界清楚。

缺点：

- 上下文割裂。
- 终端执行结果无法进入对话。
- 对话无法解释终端失败原因。
- 用户体验像两个系统。

不推荐作为长期方案。

### 5.2 模型二：对话调用终端

```text
用户在对话框表达意图
Agent 在后台调用终端执行命令
终端输出回流到对话框
```

这是 Agent 产品最核心的模式。

示例：

```text
用户：帮我分析 sales.xlsx
Agent：执行 python analyze.py
终端：stdout/stderr/exit_code
Agent：总结结果并生成报告
```

优点：

- 普通用户不需要看终端。
- 终端成为 Agent 的工具。
- 对话可以解释执行结果。

缺点：

- 需要工具权限控制。
- 需要命令审计。
- 高危命令要审批。

这是 ClawHub 应该默认采用的模式。

### 5.3 模型三：终端反哺对话

```text
用户或系统在终端执行命令
终端事件进入会话时间线
Agent 能读取终端结果并继续处理
```

示例：

```text
用户在终端执行 pytest
终端输出测试失败
对话框出现：“检测到测试失败，需要我分析原因吗？”
```

这是一种高级体验，也是未来方向。

优点：

- 对话和终端真正融合。
- 高级用户效率很高。
- 适合开发、运维、云边调试。

缺点：

- 实现复杂。
- 需要统一事件流。
- 需要会话关联。

ClawHub 可以先设计数据模型，后续逐步实现。

## 6. 推荐的 ClawHub 设计

### 6.1 三层入口

建议 ClawHub 设计三层交互入口：

```text
第一层：自然语言对话
  面向普通用户。
  例如：帮我修复龙虾、帮我安装依赖、帮我生成日报。

第二层：产品化命令
  面向轻高级用户。
  例如：/status、/logs、/repair、/cron、/files、/memory。

第三层：完整终端
  面向开发者、运维和管理员。
  例如：bash、tail、pip、python、qwenpaw doctor。
```

这样既保留易用性，又不牺牲高级能力。

### 6.2 对话页设计

对话页可以有两个模式：

```text
对话视图
  默认模式，只展示自然语言结果、文件卡片、任务状态。

执行详情
  展示 Agent 调用的命令、工具、日志、stdout/stderr。
```

普通用户默认看不到完整终端，只看到：

```text
正在分析文件
正在运行脚本
已生成报告
```

高级用户可以展开：

```text
命令：python analyze.py
退出码：0
耗时：12.3s
stdout：...
stderr：...
```

### 6.3 终端页设计

终端页不应该只是 WebSocket 终端。它应该绑定：

```text
龙虾实例
当前工作目录
当前用户
权限策略
审计日志
会话上下文
```

终端页可以提供：

- 实时命令行。
- 最近命令历史。
- 一键复制。
- 一键发送输出到对话。
- 一键让龙虾解释错误。
- 一键生成修复建议。

这会比普通终端更符合 Agent 产品。

## 7. 统一事件流

如果要让对话框和终端深度融合，最重要的是统一事件流。

建议定义 `workspace_event`：

```text
workspace_event
  id
  tenant_id
  user_id
  instance_id
  session_id
  task_id
  event_type
  source
  content
  metadata
  created_at
```

事件类型：

```text
USER_MESSAGE
ASSISTANT_MESSAGE
TOOL_CALL
TOOL_RESULT
TERMINAL_COMMAND
TERMINAL_STDOUT
TERMINAL_STDERR
TERMINAL_EXIT
FILE_UPLOAD
FILE_GENERATED
CRON_TRIGGERED
TASK_STARTED
TASK_COMPLETED
TASK_FAILED
APP_REPAIRED
APP_UPGRADED
```

来源：

```text
CHAT
TERMINAL
SYSTEM
AGENT
CRON
EDGE
IM
```

有了这个模型，对话框和终端就不是两个孤岛，而是同一个工作空间的不同视图。

## 8. 安全设计

终端比对话更危险。

### 8.1 风险

```text
rm -rf 删除数据
cat secret 泄露密钥
curl 外发文件
pip install 恶意包
反弹 shell
越权访问宿主机
读取其他用户数据
```

Agent 产品还多了一个风险：

```text
用户上传的文件、网页、邮件可能诱导 Agent 执行危险命令。
```

### 8.2 权限分级

建议分三级：

| 级别 | 能力 |
|---|---|
| 普通用户 | 只能通过对话触发受控工具，不开放完整终端 |
| 高级用户 | 可查看执行详情，可执行白名单命令 |
| 管理员/运维 | 可打开完整终端，可执行诊断和修复 |

### 8.3 命令策略

建议实现命令风险分级：

```text
LOW
  ls, pwd, cat 非敏感文件, python --version

MEDIUM
  pip install, python script.py, curl 可信域名

HIGH
  rm, chmod, chown, kill, taskkill, docker, cat secret

BLOCKED
  读取密钥目录、外发敏感文件、宿主机危险命令
```

高危命令必须审批。

## 9. 和文件管理的关系

对话框、终端、文件管理是一套闭环：

```text
用户上传文件
  -> 对话框表达任务
  -> Agent 通过终端执行脚本
  -> 生成产物文件
  -> 文件管理登记
  -> 对话框返回文件卡片
```

如果没有这个闭环，用户会卡在：

```text
结果在哪里？
日志在哪里？
脚本在哪里？
这个文件是谁生成的？
失败原因是什么？
```

所以文件管理必须关联终端事件：

```text
这个文件由哪个命令生成？
这个文件由哪个任务生成？
这个文件是否来自边侧？
这个文件是否被对话引用过？
```

## 10. 和云边协同的关系

云边场景里，对话框和终端更复杂。

### 10.1 云端对话，下发边侧执行

```text
云端对话框
  -> 下发任务到边侧
  -> 边侧 QwenPaw 执行命令或技能
  -> stdout/stderr/文件/结果回传
  -> 云端对话框展示
```

用户不应该看到“边侧终端”，但应该看到：

```text
边侧正在执行
执行进度
执行日志摘要
结果文件
失败原因
```

### 10.2 边侧终端是否开放

企业客户生产网络里的边侧机器通常不应该随便开放完整终端。

建议：

```text
默认不开放边侧终端。
只允许受控任务执行。
必要时开放只读日志或审批后的远程命令。
所有命令必须审计。
```

### 10.3 云边事件统一

边侧执行事件也应该进入 `workspace_event`：

```text
source = EDGE
event_type = TERMINAL_STDOUT / TOOL_RESULT / FILE_GENERATED
```

这样云端对话框可以展示边侧结果。

## 11. MVP 建议

### 11.1 第一阶段

先不要做完整 Web 终端。

优先做：

- 对话框展示工具执行过程。
- 对话框展示命令摘要。
- 对话框展示任务状态。
- 文件产物回到对话框。
- `/status`、`/logs`、`/repair` 这类产品化命令。

理由：

- 更安全。
- 更容易落地。
- 更符合普通用户。
- 不需要一开始解决完整 WebSocket 终端、安全沙箱、命令审计等复杂问题。

### 11.2 第二阶段

做只读执行详情：

- 展示命令。
- 展示 stdout/stderr。
- 展示退出码。
- 展示耗时。
- 展示文件产物。

用户可以点击：

```text
让龙虾解释错误
继续修复
下载日志
```

### 11.3 第三阶段

开放受控终端：

- 仅管理员/高级用户可用。
- 命令风险分级。
- 高危命令审批。
- 命令审计。
- 一键把终端输出发送给龙虾分析。

## 12. ClawHub 产品建议

### 12.1 普通用户视角

普通用户不应该看到“终端”这个词太多。

可以展示为：

```text
执行过程
运行日志
修复记录
任务详情
```

### 12.2 高级用户视角

高级用户可以看到：

```text
终端
命令历史
日志
环境变量
依赖列表
进程状态
```

### 12.3 管理员视角

管理员需要：

```text
实例诊断
批量修复
升级日志
命令审计
安全策略
终端权限配置
```

## 13. 结论

对话框和终端不是同一个东西。

但在云端龙虾产品里，它们必须组成一个统一工作空间：

```text
对话框负责表达意图；
终端负责实际执行；
文件管理负责沉淀输入和产物；
事件流负责把三者串起来；
权限系统负责控制风险。
```

JVS Claw 告诉我们：终端是 CloudSpace 的高级维修入口。

Kimi Claw 告诉我们：slash command 是对话和终端之间的优秀中间层。

ArkClaw 告诉我们：企业 SaaS 应该把终端封装成安全、可审计的操作。

MaxClaw 告诉我们：普通用户想要的是托管 Agent，不是学习 Docker 和命令行。

因此 ClawHub 应该这样设计：

```text
默认让用户使用对话框；
用产品化命令承接轻运维；
用执行详情解释 Agent 行为；
把完整终端留给高级用户和管理员；
用统一事件流连接对话、终端、文件和云边任务。
```

如果只做对话框，产品不够可控。

如果只做终端，产品不够易用。

真正有竞争力的是：

```text
对话框 + 执行详情 + 文件产物 + 受控终端 + 统一事件流
```

这才是云端龙虾工作空间的核心形态。

## 14. 参考资料

- [JVS Claw 机器人离线修复](https://docs-jvs.wuying.com/zh/docs/handbook/offline/)
- [Kimi Claw 产品介绍](https://www.kimi.com/help/kimi-claw/overview)
- [Kimi Claw 文件收发](https://www.kimi.com/zh-cn/help/kimi-claw/file-transfer)
- [Kimi Code Slash Commands](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/slash-commands.html)
- [OpenClaw CLI reference](https://documentation.openclaw.ai/cli)
- [OpenClaw Quick Start](https://clawdocs.org/getting-started/quick-start)
- [MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)
