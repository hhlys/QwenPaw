# 云端龙虾文件管理能力洞察

日期：2026-05-11

## 1. 背景

ClawHub 后续要做“文件管理”。如果只把它理解成上传、下载、删除文件，会低估这个模块的重要性。

在云端龙虾产品里，文件管理不是一个普通网盘功能，而是智能体运行系统的一部分。它同时承担：

- 用户上传输入材料。
- Agent 读取任务上下文。
- Agent 生成任务产物。
- 长期记忆和工作空间沉淀。
- 定时任务产物归档。
- 技能、插件和脚本的运行载体。
- 云端、边侧、本地和 IM 通道之间的文件交换。
- 企业安全、权限、审计和数据保留。

因此，文件管理应该被设计成“龙虾工作空间”的核心能力，而不是一个附属菜单。

本文对比 JVS Claw、Kimi Claw、ArkClaw、MaxClaw 的文件管理形态，并给出 ClawHub 的设计建议。

## 2. 总体判断

四类产品的文件管理都不是单纯“文件列表”，而是围绕 Agent 工作流展开：

| 产品 | 文件管理关键词 | 产品语义 |
|---|---|---|
| JVS Claw | ClawSpace、文件上传下载、任务文件空间、云桌面 | 文件是云端执行环境的一部分 |
| Kimi Claw | 对话收发、工作空间、飞书取回文件、Memory | 文件是对话、记忆和多入口协作的桥梁 |
| ArkClaw | TOS 对象存储、飞书文档、云端 SaaS | 文件是企业办公流和对象存储资产 |
| MaxClaw | 50GB Cloud Workspace、长期记忆、文件管理 | 文件是托管 Agent 的长期上下文资产 |

给 ClawHub 的核心启发：

```text
不要做“网盘式文件管理”。
要做“面向 Agent 的工作空间文件管理”。
```

也就是说，文件不是孤立资源，而应该天然关联：

```text
用户
租户
龙虾实例
会话
任务
定时任务
Skill
云边节点
权限策略
审计日志
```

## 3. JVS Claw 洞察

### 3.1 公开资料明确说明

JVS Claw 的功能介绍中提到，ClawSpace 是每个 ClawBot 的独立云端运行环境。用户可以在 Web 端通过悬浮球上传和下载文件：

- 本地文件上传到云端环境，供 AI 处理。
- 云端生成的结果文件可以下载到本地。
- 移动端目前偏查看，不适合完整文件上传下载。

JVS Claw 的开放公告还提到“JVS 文件空间上线，提供任务文件专属存储空间，精准找到关键文件”。

JVS 计费文档也将“JVS 专属持久文件空间”作为权益能力之一。

来源：

