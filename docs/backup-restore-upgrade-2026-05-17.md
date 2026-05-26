# 备份、恢复、升级方案设计记录（2026-05-17）

## 1. 今日任务定位

今天开始并行推进两个方向：

1. **开源定制解耦任务**
   - 目标：基于 `qwenpaw-trunk` 做通用内核定制能力，`master` 作为产品分支引入内核制品。
   - 当前已验证：模块名称定制、用户目录定制、前端源码迁移到产品分支的最小闭环。
   - 后续继续处理：Agent 人设内容、Skill CLI 名称、日志名称、环境变量名称等通用定制点。

2. **hClaw 备份、恢复、升级方案设计任务**
   - 目标：为 ClawHub 管理的云端 hClaw/QwenPaw 实例设计备份、恢复、升级能力。
   - 当前重点：分析 ArkClaw/OpenClaw/JVS Claw/OpenClaw Cloud 等产品的公开能力和可验证行为，形成可支撑评审的方案。

本文记录第二个方向，方便明天继续。

## 2. 背景与核心问题

ClawHub 当前负责创建和管理云端龙虾实例。用户提出升级诉求：Claw 内核更新很快，平台需要支持实例升级。

设计难点在于：

- 只备份工作目录无法覆盖用户在容器里额外安装的依赖。
- 换镜像重建容器会丢失容器文件系统里的非挂载目录改动。
- 用户可能通过 Agent、Skill、工具调用间接安装依赖，不一定都在标准工作区。
- 云端实例未来可能运行在 Docker 单机，也可能运行在 K8s/DSP/AgentRun 上，需要避免把设计写死。

因此需要区分：

- 数据备份
- 配置备份
- 组件升级
- 系统升级
- 环境快照
- 灾备快照

## 3. ArkClaw/OpenClaw 备份实验结论

用户在 ArkClaw 终端执行：

```bash
openclaw backup create --output /root/hhl_backup1.tar.gz
```

实际输出：

```text
Backup archive: /root/hhl_backup1.tar.gz
Included 1 path:
- state: ~/.openclaw
Skipped 2 paths:
- workspace: ~/.openclaw/workspace (covered by ~/.openclaw)
- workspace: ~/.openclaw/.arkclaw-team/agents/a-mp2rwq2f017tbs/workspace (covered by ~/.openclaw)
Created /root/hhl_backup1.tar.gz
```

结论：

- ArkClaw/OpenClaw 的普通备份是 **应用状态目录备份**。
- 备份核心是 `~/.openclaw`。
- `workspace` 在 `~/.openclaw` 下，因此被 `state` 目录覆盖。
- 没有证据表明普通备份会覆盖 `/opt`、`/usr`、全局 pip/npm/apt 依赖等系统层内容。

对 hClaw 的启发：

- `~/.hclaw` 和 `~/.hclaw.secret` 可以作为普通数据备份的核心范围。
- 普通备份不能承诺恢复用户额外安装在容器系统层的依赖。
- 如果要恢复依赖，需要单独设计环境快照能力。

## 4. ArkClaw 组件升级实验结论

用户在 ArkClaw UI 中看到组件升级：

```text
Agent 团队插件
v2026.5.14 -> v2026.5.15
```

升级前后执行：

```bash
openclaw plugins list
```

diff 结果：

```diff
-│ ArkClaw      │ arkclaw- │ openclaw │ enabled  │ global:arkclaw-team/dist/index.js │ 2026.5.14 │
+│ ArkClaw      │ arkclaw- │ openclaw │ enabled  │ global:arkclaw-team/dist/index.js │ 2026.5.15 │
```

同时在终端中观察到组件文件路径：

```text
/root/.openclaw/extensions/arkclaw-team/skills/arkclaw-team-project-builder/SKILL.md
/root/.openclaw/extensions/arkclaw-team/skills/arkclaw-team-project-builder/scripts/project-builder.py
```

以及远端模板地址：

```text
https://arkclaw-team.tos-cn-beijing.volces.com/templates/agent-templates.json
https://arkclaw-team.tos-cn-beijing.volces.com/templates/project-templates.json
https://arkclaw-team.tos-cn-beijing.volces.com/templates/skill-templates.json
```

结论：

- ArkClaw 的组件升级至少在本次实验中不是换镜像。
- 本次升级对象是一个 global plugin：`arkclaw-team`。
- 加载入口仍然是 `global:arkclaw-team/dist/index.js`。
- 组件主体位于用户态扩展目录：`~/.openclaw/extensions/arkclaw-team`。
- 该组件包含 skills、scripts、templates、远端模板源等内容。

对 hClaw 的启发：

- 组件升级应和系统升级拆开。
- cloud-edge、clawhub-chat、工具护栏、Agent 团队、模型适配器、文件管理等能力可以设计成用户态 extension/plugin。
- 组件升级优先更新 `~/.hclaw/extensions/<component>` 或受管组件目录，不必替换镜像。

## 5. JVS Claw 竞品洞察

目前未发现 JVS Claw 公开提供用户可操作的完整备份/恢复功能。

公开资料更偏向：

- Clawbot 一键升级。
- 文件空间。
- CloudSpace 异常处理。
- 重启、修复。
- 删除 `openclaw.json` 前手动备份。

判断：

- JVS Claw 可能有平台后台灾备能力，但没有在公开文档里作为用户侧“备份恢复”功能显式呈现。
- 它更强调平台托管、一键升级和异常修复。

