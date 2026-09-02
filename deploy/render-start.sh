#!/bin/sh
set -eu
sed -i "s|__JARVIS_API_KEY__|${JARVIS_API_KEY:-}|g" /etc/nginx/sites-enabled/default
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
exec nginx -g 'daemon off;'
