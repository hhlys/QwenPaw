#!/usr/bin/env bash
set -euo pipefail

APP_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_HOME/runtime/venv"
WHEELS_DIR="$APP_HOME/wheels"
APP_DIR="$APP_HOME/app"

find_python() {
  if [[ -x "$APP_HOME/runtime/python/bin/python3" ]]; then
    echo "$APP_HOME/runtime/python/bin/python3"
    return 0
  fi
  if [[ -x "$APP_HOME/runtime/python/install/bin/python3" ]]; then
    echo "$APP_HOME/runtime/python/install/bin/python3"
    return 0
  fi
  echo "Bundled Python runtime not found under runtime/python." >&2
  return 1
}

PYTHON_BIN="$(find_python)"
mkdir -p "$APP_HOME/data" "$APP_HOME/logs" "$APP_HOME/run"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[install] Creating virtual environment..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

QWENPAW_WHEEL="$(find "$APP_DIR" -maxdepth 1 -name 'qwenpaw-*.whl' | sort | tail -n 1)"
if [[ -z "$QWENPAW_WHEEL" ]]; then
  echo "[install] qwenpaw wheel not found in $APP_DIR" >&2
  exit 1
fi

echo "[install] Installing QwenPaw from offline wheelhouse..."
"$VENV_DIR/bin/python" -m pip install \
  --no-index \
  --find-links "$WHEELS_DIR" \
  --upgrade \
  "$QWENPAW_WHEEL"

echo "[install] Verifying qwenpaw command..."
"$VENV_DIR/bin/qwenpaw" --help >/dev/null

echo "[install] Done."
