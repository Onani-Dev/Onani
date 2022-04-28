#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-29 02:02:56
celery -A Onani.celery_worker.celery worker --concurrency=10 -E --loglevel INFO