#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 07:17:43
mkdir -p /logs
chown -R app:app /logs 2>/dev/null || true
exec su -s /bin/sh app -c "celery --app celery_worker.celery worker --concurrency=10 --loglevel=INFO -E --logfile=/logs/celery.log"
# watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- celery worker --app=worker.app --concurrency=1 --loglevel=INFO