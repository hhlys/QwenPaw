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

<table>
  <thead>
    <tr>
      <th>序号</th>
      <th>Clawhub 接口 URL</th>
      <th>QwenPaw 接口 URL</th>
      <th>入参</th>
      <th>出参</th>
      <th>接口功能</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td><code>POST /api/o3/chats/{chat_id}/messages/stream</code></td>
      <td><code>POST /api/console/chat</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "chat_id": "string, required"
  },
  "body": {
    "user_id": "string, required",
    "agent_id": "string, optional",
    "message": "string, required",
    "attachments": [
      {
        "file_id": "string, required",
        "type": "file | image | audio | video",
        "file_name": "string, optional"
      }
    ],
    "stream": true
  },
  "qwenpaw_forward": {
    "session_id": "string, mapped from chat_id",
    "user_id": "string",
    "channel": "console",
    "stream": true,
    "input": [
      {
        "role": "user",
        "type": "message",
        "content": [
          {
            "type": "text",
            "text": "string"
          }
        ]
      }
    ]
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "content_type": "text/event-stream",
  "event_format": "data: {...}",
  "data": {
    "object": "response | message",
    "status": "created | in_progress | completed | incomplete",
    "output": [
      {
        "role": "assistant",
        "type": "message",
        "content": [
          {
            "type": "text",
            "text": "string"
          }
        ]
      }
    ],
    "error": "string, optional"
  }
}</code></pre></td>
      <td>发起或继续一个 chat 会话，并流式返回模型回复。</td>
    </tr>
    <tr>
      <td>2</td>
      <td><code>POST /api/o3/chats/{chat_id}/messages/reconnect</code></td>
      <td><code>POST /api/console/chat</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "chat_id": "string, required"
  },
  "body": {
    "user_id": "string, required",
    "agent_id": "string, optional"
  },
  "qwenpaw_forward": {
    "session_id": "string, mapped from chat_id",
    "user_id": "string",
    "channel": "console",
    "stream": true,
    "reconnect": true
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "content_type": "text/event-stream",
  "event_format": "data: {...}",
  "data": {
    "object": "response | message",
    "status": "in_progress | completed",
    "output": [],
    "error": "string, optional"
  }
}</code></pre></td>
      <td>页面刷新、网络中断后重新连接正在生成中的 chat 流。</td>
    </tr>
    <tr>
      <td>3</td>
      <td><code>POST /api/o3/chats/{chat_id}/stop</code></td>
      <td><code>POST /api/console/chat/stop?chat_id={chat_id}</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "chat_id": "string, required"
  },
  "qwenpaw_forward": {
    "chat_id": "string, mapped QwenPaw chat_id or session_id"
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "stopped": "boolean"
}</code></pre></td>
      <td>停止当前 chat 的流式生成。</td>
    </tr>
    <tr>
      <td>4</td>
      <td><code>POST /api/o3/files</code></td>
      <td><code>POST /api/console/upload</code></td>
      <td><pre><code class="language-json">{
  "content_type": "multipart/form-data",
  "form": {
    "file": "binary, required",
    "chat_id": "string, optional",
    "user_id": "string, optional",
    "agent_id": "string, optional"
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "file_id": "string",
  "file_name": "string",
  "size": "number",
  "url": "string",
  "qwenpaw_url": "string, internal only"
}</code></pre></td>
      <td>上传 chat 附件。文件会话先上传文件，再在流式会话接口的 <code>attachments</code> 中引用 <code>file_id</code>。</td>
    </tr>
    <tr>
      <td>5</td>
      <td><code>GET /api/o3/files/{file_id}/preview</code></td>
      <td><code>GET /api/files/preview/{filepath}</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "file_id": "string, required"
  },
  "qwenpaw_forward": {
    "filepath": "string, mapped from file_id"
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "content_type": "application/octet-stream | image/* | audio/* | video/*",
  "body": "binary file stream",
  "error": {
    "status": 404,
    "detail": "Not found"
  }
}</code></pre></td>
      <td>预览或下载 chat 附件，用于 o3 UI 回显图片、音视频或文件。</td>
    </tr>
    <tr>
      <td>6</td>
      <td><code>GET /api/o3/chats</code></td>
      <td><code>GET /api/chats?user_id={user_id}&amp;channel=console</code></td>
      <td><pre><code class="language-json">{
  "query": {
    "user_id": "string, recommended",
    "agent_id": "string, optional",
    "limit": "number, optional",
    "page": "number, optional"
  },
  "qwenpaw_forward": {
    "user_id": "string, optional",
    "channel": "console"
  }
}</code></pre></td>
      <td><pre><code class="language-json">[
  {
    "chat_id": "string",
    "name": "string",
    "user_id": "string",
    "status": "idle | running",
    "created_at": "string, ISO-8601",
    "updated_at": "string, ISO-8601",
    "pinned": "boolean",
    "meta": {}
  }
]</code></pre></td>
      <td>查询 chat 会话列表，用于 o3 UI 左侧会话栏。</td>
    </tr>
    <tr>
      <td>7</td>
      <td><code>GET /api/o3/chats/{chat_id}</code></td>
      <td><code>GET /api/chats/{chat_id}</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "chat_id": "string, required"
  },
  "query": {
    "agent_id": "string, optional"
  },
  "qwenpaw_forward": {
    "chat_id": "string, mapped QwenPaw chat_id"
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "chat_id": "string",
  "status": "idle | running",
  "messages": [
    {
      "role": "user | assistant | system | tool",
      "type": "message | reasoning | plugin_call | plugin_call_output",
      "content": [
        {
          "type": "text | image | audio | video | file | data",
          "text": "string, optional",
          "image_url": "string, optional",
          "file_url": "string, optional",
          "data": "object | string, optional"
        }
      ],
      "metadata": {}
    }
  ]
}</code></pre></td>
      <td>获取 chat 详情和历史消息。</td>
    </tr>
    <tr>
      <td>8</td>
      <td><code>PATCH /api/o3/chats/{chat_id}</code></td>
      <td><code>PUT /api/chats/{chat_id}</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "chat_id": "string, required"
  },
  "body": {
    "name": "string, optional",
    "pinned": "boolean, optional"
  },
  "qwenpaw_forward": {
    "name": "string, optional",
    "pinned": "boolean, optional"
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "chat_id": "string",
  "name": "string",
  "user_id": "string",
  "status": "idle | running",
  "created_at": "string, ISO-8601",
  "updated_at": "string, ISO-8601",
  "pinned": "boolean",
  "meta": {}
}</code></pre></td>
      <td>修改 chat 元数据，例如重命名或置顶。</td>
    </tr>
    <tr>
      <td>9</td>
      <td><code>DELETE /api/o3/chats/{chat_id}</code></td>
      <td><code>DELETE /api/chats/{chat_id}</code></td>
      <td><pre><code class="language-json">{
  "path": {
    "chat_id": "string, required"
  },
  "qwenpaw_forward": {
    "chat_id": "string, mapped QwenPaw chat_id"
  }
}</code></pre></td>
      <td><pre><code class="language-json">{
  "deleted": "boolean"
}</code></pre></td>
      <td>删除单个 chat。注意 QwenPaw 当前只删除 <code>ChatSpec</code> 元数据映射，不清理底层 session JSON 状态文件。</td>
    </tr>
    <tr>
      <td>10</td>
      <td><code>POST /api/o3/chats/batch-delete</code></td>
      <td><code>POST /api/chats/batch-delete</code></td>
      <td><pre><code class="language-json">{
  "body": {
    "chat_ids": [
      "string"
    ]
  },
  "qwenpaw_forward": [
    "mapped_qwenpaw_chat_id"
  ]
}</code></pre></td>
      <td><pre><code class="language-json">{
  "deleted": "boolean"
}</code></pre></td>
      <td>批量删除 chat。若 o3 UI 没有批量操作，可暂不暴露。</td>
    </tr>
  </tbody>
