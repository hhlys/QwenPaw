"""hClaw CLI launcher.

This module intentionally stays thin: hClaw owns the product command while
QwenPaw remains the in-process core library.
"""
from __future__ import annotations

import os
from pathlib import Path

from . import __version__ as hclaw_version

_PRODUCT_ID = "hclaw"
_PRODUCT_NAME = "hClaw"


def _apply_product_environment() -> None:
    """Install product-layer defaults before QwenPaw imports constants."""
    os.environ.setdefault("HCLAW_PRODUCT_NAME", _PRODUCT_NAME)
    os.environ.setdefault("HCLAW_CORE_PACKAGE", "qwenpaw")
    os.environ.setdefault("QWENPAW_WORKING_DIR", f"~/.{_PRODUCT_ID}")
    os.environ.setdefault("QWENPAW_SECRET_DIR", f"~/.{_PRODUCT_ID}.secret")

    console_dist = Path(__file__).resolve().parents[2] / "web" / "dist"
    if (console_dist / "index.html").is_file():
        os.environ.setdefault("QWENPAW_CONSOLE_STATIC_DIR", str(console_dist))


def _install_cli_branding(qwenpaw_cli, qwenpaw_version: str) -> None:
    """Brand the root CLI without copying QwenPaw's command tree."""
    from qwenpaw.cli.metadata import apply_cli_metadata

    apply_cli_metadata(
        qwenpaw_cli,
        name=_PRODUCT_ID,
        help_text=f"{_PRODUCT_NAME} CLI.",
        version_text=(
            f"{_PRODUCT_NAME}, version {hclaw_version} "
            f"(qwenpaw core {qwenpaw_version})"
        ),
    )


def cli(*args, **kwargs):
    """Run hClaw by delegating to the QwenPaw core CLI in the same process."""
    _apply_product_environment()

    # Import QwenPaw only after product defaults are in os.environ. QwenPaw
    # computes WORKING_DIR/SECRET_DIR at import time in qwenpaw.constant.
    from qwenpaw.__version__ import __version__ as qwenpaw_version
    from qwenpaw.cli.main import cli as qwenpaw_cli

    _install_cli_branding(qwenpaw_cli, qwenpaw_version)
    return qwenpaw_cli(*args, **kwargs)


if __name__ == "__main__":
    cli()
