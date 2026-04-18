#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 07:41:20
mkdir -p /logs
celery --app celery_worker.celery worker --concurrency=10 -E --loglevel INFO --logfile=/logs/celery.log