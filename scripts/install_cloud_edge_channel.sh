#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

WORKING_DIR="${QWENPAW_WORKING_DIR:-${HOME}/.qwenpaw}"
SOURCE_DIR="${1:-${REPO_ROOT}/examples/custom_channels/cloud_edge}"
TARGET_DIR="${WORKING_DIR}/custom_channels/cloud_edge"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Source directory not found: ${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "$(dirname "${TARGET_DIR}")"
rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

echo "Installed cloud_edge custom channel to: ${TARGET_DIR}"
echo "Next: enable channels.cloud_edge in your agent.json, then restart qwenpaw app."
