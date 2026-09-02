#!/bin/sh
set -eu
: "${JARVIS_ADMIN_USER:?Set JARVIS_ADMIN_USER in Render}"
: "${JARVIS_ADMIN_PASSWORD:?Set JARVIS_ADMIN_PASSWORD in Render}"
htpasswd -bc /etc/nginx/.htpasswd "$JARVIS_ADMIN_USER" "$JARVIS_ADMIN_PASSWORD" >/dev/null
sed -i "s|__JARVIS_API_KEY__|${JARVIS_API_KEY:-}|g" /etc/nginx/sites-enabled/default
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
exec nginx -g 'daemon off;'
