#!/usr/bin/env bash
set -euo pipefail

APP_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$APP_HOME/env.sh"
PID_FILE="$APP_HOME/run/qwenpaw.pid"
LOG_FILE="$APP_HOME/logs/qwenpaw.log"
VENV_DIR="$APP_HOME/runtime/venv"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

export QWENPAW_HOST="${QWENPAW_HOST:-127.0.0.1}"
export QWENPAW_PORT="${QWENPAW_PORT:-8080}"
export QWENPAW_WORKING_DIR="${QWENPAW_WORKING_DIR:-$APP_HOME/data/.qwenpaw}"
export QWENPAW_SECRET_DIR="${QWENPAW_SECRET_DIR:-$APP_HOME/data/.qwenpaw.secret}"
export QWENPAW_BACKUP_DIR="${QWENPAW_BACKUP_DIR:-$APP_HOME/data/backups}"
export QWENPAW_OFFLINE=1
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$APP_HOME/browser/ms-playwright}"

mkdir -p "$APP_HOME/logs" "$APP_HOME/run" "$QWENPAW_WORKING_DIR" "$QWENPAW_SECRET_DIR" "$QWENPAW_BACKUP_DIR"

if [[ ! -x "$VENV_DIR/bin/qwenpaw" ]]; then
  "$APP_HOME/install.sh"
fi

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE")"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[start] QwenPaw is already running: pid=$OLD_PID"
    exit 0
  fi
fi

echo "[start] Starting QwenPaw at http://$QWENPAW_HOST:$QWENPAW_PORT ..."
nohup "$VENV_DIR/bin/qwenpaw" app --host "$QWENPAW_HOST" --port "$QWENPAW_PORT" >"$LOG_FILE" 2>&1 &
echo "$!" > "$PID_FILE"
echo "[start] pid=$(cat "$PID_FILE"), log=$LOG_FILE"
