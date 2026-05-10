# -*- coding: utf-8 -*-
"""Cloud-edge custom channel.

This channel is intentionally self-contained so it can be copied to
``~/.qwenpaw/custom_channels/cloud_edge`` without modifying QwenPaw core.

Network direction:
- Edge -> ClawHub register/heartbeat/poll.
- Edge -> ClawHub task events/results.
- No inbound port from ClawHub to edge is required.
"""

from __future__ import annotations

import asyncio
import getpass
import logging
import platform
import socket
import time
from types import SimpleNamespace
from typing import Any, Optional

import httpx

from qwenpaw.__version__ import __version__
from qwenpaw.app.channels.base import (
    BaseChannel,
    ContentType,
    OnReplySent,
    ProcessHandler,
    TextContent,
)

logger = logging.getLogger(__name__)


class CloudEdgeChannel(BaseChannel):
    """Edge-side ClawHub channel using outbound HTTP polling."""

    channel = "cloud_edge"
    uses_manager_queue = False

    def __init__(
        self,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
    ) -> None:
        super().__init__(process, on_reply_sent=on_reply_sent)
        self.config = self._normalize_config(config)
        self.enabled = self.config.enabled
        self._client: httpx.AsyncClient | None = None
        self._loop_task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ) -> "CloudEdgeChannel":
        return cls(
            process=process,
            config={"enabled": False},
            on_reply_sent=on_reply_sent,
        )

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
        **kwargs: Any,
    ) -> "CloudEdgeChannel":
        del kwargs
        return cls(
            process=process,
            config=config,
            on_reply_sent=on_reply_sent,
        )

    @staticmethod
    def _normalize_config(config: Any) -> SimpleNamespace:
        defaults = {
            "enabled": False,
            "bot_prefix": "",
            "filter_tool_messages": False,
            "filter_thinking": False,
            "dm_policy": "open",
            "group_policy": "open",
            "allow_from": [],
            "deny_message": "",
            "require_mention": False,
            "hub_url": "",
            "node_id": "",
            "tenant_id": "",
            "group_name": "",
            "username": "",
            "token": "",
            "host_ip": "",
            "port": 8088,
            "heartbeat_interval": 30,
            "poll_interval": 2,
            "capabilities": ["agent", "skill", "shell", "file", "cron"],
            "metadata": {},
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

    def resolve_session_id(
        self,
        sender_id: str,
        channel_meta: Optional[dict] = None,
    ) -> str:
        del sender_id
        if channel_meta and channel_meta.get("conversation_id"):
            return str(channel_meta["conversation_id"])
        if channel_meta and channel_meta.get("session_id"):
            return str(channel_meta["session_id"])
        return f"edge:{self.config.node_id}:default"

    def build_agent_request_from_native(self, native_payload: Any) -> Any:
        payload = native_payload if isinstance(native_payload, dict) else {}
        meta = payload.get("meta") or {}
        instruction = payload.get("instruction") or payload.get("message") or ""
        sender_id = payload.get("sender_id") or "clawhub"
        session_id = self.resolve_session_id(sender_id, meta)

        content_parts = []
        if instruction:
            content_parts.append(
                TextContent(type=ContentType.TEXT, text=str(instruction)),
            )

        request = self.build_agent_request_from_user_content(
            channel_id=self.channel,
            sender_id=sender_id,
            session_id=session_id,
            content_parts=content_parts,
            channel_meta=meta,
        )
        request.channel_meta = meta
        return request

    async def start(self) -> None:
        if not self.enabled:
            logger.debug("cloud_edge custom channel disabled")
            return
        self._validate_config()
        self._stop_event = asyncio.Event()
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0, read=30.0),
        )
        self._loop_task = asyncio.create_task(
            self._run_loop(),
            name="cloud_edge_loop",
        )
        logger.info(
            "cloud_edge custom channel started: node_id=%s",
            self.config.node_id,
        )

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._loop_task is not None:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        logger.info("cloud_edge custom channel stopped")

    async def health_check(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "channel": self.channel,
                "status": "disabled",
                "detail": "cloud_edge custom channel is disabled.",
            }
        if not self.config.hub_url or not self.config.node_id:
            return {
                "channel": self.channel,
                "status": "unhealthy",
                "detail": "hub_url and node_id are required.",
            }
        return {
            "channel": self.channel,
            "status": "healthy" if self._loop_task else "starting",
            "detail": f"Polling {self._base_url()} as {self.config.node_id}.",
        }

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        """Send cron/proactive output back to ClawHub as a node event."""

        del to_handle
        meta = dict(meta or {})
        conversation_id = str(
            meta.get("conversation_id")
            or meta.get("session_id")
            or f"edge:{self.config.node_id}:events",
        )
        event_type = str(meta.get("event_type") or "cron_message")
        await self._post_json(
            "/api/edge/tasks/events",
            {
                "nodeId": self.config.node_id,
                "conversationId": conversation_id,
                "eventType": event_type,
                "content": text,
                "rawEvent": {
                    "object": "cloud_edge_channel_send",
                    "event_type": event_type,
                    "node_id": self.config.node_id,
                    "conversation_id": conversation_id,
                    "content": text,
                    "meta": meta,
                },
                "token": self.config.token,
            },
        )

    def to_handle_from_target(self, *, user_id: str, session_id: str) -> str:
        return user_id or session_id or "clawhub"

    def _validate_config(self) -> None:
        missing = []
        if not self.config.hub_url:
            missing.append("hub_url")
        if not self.config.node_id:
            missing.append("node_id")
        if not self.config.tenant_id:
            missing.append("tenant_id")
        if not self.config.group_name:
            missing.append("group_name")
        if missing:
            raise ValueError(
                "cloud_edge custom channel missing required config: "
                + ", ".join(missing),
            )

    def _base_url(self) -> str:
        return str(self.config.hub_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"X-Edge-Token": self.config.token} if self.config.token else {}

    def _reported_host_ip(self) -> str:
        if self.config.host_ip:
            return str(self.config.host_ip)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "127.0.0.1"

    def _register_payload(self) -> dict[str, Any]:
        username = self.config.username or getpass.getuser()
        return {
            "nodeId": self.config.node_id,
            "tenantId": self.config.tenant_id,
            "groupName": self.config.group_name,
            "username": username,
            "hostIp": self._reported_host_ip(),
            "port": self.config.port,
            "osName": platform.system().lower(),
            "arch": platform.machine(),
            "qwenpawVersion": __version__,
            "capabilities": self.config.capabilities,
            "metadata": self.config.metadata,
            "token": self.config.token,
        }

    def _heartbeat_payload(self) -> dict[str, Any]:
        return {
            "nodeId": self.config.node_id,
            "hostIp": self._reported_host_ip(),
            "port": self.config.port,
            "qwenpawVersion": __version__,
            "capabilities": self.config.capabilities,
            "metadata": self.config.metadata,
            "token": self.config.token,
        }

    async def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("cloud_edge client is not started")
        response = await self._client.post(
            f"{self._base_url()}{path}",
            json=payload,
            headers=self._headers(),
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}

    async def _run_loop(self) -> None:
        assert self._stop_event is not None
        registered = False
        next_heartbeat = 0.0

        while not self._stop_event.is_set():
            try:
                if not registered:
                    await self._register()
                    registered = True

                now = time.monotonic()
                if now >= next_heartbeat:
                    await self._heartbeat()
                    next_heartbeat = now + max(
                        int(self.config.heartbeat_interval),
                        1,
                    )

                task = await self._poll_task()
                if task.get("taskId"):
                    await self._execute_task(task)
                    continue

                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=max(int(self.config.poll_interval), 1),
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                registered = False
                logger.warning(
                    "cloud_edge loop iteration failed",
                    exc_info=True,
                )
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass

    async def _register(self) -> None:
        result = await self._post_json(
            "/api/edge/nodes/register",
            self._register_payload(),
        )
        logger.info(
            "cloud_edge registered: node_id=%s status=%s",
            result.get("nodeId", self.config.node_id),
            result.get("status", "-"),
        )

    async def _heartbeat(self) -> None:
        result = await self._post_json(
            "/api/edge/nodes/heartbeat",
            self._heartbeat_payload(),
        )
        logger.debug(
            "cloud_edge heartbeat ok: node_id=%s status=%s",
            result.get("nodeId", self.config.node_id),
            result.get("status", "-"),
        )

    async def _poll_task(self) -> dict[str, Any]:
        return await self._post_json(
            "/api/edge/tasks/poll",
            {"nodeId": self.config.node_id, "token": self.config.token},
        )

    async def _execute_task(self, task: dict[str, Any]) -> None:
        task_id = str(task["taskId"])
        conversation_id = str(
            task.get("conversationId") or f"edge:{self.config.node_id}:default",
        )
        instruction = str(task.get("instruction") or "")
        logger.info(
            "cloud_edge task received: task_id=%s conversation_id=%s",
            task_id,
            conversation_id,
        )

        payload = {
            "instruction": instruction,
            "sender_id": "clawhub",
            "meta": {
                "conversation_id": conversation_id,
                "task_id": task_id,
                "node_id": self.config.node_id,
            },
        }
        request = self.build_agent_request_from_native(payload)
        sequence = 0
        final_response = ""
        status = "completed"
        error = ""

        try:
            async for event in self._process(request):
                sequence += 1
                raw_event = self._event_to_dict(event)
                content = self._extract_event_text(raw_event)
                if content and (
                    raw_event.get("object") == "content" or not final_response
                ):
                    final_response += content
                if raw_event.get("error"):
                    status = "failed"
                    error = str(raw_event["error"])
                await self._report_task_event(
                    task_id=task_id,
                    conversation_id=conversation_id,
                    sequence=sequence,
                    event_type=str(raw_event.get("object") or "event"),
                    content=content,
                    raw_event=raw_event,
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            status = "failed"
            error = str(exc) or exc.__class__.__name__
            logger.exception("cloud_edge task failed: task_id=%s", task_id)

        await self._complete_task(
            task_id=task_id,
            conversation_id=conversation_id,
            status=status,
            response=final_response,
            error=error,
        )
        logger.info(
            "cloud_edge task completed: task_id=%s status=%s",
            task_id,
            status,
        )

    async def _report_task_event(
        self,
        *,
        task_id: str,
        conversation_id: str,
        sequence: int,
        event_type: str,
        content: str,
        raw_event: dict[str, Any],
    ) -> None:
        await self._post_json(
            f"/api/edge/tasks/{task_id}/events",
            {
                "nodeId": self.config.node_id,
                "conversationId": conversation_id,
                "sequence": sequence,
                "eventType": event_type,
                "content": content,
                "rawEvent": raw_event,
                "token": self.config.token,
            },
        )

    async def _complete_task(
        self,
        *,
        task_id: str,
        conversation_id: str,
        status: str,
        response: str,
        error: str,
    ) -> None:
        await self._post_json(
            f"/api/edge/tasks/{task_id}/complete",
            {
                "nodeId": self.config.node_id,
                "conversationId": conversation_id,
                "status": status,
                "response": response,
                "error": error,
                "rawResult": {
                    "status": status,
                    "response": response,
                    "error": error,
                },
                "token": self.config.token,
            },
        )

    def _append_native_cron_usage(
        self,
        instruction: str,
        *,
        task_id: str,
        conversation_id: str,
    ) -> str:
        agent_id = getattr(self._workspace, "agent_id", None) or "default"
        local_base_url = f"http://127.0.0.1:{int(self.config.port)}"
        usage = f"""

---
边侧定时任务规则：
如果本次云端任务要求创建“定时任务、周期任务、每隔一段时间执行的任务”，必须使用 QwenPaw 原生 cron 能力创建任务，不要自己创建后台脚本、while 循环、外部计划任务或单独的 Python 进程。

创建后的任务应该能在边侧 QwenPaw 控制台“定时任务”页面看到。

推荐命令格式：

```bash
qwenpaw cron create \\
  --base-url {local_base_url} \\
  --agent-id {agent_id} \\
  --type agent \\
  --name "任务名称" \\
  --cron "*/5 * * * *" \\
  --channel cloud_edge \\
  --target-user "clawhub" \\
  --target-session "{conversation_id}" \\
  --text "这里填写每次定时执行时要交给边侧 agent 的具体任务"
```

上下文：
- task_id: {task_id}
- conversation_id: {conversation_id}

注意：
- `--channel` 必须是 `cloud_edge`，这样定时任务执行结果会回传 ClawHub。
- `--target-session` 必须使用本次 conversation_id，这样结果会显示到同一个云端会话。
- 如果只是立即执行一次，不要创建 cron。
"""
        return instruction.rstrip() + usage

    @staticmethod
    def _event_to_dict(event: Any) -> dict[str, Any]:
        if hasattr(event, "model_dump"):
            return event.model_dump(mode="json")
        if hasattr(event, "dict"):
            return event.dict()
        return {"object": getattr(event, "object", "event"), "text": str(event)}

    @staticmethod
    def _extract_event_text(event: dict[str, Any]) -> str:
        text = event.get("text")
        if isinstance(text, str) and text:
            return text

        content = event.get("content")
        if isinstance(content, list):
            parts = [
                str(part.get("text"))
                for part in content
                if isinstance(part, dict)
                and part.get("type") == "text"
                and part.get("text")
            ]
            if parts:
                return "".join(parts)

        output = event.get("output")
        if isinstance(output, list):
            parts: list[str] = []
            for message in output:
                if not isinstance(message, dict):
                    continue
                for part in message.get("content") or []:
                    if (
                        isinstance(part, dict)
                        and part.get("type") == "text"
                        and part.get("text")
                    ):
                        parts.append(str(part["text"]))
            if parts:
                return "".join(parts)

        err = event.get("error")
        return str(err) if err else ""
