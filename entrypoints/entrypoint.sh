#!/bin/sh
flask db init
flask init-db
flask db upgrade

# Start cron and add the jobs
crond
flask crontab add

gunicorn -b 0.0.0.0:5000 -w 10 --threads 100 run:app