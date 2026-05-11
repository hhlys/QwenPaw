# 云端龙虾升级与持久化数据洞察

日期：2026-05-11

## 1. 背景

ClawHub 当前正在从“云端 QwenPaw 容器管理平台”逐步演进为“云端龙虾智能体托管平台”。在这个阶段，升级和持久化是两个绕不开的问题：

- 用户创建的是“龙虾”，但底层实际是 QwenPaw 容器、镜像、工作目录、密钥目录、模型配置、插件和依赖。
- 如果只持久化工作目录，换镜像重建容器后，用户在容器内安装的 Python 依赖、系统工具、浏览器状态、插件缓存等可能丢失。
- 如果直接在容器内热升级 wheel 包，用户环境不丢，但容器运行态会逐渐漂移，回滚和排障难度增加。

因此，需要参考 JVS Claw、Kimi Claw、ArkClaw、MaxClaw 等同类产品的产品语义和技术取舍，形成适合 ClawHub 的升级与持久化设计。

本文区分两类信息：

- **公开资料明确说明**：来自产品文档、帮助中心、新闻或产品页。
- **基于产品形态的推断**：公开资料没有直接说明，但可以从功能设计和用户体验反推出可能的实现方式。

## 2. 总体结论

同类产品几乎都在隐藏 Docker、镜像、API Key、插件版本等技术复杂度。用户看到的是：

- 创建龙虾
- 进入对话
- 工作空间
- 记忆
- 定时任务
- 修复
- 升级
- 备份或恢复

用户不应该直接感知：

- 镜像 tag
- 容器 ID
- 挂载目录
- wheel 包
- Python site-packages
- Docker volume
- QwenPaw 内部配置路径

对 ClawHub 来说，合理的方向不是做成 Docker 面板，而是做成：

```text
龙虾智能体托管平台
  = 实例生命周期管理
  + 工作空间持久化
  + 应用升级
  + 插件兼容管理
  + 修复与回滚
  + 云边协同
```

## 3. 竞品对比

| 产品 | 产品定位 | 升级用户感知 | 持久化用户感知 | 对 ClawHub 的启发 |
|---|---|---|---|---|
| JVS Claw | 云端 CloudSpace + 可视化执行环境 | 一键升级，能力进化无需重建 | 文件空间、CloudSpace、任务历史 | 强调“云端环境长期存在”，升级不能让用户感觉龙虾被重建 |
| Kimi Claw | Kimi 生态内的托管 OpenClaw | 不建议手动升级，等待官方统一推送 | 工作空间和记忆保留，配置可能需重配 | 强版本兼容矩阵，禁止用户随意升级插件 |
| ArkClaw | 火山引擎 SaaS + 飞书/钉钉办公入口 | 平台自动维护，用户不管服务器 | 云端托管，强调免运维和安全 | 企业 SaaS 化，用户只关心工作流和安全 |
| MaxClaw | MiniMax 模型驱动的托管 Agent 平台 | 官方托管、自动维护 | 50GB 云工作空间、长期记忆 | 低成本模型 + 开箱即用 + 多 IM 入口 |

## 4. JVS Claw 洞察

### 4.1 公开资料明确说明

JVS Claw 在全面开放公告中提到：

- JVS 文件空间上线，提供任务文件专属存储空间。
- 定时任务升级，新增定时任务入口。
- Skill 调用优化，新增 skill 开关能力。
- Clawbot 支持一键升级，能力进化无需重建。