</table>

## 第 2 章 模型管理类接口

QwenPaw 的模型配置核心入口是 `/api/models` 和 `/api/models/active`。其中“默认模型”和“激活模型”都通过 `/api/models/active` 完成，区别在 `scope`：

- `scope=global`：配置或查询全局默认模型。某个 Agent 没有单独配置模型时，会回退使用它。
- `scope=agent`：配置或查询指定 Agent 的模型，需要 `agent_id`。
- `scope=effective`：查询当前实际生效模型，优先返回 Agent 模型，没有则回退全局默认模型。

<table>
  <thead>
    <tr>
      <th>序号</th>
      <th>Clawhub 接口 URL</th>
      <th>QwenPaw 接口 URL</th>
      <th>入参</th>
      <th>出参</th>
      <th>接口功能</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>11</td>
      <td><code>GET /api/o3/models</code></td>
      <td><code>GET /api/models</code></td>
      <td>

```json
{
  "query": {
    "agent_id": "string, optional, 仅用于 Clawhub 做权限或上下文判断"
  }
}
```

      </td>
      <td>

```json
[
  {
    "id": "string",
    "name": "string",
    "base_url": "string",
    "api_key_prefix": "string",
    "chat_model": "OpenAIChatModel | AnthropicChatModel | GeminiChatModel",
    "models": [
      {
        "id": "string",
        "name": "string",
        "is_free": "boolean",
        "supports_multimodal": "boolean | null",
        "supports_image": "boolean | null",
        "supports_video": "boolean | null",
        "probe_source": "string | null"
      }
    ],
    "extra_models": [
      {
        "id": "string",
        "name": "string"
      }
    ],
    "is_custom": "boolean",
    "supports_discover": "boolean",
    "requires_api_key": "boolean"
  }
]
```

      </td>
      <td>查询当前可用 provider 和模型列表，用于 o3 UI 展示模型选择器。</td>
    </tr>
    <tr>
      <td>12</td>
      <td><code>GET /api/o3/models/default</code></td>
      <td><code>GET /api/models/active?scope=global</code></td>
      <td>

