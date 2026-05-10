# clawhub_chat custom channel

`clawhub_chat` 是云端容器 QwenPaw 给 ClawHub 页面聊天窗口使用的 custom channel。

它和 `cloud_edge` 分工不同：

- `cloud_edge`: 边侧 QwenPaw 主动注册、心跳、拉任务、上报结果。
- `clawhub_chat`: ClawHub 管理的云端容器 QwenPaw 接收页面聊天消息，并把流式事件返回给 ClawHub。

## 安装位置

把整个目录复制到 QwenPaw 工作目录：

```text
~/.qwenpaw/custom_channels/clawhub_chat
```

Docker 容器内通常是：

```text
/root/.qwenpaw/custom_channels/clawhub_chat
```

## 暴露接口

安装后，QwenPaw 启动时会注册：

```text
POST /api/custom/clawhub-chat/stream
```

ClawHub 会把当前页面聊天消息转发到这个接口，并把返回的 SSE 事件流展示在页面中。

## 配置

如果只是让 HTTP route 生效，复制目录后重启 QwenPaw 即可。

如果希望在 channel manager 里也能看到它，可以在 `agent.json` 的 `channels` 下加入：

```json
{
  "channels": {
    "clawhub_chat": {
      "enabled": true,
      "token": ""
    }
  }
}
```

`token` 可选。若配置了 `token`，ClawHub 转发请求时需要带 `X-ClawHub-Token`。
