#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-09 13:58:23
celery --app Onani.celery_worker.celery worker --concurrency=10 --loglevel=INFO -E
# watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- celery worker --app=worker.app --concurrency=1 --loglevel=INFO