# -*- coding: utf-8 -*-
"""Cloud channel API — receives dispatched intents from ClawHub."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import StreamingResponse

from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from ..agent_context import get_agent_for_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cloud", tags=["cloud"])


def _build_native_payload(body: Dict[str, Any]) -> Dict[str, Any]:
    """Build native payload from a plain dict (ClawHub dispatch format).

    Expected::

        {"message": "...", "user_id": "admin", "session_id": "cloud:..."}
    """
    channel_id = body.get("channel", "cloud")
    sender_id = body.get("user_id", "clawhub")
    session_id = body.get("session_id", "cloud:default")
    message = body.get("message", "")

    content_parts = []
    if message:
        content_parts.append({"type": "text", "text": message})

    return {
        "channel_id": channel_id,
        "sender_id": sender_id,
        "user_id": sender_id,
        "message": message,
        "content_parts": content_parts,
        "meta": {
            "session_id": session_id,
            "user_id": sender_id,
        },
    }


@router.post(
    "/chat",
    status_code=200,
    summary="Dispatch intent from ClawHub (streaming)",
    description="Cloud channel endpoint called by ClawHub to dispatch "
    "an intent to the edge node. Returns SSE streaming response.",
)
async def post_cloud_chat(request: Request) -> StreamingResponse:
    # Accept raw JSON body — avoids Pydantic Union validation issues
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    workspace = await get_agent_for_request(request)
    cloud_channel = await workspace.channel_manager.get_channel("cloud")
    if cloud_channel is None:
        raise HTTPException(
            status_code=503,
            detail="Cloud channel not found. Add 'cloud' to agent channel config.",
        )

    native_payload = _build_native_payload(body)
    session_id = cloud_channel.resolve_session_id(
        sender_id=native_payload["sender_id"],
        channel_meta=native_payload["meta"],
    )

    chat = await workspace.chat_manager.get_or_create_chat(
        session_id,
        native_payload["sender_id"],
        native_payload["channel_id"],
        name=native_payload.get("message", "Cloud Intent")[:20] or "Cloud Intent",
    )

    tracker = workspace.task_tracker
    queue, _ = await tracker.attach_or_start(
        chat.id,
        native_payload,
        cloud_channel.stream_one,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        stream_it = tracker.stream_from_queue(queue, chat.id)
        try:
            async for event_data in stream_it:
                yield event_data
        except Exception as e:
            logger.exception("Cloud chat stream error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await stream_it.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
