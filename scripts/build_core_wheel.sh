#!/usr/bin/env bash
set -euo pipefail

# Build the QwenPaw core/lib wheel for product-layer packaging.
# Run from repo root:
#   bash scripts/build_core_wheel.sh

OUT_DIR="${1:-dist-core}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"
echo "[build_core_wheel] Building qwenpaw core wheel -> $REPO_ROOT/$OUT_DIR"

python -m pip install --quiet build
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

python -m build --wheel --outdir "$OUT_DIR" .

echo "[build_core_wheel] Done. Wheel(s) in: $REPO_ROOT/$OUT_DIR"
