# -*- coding: utf-8 -*-
"""Edge node commands for ClawHub registration."""

from __future__ import annotations

import getpass
import json
import platform
import socket
import time
from typing import Any

import click
import httpx

from ..__version__ import __version__


def _detect_host_ip() -> str:
    """Best-effort local IP detection without requiring external traffic."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def _parse_metadata(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"--metadata must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise click.ClickException("--metadata must be a JSON object")
    return data


def _post_json(
    client: httpx.Client,
    url: str,
    payload: dict[str, Any],
    token: str,
) -> dict[str, Any]:
    headers = {"X-Edge-Token": token} if token else {}
    response = client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


@click.group(name="edge")
def edge_group() -> None:
    """Register and run a Linux edge QwenPaw node."""


@edge_group.command("daemon")
@click.option(
    "--hub-url",
    required=True,
    envvar="QWENPAW_EDGE_HUB_URL",
    help="ClawHub base URL, e.g. http://host:18080",
)
@click.option(
    "--node-id",
    required=True,
    envvar="QWENPAW_EDGE_NODE_ID",
    help="Stable edge node id.",
)
@click.option(
    "--tenant-id",
    required=True,
    envvar="QWENPAW_EDGE_TENANT_ID",
    help="Tenant id managed by ClawHub.",
)
@click.option(
    "--group",
    "group_name",
    required=True,
    envvar="QWENPAW_EDGE_GROUP",
    help="Edge node group name.",
)
@click.option(
    "--username",
    default=lambda: getpass.getuser(),
    show_default="current user",
    envvar="QWENPAW_EDGE_USERNAME",
)
@click.option("--host-ip", default="", help="Reported edge host IP. Auto-detected if omitted.")
@click.option("--port", default=8088, show_default=True, type=int, help="Reported QwenPaw service port.")
@click.option(
    "--token",
    default="",
    envvar="QWENPAW_EDGE_TOKEN",
    help="Optional ClawHub edge registration token.",
)
@click.option("--interval", default=30, show_default=True, type=int, help="Heartbeat interval seconds.")
@click.option(
    "--capability",
    "capabilities",
    multiple=True,
    help="Capability value. Can be repeated.",
)
@click.option("--metadata", default="", help="Optional JSON object metadata.")
@click.option("--once", is_flag=True, help="Register once and exit without heartbeat loop.")
def edge_daemon(
    hub_url: str,
    node_id: str,
    tenant_id: str,
    group_name: str,
    username: str,
    host_ip: str,
    port: int,
    token: str,
    interval: int,
    capabilities: tuple[str, ...],
    metadata: str,
    once: bool,
) -> None:
    """Register this QwenPaw process as an edge node and keep heartbeats."""
    base_url = hub_url.rstrip("/")
    reported_ip = host_ip.strip() or _detect_host_ip()
    caps = list(capabilities) or ["agent", "skill", "shell", "file"]
    metadata_obj = _parse_metadata(metadata)

    register_payload = {
        "nodeId": node_id,
        "tenantId": tenant_id,
        "groupName": group_name,
        "username": username,
        "hostIp": reported_ip,
        "port": port,
        "osName": platform.system().lower(),
        "arch": platform.machine(),
        "qwenpawVersion": __version__,
        "capabilities": caps,
        "metadata": metadata_obj,
        "token": token,
    }
    heartbeat_payload = {
        "nodeId": node_id,
        "hostIp": reported_ip,
        "port": port,
        "qwenpawVersion": __version__,
        "capabilities": caps,
        "metadata": metadata_obj,
        "token": token,
    }

    register_url = f"{base_url}/api/edge/nodes/register"
    heartbeat_url = f"{base_url}/api/edge/nodes/heartbeat"

    timeout = httpx.Timeout(15.0, connect=10.0)
    with httpx.Client(timeout=timeout) as client:
        try:
            result = _post_json(client, register_url, register_payload, token)
        except httpx.HTTPError as exc:
            raise click.ClickException(f"Edge register failed: {exc}") from exc

        click.echo(
            "[edge] registered: "
            f"node_id={result.get('nodeId', node_id)} "
            f"status={result.get('status', '-')}"
        )

        if once:
            return

        click.echo(f"[edge] heartbeat loop started: interval={interval}s")
        while True:
            try:
                time.sleep(max(interval, 1))
                result = _post_json(client, heartbeat_url, heartbeat_payload, token)
                click.echo(
                    "[edge] heartbeat ok: "
                    f"node_id={result.get('nodeId', node_id)} "
                    f"status={result.get('status', '-')}"
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    click.echo("[edge] node not found on hub, registering again...")
                    _post_json(client, register_url, register_payload, token)
                    continue
                click.echo(f"[edge] heartbeat failed: {exc}", err=True)
            except httpx.HTTPError as exc:
                click.echo(f"[edge] heartbeat failed: {exc}", err=True)
            except KeyboardInterrupt:
                click.echo("\n[edge] stopped")
                return
