# O3 Platform API

本文档描述 o3 平台通过 Clawhub 调用 QwenPaw 的精简 chat 接口方案。

## 命名约定

Clawhub 对外接口统一使用 `chat/chats`，不使用 `sessions`。原因是 QwenPaw 现有 HTTP 接口、数据模型和 CLI 都使用 `chats` / `ChatSpec` 命名，对外保持一致可以减少概念转换和排障成本。

Clawhub 内部仍需维护必要映射：

- `clawhub chat_id` 或 o3 业务会话 ID -> QwenPaw `chat_id`
- `clawhub chat_id` -> QwenPaw `session_id`
- `file_id` -> QwenPaw 上传后的真实文件路径

推荐固定使用 `channel=console`。如需指定目标 QwenPaw Agent，Clawhub 转发 QwenPaw 请求时推荐携带请求头 `X-Agent-Id: <agent_id>`；未指定时 QwenPaw 默认使用 `default`。

## 第 1 章 会话管理类接口

| 序号 | Clawhub 接口 URL | QwenPaw 接口 URL | 入参 | 出参 | 接口功能 |
|---:|---|---|---|---|---|
| 1 | `POST /api/o3/chats/{chat_id}/messages/stream` | `POST /api/console/chat` | **Path**: `chat_id`，Clawhub 对外 chat 会话 ID。**Body**: `message` string，用户输入文本；`attachments` array，可选附件列表，每项包含 `file_id`、`type`、`file_name`；`user_id` string，o3 用户 ID；`agent_id` string，可选目标 QwenPaw Agent；`stream` boolean，固定为 `true`。Clawhub 转发时组装 QwenPaw `input`、`session_id`、`user_id`、`channel=console`、`stream=true`。 | `text/event-stream`。每条事件格式为 `data: {...}`。事件内容为 QwenPaw runtime message 或 response payload；错误事件可能为 `{"error":"..."}`。 | 发起或继续一个 chat 会话，并流式返回模型回复。 |
| 2 | `POST /api/o3/chats/{chat_id}/messages/reconnect` | `POST /api/console/chat` | **Path**: `chat_id`。**Body**: `user_id` string，o3 用户 ID；`agent_id` string，可选目标 QwenPaw Agent。Clawhub 转发时传 `reconnect=true`、对应 QwenPaw `session_id`、`user_id`、`channel=console`，不追加新的用户消息。 | `text/event-stream`。继续接收该 chat 当前运行中的 SSE 输出；如果没有运行中的流，可能返回空流或直接结束。 | 页面刷新、网络中断后重新连接正在生成中的 chat 流。 |
| 3 | `POST /api/o3/chats/{chat_id}/stop` | `POST /api/console/chat/stop?chat_id={chat_id}` | **Path**: `chat_id`。Clawhub 内部优先映射为 QwenPaw `chat_id` 后转发；如没有映射，可尝试传 QwenPaw `session_id`，QwenPaw 会按 console channel 尝试反查。 | JSON: `stopped` boolean，是否成功停止运行中的生成任务。 | 停止当前 chat 的流式生成。 |
| 4 | `POST /api/o3/files` | `POST /api/console/upload` | **Body**: `multipart/form-data`，`file` 必填。Clawhub 可额外接收 `chat_id`、`user_id`、`agent_id` 用于业务记录，但转发 QwenPaw 时核心字段只有 `file`。QwenPaw 当前限制文件大小约 10 MB。 | JSON: `file_id` string，Clawhub 生成的文件 ID；`file_name` string，安全文件名；`size` number，文件大小；`url` string，Clawhub 文件访问 URL。Clawhub 内部需保存 QwenPaw 返回的真实 `url` 文件路径。 | 上传 chat 附件。文件会话先上传文件，再在流式会话接口的 `attachments` 中引用 `file_id`。 |
| 5 | `GET /api/o3/files/{file_id}/preview` | `GET /api/files/preview/{filepath}` | **Path**: `file_id`。Clawhub 内部将 `file_id` 映射为 QwenPaw 上传返回的真实 `filepath`。 | 文件流。文件不存在时返回 `404`。 | 预览或下载 chat 附件，用于 o3 UI 回显图片、音视频或文件。 |
| 6 | `GET /api/o3/chats` | `GET /api/chats?user_id={user_id}&channel=console` | **Query**: `user_id` string，建议必传，用于用户隔离；`agent_id` string，可选目标 QwenPaw Agent；`limit`、`page` 可选，如 o3 UI 需要分页，由 Clawhub 自行分页或裁剪。Clawhub 转发 QwenPaw 时固定 `channel=console`。 | JSON array。建议 Clawhub 返回字段：`chat_id`、`name`、`user_id`、`status`、`created_at`、`updated_at`、`pinned`、`meta`。QwenPaw 原始 `ChatSpec.id` 即 QwenPaw `chat_id`。 | 查询 chat 会话列表，用于 o3 UI 左侧会话栏。 |
| 7 | `GET /api/o3/chats/{chat_id}` | `GET /api/chats/{chat_id}` | **Path**: `chat_id`。Clawhub 内部映射为 QwenPaw `chat_id`。**Query**: `agent_id` 可选。 | JSON: `chat_id` string；`status` string；`messages` array。`messages[].role` 可能为 `user`、`assistant`、`system`、`tool`；`messages[].content[]` 可能包含 `text`、`image`、`audio`、`video`、`file`、`data` 等内容块。 | 获取 chat 详情和历史消息。 |
| 8 | `PATCH /api/o3/chats/{chat_id}` | `PUT /api/chats/{chat_id}` | **Path**: `chat_id`。**Body**: `name` string，可选 chat 标题；`pinned` boolean，可选是否置顶。Clawhub 转发 QwenPaw 时只传 `{ "name": ..., "pinned": ... }`。 | JSON: 更新后的 chat 对象，建议包含 `chat_id`、`name`、`user_id`、`status`、`created_at`、`updated_at`、`pinned`、`meta`。 | 修改 chat 元数据，例如重命名或置顶。 |
| 9 | `DELETE /api/o3/chats/{chat_id}` | `DELETE /api/chats/{chat_id}` | **Path**: `chat_id`。Clawhub 内部映射为 QwenPaw `chat_id`。 | JSON: `deleted` boolean。不存在时返回 `404`。 | 删除单个 chat。注意 QwenPaw 当前只删除 `ChatSpec` 元数据映射，不清理底层 session JSON 状态文件。 |
| 10 | `POST /api/o3/chats/batch-delete` | `POST /api/chats/batch-delete` | **Body**: `chat_ids` string array，Clawhub 对外 chat ID 列表。Clawhub 内部映射为 QwenPaw `chat_id` 数组后转发；QwenPaw 接收原始 JSON 数组，例如 `["id1","id2"]`。 | JSON: `deleted` boolean，表示是否执行删除。 | 批量删除 chat。若 o3 UI 没有批量操作，可暂不暴露。 |

