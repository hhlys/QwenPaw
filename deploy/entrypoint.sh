#!/bin/sh
# Substitute QWENPAW_PORT in supervisord template and start supervisord.
# Default port 8088; override at runtime with -e QWENPAW_PORT=3000.
set -e

# Auto-initialize if config.json is missing (bind mount with empty directory).
if [ ! -f "${QWENPAW_WORKING_DIR}/config.json" ]; then
  echo "⚠️  No config.json found in ${QWENPAW_WORKING_DIR}"
  echo "📦 Running initialization..."
  qwenpaw init --defaults --accept-security
  echo "✅ Initialization complete!"
else
  echo "✓ Config found in ${QWENPAW_WORKING_DIR}, skipping initialization."
fi

# Install bundled managed-instance chat channel for ClawHub if not present.
if [ -d "/app/bundled_custom_channels/clawhub_chat" ] \
  && [ ! -d "${QWENPAW_WORKING_DIR}/custom_channels/clawhub_chat" ]; then
  echo "Installing bundled clawhub_chat custom channel..."
  mkdir -p "${QWENPAW_WORKING_DIR}/custom_channels"
  cp -R /app/bundled_custom_channels/clawhub_chat \
    "${QWENPAW_WORKING_DIR}/custom_channels/clawhub_chat"
fi

export QWENPAW_PORT="${QWENPAW_PORT:-8088}"
envsubst '${QWENPAW_PORT}' \
  < /etc/supervisor/conf.d/supervisord.conf.template \
  > /etc/supervisor/conf.d/supervisord.conf
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