```json
{
  "query": {
    "agent_id": "string, optional, 仅用于 Clawhub 做权限判断，不转发给 QwenPaw"
  },
  "qwenpaw_forward": {
    "scope": "global"
  }
}
```

      </td>
      <td>

```json
{
  "active_llm": {
    "provider_id": "string",
    "model": "string"
  },
  "nullable_fields": {
    "active_llm": true
  }
}
```

      </td>
      <td>查询全局默认模型。默认模型是所有未单独配置 Agent 模型时的兜底模型。</td>
    </tr>
    <tr>
      <td>13</td>
      <td><code>PUT /api/o3/models/default</code></td>
      <td><code>PUT /api/models/active</code></td>
      <td>

```json
{
  "body": {
    "provider_id": "string, required, 目标 provider",
    "model": "string, required, 目标模型 ID"
  },
  "qwenpaw_forward": {
    "provider_id": "string",
    "model": "string",
    "scope": "global"
  }
}
```

      </td>
      <td>

```json
{
  "active_llm": {
    "provider_id": "string",
    "model": "string"
  },
  "errors": {
    "404": "provider not found",
    "400": "model not found or invalid"
  }
}
```

      </td>
      <td>配置全局默认模型。等价于调用 QwenPaw 激活模型接口并使用 <code>scope=global</code>。</td>
    </tr>
    <tr>
      <td>14</td>
      <td><code>GET /api/o3/models/active</code></td>
      <td><code>GET /api/models/active?scope=effective&amp;agent_id={agent_id}</code></td>
      <td>

```json
{
  "query": {
    "agent_id": "string, optional, 目标 QwenPaw Agent",
    "scope": "effective | global | agent, optional, default effective"
  },
  "rules": {
    "scope_agent_requires_agent_id": true
  }
}
```

      </td>
      <td>