对 hClaw 的启发：

- 首期可以不把完整环境备份暴露成强产品功能。
- 但升级前的数据保护、失败回滚、修复能力必须作为底层能力存在。

## 6. OpenClaw Cloud 分层备份参考

OpenClaw Cloud 文档中提到两类能力：

1. **OpenClaw Config**
   - 备份配置、模型选择、API Keys、偏好设置。
   - 不影响 files 或 installed software。

2. **Computer TimeMachine**
   - full disk-level backup。
   - 覆盖 files、packages、data、system state。

对 hClaw 的启发：

- 不应把“备份”设计成一个含糊按钮。
- 应拆成配置备份、数据备份、环境快照。
- 只有环境快照才承诺恢复用户安装的依赖和系统状态。

## 7. 关键概念澄清

### 7.1 数据备份

备份受管应用数据，例如：

```text
~/.hclaw
~/.hclaw.secret
workspace
sessions
agents
skills
extensions 配置
模型配置
会话记录
```

特点：

- 快。
- 成本低。
- 易迁移。
- 不覆盖系统层依赖。

### 7.2 组件升级

升级用户态 extension/plugin/skill/channel，例如：

```text
~/.hclaw/extensions/cloud-edge
~/.hclaw/extensions/clawhub-chat
~/.hclaw/skills/*
```

特点：

- 粒度小。
- 风险低。
- 不需要换镜像。
- 参考 ArkClaw 的 global plugin 升级模式。

### 7.3 系统升级

升级 hClaw/QwenPaw 内核、运行时、基础服务等。

可能方式：

- in-place 安装新的 wheel 包。
- 更新前端静态资源。
- 更新内置组件。
- 执行迁移脚本。
- 健康检查。
- 失败回滚。

特点：

- 风险高于组件升级。
- 需要版本兼容检查。
- 升级前必须做数据备份。

### 7.4 环境快照

环境快照是泛称，不等于单一技术。

可实现为：

- Docker 单机：`docker commit` 生成容器快照镜像。
- K8s：PVC 快照或 VolumeSnapshot。
- 云主机：云盘快照。

特点：

- 用于保留用户额外安装的依赖。
- 成本高。
- 粒度粗。
- 可能带入缓存、临时文件、敏感信息。

## 8. PVC 快照、镜像快照、磁盘快照对比

| 类型 | 拍的是谁 | 保存内容 | 是否保留用户装的依赖 | 适用场景 |
|---|---|---|---|---|
| 镜像快照 | 容器文件系统 | 容器里安装的软件、依赖、系统文件改动 | 是，前提依赖在容器文件系统内 | Docker 单机 |
| PVC 快照 | K8s 持久卷 | 挂载卷里的数据 | 否，除非依赖安装到 PVC 内 | K8s 数据持久化 |
| 磁盘快照 | 云盘 | 整块系统盘或数据盘 | 是，前提这些内容在该磁盘上 | 云主机灾备 |

PVC 解决节点漂移问题的方式：

```text
Pod 可以漂移到新节点
数据不绑本地节点目录
PVC 由存储系统重新挂载到新节点
```

但 PVC 只保护挂载进去的数据，不自动保护容器系统层依赖。

## 9. hClaw 初步方案建议

### 9.1 备份能力分层

首期建议实现：

1. **数据备份**
   - 备份 `~/.hclaw`。
   - 备份 `~/.hclaw.secret`。
   - 备份会话、agents、workspace、skills、extensions、模型配置。

2. **升级前自动备份**
   - 每次系统升级前自动生成备份点。
   - 失败时可恢复数据备份。

3. **环境快照作为高级能力**
   - Docker 单机先支持 `docker commit`。
   - K8s/DSP 后续使用 PVC 快照或底层平台快照。
   - 明确标注：环境快照才用于保留用户额外安装的依赖。

### 9.2 升级能力分层

1. **组件升级**
   - 优先落地。
   - 升级 extension/plugin/skill/channel。
   - 参考 ArkClaw global plugin 模型。

2. **系统升级**
   - 升级 hClaw/QwenPaw 内核和前端。
   - 使用升级任务状态机。
   - 执行 pre-check、backup、install、migrate、restart、health-check、rollback。

3. **镜像升级**
   - 不作为默认方案。
   - 仅适合全新环境、无用户自定义依赖、或已完成环境快照的实例。

## 10. 明天继续事项

1. 将今天的结论整理成正式设计文档，建议文件名：
   - `docs/hclaw-backup-restore-upgrade-design.md`

2. 明确 ClawHub 产品能力边界：
   - 普通备份是否只承诺数据目录。
   - 是否提供环境快照。
   - 是否允许用户手动安装依赖。
   - 是否要求依赖通过受管 skill/plugin manifest 安装。

3. 设计 ClawHub 数据模型：
   - backup_jobs
   - backup_artifacts
   - upgrade_packages
   - upgrade_jobs
   - component_versions
   - environment_snapshots

4. 设计升级任务状态机：
   - PENDING
   - PRECHECKING
   - BACKING_UP
   - INSTALLING
   - MIGRATING
   - RESTARTING
   - HEALTH_CHECKING
   - COMPLETED
   - FAILED
   - ROLLING_BACK
   - ROLLED_BACK

5. 继续开源定制任务：
   - Agent 人设内容定制。
   - Skill CLI 名称兼容策略。
   - 日志名称定制。
   - 环境变量名称定制。