- [JVS Claw 功能介绍](https://docs-jvs.wuying.com/zh/docs/intro/feature/)
- [JVS Claw 全面开放公告](https://docs-jvs.wuying.com/zh/blog/v2.0.0/)
- [JVS Claw 计费说明](https://docs-jvs.wuying.com/zh/docs/billing/)

### 3.2 产品层洞察

JVS 的文件管理有三个层次：

```text
第一层：云桌面级文件传输
  本地 <-> ClawSpace

第二层：任务产物文件空间
  任务生成的 Excel、PPT、PDF、代码、截图等集中管理

第三层：环境持久化
  安装的软件、生成文件、工作目录能够随 ClawBot 长期存在
```

这说明 JVS 没有把文件管理当作“对象列表”，而是当作 ClawSpace 的一部分。用户感知是：

```text
我的龙虾有一台自己的云电脑；
文件在这台云电脑里；
任务生成物可以拿出来；
下次回来还在。
```

### 3.3 对 ClawHub 的启发

如果 ClawHub 继续使用容器承载 QwenPaw，则至少要提供：

```text
容器内工作空间文件浏览
本地上传到容器
容器文件下载到本地
任务产物快速定位
实例重建后文件保留
```

更重要的是，要将文件与“任务”绑定：

```text
这个文件是哪个会话上传的？
这个文件是哪个任务生成的？
这个文件是否来自定时任务？
这个文件是否被某个 Skill 使用过？
这个文件是否应该出现在最近对话里？
```

JVS 的“任务文件专属存储空间”值得重点学习。ClawHub 后续不应只做树形目录，还要做“任务产物视图”。

## 4. Kimi Claw 洞察

### 4.1 公开资料明确说明

Kimi Claw 文件收发文档明确写到：

- 可以通过对话向 Kimi Claw 发送图片、文件等内容。
- 支持图片、PDF、Word、Excel 等常见格式。
- Kimi Claw 可以向用户发送文件。
- Web 端有“工作空间”入口，可以浏览和下载 Kimi Claw 生成的所有文件。
- iOS/Android 端也支持文件管理。
- 如果配置了飞书机器人，可以在飞书中要求机器人把生成文件发回来。

来源：[Kimi Claw 文件收发](https://www.kimi.com/zh-cn/help/kimi-claw/file-transfer)

Kimi Claw 的记忆文档还提到：

- OpenClaw 会定期重置对话上下文。
- 重要信息要写入 Memory。
- Memory 存储在工作空间中，可以查看和下载。
- 会员到期后云主机会保留一定时间。
- 团队正在开发记忆备份能力。

来源：[Kimi Claw 记忆丢失与上下文保存](https://www.kimi.com/zh-cn/help/kimi-claw/memory-loss)

Kimi Claw 的终端命令文档提到：

- `/file` 或 `/upload` 可以查看/管理已上传文件列表。
- `/memory export` 可以导出记忆文件。
- `/cron log` 可以查看定时任务执行日志。

来源：[Kimi Claw 常见终端命令](https://www.kimi.com/zh-cn/help/kimi-claw/concepts)

### 4.2 产品层洞察

Kimi 的文件体系最值得学习的一点是：**文件不是单一入口，而是多入口统一资产。**

```text
对话里上传
工作空间里浏览
移动端查看
飞书机器人取回
命令行管理
Memory 导出
定时任务日志查看
```

这背后的产品模型应该是：

```text
文件资产归属于 Kimi Claw 工作空间；
不同入口只是访问同一份资产的不同方式。
```

这对 ClawHub 非常关键。我们现在已经有：

```text
Web UI
云边通道
飞书入口验证
定时任务
容器内 QwenPaw
```

如果每个入口都各自处理文件，系统会很快失控。正确做法应该是：

```text
统一文件资产层
  Web 上传的文件
  IM 上传的文件
  云边任务生成的文件
  定时任务生成的文件
  Skill 生成的文件
  容器内工作目录文件
```

都登记到一个统一的文件资产表里。

### 4.3 Kimi 对“文件”和“记忆”的处理启发

Kimi 把 Memory 放在工作空间中，说明文件和记忆不是完全分离的。

对 Agent 来说，文件可以分为两类：

```text
任务文件
  用户上传的 Excel、PDF、图片、代码包。

认知文件
  MEMORY、AGENTS、USER、角色设定、偏好、长期规则。
```

ClawHub 文件管理如果只管任务文件，不管认知文件，就会缺一块关键能力。后续可以设计两个视图：

```text
文件空间
  给用户看任务文件、产物文件、上传文件。

记忆与配置空间
  给高级用户或管理员看 Memory、Agent 配置、通道配置。
```

MVP 可以先隐藏第二类，只在备份、迁移和恢复里处理。

## 5. ArkClaw 洞察

### 5.1 公开资料明确说明

公开评测资料称，ArkClaw 使用火山引擎 TOS 对象存储作为文件系统，支持把本地文件上传到云端，让 AI 直接读取和分析。对于内容创作者和研究人员，这能减少手动复制粘贴大量文本。

ArkClaw 也强调飞书深度集成，可以创建、编辑飞书文档，操作多维表格，提取会议纪要并推送总结。

来源：[ArkClaw Review](https://openclawai.net/blog/arkclaw-review)

另一个 ArkClaw 介绍页强调它是托管工作空间，用户不需要关心 Docker、环境变量和维护。

来源：[ArkClaw Managed OpenClaw](https://arkclaw.lol/)

### 5.2 产品层洞察

ArkClaw 的文件能力不是“云盘”，而是更偏企业办公资产：

```text
对象存储
飞书文档
多维表格
会议纪要
定时总结
群聊推送
```

这意味着它的文件管理重点不是“浏览目录”，而是“让 Agent 进入企业内容流”。

企业用户关心的问题会变成：

```text
这个文件来自哪里？
谁上传的？
谁可以读？
Agent 什么时候读过？
是否外发过？
是否包含敏感信息？
是否进入了模型上下文？
是否被定时任务重复处理？
```

### 5.3 对 ClawHub 的启发

如果 ClawHub 面向企业客户，文件管理必须天然考虑：

```text
租户隔离
用户隔离
实例隔离
云边隔离
文件权限
访问审计
敏感信息扫描
外发审批
生命周期策略
```

尤其云边场景里，文件可能在三处存在：

```text
ClawHub 云端对象存储
云端 QwenPaw 容器工作目录
客户边侧 QwenPaw 工作目录
```

这时文件管理不只是“文件列表”，而是“文件流转治理”。

建议 ClawHub 从一开始就给文件资产增加来源字段：

```text
source_type:
  WEB_UPLOAD
  CHAT_UPLOAD
  IM_UPLOAD
  CLOUD_CONTAINER_OUTPUT
  EDGE_OUTPUT
  CRON_OUTPUT
  SKILL_OUTPUT
  SYSTEM_BACKUP
```

以及位置字段：

```text
storage_location:
  MINIO
  CLOUD_CONTAINER
  EDGE_NODE
  EXTERNAL_DOC
```

这样后续才有机会支撑企业审计。

## 6. MaxClaw 洞察

### 6.1 公开资料明确说明

MiniMax 的 MaxClaw 页面明确强调：

- 10 秒部署。
- 不需要服务器、Docker、API Key。
- 新用户获得 50GB 云存储。
- 云存储用于长期记忆、文件管理和多设备协作。
- 内置文件操作、浏览器操作、代码执行、图像/视频生成等工具。
- 可以连接 Telegram、Discord、Slack。

来源：[MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)

MaxClaw 介绍页也提到：

- MaxClaw 是云托管 Agent。
- 支持 long-term memory。
- 支持 file analysis。
- 支持 web browsing、code execution、automation scripts、schedule management。

来源：[MaxClaw by MiniMax](https://maxclaw.ai/)

### 6.2 产品层洞察

MaxClaw 对文件管理的包装方式很值得学习。它没有强调“上传下载”，而是把文件管理归入：

```text
Cloud Workspace
Long-Term Memory
Multi-device Collaboration
Built-in Tool Ecosystem
```

这说明对普通用户来说，文件管理不是一个功能点，而是“我的 Agent 记得我、能处理我的资料、能跨设备继续工作”的基础设施。

### 6.3 对 ClawHub 的启发

ClawHub 的文件管理可以分两种叙事：

面向普通用户：

```text
龙虾工作空间
文件空间
任务产物
长期记忆
跨设备访问
```

面向管理员或企业客户：

```text
对象存储
持久化目录
权限策略
审计日志
备份恢复
生命周期规则
```

UI 上不要一上来讲 MinIO、容器路径、挂载目录。用户只需要知道：

```text
我上传的文件在哪里？
龙虾生成的文件在哪里？
这个文件对应哪个任务？
我能不能下载？
我能不能让龙虾继续处理？
这个文件会保存多久？
```

## 7. 文件类型分层

建议 ClawHub 不要把所有文件混在一个列表里，而是从产品上分成五类：

| 类型 | 示例 | 用户感知 | 是否进入 Agent 上下文 |
|---|---|---|---|
| 输入文件 | 用户上传的 PDF、Excel、图片、代码包 | 给龙虾处理的材料 | 可选 |
| 产物文件 | 报告、PPT、Excel、截图、日志包 | 龙虾完成任务的结果 | 通常不自动进入 |
| 工作文件 | 中间脚本、临时数据、缓存 | 任务过程文件 | 默认隐藏 |
| 记忆文件 | MEMORY、偏好、用户档案 | 龙虾长期记忆 | 需要受控进入 |
| 系统文件 | 配置、密钥、通道凭证、备份包 | 系统维护资产 | 禁止进入普通对话 |

这五类文件的权限和展示策略不一样。

如果不做分层，后面会遇到两个问题：

- 用户看到一堆系统文件，体验很乱。
- Agent 可能误读敏感配置或系统文件，带来安全风险。

## 8. ClawHub 推荐产品形态

### 8.1 一级菜单

建议保留左侧“文件”菜单，但它不应该只是文件浏览器。

可以命名为：

```text
文件
```

进入后分三个视图：

```text
全部文件
任务产物
上传文件
```

后续高级版再增加：

```text
记忆文件
备份文件
云边文件
```

### 8.2 龙虾内文件空间

在“我的龙虾”卡片或对话页里，应有与当前龙虾绑定的文件入口：

```text
当前龙虾的文件
当前会话的文件
当前任务的产物
```

这比全局文件列表更符合用户心智。

### 8.3 对话中的文件体验

用户在对话中上传文件时，系统应该自动做三件事：

```text
1. 上传到对象存储或实例工作目录
2. 登记文件资产表
3. 在当前会话中生成一个文件消息卡片
```

文件卡片至少包含：

```text
文件名
文件类型
文件大小
上传时间
来源
下载按钮
让龙虾处理按钮
```

如果是 Agent 生成的产物，卡片应显示：

```text
由哪个任务生成
生成时间
关联会话
下载
继续处理
发送到 IM
```

### 8.4 任务产物视图

这是最值得做的差异化。

不要让用户自己翻目录找文件，而是按任务聚合：

```text
任务：整理本周销售数据
  输入：
    sales.xlsx
  产物：
    sales_report.docx
    sales_chart.png
    summary.md
  执行日志：
    run.log
```

对定时任务也一样：

```text
任务：每天 9 点生成日报
  2026-05-11
    daily_report.md
    daily_report.xlsx
  2026-05-12
    daily_report.md
    daily_report.xlsx
```

这比普通文件树更适合 Agent 产品。

## 9. ClawHub 推荐技术架构

建议文件管理采用“三层存储模型”：

```text
元数据层：ClawHub 数据库
  记录文件归属、来源、权限、状态、关联会话和任务。

对象层：MinIO / OSS / TOS
  存放用户上传文件、任务产物、备份包。

运行层：QwenPaw 容器或边侧节点工作目录
  存放 Agent 执行时真实可访问的文件。
```

不要把“容器文件系统”直接当成唯一文件系统。原因是：

- 容器可能重建。
- 文件需要跨实例下载。
- 文件需要通过 IM 发送。
- 文件需要审计和生命周期管理。
- 云边文件可能不在云端容器里。

更合理的设计是：

```text
ClawHub 管元数据和对象存储；
QwenPaw 管运行时读写；
两者通过文件同步或任务输入输出协议衔接。
```

## 10. 推荐数据模型

### 10.1 文件资产表

```text
file_asset
  id
  tenant_id
  user_id
  instance_id
  edge_node_id
  session_id
  task_id
  cron_task_id
  file_name
  display_name
  file_ext
  mime_type
  size
  sha256
  category
  source_type
  storage_location
  object_key
  container_path
  edge_path
  visibility
  status
  created_at
  updated_at
  expires_at
```

### 10.2 文件事件表

```text
file_event
  id
  file_id
  tenant_id
  user_id
  event_type
  actor_type
  actor_id
  detail
  created_at
```

事件类型：

```text
UPLOAD
DOWNLOAD
READ_BY_AGENT
GENERATED_BY_AGENT
SENT_TO_IM
SYNC_TO_EDGE
SYNC_FROM_EDGE
DELETE
RESTORE
BACKUP
```

### 10.3 文件关系表

用于表达输入和产物关系：

```text
file_relation
  id
  from_file_id
  to_file_id
  relation_type
  task_id
  created_at
```

关系类型：

```text
INPUT_TO_OUTPUT
DERIVED_FROM
VERSION_OF
BACKUP_OF
```

## 11. 云边场景下的文件管理

ClawHub 后续要做云边协同，所以文件管理必须提前考虑“文件在哪里”。

### 11.1 云端文件

```text
用户通过 Web 上传
云端 QwenPaw 处理
产物存回 MinIO
用户下载或继续对话
```

### 11.2 边侧文件

边侧在客户机房，文件可能不能上传云端，或者只能上传摘要和结果。

需要支持三种策略：

```text
全量同步
  文件可以从边侧上传到云端对象存储。

结果同步
  只上传执行结果、报告、日志，不上传原始输入。

引用同步
  云端只保存文件引用和元数据，原文件留在边侧。
```

文件资产表需要能表达：

```text
这个文件真实在边侧；
云端只有索引；
用户请求下载时，需要边侧在线；
如果边侧离线，只能查看历史元数据。
```

### 11.3 云边文件安全

云边场景一定要避免默认全量上传客户文件。

建议设计权限策略：

```text
边侧文件默认不出客户机房。
只有任务产物或用户明确授权的文件可以上传云端。
敏感文件上传前需要脱敏或审批。
```

这可以成为 ClawHub 的企业卖点。

## 12. 安全与审计

Agent 文件管理比普通网盘更危险，因为 Agent 会主动读写文件。

必须关注：

```text
敏感信息泄露
Prompt Injection 文件诱导
Agent 误删文件
Agent 外发文件
第三方 Skill 读取文件
边侧客户数据越界上传
```

建议 MVP 至少做：

- 文件归属隔离。
- 下载鉴权。
- 删除二次确认。
- 系统文件不展示给普通用户。
- `.secret` 永不进入文件管理。
- Agent 读取文件要记录事件。
- 文件外发到 IM 要记录事件。

后续企业版再做：

- 敏感信息扫描。
- 文件外发审批。
- 文件水印。
- 文件生命周期策略。
- 文件访问审计报表。
- Skill 文件访问白名单。

## 13. 文件生命周期

不同文件的保存周期应该不同：

| 类型 | 建议策略 |
|---|---|
| 用户上传输入文件 | 默认长期保留，可手动删除 |
| Agent 产物文件 | 默认长期保留，随任务归档 |
| 临时工作文件 | 短期保留，自动清理 |
| 日志文件 | 保留 7-30 天 |
| 备份文件 | 按套餐或策略保留 |
| 边侧文件引用 | 元数据保留，原文件不保证可下载 |

这也是产品套餐设计的基础：

```text
免费版：较小文件空间，短保留周期
专业版：更大文件空间，长期保留
企业版：审计、备份、合规保留
```

## 14. MVP 建议

第一版不要贪大，建议实现：

### 14.1 用户功能

- 文件菜单。
- 按龙虾实例查看文件。
- 上传文件。
- 下载文件。
- 删除文件。
- 查看任务产物。
- 对话中展示上传文件卡片。
- 对话中展示产物文件卡片。

### 14.2 系统功能

- 文件元数据入库。
- 文件存 MinIO。
- 文件关联 instance/session/task。
- QwenPaw 容器可读取上传文件。
- QwenPaw 生成产物后回传 ClawHub 登记。
- 文件下载鉴权。

### 14.3 暂不做

- 多版本文件。
- 在线预览 Office。
- 协同编辑。
- 全文搜索。
- 敏感信息扫描。
- 边侧文件全量同步。
- 文件水印。

## 15. 推荐演进路线

### V0：可用

```text
上传 / 下载 / 删除
文件关联龙虾和会话
任务产物登记
MinIO 存储
```

### V1：好用

```text
任务产物视图
定时任务产物归档
文件卡片
文件发送到 IM
文件继续处理
```

### V2：可信

```text
权限策略
审计日志
敏感扫描
外发审批
生命周期管理
```

### V3：云边

```text
边侧文件索引
边侧结果回传
云边文件同步策略
离线文件状态
客户机房数据不出域策略
```

## 16. 结论

四家 Claw 产品共同透露出一个趋势：

```text
文件管理不是网盘，而是 Agent 工作空间。
```

JVS Claw 强调 ClawSpace 和任务文件空间，说明文件是云端执行环境的一部分。

Kimi Claw 强调对话、工作空间、飞书机器人、Memory，说明文件是多入口协作和长期记忆的桥梁。

ArkClaw 强调对象存储和飞书文档，说明文件管理会进入企业办公资产治理。

MaxClaw 强调 50GB Cloud Workspace 和长期记忆，说明文件是托管 Agent 长期上下文的一部分。

因此，ClawHub 的文件管理应按这个方向设计：

```text
以龙虾工作空间为中心；
以任务产物为主线；
以对象存储为底座；
以会话和任务为索引；
以权限和审计为护城河；
为云边文件流转预留模型。
```

如果只做一个“文件列表 + 上传下载”，短期能交付，但很快会挡住后面的定时任务、云边协同、Skill 产物、企业审计和备份恢复。

## 17. 参考资料

- [JVS Claw 功能介绍](https://docs-jvs.wuying.com/zh/docs/intro/feature/)
- [JVS Claw 全面开放公告](https://docs-jvs.wuying.com/zh/blog/v2.0.0/)
- [JVS Claw 计费说明](https://docs-jvs.wuying.com/zh/docs/billing/)
- [Kimi Claw 文件收发](https://www.kimi.com/zh-cn/help/kimi-claw/file-transfer)
- [Kimi Claw 记忆丢失与上下文保存](https://www.kimi.com/zh-cn/help/kimi-claw/memory-loss)
- [Kimi Claw 常见终端命令](https://www.kimi.com/zh-cn/help/kimi-claw/concepts)
- [ArkClaw Review](https://openclawai.net/blog/arkclaw-review)
- [ArkClaw Managed OpenClaw](https://arkclaw.lol/)
- [MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)
- [MaxClaw by MiniMax](https://maxclaw.ai/)