## 第 2 章 模型管理类接口

QwenPaw 的模型配置核心入口是 `/api/models` 和 `/api/models/active`。其中“默认模型”和“激活模型”都通过 `/api/models/active` 完成，区别在 `scope`：

- `scope=global`：配置或查询全局默认模型。某个 Agent 没有单独配置模型时，会回退使用它。
- `scope=agent`：配置或查询指定 Agent 的模型，需要 `agent_id`。
- `scope=effective`：查询当前实际生效模型，优先返回 Agent 模型，没有则回退全局默认模型。

| 序号 | Clawhub 接口 URL | QwenPaw 接口 URL | 入参 | 出参 | 接口功能 |
|---:|---|---|---|---|---|
| 11 | `GET /api/o3/models` | `GET /api/models` | **Query**: `agent_id` 可选，仅用于 Clawhub 做权限或上下文判断；QwenPaw 原接口不需要该参数。 | JSON array。每项为 provider 信息：`id` provider ID；`name` provider 名称；`base_url`；`api_key_prefix`；`chat_model`；`models` 内置或可用模型数组；`extra_models` 用户额外添加模型数组；`is_custom` 是否自定义 provider；`supports_discover` 是否支持模型发现；`requires_api_key` 是否需要 API key。模型项通常包含 `id`、`name`、`is_free`、`supports_multimodal`、`supports_image`、`supports_video`、`probe_source`。 | 查询当前可用 provider 和模型列表，用于 o3 UI 展示模型选择器。 |
| 12 | `GET /api/o3/models/default` | `GET /api/models/active?scope=global` | 无必填参数。**Query**: `agent_id` 可选，仅用于 Clawhub 做权限判断，不转发给 QwenPaw。 | JSON: `active_llm`。已配置时为 `{ "provider_id": "openai", "model": "gpt-4.1" }`；未配置时可能为 `null`。 | 查询全局默认模型。默认模型是所有未单独配置 Agent 模型时的兜底模型。 |
| 13 | `PUT /api/o3/models/default` | `PUT /api/models/active` | **Body**: `provider_id` string，目标 provider；`model` string，目标模型 ID。Clawhub 转发 QwenPaw 时补齐 `scope="global"`，无需 `agent_id`。 | JSON: `active_llm`，结构为 `{ "provider_id": "...", "model": "..." }`。provider 不存在可能返回 `404`；model 不存在或不可用可能返回 `400`。 | 配置全局默认模型。等价于调用 QwenPaw 激活模型接口并使用 `scope=global`。 |
| 14 | `GET /api/o3/models/active` | `GET /api/models/active?scope=effective&agent_id={agent_id}` | **Query**: `agent_id` 可选目标 QwenPaw Agent；`scope` 可选，建议默认 `effective`。可选值：`effective`、`global`、`agent`。当 `scope=agent` 时必须传 `agent_id`。 | JSON: `active_llm`。已配置时为 `{ "provider_id": "...", "model": "..." }`；未配置时可能为 `null`。 | 查询当前实际生效模型。o3 UI 展示“当前使用模型”时建议使用此接口。 |
| 15 | `PUT /api/o3/models/active` | `PUT /api/models/active` | **Body**: `provider_id` string；`model` string；`scope` string，`global` 或 `agent`；`agent_id` string，当 `scope=agent` 时必填。建议 o3 给指定 Agent 切换模型时使用 `scope=agent`，避免误改全局默认模型。 | JSON: `active_llm`，结构为 `{ "provider_id": "...", "model": "..." }`。provider 不存在可能返回 `404`；model 不存在或不可用可能返回 `400`；保存 Agent 配置失败可能返回 `500`。 | 激活模型。`scope=global` 时表示设置默认模型；`scope=agent` 时表示设置指定 Agent 的激活模型。 |
| 16 | `POST /api/o3/models/custom-providers` | `POST /api/models/custom-providers`；必要时 Clawhub 可继续调用 `PUT /api/models/{provider_id}/config` | **Body**: `id` string，自定义 provider ID；`name` string，展示名称；`default_base_url` string，模型服务地址；`api_key` string，可选，若提供则由 Clawhub 额外转发配置接口；`api_key_prefix` string，可选；`chat_model` string，可选，`OpenAIChatModel`、`AnthropicChatModel`、`GeminiChatModel`，默认建议 `OpenAIChatModel`；`models` array，可选初始模型列表，每项包含 `id`、`name`、`is_free`、`supports_multimodal`、`supports_image`、`supports_video`、`probe_source`。 | JSON: provider 信息，包含 `id`、`name`、`base_url`、`chat_model`、`models`、`extra_models`、`is_custom` 等。provider ID 冲突或字段非法时返回 `400`。 | 添加自定义模型供应商。适合 o3 接入 OpenAI-compatible、Anthropic-compatible 或 Gemini-compatible 私有模型服务。 |
| 17 | `POST /api/o3/models/{provider_id}/models` | `POST /api/models/{provider_id}/models` | **Path**: `provider_id`。**Body**: `id` string，模型 ID；`name` string，展示名；`is_free` boolean，可选；`supports_multimodal` boolean/null，可选；`supports_image` boolean/null，可选；`supports_video` boolean/null，可选；`probe_source` string/null，可选。 | JSON: 更新后的 provider 信息，包含该 provider 下最新 `models` / `extra_models`。provider 不存在返回 `404`。 | 给已有 provider 添加模型 ID。适合 provider 已存在，只需要补充一个自定义模型。 |

