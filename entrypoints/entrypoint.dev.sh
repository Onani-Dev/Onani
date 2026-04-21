#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-04-12 03:41:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-07 14:42:48

# Initialize the database if it has not been already.
flask db init
flask init-db

# Apply any pending migrations (safe to run on both fresh and existing DBs).
flask db upgrade

# Start cron and add the jobs
crond
flask crontab add

# Run Flask's built-in dev server in debug mode
flask run --host=0.0.0.0 --port=5000 --debug