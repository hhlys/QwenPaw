# -*- coding: utf-8 -*-
"""Helpers for adjusting CLI metadata on top of the QwenPaw core CLI."""
from __future__ import annotations

from collections.abc import Callable

import click


def apply_cli_metadata(
    cli: click.Command,
    *,
    name: str,
    help_text: str,
    version_text: str | Callable[[], str] | None = None,
) -> click.Command:
    """Apply display-only metadata to a Click command.

    Downstream launchers can reuse the QwenPaw command tree in-process while
    presenting their own command name and version text. This deliberately only
    touches Click metadata; it does not scaffold projects or encode product
    naming rules in the core.
    """
    cli.name = name
    cli.help = help_text

    if version_text is not None:

        def _version_callback(ctx, _param, value):
            if not value or ctx.resilient_parsing:
                return
            resolved = version_text() if callable(version_text) else version_text
            click.echo(resolved)
            ctx.exit()

        for param in getattr(cli, "params", []):
            if getattr(param, "name", None) == "version":
                param.callback = _version_callback
                break

    return cli
