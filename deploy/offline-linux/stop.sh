#!/usr/bin/env bash
set -euo pipefail

APP_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$APP_HOME/run/qwenpaw.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "[stop] QwenPaw is not running (pid file missing)."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if [[ -z "$PID" ]] || ! kill -0 "$PID" 2>/dev/null; then
  echo "[stop] QwenPaw is not running."
  rm -f "$PID_FILE"
  exit 0
fi

echo "[stop] Stopping QwenPaw pid=$PID ..."
kill "$PID"
for _ in $(seq 1 30); do
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "[stop] Done."
    exit 0
  fi
  sleep 1
done

echo "[stop] Process did not exit in 30s, killing..."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "[stop] Done."
