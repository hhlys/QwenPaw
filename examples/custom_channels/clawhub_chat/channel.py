# -*- coding: utf-8 -*-
"""ClawHub managed-instance chat custom channel.

This channel is intentionally separate from ``cloud_edge``:

- ``cloud_edge`` handles edge nodes that call ClawHub from customer networks.
- ``clawhub_chat`` handles ClawHub's in-page chat for managed cloud
  QwenPaw containers.

The module registers an HTTP streaming endpoint when installed under
``~/.qwenpaw/custom_channels/clawhub_chat``.
"""

from __future__ import annotations

import logging
import json
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Optional

from fastapi import Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from qwenpaw.app.channels.base import (
    BaseChannel,
    ContentType,
    OnReplySent,
    ProcessHandler,
    TextContent,
)

logger = logging.getLogger(__name__)


class ClawHubChatChannel(BaseChannel):
    """QwenPaw side of ClawHub's managed-instance chat window."""

    channel = "clawhub_chat"
    uses_manager_queue = False

    def __init__(
        self,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
    ) -> None:
        super().__init__(process, on_reply_sent=on_reply_sent)
        self.config = self._normalize_config(config)
        self.enabled = bool(self.config.enabled)

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ) -> "ClawHubChatChannel":
        return cls(process=process, config={"enabled": False}, on_reply_sent=on_reply_sent)

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
        **kwargs: Any,
    ) -> "ClawHubChatChannel":
        del kwargs
        return cls(process=process, config=config, on_reply_sent=on_reply_sent)

    @staticmethod
    def _normalize_config(config: Any) -> SimpleNamespace:
        defaults = {
            "enabled": False,
            "bot_prefix": "",
            "filter_tool_messages": False,
            "filter_thinking": False,
            "token": "",
        }
        if hasattr(config, "model_dump"):
            defaults.update(config.model_dump())
        elif isinstance(config, dict):
            defaults.update(config)
        else:
            for key in defaults:
                if hasattr(config, key):
                    defaults[key] = getattr(config, key)
        return SimpleNamespace(**defaults)

    async def start(self) -> None:
        logger.info("clawhub_chat custom channel %s", "enabled" if self.enabled else "route-only")

    async def stop(self) -> None:
        logger.info("clawhub_chat custom channel stopped")

    async def health_check(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "status": "healthy",
            "detail": "ClawHub chat route is available.",
        }

    def resolve_session_id(
        self,
        sender_id: str,
        channel_meta: Optional[dict] = None,
    ) -> str:
        meta = channel_meta or {}
        conversation_id = meta.get("conversation_id") or meta.get("session_id")
        if conversation_id:
            return str(conversation_id)
        return f"clawhub:{sender_id}:default"

    def build_agent_request_from_native(self, native_payload: Any) -> Any:
        payload = native_payload if isinstance(native_payload, dict) else {}
        message = str(payload.get("message") or payload.get("text") or "")
        sender_id = str(payload.get("sender_id") or "clawhub")
        meta = dict(payload.get("meta") or {})
        session_id = self.resolve_session_id(sender_id, meta)

        request = self.build_agent_request_from_user_content(
            channel_id=self.channel,
            sender_id=sender_id,
            session_id=session_id,
            content_parts=[TextContent(type=ContentType.TEXT, text=message)],
            channel_meta=meta,
        )
        request.channel_meta = meta
        return request

    async def stream_one(self, payload: dict[str, Any]) -> AsyncGenerator[str, None]:
        event_count = 0

        try:
            request = self.build_agent_request_from_native(payload)
            async for event in self._process(request):
                event_count += 1
                yield f"data: {self._serialize_event_for_sse(event)}\n\n"

            logger.info(
                "clawhub_chat stream done: session=%s event_count=%s",
                getattr(request, "session_id", ""),
                event_count,
            )

            if self._on_reply_sent:
                self._on_reply_sent(
                    self.channel,
                    getattr(request, "user_id", "") or "clawhub",
                    getattr(request, "session_id", ""),
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("clawhub_chat stream failed")
            err = json.dumps(
                {
                    "object": "error",
                    "message": str(exc) or exc.__class__.__name__,
                },
                ensure_ascii=True,
            )
            yield f"data: {err}\n\n"

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        del to_handle, text, meta
        # ClawHub chat is request/stream based. Proactive sends are not part
        # of this channel; use cloud_edge for edge-node proactive reporting.


async def _get_channel_for_agent(app: Any, agent_id: str) -> ClawHubChatChannel:
    manager = getattr(app.state, "multi_agent_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="QwenPaw is still starting")

    workspace = await manager.get_agent(agent_id or "default")
    channel_manager = getattr(workspace, "channel_manager", None)

    if channel_manager is not None:
        configured = await channel_manager.get_channel(ClawHubChatChannel.channel)
        if isinstance(configured, ClawHubChatChannel):
            return configured

    # Route-only fallback: the custom channel route is installed, but the
    # channel does not have to be enabled in agent.json for managed-instance
    # chat to work.
    return ClawHubChatChannel(
        process=workspace.runner.stream_query,
        config={"enabled": True},
    )


def register_app_routes(app: Any) -> None:
    """Register ClawHub-facing HTTP routes.

    The registry calls this for every custom channel module. Keep routes
    under /api/ so they are not swallowed by the SPA fallback.
    """

    @app.post("/api/custom/clawhub-chat/stream")
    async def clawhub_chat_stream(
        request: Request,
        x_clawhub_token: str | None = Header(default=None),
    ) -> StreamingResponse:
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise HTTPException(status_code=400, detail="JSON object expected")

            agent_id = str(payload.get("agentId") or payload.get("agent_id") or "default")
            channel = await _get_channel_for_agent(app, agent_id)

            expected_token = str(getattr(channel.config, "token", "") or "")
            if expected_token and x_clawhub_token != expected_token:
                raise HTTPException(status_code=401, detail="Invalid ClawHub token")

            message = str(payload.get("message") or "").strip()
            if not message:
                raise HTTPException(status_code=400, detail="message is required")

            conversation_id = str(
                payload.get("conversationId")
                or payload.get("conversation_id")
                or "clawhub:default",
            )
            sender_id = str(payload.get("senderId") or payload.get("sender_id") or "clawhub")

            native_payload = {
                "message": message,
                "sender_id": sender_id,
                "meta": {
                    "conversation_id": conversation_id,
                    "source": "clawhub_chat",
                },
            }
        except HTTPException:
            raise
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("clawhub_chat route failed before streaming")

            async def error_stream() -> AsyncGenerator[str, None]:
                data = json.dumps(
                    {
                        "object": "error",
                        "message": str(exc) or exc.__class__.__name__,
                    },
                    ensure_ascii=True,
                )
                yield f"data: {data}\n\n"

            return StreamingResponse(error_stream(), media_type="text/event-stream")

        return StreamingResponse(
            channel.stream_one(native_payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
