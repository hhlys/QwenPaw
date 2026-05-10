# cloud_edge custom channel

`cloud_edge` 是一个外置 custom channel，用于边侧 QwenPaw 通过出站 HTTP 接入 ClawHub。
它不需要修改 QwenPaw 主工程源码。部署时只需要把本目录复制到 QwenPaw 工作目录的 `custom_channels` 下，并在 `agent.json` 中启用 `channels.cloud_edge`。

## 安装位置

Windows 默认位置：

```powershell
C:\Users\<你的用户名>\.qwenpaw\custom_channels\cloud_edge
```

Linux 默认位置：

```bash
~/.qwenpaw/custom_channels/cloud_edge
```

如果设置了 `QWENPAW_WORKING_DIR`，则安装到：

```text
${QWENPAW_WORKING_DIR}/custom_channels/cloud_edge
```

## 目录结构

```text
cloud_edge/
  __init__.py
  channel.py
  channel.json
  README.zh.md
```

## 配置示例

编辑边侧 QwenPaw 的 agent 配置文件：

```text
~/.qwenpaw/workspaces/default/agent.json
```

在 `channels` 下增加：

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

字段说明：

- `hub_url`: ClawHub 地址。
- `node_id`: 边侧节点唯一 ID。
- `tenant_id`: 租户 ID。
- `group_name`: 节点分组。
- `username`: 展示用用户名。
- `token`: 可选共享密钥，会通过 `X-Edge-Token` 请求头上报。
- `heartbeat_interval`: 心跳间隔，单位秒。
- `poll_interval`: 任务轮询间隔，单位秒。

## 启动

```powershell
python -m qwenpaw app --host 127.0.0.1 --port 8088
```

启动日志中应出现：

```text
custom channel registered: cloud_edge
cloud_edge custom channel started: node_id=...
cloud_edge registered: node_id=... status=online
```

## 原生定时任务

如果云端意图要求边侧创建定时任务，必须使用 QwenPaw 原生 cron 能力，不要创建外部脚本、后台循环或系统计划任务。

原因是 QwenPaw 控制台的“定时任务”页面读取的是 workspace 下的原生 `jobs.json`，并由 `CronManager` 管理。只有通过 `qwenpaw cron create` 或 `/cron/jobs` API 创建的任务，才能在控制台里看到、暂停、恢复、删除和手动运行。

创建云地定时任务时，目标 channel 应该设置为 `cloud_edge`：

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

这样任务会进入边侧 QwenPaw 控制台“定时任务”页面；每次 cron 执行完成后，`CronExecutor` 会通过 `cloud_edge.send()` 把结果回传到 ClawHub 的同一个云端会话。

## 验证

1. 在 ClawHub 中查看边侧节点是否在线。
2. 在 ClawHub 中向该节点下发一条要求创建定时任务的意图。
3. 边侧日志应出现 `cloud_edge task received`。
4. 边侧 QwenPaw 控制台“定时任务”页面应能看到新任务。
5. 等 cron 触发，或用 `qwenpaw cron run <job_id> --agent-id default` 手动触发。
6. ClawHub 应收到 cron 执行结果。

## 设计边界

这个方案使用 QwenPaw 已有的 `custom_channels` 机制，不依赖 QwenPaw 的 `plugins` 系统。

优点：

- 不修改 QwenPaw 主工程源码。
- 可作为独立目录复制交付。
- 复用 QwenPaw 原生 cron 管理能力。
- 网络方向始终是边侧主动访问云端，不要求客户机房开放入站端口。

限制：

- 不会出现在 QwenPaw 插件管理页面。
- 配置 schema 不由 QwenPaw 主工程强校验。
- 启停通过 `agent.json` 的 `enabled` 字段控制。
- 边侧本地手工发起的无归属任务不会自动上报云端。
