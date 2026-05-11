# 云端龙虾任务体系洞察

日期：2026-05-12

## 1. 背景

ClawHub 后续一定会有“任务”能力。这里的任务不只是定时任务，也不只是后台接口里的 task 表。

在云端龙虾产品里，任务至少包含：

- 用户在对话里下发的一次性任务。
- 定时任务。
- 长时间运行的后台任务。
- 文件处理任务。
- Skill 执行任务。
- 云端实例运维任务。
- 云边协同任务。
- 多龙虾协作任务。
- 失败重试、补偿、恢复任务。

因此，任务系统不应该只是“cron 配置页面”，而应该是整个 ClawHub 的调度中枢。

本文对 JVS Claw、Kimi Claw、ArkClaw、MaxClaw 的任务能力做产品洞察，并重点分析它们对 ClawHub 云边任务的参考意义。

## 2. 总体判断

同类 Claw 产品的任务能力正在从“用户说一句话”进化到“可计划、可追踪、可复用、可协作”的自动化系统。

| 产品 | 任务特征 | 对 ClawHub 的启发 |
|---|---|---|
| JVS Claw | 定时任务入口、任务文件空间、ClawSpace 可视化执行链路 | 任务要能看过程、看产物、可管理 |
| Kimi Claw | 定时任务、`/cron`、群聊 Conductor 拆分任务、Memory 保留定时任务 | 任务要有结构化描述、状态、日志、长期执行能力 |
| ArkClaw | 企业办公自动化、飞书/钉钉、会议纪要、文档处理 | 任务要接入企业工作流和权限审计 |
| MaxClaw | 低成本高频自动化、云工作空间、专家 Agent、跨 IM | 任务要能低成本长期运行，并沉淀成智能体能力 |

核心结论：

```text
任务不是对话的附属品。
任务应该成为对话、文件、终端、技能、云边节点之间的统一调度对象。
```

## 3. 任务的本质

在传统系统里，任务通常是：

```text
定时任务
异步任务
后台 Job
```

但在 Agent 系统里，任务更复杂。它既包含意图，又包含执行计划、上下文、工具调用、文件输入、产物输出和状态回传。

一个完整的 Agent 任务应该包含：

```text
谁发起
在哪个龙虾上执行
是否需要边侧节点
输入是什么
期望输出是什么
是否有时间计划
是否允许调用工具
是否允许访问文件
是否允许联网
是否需要审批
执行过程是什么
结果在哪里
失败后怎么办
```

所以 ClawHub 的任务模型不能只设计成：

```text
id, cron, content, status
```

而应该设计成：

```text
意图 + 调度 + 执行 + 事件 + 产物 + 审计
```

## 4. JVS Claw 洞察

### 4.1 公开资料明确说明

JVS Claw 的全面开放公告提到：

- JVS 文件空间上线，提供任务文件专属存储空间。
- 定时任务升级，新增定时任务入口，可配置可管理。
- 云端专属环境状态全程可观、可控。