## 流式会话请求示例

### Clawhub 接收 o3 文本消息

```json
{
  "user_id": "o3_user_123",
  "agent_id": "default",
  "message": "你好，帮我总结一下今天的任务。",
  "stream": true
}
```

### Clawhub 转发 QwenPaw payload

```json
{
  "session_id": "clawhub_chat_456",
  "user_id": "o3_user_123",
  "channel": "console",
  "stream": true,
  "input": [
    {
      "role": "user",
      "type": "message",
      "content": [
        {
          "type": "text",
          "text": "你好，帮我总结一下今天的任务。"
        }
      ]
    }
  ]
}
```

## 文件会话请求示例

文件 chat 分两步：

1. o3 调用 `POST /api/o3/files` 上传文件。
2. o3 调用 `POST /api/o3/chats/{chat_id}/messages/stream`，在 `attachments` 中引用上传得到的 `file_id`。

### Clawhub 接收 o3 文件消息

```json
{
  "user_id": "o3_user_123",
  "message": "帮我分析这个文件。",
  "attachments": [
    {
      "file_id": "file_abc123",
      "type": "file",
      "file_name": "report.pdf"
    }
  ],
  "stream": true
}
```

### Clawhub 转发 QwenPaw payload

```json
{
  "session_id": "clawhub_chat_456",
  "user_id": "o3_user_123",
  "channel": "console",
  "stream": true,
  "input": [
    {
      "role": "user",
      "type": "message",
      "content": [
        {
          "type": "text",
          "text": "帮我分析这个文件。"
        },
        {
          "type": "file",
          "filename": "report.pdf",
          "file_url": "/absolute/qwenpaw/media/path/report.pdf"
        }
      ]
    }
  ]
}
```

