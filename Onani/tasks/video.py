# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-26 00:35:31
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-04-28 21:16:05

from celery import shared_task
import ffmpeg


@shared_task
def test(string):
    return "".join(reversed(string))


@shared_task
def encode(inname, outname):
    stream = ffmpeg.input(inname)
    stream = ffmpeg.output(
        stream,
        outname,
        **{"crf": 50, "preset": "fast", "cpu-used": -8, "deadline": "realtime"}
    )
    ffmpeg.run(stream)
