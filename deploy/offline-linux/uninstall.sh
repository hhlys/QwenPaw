#!/usr/bin/env bash
set -euo pipefail

APP_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$APP_HOME/stop.sh" || true

echo "This script stops QwenPaw only. It does not delete user data."
echo "To remove all files, delete the extracted directory manually:"
echo "  rm -rf '$APP_HOME'"