附件类型可按文件类型映射为：

- 普通文件：`{ "type": "file", "filename": "...", "file_url": "..." }`
- 图片：`{ "type": "image", "image_url": "..." }`
- 音频：`{ "type": "audio", "data": "...", "format": "mp3" }`
- 视频：`{ "type": "video", "video_url": "..." }`

## 重连请求示例

### Clawhub 接收 o3 重连请求

```json
{
  "user_id": "o3_user_123",
  "agent_id": "default"
}
```

### Clawhub 转发 QwenPaw payload

```json
{
  "session_id": "clawhub_chat_456",
  "user_id": "o3_user_123",
  "channel": "console",
  "stream": true,
  "reconnect": true
}
```

## 实现注意事项

- Clawhub 对外暴露 `chat_id`，不要把 QwenPaw 内部 `session_id` 和本地文件路径直接暴露给 o3。
- Clawhub 应负责鉴权、用户隔离、`chat_id` 映射、`file_id` 映射，以及请求头 `X-Agent-Id` 的转发。
- o3 只使用 console 通道即可满足自建 UI 的聊天、上传、历史、停止、删除等需求。
- 不建议对 o3 暴露 QwenPaw 多 channel、主动推送、Agent-to-Agent、后台 task 等接口，避免接口面过大。
- QwenPaw 删除 chat 当前只删除 chat 元数据映射，不清理底层 session JSON 状态文件；如 Clawhub 需要“彻底删除”，需额外设计清理策略。
