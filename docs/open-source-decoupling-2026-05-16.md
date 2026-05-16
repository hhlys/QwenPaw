# hClaw 开源解耦工作记录 2026-05-16

## 背景

当前 hClaw 基于 QwenPaw 源码做侵入式定制，存在开源合规、上游合入、内核切换和长期维护成本问题。

本轮目标是探索一种更清晰的分层方式：

- `qwenpaw-trunk`：基于 QwenPaw v1.1.7 的内核分支，只提供通用内核能力和必要扩展点。
- `master`：hClaw 产品分支，引入 `qwenpaw-trunk` 构建出的 wheel/lib，在产品层实现启动命令、前端、人设、产品配置等定制。

核心原则：

- trunk 不做产品化脚手架，不知道 hClaw/lClaw 等产品名。
- master 可以定制产品名、启动命令、用户目录、前端、人设和产品工程能力。
- 运行时仍是一个进程：`hclaw` 启动器导入并组合 `qwenpaw` 内核，而不是再启动一个独立 qwenpaw 进程。

## 当前分支与目录

- QwenPaw trunk 分支：`D:\home\github\QwenPaw`，当前分支 `qwenpaw-trunk`。
- hClaw master worktree：`D:\home\github\QwenPaw\.worktrees\hclaw-master`，当前分支 `master`。

## 已完成工作

### 1. trunk 构建内核 wheel

在 `qwenpaw-trunk` 新增了内核 wheel 构建脚本：

- `scripts/build_core_wheel.ps1`
- `scripts/build_core_wheel.sh`

构建产物输出到：

```text
dist-core/qwenpaw-1.1.7-py3-none-any.whl
```

该 wheel 作为内核 lib 被 master 产品分支安装和复用。

### 2. master 产品层最小启动闭环

在 `master` worktree 中新增了 hClaw 产品层：

- `pyproject.toml`
- `README.md`
- `src/hclaw/__init__.py`
- `src/hclaw/app.py`
- `scripts/build_product.ps1`
- `scripts/build_frontend.ps1`

产品启动命令为：

```powershell
hclaw app --host 127.0.0.1 --port 8088
```

运行关系：

```text
hclaw.exe
  -> hclaw.app:cli
  -> 设置产品层环境变量
  -> 导入 qwenpaw 内核 CLI
  -> 启动 qwenpaw FastAPI / runner / channel 等能力
```

### 3. 模块名称定制

已验证产品层可以提供自己的命令名：

```text
hclaw --version
=> hClaw, version 0.1.0 (qwenpaw core 1.1.7)
```

```text
hclaw --help
=> Usage: hclaw [OPTIONS] COMMAND [ARGS]...
```

trunk 提供的最小扩展点：

- `src/qwenpaw/cli/metadata.py`

该文件只负责 Click CLI 的显示元数据覆盖，包括命令名、help 文案和 version 文案。它不生成产品项目，也不编码任何产品名。

### 4. 用户目录定制

hClaw 产品层已在导入 qwenpaw 内核前设置：

```text
QWENPAW_WORKING_DIR=~/.hclaw
QWENPAW_SECRET_DIR=~/.hclaw.secret
```

验证结果：

```text
WORKING_DIR= C:\Users\11204\.hclaw
SECRET_DIR= C:\Users\11204\.hclaw.secret
```

这样 hClaw 的用户数据、工作区、模型密钥等不会落到默认的 `~/.qwenpaw` 和 `~/.qwenpaw.secret`。

### 5. 前端定制路径

master 分支已复制一份 QwenPaw 前端源码到：

```text
web/console
```

构建输出到：

```text
web/dist
```

hClaw 启动时会把：

```text
QWENPAW_CONSOLE_STATIC_DIR=<master>/web/dist
```

设置到环境变量中，让 qwenpaw 内核服务 master 产品层的前端资源。

当前前端仍基本是 QwenPaw 原始前端，后续可在 master 分支直接重写或逐步替换为 hClaw 前端。

## 已讨论但尚未实施

### 1. Agent 人设内容定制

QwenPaw 的人设主要由以下 Markdown 文件组成：

```text
AGENTS.md
SOUL.md
PROFILE.md
```

默认模板在 trunk 中：

```text
src/qwenpaw/agents/md_files/<language>/
```

运行时会复制到工作区，例如 hClaw 下：

```text
~/.hclaw/workspaces/default/AGENTS.md
~/.hclaw/workspaces/default/SOUL.md
~/.hclaw/workspaces/default/PROFILE.md
```

推荐方案：

- trunk 保留 QwenPaw 默认模板。
- master 提供 hClaw 自己的模板目录，例如 `templates/agents/zh/`。
- hClaw 首次初始化或启动时，将产品模板复制到 `~/.hclaw/workspaces/default/`。

暂未实施。

### 2. Skill CLI 名称定制

已发现内置 skill 中存在大量硬编码 `qwenpaw` 命令，例如：

- `qwenpaw cron ...`
- `qwenpaw chats list`
- `qwenpaw channels send`
- `qwenpaw agents chat`
- `which qwenpaw`

如果产品只提供 `hclaw` 命令，不保留 `qwenpaw` 兼容入口，部分 skill 会不兼容。

建议分阶段处理：

1. master 短期同时保留 `hclaw` 和 `qwenpaw` 命令入口，保证内置 skill 不挂。
2. master 后续提供 hClaw 版本的 skill 模板，将用户可见命令改成 `hclaw`。
3. trunk 长期可考虑 skill 模板变量化，例如 `{{CLI_NAME}} cron list`，但这属于内核能力增强，需要单独设计。

暂未实施。

## 当前验证命令

在 trunk 构建内核 wheel：

```powershell
cd D:\home\github\QwenPaw
powershell -ExecutionPolicy Bypass -File scripts\build_core_wheel.ps1
```

在 master worktree 安装产品层：

```powershell
cd D:\home\github\QwenPaw\.worktrees\hclaw-master
.\venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_product.ps1 -CoreWheel ..\..\dist-core\qwenpaw-1.1.7-py3-none-any.whl -Editable -NoDeps
```

验证命令名：

```powershell
hclaw --version
hclaw --help
```

验证用户目录：

```powershell
python -c "from hclaw.app import _apply_product_environment; _apply_product_environment(); from qwenpaw.constant import WORKING_DIR, SECRET_DIR; print(WORKING_DIR); print(SECRET_DIR)"
```

验证 app 启动：

```powershell
hclaw app --host 127.0.0.1 --port 8088
```

## 下一步建议

后续如果继续这项开源解耦工作，建议顺序如下：

1. 实施 Agent 人设模板定制。
2. 实施 Skill CLI 兼容入口或模板覆盖。
3. 梳理日志名称定制。
4. 梳理环境变量名称定制。
5. 梳理前端产品名和用户可见文案。
6. 明确 trunk 哪些扩展点可以接受，哪些必须留在 master 产品层。

## 当前结论

模块名称和用户目录定制已经证明该分层方案可行：

- trunk 可以作为 qwenpaw 内核 wheel 存在。
- master 可以作为 hClaw 产品层启动并组合内核。
- 当前运行方式是单进程，不会引入额外 qwenpaw 子进程。
- 产品层可以在导入内核前设置运行目录、前端静态目录和 CLI 元数据。

未完成项主要集中在人设模板、skill 命令兼容、日志与环境变量命名等更细的产品化定制点。