来源：[JVS Claw 全面开放公告](https://docs-jvs.wuying.com/zh/blog/v2.0.0/)

JVS 的离线修复文档也说明了云端 Bot 的修复路径：

- 先在对话里确认是否可聊。
- 如果不能聊，进入 CloudSpace，尝试重启 CloudSpace。
- 如果 CloudSpace 内也不能聊，在 terminal 执行 `openclaw doctor --fix`，再重启。
- 仍不能恢复时，备份配置后删除配置文件并重启。
- 最后才考虑删除 Bot 重建或联系客服。

来源：[JVS Claw 机器人离线修复](https://docs-jvs.wuying.com/zh/docs/handbook/offline/)

### 4.2 产品语义

JVS Claw 的关键词不是“容器”，而是：

```text
CloudSpace
文件空间
定时任务
Skill
一键升级
修复
```

这说明它更强调“一个可持续存在的云端工作环境”，而不是“一个可随时销毁的容器”。

### 4.3 对 ClawHub 的启发

ClawHub 的云端龙虾不应只是 `docker run qwenpaw:local` 的结果，而应该包装成长期资源：

```text
龙虾实例
  - 对话
  - 工作空间
  - 文件
  - 记忆
  - 定时任务
  - 技能
  - 模型配置
  - 通道配置
```

升级按钮的语义也不应该是“换镜像”，而应该是：

```text
升级龙虾能力
```

底层可以热升级 wheel，也可以换镜像重建，但用户不需要知道。

## 5. Kimi Claw 洞察

### 5.1 公开资料明确说明

Kimi Claw 的升级注意事项非常关键：

- 不要手动升级 OpenClaw 版本。
- 手动升级或开启自动更新可能导致 Kimi 插件失效，微信、飞书、企微、微博等插件也可能不可用。
- 应等待官方升级推送。
- 误升级后可以恢复初始设置。
- 恢复时工作空间和记忆会保留，但聊天机器人配置需要重新配置。

来源：[Kimi Claw 升级注意事项](https://www.kimi.com/zh-cn/help/kimi-claw/upgrade-notice)

Kimi Claw 的记忆文档说明：

- 记忆文件存储在工作空间中。
- 会员到期后云主机会保留一段时间。
- 团队正在开发记忆备份能力。

来源：[Kimi Claw 记忆丢失与上下文保存](https://www.kimi.com/zh-cn/help/kimi-claw/memory-loss)

### 5.2 产品语义

Kimi Claw 非常强调“不要用户自行升级”。这背后反映出一个事实：

```text
OpenClaw 主程序
Kimi 插件
微信插件
飞书插件
企微插件
微博插件
模型配置
工作空间
长期记忆
```

这些组件之间存在版本兼容关系。用户自己升级其中一块，可能导致整个龙虾不可用。

### 5.3 对 ClawHub 的启发

ClawHub 应该建立“版本兼容矩阵”，而不是让用户自由选择升级包：

```text
qwenpaw_version
image_version
custom_channel_version
cloud_edge_protocol_version
feishu_channel_version
model_provider_config_version
workspace_schema_version
```

升级前先判断：

- 当前版本是否可升级到目标版本。
- 是否需要备份。
- 是否需要重启 QwenPaw 进程。
- 是否需要重建容器。
- 是否需要用户重新配置通道。
- 是否支持回滚。

Kimi 的思路对 ClawHub 很重要：**升级是平台行为，不是用户自由操作。**

## 6. ArkClaw 洞察

### 6.1 公开资料明确说明

公开新闻资料显示，ArkClaw 是字节火山引擎推出的云端 SaaS 版 OpenClaw，强调：

- 开箱即用。
- 云端部署。
- 打开网页即可使用 24/7 在线助手。
- 支持 Doubao、Kimi、MiniMax、GLM 等模型。
- 支持主流即时通讯应用，并适配飞书插件。
- 内置安全扫描，降低数据泄露风险。

来源：[CnTechPost - ByteDance joins OpenClaw race with launch of cloud-based ArkClaw](https://cntechpost.com/2026/03/09/bytedance-joins-openclaw-race-launch-cloud-based-arkclaw/)

### 6.2 产品语义

ArkClaw 的重点不是开放性，而是：

```text
企业 SaaS
免运维
飞书/钉钉办公入口
云端安全
火山引擎生态
```

这说明它更像“企业办公智能体托管服务”，而不是“给开发者使用的 OpenClaw 自托管工具”。

### 6.3 对 ClawHub 的启发

如果 ClawHub 要面向企业客户，升级与持久化不能只解决技术问题，还要解决企业信任问题：

- 实例隔离
- 操作日志
- 高危命令审批
- 文件外发审计
- Skill 安装审计
- 模型 Key 托管
- 备份恢复
- 用户/租户隔离
- 云边节点绑定

ArkClaw 给我们的启发是：**云端龙虾平台要有企业安全叙事。**

升级能力也应该纳入安全体系：

```text
升级前备份
升级包签名
升级包来源校验
升级过程日志
升级失败回滚
升级后健康检查
```

## 7. MaxClaw 洞察

### 7.1 公开资料明确说明

MaxClaw 的产品页强调：

- 10 秒部署。
- 无服务器、无 Docker、无 API Key。
- 基于 MiniMax 模型。
- 50GB 云工作空间。
- 支持长期记忆、文件管理、多设备协作。
- 支持 Telegram、Discord、Slack。
- 内置工具生态，包括图片/视频生成、文件操作、浏览器操作等。
- 官方托管和自动维护。

来源：[MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)

### 7.2 产品语义

MaxClaw 的差异点更偏模型与成本：

```text
低成本模型
长上下文
高频自动化
托管 Agent runtime
多 IM 入口
专家型 Agent
```

相比 JVS 的 CloudSpace 可视化、Kimi 的浏览器生态、ArkClaw 的企业办公生态，MaxClaw 更像“MiniMax 模型驱动的托管 Agent 平台”。

### 7.3 对 ClawHub 的启发

MaxClaw 提醒我们：创建龙虾之后要“立刻可用”。

这意味着 ClawHub 需要默认预置：

- 可用模型。
- 工作空间。
- 长期记忆。
- 文件管理。
- 默认技能。
- 默认通道。
- 默认角色模板。

用户不应该在创建后再配置 API Key、模型 provider、镜像版本、容器端口。

产品上应该说：

```text
创建一只研发助手龙虾
创建一只运维助手龙虾
创建一只数据分析龙虾
创建一只运营助手龙虾
```

而不是：

```text
创建一个 qwenpaw:local 容器
```

## 8. 升级方案对比

### 8.1 方案一：换镜像重建容器

流程：

```text
拉取新镜像
停止旧容器
删除旧容器
用新镜像创建新容器
挂回持久化目录
启动健康检查
```

优点：

- 符合 Docker 标准使用方式。
- 环境干净，可重复。
- 回滚简单，切回旧镜像即可。
- 适合系统依赖、基础镜像、安全补丁升级。

缺点：

- 有停机。
- 如果持久化范围不足，用户安装的依赖会丢。
- 用户运行态可能被重置。
- 需要严格设计数据目录、密钥目录、运行时扩展目录。

适合：

- 大版本升级。
- 基础镜像升级。
- 系统依赖升级。
- 安全漏洞修复。
- 容器环境严重损坏时的重建。

### 8.2 方案二：容器内应用热升级

流程：

```text
上传 qwenpaw wheel 或升级包
进入容器执行升级命令
替换 QwenPaw 应用层
重启 QwenPaw 进程
健康检查
```

优点：

- 不重建容器。
- 用户安装的 Python 依赖、工具、缓存不容易丢。
- 停机时间短。
- 更接近 JVS/Kimi 这类“能力升级无需重建”的用户感知。

缺点：

- 容器环境会逐渐漂移。
- 失败后排障复杂。
- 多实例一致性弱。
- 回滚需要额外记录旧 wheel 和配置快照。
- 如果升级涉及系统依赖，热升级无法覆盖。

适合：

- 小版本升级。
- QwenPaw 应用层升级。
- custom-channel 插件升级。
- UI 静态资源升级。
- 快速补丁。

### 8.3 方案三：声明式恢复运行时

流程：

```text
持久化 requirements.txt / skills_manifest.json / tools_manifest.json
重建容器
启动时自动恢复依赖、技能和工具
```

优点：

- 环境可审计。
- 可复现。
- 避免直接保存一坨不可控 site-packages。

缺点：

- 恢复慢。
- 依赖外部网络或私有包仓库。
- 客户环境离线时复杂。

适合：

- 企业环境。
- 边侧部署。
- 可控私有仓库。
- 需要合规审计的客户。

### 8.4 方案四：运行时扩展目录持久化

流程：

```text
持久化 /root/.qwenpaw-runtime
将用户安装的 Python 包、工具、插件缓存放进去
重建容器后重新挂载
```

推荐目录：

```text
/root/.qwenpaw              工作空间、会话、记忆、任务数据
/root/.qwenpaw.secret       密钥、模型 Key、通道凭证
/root/.qwenpaw-runtime      用户安装依赖、插件缓存、工具缓存
```

优点：

- 换镜像重建时用户依赖不丢。
- 比热升级更干净。
- 比声明式恢复更快。

缺点：

- Python ABI、系统库版本变化时可能不兼容。
- 长期积累后目录可能膨胀。
- 需要定期清理和兼容检查。

适合：

- 当前 ClawHub 的中期方案。
- 用户依赖多但不想每次恢复。
- 需要兼顾产品体验和工程复杂度。

## 9. 推荐给 ClawHub 的升级分层

建议把升级拆成三层，而不是只提供一个“升级”按钮：

```text
应用层升级
  - QwenPaw wheel
  - console 静态资源
  - custom-channel
  - 小版本补丁

运行时层升级
  - 用户依赖
  - skills
  - plugins
  - browser profile
  - runtime cache

环境层升级
  - 基础镜像
  - Python / Node.js
  - Chromium
  - apt 包
  - supervisor / entrypoint
```

用户 UI 上只看到：

```text
升级
修复
备份
恢复初始设置
```

后台根据升级包类型决定执行哪种策略：

| 升级类型 | 后台策略 | 用户感知 |
|---|---|---|
| 小版本应用升级 | 容器内热升级 wheel | 短暂重启 |
| custom-channel 升级 | 替换插件目录并重载 | 通道能力升级 |
| 安全补丁 | 视补丁类型决定热升级或重建 | 安全增强 |
| 基础环境升级 | 换镜像重建容器 | 需要更长升级时间 |
| 大版本升级 | 备份后重建，必要时迁移数据 | 版本升级完成 |

## 10. 推荐持久化范围

只持久化 `.qwenpaw` 和 `.qwenpaw.secret` 不够。

建议 ClawHub 标准化三类目录：

```text
/root/.qwenpaw
  - workspace
  - sessions
  - memory
  - cron jobs
  - uploaded files
  - generated files

/root/.qwenpaw.secret
  - model provider secrets
  - channel credentials
  - cloud-edge token
  - user private config

/root/.qwenpaw-runtime
  - pip target packages
  - npm/global tools if needed
  - skill/plugin caches
  - browser profile/cache if needed
  - user installed tools manifest
```

容器启动时设置：

```bash
QWENPAW_WORKING_DIR=/root/.qwenpaw
QWENPAW_SECRET_DIR=/root/.qwenpaw.secret
QWENPAW_RUNTIME_DIR=/root/.qwenpaw-runtime
```

如果后续支持用户安装 Python 依赖，建议统一安装到 runtime 目录，而不是系统 site-packages。

## 11. 备份策略

备份不应该只在用户手动点击时发生。

建议四类备份：

| 场景 | 是否自动备份 | 说明 |
|---|---|---|
| 用户手动备份 | 是 | 用户主动点击 |
| 升级前 | 强制 | 防止升级失败 |
| 删除前 | 可选但默认建议 | 防误删 |
| 修复前 | 建议 | 防止修复动作破坏配置 |

备份对象：

```text
/root/.qwenpaw
/root/.qwenpaw.secret
/root/.qwenpaw-runtime/manifests
```

是否备份完整 runtime 目录需要谨慎：

- 完整备份恢复快，但体积大。
- 只备份 manifest 更干净，但恢复慢。

建议 MVP：

```text
备份 .qwenpaw 和 .qwenpaw.secret
runtime 先只备份 manifest
后续支持完整 runtime 快照
```

MinIO 对象路径建议：

```text
tenant/{tenantId}/user/{userId}/instances/{instanceId}/backups/{backupId}.tar.gz
```

## 12. 修复能力定义

参考 JVS 和 Kimi，修复不是简单 restart，而是分级动作。

建议 ClawHub 的“修复”定义为：

```text
1. 检查容器是否存在
2. 检查容器是否运行
3. 检查 QwenPaw 进程是否健康
4. 检查端口是否可访问
5. 检查模型配置是否存在
6. 检查工作目录是否可读写
7. 检查 secret 目录是否存在
8. 检查 custom-channel 是否加载
9. 尝试重启 QwenPaw 进程
10. 尝试重建容器但保留数据目录
11. 仍失败则提示恢复初始设置或联系客服
```

可以分成三档：

| 修复档位 | 动作 | 是否破坏数据 |
|---|---|---|
| 轻修复 | 重启进程、重载配置 | 不破坏 |
| 中修复 | 重建容器、保留目录 | 不破坏用户数据 |
| 重修复 | 恢复初始配置、保留工作空间和记忆 | 可能需要重新配置通道 |

## 13. ClawHub 产品建议

### 13.1 UI 文案

用户侧不要出现：

```text
Docker
镜像
容器
端口
挂载目录
wheel
site-packages
```

用户侧应该出现：

```text
龙虾
工作空间
记忆
文件
技能
定时任务
升级
修复
备份
恢复
```

### 13.2 卡片三点菜单

建议保留：

```text
重启
修复
升级
备份
删除
```

如果需要极简，卡片上直接显示：

```text
对话
更多
```

更多菜单里放：

```text
重启
升级
修复
备份
删除
```

### 13.3 升级弹窗

不要让用户选镜像。可以展示：

```text
当前版本：1.0.0
可升级版本：1.0.1
升级类型：应用升级
预计耗时：1 分钟
是否需要重启：是
升级前将自动备份：是
```

高级用户或管理员后台再展示：

```text
image_version
qwenpaw_version
custom_channel_version
protocol_version
```

## 14. ClawHub 技术建议

### 14.1 数据模型

建议增加版本与备份模型：

```text
instance
  - id
  - name
  - user_id
  - tenant_id
  - status
  - image_version
  - qwenpaw_version
  - channel_version
  - runtime_version
  - workspace_schema_version

image_version
  - id
  - image_url
  - qwenpaw_version
  - runtime_version
  - compatible_from
  - compatible_to

upgrade_task
  - id
  - instance_id
  - from_version
  - to_version
  - strategy
  - status
  - backup_id
  - logs

backup
  - id
  - instance_id
  - object_key
  - backup_type
  - status
  - size
```

### 14.2 升级策略枚举

```text
HOT_PATCH
  容器内热升级 wheel/custom-channel

RECREATE_CONTAINER
  换镜像重建容器，挂回数据目录

RESTORE_INITIAL_CONFIG
  恢复初始配置，保留 workspace 和 memory

ROLLBACK
  回滚到上一个版本或备份点
```

### 14.3 健康检查

升级后至少检查：

```text
容器状态
HTTP /api/health
前端静态资源
模型 active 配置
默认 agent 可加载
custom-channel 可加载
最近一次对话可执行
```

## 15. 建议路线图

### MVP

- 保留 `.qwenpaw` 和 `.qwenpaw.secret` 挂载。
- 创建实例时预置模型配置。
- 支持手动备份到 MinIO。
- 支持重启、删除。
- 支持修复：保留数据目录重建容器。
- 支持升级：先采用换镜像重建容器。

### V1

- 增加 `.qwenpaw-runtime`。
- 支持应用层热升级 wheel。
- 支持升级前自动备份。
- 支持升级任务记录和日志。
- 支持失败回滚。
- 增加版本兼容矩阵。

### V2

- 支持灰度升级。
- 支持租户级统一升级。
- 支持插件版本治理。
- 支持 runtime manifest 恢复。
- 支持完整 runtime 快照。
- 支持 AI 自动诊断修复。

## 16. 最终建议

ClawHub 应采用“双轨升级”：

```text
默认：应用热升级
  用于 QwenPaw wheel、custom-channel、小版本补丁。

必要时：环境重建升级
  用于基础镜像、系统依赖、安全补丁、大版本升级。
```

同时持久化分三层：

```text
工作数据：.qwenpaw
密钥数据：.qwenpaw.secret
运行扩展：.qwenpaw-runtime
```

产品上，不要向用户解释 Docker 和镜像。用户只需要知道：

```text
我的龙虾可以升级
我的文件和记忆会保留
升级前会自动备份
失败可以修复或回滚
```

这才更接近 JVS Claw、Kimi Claw、ArkClaw、MaxClaw 共同体现出的产品方向：**托管式智能体平台，而不是容器管理平台。**

## 17. 参考资料

- [JVS Claw 全面开放公告](https://docs-jvs.wuying.com/zh/blog/v2.0.0/)
- [JVS Claw 机器人离线修复](https://docs-jvs.wuying.com/zh/docs/handbook/offline/)
- [Kimi Claw 升级注意事项](https://www.kimi.com/zh-cn/help/kimi-claw/upgrade-notice)
- [Kimi Claw 记忆丢失与上下文保存](https://www.kimi.com/zh-cn/help/kimi-claw/memory-loss)
- [CnTechPost - ByteDance joins OpenClaw race with launch of cloud-based ArkClaw](https://cntechpost.com/2026/03/09/bytedance-joins-openclaw-race-launch-cloud-based-arkclaw/)
- [MiniMax MaxClaw](https://agent.minimax.io/activity/max-claw)