来源：[JVS Claw 全面开放公告](https://docs-jvs.wuying.com/zh/blog/v2.0.0/)

JVS Claw 功能介绍中提到：

- 对话区域支持直接输入任务。
- 系统会实时显示 AI 在云端环境的操作链路，让任务执行过程透明、可随时介入。
- ClawSpace 是独立云端运行环境，预装 Python、Node.js 等开发环境。

来源：[JVS Claw 功能介绍](https://docs-jvs.wuying.com/zh/docs/intro/feature/)

JVS 积分节省指南里提到：

- 复杂任务应该先写计划文件，把状态、结论、待办写进文件，不靠聊天上下文堆积。
- 任务执行会消耗模型、工具、网页、日志、图片、文档分析等成本。
- 示例里包含“汇总 AI 热点并定时发送”“定时发简报”等任务。

来源：[JVS Claw 积分节省指南](https://docs-jvs.wuying.com/zh/docs/billing/saving)

### 4.2 产品洞察

JVS 的任务能力有三个关键特征：

```text
任务可视化
  用户可以看到 AI 在云端环境里的操作链路。

任务产物化
  任务文件有专属空间，用户可以精准找到关键文件。

任务持久化
  复杂任务靠计划文件和进度文件推进，而不是完全依赖对话上下文。
```

JVS 给我们的最重要启发是：

```text
任务不是一次回复；
任务是一个可以产生过程、状态和文件产物的执行单元。
```

### 4.3 对云边任务的参考意义

云边任务尤其需要 JVS 这种“任务过程透明”的能力。

因为边侧执行通常在客户机房，云端用户看不到边侧机器。如果只返回最终一句话，用户会不信任：

```text
边侧是否真的执行了？
执行到了哪一步？
是否读取了正确文件？
是否调用了正确 Skill？
失败在哪个阶段？
有没有生成产物？
```

所以云边任务应该支持：

```text
任务状态
任务步骤
执行日志摘要
工具调用事件
文件产物
边侧节点信息
失败原因
```

这和 JVS 的“实时显示操作链路”是一脉相承的。

## 5. Kimi Claw 洞察

### 5.1 公开资料明确说明

Kimi Claw 使用技巧文档明确说明：

- Kimi Claw 支持定时完成任务。
- 定时任务不只是提醒，也可以作为信息雷达。
- 推荐在定时任务里一次说清楚三件事：执行时间、输出格式、约束条件。
- 建议避免整点任务，使用非整点时间减少拥堵和延迟。

来源：[Kimi Claw 使用技巧](https://www.kimi.com/zh-cn/help/kimi-claw/usage-tips)

Kimi Claw 群聊文档说明：

- Kimi Conductor 会理解目标，把复杂任务拆分成多个 Thread。
- 多个 Claw 分工执行具体任务并汇报结果。
- 群聊适合多 Claw 协作、跨设备、跨权限、长程任务。

来源：[Kimi Claw 群聊](https://www.kimi.com/zh-cn/help/kimi-claw/kimiclaw-group-chat)

Kimi 响应慢或不回复文档说明：

- 恢复初始设置时，会保留工作空间文件、长期记忆和定时任务。
- 可以通过 `/status` 查看系统状态，通过 `/logs` 查看最近日志。

来源：[Kimi Claw 响应慢或不回复](https://www.kimi.com/zh-cn/help/kimi-claw/slow-no-response)

Kimi 会员文档还显示了 Agent 并发任务、Agent Swarm 并发子任务等配额维度。

来源：[Kimi Membership Plans](https://www.kimi.com/help/membership/membership-overview)

### 5.2 产品洞察

Kimi 的任务体系最有价值的地方有四点：

#### 5.2.1 定时任务必须结构化

Kimi 推荐定时任务必须说清：

```text
什么时候执行
做什么
输出格式
约束条件
```

这说明自然语言创建任务可以保留，但后台必须结构化存储。

例如用户说：

```text
每天 9:17 汇总最新市场新闻，输出 3 条要点 + 1 条风险提示，中文，200 字以内。
```

后台应该解析成：

```text
schedule: daily 09:17
instruction: 汇总最新市场新闻
output_format: 3 条要点 + 1 条风险提示
language: zh-CN
max_length: 200
constraints: 带风险提示
```

#### 5.2.2 任务要避开资源峰值

Kimi 建议不要设置整点任务，这是很现实的调度经验。

ClawHub 后续如果有大量定时任务，也会遇到：

```text
每天 9:00 大量任务同时触发
模型调用拥堵
边侧节点连接拥堵
文件下载拥堵
任务延迟
用户投诉
```

因此 ClawHub 需要调度层支持：

```text
错峰执行
抖动 jitter
优先级
并发限制
队列状态
超时控制
```

#### 5.2.3 复杂任务需要 Conductor

Kimi 群聊里的 Conductor 很重要。它说明复杂任务不是一个 Agent 从头干到尾，而是：

```text
理解目标
拆分 Thread
选择合适 Claw
分配子任务
收集结果
汇总回复
```

这对云边任务非常有参考意义。

云边场景里，未来可能有：

```text
云端 QwenPaw
边侧 QwenPaw
端侧 QwenPaw
多个边侧节点
多个 Skill
不同权限的数据源
```

这时云端需要一个调度者，决定：

```text
这个任务在云端做还是边侧做？
需要哪个边侧节点？
是否需要拆成多个子任务？
是否需要等待多个结果汇总？
失败后是否换节点？
```

#### 5.2.4 定时任务是长期资产

Kimi 恢复初始设置时保留定时任务，这说明定时任务不是临时会话数据，而是用户资产。

ClawHub 也应该把任务分成：

```text
临时任务
长期任务
系统任务
运维任务
```

定时任务、监控任务、自动日报、边侧巡检都属于长期资产，需要备份和迁移。

## 6. ArkClaw 洞察

### 6.1 公开资料侧重点

ArkClaw 的公开资料更强调企业办公自动化、云端托管、飞书/钉钉集成和安全能力。

相关资料描述了它能够处理会议纪要、文档、表格、企业办公流，并以 SaaS 方式提供托管能力。

来源：

- [ArkClaw Review](https://openclawai.net/blog/arkclaw-review)
- [CnTechPost - ByteDance joins OpenClaw race with launch of cloud-based ArkClaw](https://cntechpost.com/2026/03/09/bytedance-joins-openclaw-race-launch-cloud-based-arkclaw/)

### 6.2 产品洞察

ArkClaw 的任务能力更偏企业工作流：

```text
会议纪要
文档处理
多维表格
群消息总结
定期报告
审批和权限
企业数据安全
```

它给 ClawHub 的启发是：

```text
任务不只是执行，更是企业流程的一部分。
```

企业客户会问：

```text
谁创建了这个任务？
任务读了哪些文件？
任务调用了哪些外部系统？
任务是否访问了边侧生产数据？
结果发给了谁？
失败有没有告警？
是否有审计记录？
```

所以 ClawHub 的云边任务必须从一开始就考虑：

```text
租户隔离
用户权限
任务审计
文件访问记录
边侧数据不出域策略
结果外发审批
```

## 7. MaxClaw 洞察

### 7.1 公开资料明确说明

MaxClaw 产品页强调：

- 10 秒部署。
- 无服务器、无 Docker、无 API Key。
- 50GB 云工作空间。
- 长期记忆。
- 文件管理。
- 内置工具生态。
- 多 IM 入口。

MaxClaw 介绍页还强调高频自动化、定时管理、自动脚本、文件分析等能力。

来源：

- [MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)
- [MaxClaw by MiniMax](https://maxclaw.ai/)

### 7.2 产品洞察

MaxClaw 的任务能力偏向：

```text
低成本高频自动化
长期运行
多工具调用
多入口触发
专家 Agent 模板
```

对 ClawHub 来说，MaxClaw 提醒我们：

```text
任务数量会很多；
任务频率会很高；
任务成本必须可控；
任务需要模板化。
```

因此不能只做一个“新增定时任务”弹窗。应该支持：

```text
任务模板
任务配额
任务成本预估
任务频率限制
任务执行历史
任务产物归档
```

## 8. 任务分类模型

建议 ClawHub 将任务分成八类。

### 8.1 对话派生任务

用户在对话里临时发起：

```text
帮我分析这个文件
帮我查一下服务器状态
帮我调用边侧节点执行巡检
```

特点：

- 一次性。
- 和会话强关联。
- 用户等待结果。
- 适合流式返回。

### 8.2 定时任务

周期性执行：

```text
每天 9 点生成日报
每小时检查一次边侧服务
每周生成客户数据摘要
```

特点：

- 长期存在。
- 需要可管理。
- 需要执行历史。
- 需要失败告警。

### 8.3 长任务

单次但耗时较长：

```text
分析一个大代码仓
处理一批 Excel
生成完整报告
执行系统巡检
```

特点：

- 需要进度。
- 需要中间日志。
- 需要可取消。
- 需要断点或状态文件。

### 8.4 Skill 任务

由 Skill 触发：

```text
调用竞品分析 Skill
调用运维巡检 Skill
调用金融监控 Skill
```

特点：

- 需要 Skill 版本。
- 需要输入输出 schema。
- 需要权限控制。

### 8.5 云边任务

云端下发到边侧执行：

```text
边侧执行生产环境巡检
边侧读取内网文件
边侧运行本地脚本
边侧执行客户系统操作
```

特点：

- 边侧主动拉取任务。
- 云端不能直接访问边侧端口。
- 需要节点选择。
- 需要状态回传。
- 需要离线容错。

### 8.6 运维任务

ClawHub 对实例执行：

```text
重启龙虾
修复龙虾
升级龙虾
备份龙虾
恢复龙虾
```

特点：

- 高风险。
- 需要审计。
- 需要回滚。
- 需要任务化，不应同步阻塞接口。

### 8.7 系统任务

平台内部周期任务：

```text
清理临时文件
检查实例健康
刷新节点在线状态
备份过期清理
统计用量
```

特点：

- 用户不一定可见。
- 需要稳定性。
- 需要可观测。

### 8.8 多 Agent 协作任务

类似 Kimi 群聊的 Conductor 模型：

```text
云端拆解任务
边侧执行子任务
端侧执行浏览器任务
云端汇总结果
```

特点：

- 需要主任务和子任务。
- 需要调度者。
- 需要结果汇总。
- 需要部分失败策略。

## 9. 云边任务的关键参考意义

定时任务和云边任务表面不同，但底层非常像。

共同点：

```text
都不是即时对话回复。
都需要持久化任务状态。
都需要异步执行。
都需要执行历史。
都需要失败重试。
都需要产物归档。
都需要状态回传。
```

差异是：

```text
定时任务由时间触发。
云边任务由云端意图或系统事件触发。
```

因此 ClawHub 可以设计一个统一任务模型：

```text
trigger_type:
  MANUAL
  CHAT
  CRON
  WEBHOOK
  SYSTEM
  EDGE_EVENT

execution_target:
  CLOUD_QWENPAW
  EDGE_QWENPAW
  LOCAL_DEVICE
  CLAWHUB_SYSTEM
```

这样定时任务、云边任务、运维任务都能用同一套底座。

## 10. 云边任务模型建议

### 10.1 地调云，而不是云调地

生产环境里，边侧在客户机房，通常不会开放公网端口。

所以云边任务应采用：

```text
边侧主动注册
边侧定期心跳
边侧主动拉取任务
边侧流式上报事件
边侧上报最终结果
```

这和我们之前讨论的方向一致。

### 10.2 云边任务状态机

建议状态：

```text
CREATED
QUEUED
DISPATCHED
LEASED
RUNNING
STREAMING
WAITING_APPROVAL
SUCCEEDED
FAILED
CANCELED
TIMEOUT
RETRYING
```

云边场景要特别关注：

```text
节点离线
任务租约过期
重复拉取
幂等执行
边侧执行中断
结果上报失败
```

### 10.3 主任务与子任务

复杂任务应支持：

```text
task
  parent_task_id
  root_task_id
```

例如：

```text
主任务：生成客户生产环境巡检报告
  子任务 1：边侧 A 检查数据库
  子任务 2：边侧 B 检查应用日志
  子任务 3：云端汇总报告
```

这对未来 1 对 2 边侧/端侧架构非常重要。

## 11. 任务与对话的关系

任务不应该脱离对话，但也不应该完全等同于对话。

建议关系：

```text
一个会话可以创建多个任务。
一个任务可以向会话回写多个事件。
一个任务可以生成多个文件产物。
一个定时任务可以对应一个固定会话或每次执行创建新会话。
```

定时任务建议：

```text
配置任务时创建一个任务会话。
每次执行结果写入该任务会话。
最近对话里显示任务标识。
```

这样用户可以像 JVS/Kimi 一样，在会话列表里看到：

```text
每天 9 点日报    任务
边侧巡检报告     任务
市场风向标       任务
```

## 12. 任务与文件的关系

任务一定会产生文件。

建议：

```text
任务输入文件
任务中间文件
任务产物文件
任务日志文件
```

都要关联 `task_id`。

任务详情页应该展示：

```text
输入
执行过程
产物
日志
成本
```

这直接承接前一篇文件管理洞察里的“任务产物视图”。

## 13. 任务与终端的关系

Agent 执行任务时，经常会调用终端或工具。

因此任务事件里应该包含：

```text
TOOL_CALL
TOOL_RESULT
TERMINAL_COMMAND
TERMINAL_STDOUT
TERMINAL_STDERR
TERMINAL_EXIT
FILE_GENERATED
```

这样用户在任务详情里能看到：

```text
龙虾到底做了什么？
为什么失败？
日志在哪里？
是否有高危命令？
```

## 14. 任务调度策略

### 14.1 错峰

借鉴 Kimi 的非整点建议，ClawHub 应在创建定时任务时提示：

```text
建议设置为 09:13、12:47 等非整点时间，降低拥堵概率。
```

平台也可以自动加 jitter：

```text
09:00 任务实际在 09:00-09:05 之间分散触发。
```

### 14.2 并发限制

需要按以下维度限制：

```text
用户并发任务数
龙虾实例并发任务数
边侧节点并发任务数
租户并发任务数
模型调用并发数
```

Kimi 会员体系里已经把 Agent concurrent tasks 当作权益维度，这说明并发任务是商业化和资源控制的重要指标。

### 14.3 优先级

任务优先级：

```text
HIGH: 用户正在等待的对话任务
NORMAL: 用户主动创建的后台任务
LOW: 定时摘要、批处理
SYSTEM: 健康检查、清理任务
```

### 14.4 重试

不同失败原因重试策略不同：

```text
模型限流：延迟重试
边侧离线：等待节点上线
权限不足：不重试，提示用户授权
脚本失败：不自动重试，返回错误
网络超时：有限次数重试
```

## 15. 任务数据模型建议

### 15.1 task 表

```text
task
  id
  tenant_id
  user_id
  instance_id
  session_id
  parent_task_id
  root_task_id
  title
  instruction
  task_type
  trigger_type
  execution_target
  target_node_id
  status
  priority
  timeout_seconds
  max_retries
  retry_count
  lease_owner
  lease_until
  created_at
  started_at
  finished_at
```

### 15.2 task_schedule 表

```text
task_schedule
  id
  task_template_id
  tenant_id
  user_id
  instance_id
  cron_expr
  timezone
  jitter_seconds
  enabled
  next_run_at
  last_run_at
```

### 15.3 task_event 表

```text
task_event
  id
  task_id
  event_type
  source
  content
  metadata
  sequence
  created_at
```

### 15.4 task_artifact 表

```text
task_artifact
  id
  task_id
  file_id
  artifact_type
  created_at
```

## 16. ClawHub 产品建议

### 16.1 任务菜单

可以在云边对话或龙虾侧边栏里保留“定时任务”，但底层叫“任务中心”。

用户视角：

```text
定时任务
执行记录
任务产物
失败任务
```

管理员视角：

```text
全部任务
云边任务
运维任务
系统任务
队列状态
```

### 16.2 创建任务弹窗

不要只让用户填 cron。

建议让用户填：

```text
任务名称
执行内容
执行对象：云端龙虾 / 边侧节点
执行频率：一次 / 每天 / 每周 / 每隔一段时间
输出方式：写入当前会话 / 新建任务会话 / 发送通知
失败处理：提醒 / 重试 / 忽略
```

### 16.3 任务详情页

任务详情应展示：

```text
基本信息
执行目标
时间计划
执行状态
事件流
日志
输入文件
产物文件
成本
失败原因
重试记录
```

这比只显示一行状态更像产品。

## 17. 对当前云边任务的直接建议

结合我们现在的云边需求，建议下一步不要单独做一套 relay task，而是往统一 task 模型靠。

MVP 可以先实现：

```text
云边任务 = task.execution_target = EDGE_QWENPAW
边侧拉取任务 = task.status 从 QUEUED 到 LEASED
边侧执行过程 = task_event
边侧结果 = task_event + task_artifact
云端对话显示 = 读取 task_event 流
```

这样未来可以自然扩展：

- 定时任务下发边侧。
- Skill 下发边侧。
- 多边侧节点协作。
- 边侧失败后云端重试。
- 任务结果写入会话。
- 任务产物进入文件管理。

## 18. MVP 路线

### V0

- 统一 task 表。
- 支持手动云边任务。
- 支持任务事件回传。
- 支持任务结果写入对话。
- 支持任务状态查看。

### V1

- 支持定时任务。
- 支持每次执行生成 task_run。
- 支持任务产物文件。
- 支持失败重试。
- 支持任务会话标识。

### V2

- 支持边侧节点选择。
- 支持多边侧子任务。
- 支持云端 Conductor 汇总。
- 支持任务成本统计。
- 支持审计和权限。

### V3

- 支持任务模板市场。
- 支持企业审批流。
- 支持任务自动优化。
- 支持基于历史结果的自进化。

## 19. 结论

定时任务当然有参考意义，但它只是任务体系的一种触发方式。

真正值得借鉴的是：

```text
JVS：任务过程透明、任务产物可管理。
Kimi：定时任务结构化、错峰调度、Conductor 拆分协作。
ArkClaw：任务进入企业办公流，需要权限和审计。
MaxClaw：任务要低成本、高频、长期运行，并模板化。
```

对 ClawHub 来说，云边任务应该从一开始就设计成统一任务体系的一部分，而不是临时 relay 表。

推荐方向：

```text
对话产生任务；
任务驱动云端或边侧执行；
执行过程形成事件流；
结果进入对话；
产物进入文件管理；
长期任务进入任务中心；
审计贯穿全链路。
```

这套模型可以同时覆盖：

- 对话任务。
- 定时任务。
- 云边任务。
- Skill 任务。
- 运维任务。
- 多 Agent 协作任务。

如果任务系统设计好了，ClawHub 才能从“能聊天的容器管理平台”升级成“能长期自动工作的龙虾托管平台”。

## 20. 参考资料

- [JVS Claw 全面开放公告](https://docs-jvs.wuying.com/zh/blog/v2.0.0/)
- [JVS Claw 功能介绍](https://docs-jvs.wuying.com/zh/docs/intro/feature/)
- [JVS Claw 积分节省指南](https://docs-jvs.wuying.com/zh/docs/billing/saving)
- [Kimi Claw 使用技巧](https://www.kimi.com/zh-cn/help/kimi-claw/usage-tips)
- [Kimi Claw 群聊](https://www.kimi.com/zh-cn/help/kimi-claw/kimiclaw-group-chat)
- [Kimi Claw 响应慢或不回复](https://www.kimi.com/zh-cn/help/kimi-claw/slow-no-response)
- [Kimi Membership Plans](https://www.kimi.com/help/membership/membership-overview)
- [ArkClaw Review](https://openclawai.net/blog/arkclaw-review)
- [CnTechPost - ByteDance joins OpenClaw race with launch of cloud-based ArkClaw](https://cntechpost.com/2026/03/09/bytedance-joins-openclaw-race-launch-cloud-based-arkclaw/)
- [MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)
- [MaxClaw by MiniMax](https://maxclaw.ai/)
