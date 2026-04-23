#!/bin/sh
set -e

flask db init
flask init-db
flask db upgrade

crond
flask crontab add

# Start Caddy in background
caddy run --config /onani/caddy/Caddyfile &
CADDY_PID=$!

# Start Gunicorn; clean up Caddy when it exits
gunicorn -b 127.0.0.1:8000 -w 10 --threads 100 run:app &
GUNICORN_PID=$!

trap 'kill $CADDY_PID $GUNICORN_PID 2>/dev/null' TERM INT

wait $GUNICORN_PID
