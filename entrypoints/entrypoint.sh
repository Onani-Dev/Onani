#!/bin/sh
set -e

# Initialize Alembic only on first boot; production volumes already contain migrations.
FRESH_DB=0
if [ ! -f /onani/migrations/alembic.ini ]; then
	flask db init
	FRESH_DB=1
fi
flask init-db
flask db upgrade

# Seed default tags on first boot.
if [ "$FRESH_DB" = "1" ]; then
	flask tags --filename meta.json
	flask tags --filename explicit.json
fi

if command -v crond >/dev/null 2>&1; then
	crond
elif command -v cron >/dev/null 2>&1; then
	cron
else
	echo "WARNING: no cron daemon found (expected 'crond' or 'cron'); scheduled tasks will not run." >&2
fi
flask crontab add

# Start Caddy in background
caddy run --config /onani/caddy/Caddyfile &
CADDY_PID=$!

# Start Gunicorn; clean up Caddy when it exits
gunicorn -b 127.0.0.1:8000 -w 10 --threads 100 run:app &
GUNICORN_PID=$!

trap 'kill $CADDY_PID $GUNICORN_PID 2>/dev/null' TERM INT

wait $GUNICORN_PID
