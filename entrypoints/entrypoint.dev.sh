#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-04-12 03:41:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-07 14:42:48

# Initialize the database if it has not been already.
FRESH_DB=0
if [ ! -f migrations/alembic.ini ]; then
	flask db init
	FRESH_DB=1
fi
flask init-db

# Apply any pending migrations (safe to run on both fresh and existing DBs).
flask db upgrade

# Seed default tags on first boot.
if [ "$FRESH_DB" = "1" ]; then
	flask tags --filename meta.json
	flask tags --filename explicit.json
fi

# Start cron and add the jobs
if command -v crond >/dev/null 2>&1; then
	crond
elif command -v cron >/dev/null 2>&1; then
	cron
else
	echo "WARNING: no cron daemon found (expected 'crond' or 'cron'); scheduled tasks will not run." >&2
fi
flask crontab add

# Run Flask's built-in dev server in debug mode
flask run --host=0.0.0.0 --port=5000 --debug