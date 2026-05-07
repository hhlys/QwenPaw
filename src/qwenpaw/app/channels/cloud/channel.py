# -*- coding: utf-8 -*-
"""Cloud Channel.

Receives intent messages dispatched from ClawHub and streams agent
responses back via SSE. The cloud (ClawHub) is treated as a channel
just like console / dingtalk / wechat — messages flow through the
same agent pipeline.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from ..base import (
    BaseChannel,
    ContentType,
    OnReplySent,
    OutgoingContentPart,
    ProcessHandler,
    TextContent,
)

logger = logging.getLogger(__name__)


class CloudChannel(BaseChannel):
    """Cloud Channel: receives dispatched intents from ClawHub.

    Messages arrive via ``POST /api/cloud/chat`` and are processed
    through the agent pipeline.  Responses are streamed back as SSE
    events so the ClawHub admin sees real-time output.
    """

    channel = "cloud"

    def __init__(
        self,
        process: ProcessHandler,
        enabled: bool,
        on_reply_sent: OnReplySent = None,
    ):
        super().__init__(process, on_reply_sent=on_reply_sent)
        self.enabled = enabled

    # ── factories ──────────────────────────────────────────────────

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ) -> "CloudChannel":
        return cls(
            process=process,
            enabled=os.getenv("CLOUD_CHANNEL_ENABLED", "1") == "1",
            on_reply_sent=on_reply_sent,
        )

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
        **kwargs,
    ) -> "CloudChannel":
        enabled = getattr(config, "enabled", True)
        return cls(
            process=process,
            enabled=enabled,
            on_reply_sent=on_reply_sent,
        )

    # ── session ────────────────────────────────────────────────────

    def resolve_session_id(
        self,
        sender_id: str,
        channel_meta: Optional[dict] = None,
    ) -> str:
        if channel_meta and channel_meta.get("session_id"):
            return channel_meta["session_id"]
        return f"{self.channel}:{sender_id}"

    # ── native → AgentRequest ──────────────────────────────────────

    def build_agent_request_from_native(self, native_payload: Any) -> Any:
        """Build AgentRequest from cloud native payload.

        Expected payload shape::

            {
                "message": "用户意图文本",
                "session_id": "cloud:node-xxx:...",
                "user_id": "admin"
            }
        """
        payload = native_payload if isinstance(native_payload, dict) else {}
        channel_id = payload.get("channel_id") or self.channel
        sender_id = payload.get("sender_id") or payload.get("user_id") or "clawhub"
        message_text = payload.get("message") or ""
        meta = payload.get("meta") or {}

        session_id = self.resolve_session_id(sender_id, meta)

        content_parts = []
        if message_text:
            content_parts.append(
                TextContent(type=ContentType.TEXT, text=message_text)
            )

        content_parts = self._resolve_upload_refs(content_parts)

        request = self.build_agent_request_from_user_content(
            channel_id=channel_id,
            sender_id=sender_id,
            session_id=session_id,
            content_parts=content_parts,
            channel_meta=meta,
        )
        request.channel_meta = meta
        return request

    def _resolve_upload_refs(self, content_parts: list) -> list:
        """Minimal resolver — cloud channel doesn't have a media_dir."""
        return content_parts

    # ── streaming ──────────────────────────────────────────────────

    async def stream_one(self, payload: Any) -> AsyncGenerator[str, None]:
        """Process one payload and yield SSE-formatted events."""
        if isinstance(payload, dict) and "message" in payload:
            session_id = self.resolve_session_id(
                payload.get("user_id") or payload.get("sender_id") or "",
                payload.get("meta"),
            )
            msg_text = payload.get("message", "")
            should_process, merged = self._apply_no_text_debounce(
                session_id,
                [TextContent(type=ContentType.TEXT, text=msg_text)],
            )
            if not should_process:
                return
            if merged and hasattr(merged[0], "text"):
                msg_text = merged[0].text or msg_text
            payload = {**payload, "message": msg_text}
            request = self.build_agent_request_from_native(payload)
        else:
            request = payload
            session_id = getattr(request, "session_id", "") or ""

        try:
            last_response = None
            event_count = 0

            async for event in self._process(request):
                event_count += 1
                obj = getattr(event, "object", None)
                status_val = getattr(event, "status", None)

                logger.debug(
                    "cloud event #%s: object=%s status=%s",
                    event_count,
                    obj,
                    status_val,
                )

                data = self._serialize_event_for_sse(event)
                yield f"data: {data}\n\n"

                if obj == "response":
                    last_response = event

            logger.info(
                "cloud stream done: event_count=%s has_response=%s",
                event_count,
                last_response is not None,
            )

            if self._on_reply_sent:
                to_handle = getattr(request, "user_id", "") or ""
                self._on_reply_sent(
                    self.channel,
                    to_handle,
                    session_id,
                )

        except Exception:
            logger.exception("cloud process/reply failed")

    async def consume_one(self, payload: Any) -> None:
        """Process one payload; drain stream_one."""
        async for _ in self.stream_one(payload):
            pass

    # ── send (proactive / cron push back to ClawHub — future) ──────

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.enabled:
            return
        logger.info("cloud send to %s: %s", to_handle, text[:200])

    # ── lifecycle ──────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "channel": self.channel,
                "status": "disabled",
                "detail": "Cloud channel is disabled.",
            }
        return {
            "channel": self.channel,
            "status": "healthy",
            "detail": "Cloud channel is running.",
        }

    async def start(self) -> None:
        if not self.enabled:
            logger.debug("cloud channel disabled")
            return
        logger.info("Cloud channel started")

    async def stop(self) -> None:
        if not self.enabled:
            return
        logger.info("cloud channel stopped")
