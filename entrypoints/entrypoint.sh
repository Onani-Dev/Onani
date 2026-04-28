#!/bin/sh
set -e

# Disable GPU acceleration unless explicitly enabled.  Must be set before any
# TensorFlow import; TF's self_check preloads GPU libs (libhsa-runtime64 for
# ROCm, libcuda for NVIDIA) at import time and will fail if they are absent.
if [ -z "${DEEPDANBOORU_ALLOW_GPU}" ]; then
	export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:--1}"
	export ROCR_VISIBLE_DEVICES="${ROCR_VISIBLE_DEVICES:-}"
	export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:--1}"
fi

# Initialize Alembic only on first boot; production volumes already contain migrations.
FRESH_DB=0
if [ ! -f /onani/migrations/alembic.ini ]; then
	flask db init
	FRESH_DB=1
fi

# Sync migration version files from the image into the (possibly volume-mounted)
# migrations directory. Uses -n so existing files are never overwritten, and new
# migrations bundled in a newer image are picked up automatically on first start.
if [ -d /onani/migrations_bundled/versions ] && [ -d /onani/migrations/versions ]; then
	cp -n /onani/migrations_bundled/versions/*.py /onani/migrations/versions/ 2>/dev/null || true
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
