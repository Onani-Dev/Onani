#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-30 16:11:15
watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- celery --app Onani.celery_worker.celery worker --concurrency=10 --loglevel=INFO -E
# watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- celery worker --app=worker.app --concurrency=1 --loglevel=INFO