```json
{
  "active_llm": {
    "provider_id": "string",
    "model": "string"
  },
  "nullable_fields": {
    "active_llm": true
  }
}
```

      </td>
      <td>查询当前实际生效模型。o3 UI 展示“当前使用模型”时建议使用此接口。</td>
    </tr>
    <tr>
      <td>15</td>
      <td><code>PUT /api/o3/models/active</code></td>
      <td><code>PUT /api/models/active</code></td>
      <td>

```json
{
  "body": {
    "provider_id": "string, required",
    "model": "string, required",
    "scope": "global | agent, required",
    "agent_id": "string, required when scope is agent"
  }
}
```

      </td>
      <td>

```json
{
  "active_llm": {
    "provider_id": "string",
    "model": "string"
  },
  "errors": {
    "404": "provider not found",
    "400": "model not found or invalid",
    "500": "failed to save agent config"
  }
}
```

      </td>
      <td>激活模型。<code>scope=global</code> 时表示设置默认模型；<code>scope=agent</code> 时表示设置指定 Agent 的激活模型。</td>
    </tr>
    <tr>
      <td>16</td>
      <td><code>POST /api/o3/models/custom-providers</code></td>
      <td><code>POST /api/models/custom-providers</code>；必要时 Clawhub 可继续调用 <code>PUT /api/models/{provider_id}/config</code></td>
      <td>

```json
{
  "body": {
    "id": "string, required, 自定义 provider ID",
    "name": "string, required, 展示名称",
    "default_base_url": "string, optional, 模型服务地址",
    "api_key": "string, optional, 若提供则由 Clawhub 额外转发配置接口",
    "api_key_prefix": "string, optional",
    "chat_model": "OpenAIChatModel | AnthropicChatModel | GeminiChatModel, optional, default OpenAIChatModel",
    "models": [
      {
        "id": "string, required",
        "name": "string, required",
        "is_free": "boolean, optional",
        "supports_multimodal": "boolean | null, optional",
        "supports_image": "boolean | null, optional",
        "supports_video": "boolean | null, optional",
        "probe_source": "string | null, optional"
      }
    ]
  },
  "qwenpaw_forward": {
    "create_provider": "POST /api/models/custom-providers",
    "configure_provider_when_api_key_present": "PUT /api/models/{provider_id}/config"
  }
}
```

      </td>
      <td>

```json
{
  "id": "string",
  "name": "string",
  "base_url": "string",
  "api_key_prefix": "string",
  "chat_model": "string",
  "models": [
    {
      "id": "string",
      "name": "string"
    }
  ],
  "extra_models": [],
  "is_custom": true,
  "errors": {
    "400": "provider id duplicated or invalid fields"
  }
}
```

      </td>
      <td>添加自定义模型供应商。适合 o3 接入 OpenAI-compatible、Anthropic-compatible 或 Gemini-compatible 私有模型服务。</td>
    </tr>
    <tr>
      <td>17</td>
      <td><code>POST /api/o3/models/{provider_id}/models</code></td>
      <td><code>POST /api/models/{provider_id}/models</code></td>
      <td>

```json
{
  "path": {
    "provider_id": "string, required"
  },
  "body": {
    "id": "string, required, 模型 ID",
    "name": "string, required, 展示名",
    "is_free": "boolean, optional",
    "supports_multimodal": "boolean | null, optional",
    "supports_image": "boolean | null, optional",
    "supports_video": "boolean | null, optional",
    "probe_source": "string | null, optional"
  }
}
```

      </td>
      <td>

```json
{
  "id": "string",
  "name": "string",
  "models": [
    {
      "id": "string",
      "name": "string"
    }
  ],
  "extra_models": [
    {
      "id": "string",
      "name": "string"
    }
  ],
  "errors": {
    "404": "provider not found"
  }
}
```

      </td>
      <td>给已有 provider 添加模型 ID。适合 provider 已存在，只需要补充一个自定义模型。</td>
    </tr>
  </tbody>
</table>

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
