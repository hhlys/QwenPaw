# QwenPaw 离线 Linux 裸机部署指导

## 1. 适用场景

本文档适用于客户侧 Linux 内网环境部署 QwenPaw，典型约束如下：

- 客户环境与外网不通。
- 客户不允许使用 Docker。
- 现场只能使用完整离线安装包。
- 如需浏览器 UI，访问入口需要符合客户 4A、堡垒机、网关或防火墙策略。

本方案交付一个 `qwenpaw-offline-linux-x86_64-<version>.tar.gz` 包。现场解压后即可通过内置脚本完成离线安装和启动，不需要访问互联网。

## 2. 交付包内容

离线包结构如下：

```text
qwenpaw-offline-linux-x86_64-<version>/
├── app/
│   └── qwenpaw-*.whl
├── runtime/
│   ├── python/
│   └── venv/                 # 首次 install/start 时离线创建
├── wheels/
│   └── *.whl                 # Linux x86_64 Python 依赖轮子
├── data/
│   ├── .qwenpaw/             # 默认工作目录
│   └── .qwenpaw.secret/      # 默认密钥目录
├── logs/
├── run/
├── env.example
├── env.sh                    # 可选，按需从 env.example 复制
├── install.sh
├── start.sh
├── stop.sh
├── status.sh
├── uninstall.sh
└── qwenpaw.service.template
```

## 3. 目标机器要求

推荐目标环境：

- Linux x86_64。
- glibc Linux 发行版。
- 能执行普通 shell 脚本。
- 部署目录具备读写权限。

交付前建议在与客户相同或相近的 Linux 发行版上做一次验收。若客户系统 glibc 过低，需要为该系统单独构建运行时包。

## 4. 安装步骤

假设安装到 `/opt/qwenpaw`：

```bash
mkdir -p /opt/qwenpaw
tar -xzf qwenpaw-offline-linux-x86_64-1.1.7.tar.gz -C /opt/qwenpaw --strip-components=1
cd /opt/qwenpaw
./install.sh
```

`install.sh` 会使用包内 Python 和 `wheels/` 目录创建离线虚拟环境，不访问外网。

## 5. 启动与停止

默认启动方式：

```bash
cd /opt/qwenpaw
./start.sh
```

查看状态：

```bash
./status.sh
```

查看日志：

```bash
tail -f logs/qwenpaw.log
```

停止：

```bash
./stop.sh
```

## 6. 访问 UI

默认只监听本机：

```text
127.0.0.1:8080
```

这是为了适配 4A 内网安全要求，避免安装后直接暴露端口。

如果客户允许通过内网访问，可以创建 `env.sh`：

```bash
cp env.example env.sh
vi env.sh
```

将监听地址改为：

```bash
QWENPAW_HOST=0.0.0.0
QWENPAW_PORT=8080
```

然后重启：

```bash
./stop.sh
./start.sh
```

更推荐的生产方式是：

```text
QwenPaw 监听 127.0.0.1:8080
客户侧 Nginx / 4A 网关 / 统一门户 通过 HTTPS 反向代理访问
```

这样对外只暴露客户批准的入口，例如 `https://qwenpaw.xxx.customer.local`。

## 7. 数据目录

默认数据在安装目录下：

```text
data/.qwenpaw
data/.qwenpaw.secret
data/backups
```

生产环境也可以通过 `env.sh` 指向独立持久化目录：

```bash
QWENPAW_WORKING_DIR=/data/qwenpaw/.qwenpaw
QWENPAW_SECRET_DIR=/data/qwenpaw/.qwenpaw.secret
```

注意：`QWENPAW_SECRET_DIR` 存放模型密钥等敏感信息，应限制目录权限。

## 8. systemd 托管

如果客户允许使用 systemd，可生成服务文件：

```bash
cd /opt/qwenpaw
sed "s#__APP_HOME__#/opt/qwenpaw#g" qwenpaw.service.template > /etc/systemd/system/qwenpaw.service
systemctl daemon-reload
systemctl enable qwenpaw
systemctl start qwenpaw
systemctl status qwenpaw
```

## 9. 版本升级建议

离线包升级建议分两种：

1. **应用升级**
   - 停止旧服务。
   - 备份 `data/.qwenpaw` 和 `data/.qwenpaw.secret`。
   - 解压新包。
   - 复用或恢复数据目录。
   - 执行 `install.sh` 和 `start.sh`。

2. **运行时升级**
   - Python 运行时或系统依赖变更时，建议使用完整新包。
   - 升级前必须备份数据目录。

## 10. 当前边界

本离线包覆盖 QwenPaw 服务端 UI 和 Python 依赖。若启用浏览器自动化能力，需要额外验证目标 Linux 是否具备 Chromium 所需系统库。若客户要求浏览器自动化也完全离线交付，应在客户目标系统上单独制作包含浏览器和系统库的专版包。

