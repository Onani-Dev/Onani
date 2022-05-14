# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 01:40:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 07:15:52

from celery import Celery


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
