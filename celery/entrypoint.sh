#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 07:41:20

# Disable GPU acceleration unless explicitly enabled.  Must be set before any
# TensorFlow import; TF's self_check preloads GPU libs at import time and will
# fail if they are absent on the host.
if [ -z "${DEEPDANBOORU_ALLOW_GPU}" ]; then
	export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:--1}"
	export ROCR_VISIBLE_DEVICES="${ROCR_VISIBLE_DEVICES:-}"
	export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:--1}"
fi

mkdir -p /logs
celery --app celery_worker.celery worker --concurrency=10 -E --loglevel INFO --logfile=/logs/celery.log