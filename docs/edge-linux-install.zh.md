# 边侧 QwenPaw Linux 直装指导文档

本文面向运维人员，说明如何在客户生产网络 Linux 服务器上直接安装边侧 QwenPaw，并将其注册到 ClawHub 纳管中心。

## 1. 部署目标

边侧 QwenPaw 不使用 Docker，直接运行在客户 Linux 主机上。MVP 阶段先完成：

- 安装 Python 运行环境和 QwenPaw 依赖。
- 准备模型配置、`AGENTS.md` 等基础配置。
- 以 systemd 服务方式启动边侧注册进程。
- 边侧启动后主动向 ClawHub 注册并持续心跳。

## 2. 环境要求

- Linux x86_64，推荐 Ubuntu 22.04、Debian 12、CentOS Stream 9 或同等级发行版。
- Python `>=3.10,<3.14`。
- Node.js 18+，用于后续需要本机重建前端或扩展运行环境的场景。
- 服务器可主动访问 ClawHub 地址，例如 `http://clawhub.example.com:8080`。
- 运维账号具有 `sudo` 权限。

## 3. 创建运行用户

```bash
sudo useradd --create-home --shell /bin/bash qwenpaw
sudo mkdir -p /opt/qwenpaw
sudo chown -R qwenpaw:qwenpaw /opt/qwenpaw /home/qwenpaw
```

## 4. 安装基础运行环境

Ubuntu / Debian 示例：

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm curl git
```

CentOS / RHEL 示例：

```bash
sudo dnf install -y python3 python3-pip nodejs npm curl git
```

生产网络不能访问公网时，建议提前准备内网 PyPI 源、离线 wheelhouse 或由运维统一分发 QwenPaw wheel 包。

## 5. 安装 QwenPaw

切换到运行用户：

```bash
sudo su - qwenpaw
cd /opt/qwenpaw
python3 -m venv venv
source /opt/qwenpaw/venv/bin/activate
python -m pip install --upgrade pip
```

如果使用 wheel 包：

```bash
python -m pip install /path/to/qwenpaw-*.whl
```

如果使用内网源：

```bash
python -m pip install qwenpaw --index-url http://your-internal-pypi/simple
```

验证命令：

```bash
qwenpaw --version
qwenpaw edge --help
```

## 6. 初始化基础配置

首次初始化：

```bash
qwenpaw init --defaults --accept-security
```

默认工作目录通常为：

```bash
/home/qwenpaw/.qwenpaw
```

建议准备：

- 模型配置：确保边侧默认 agent 有可用模型。
- `AGENTS.md`：定义边侧执行角色和操作边界。
- 工具安全策略：生产环境谨慎开启 shell、文件写入等高风险工具。

示例 `AGENTS.md`：

```markdown
你是部署在客户生产网络 Linux 服务器上的边侧 QwenPaw。
你的任务是根据 ClawHub 下发的意图执行本地环境检查、文件读取、脚本执行和运维辅助操作。
执行高风险命令前必须谨慎说明风险。
```

## 7. 注册到 ClawHub

MVP 注册命令：

```bash
/opt/qwenpaw/venv/bin/qwenpaw edge daemon \
  --hub-url http://clawhub.example.com:8080 \
  --node-id edge-prod-001 \
  --tenant-id tenant-a \
  --group prod-linux \
  --username qwenpaw \
  --port 8088 \
  --token 'CHANGE_ME'
```

参数说明：

- `--hub-url`：ClawHub 访问地址。
- `--node-id`：边侧节点稳定唯一 ID。
- `--tenant-id`：租户标识。
- `--group`：节点所属群组。
- `--username`：边侧运行用户。
- `--port`：边侧 QwenPaw 服务端口，MVP 阶段作为元数据上报。
- `--token`：ClawHub 边侧注册 token。如果 ClawHub 未配置 token，可先不传。

只注册一次并退出：

```bash
/opt/qwenpaw/venv/bin/qwenpaw edge daemon \
  --hub-url http://clawhub.example.com:8080 \
  --node-id edge-prod-001 \
  --tenant-id tenant-a \
  --group prod-linux \
  --once
```

## 8. systemd 服务

创建服务文件：

```bash
sudo tee /etc/systemd/system/qwenpaw-edge.service >/dev/null <<'EOF'
[Unit]
Description=QwenPaw Edge Registration Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=qwenpaw
WorkingDirectory=/opt/qwenpaw
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/qwenpaw/venv/bin/qwenpaw edge daemon \
  --hub-url http://clawhub.example.com:8080 \
  --node-id edge-prod-001 \
  --tenant-id tenant-a \
  --group prod-linux \
  --username qwenpaw \
  --port 8088 \
  --token CHANGE_ME
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now qwenpaw-edge
sudo systemctl status qwenpaw-edge
```

查看日志：

```bash
journalctl -u qwenpaw-edge -f
```

## 9. ClawHub 验证

管理员登录 ClawHub 后，进入：

```text
Edge Nodes / 边侧节点
```

确认节点状态为 `online`，并检查：

- 节点 ID。
- 租户和群组。
- IP 和端口。
- QwenPaw 版本。
- 最后心跳时间。

## 10. 常见问题

### 注册失败

检查 ClawHub 地址是否可达：

```bash
curl -v http://clawhub.example.com:8080/api/edge/nodes/register
```

该接口只接受 `POST`，`GET` 返回 405/404 不代表网络不通。

### 401 Invalid edge registration token

说明 ClawHub 配置了 `clawhub.edge.registration-token`，边侧 `--token` 不匹配。

### 页面显示 offline

检查 systemd 服务是否仍在运行：

```bash
systemctl status qwenpaw-edge
journalctl -u qwenpaw-edge --tail 100
```

ClawHub 默认超过 90 秒未收到心跳即显示 `offline`。

### 生产网络不能访问公网

边侧只需要主动访问 ClawHub；Python 包、Node.js 包和 QwenPaw wheel 建议由运维提前放入内网源或离线目录。
