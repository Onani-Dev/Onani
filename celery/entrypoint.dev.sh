#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-29 02:38:19
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A Onani.celery_worker.celery worker --concurrency=10 -E --loglevel INFO