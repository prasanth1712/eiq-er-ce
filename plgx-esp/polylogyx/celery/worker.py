# -*- coding: utf-8 -*-

from celery.signals import after_task_publish, before_task_publish, task_postrun, task_prerun
from flask import current_app

from polylogyx.application import create_app
from polylogyx.celery.tasks import celery  # noqa
from polylogyx.settings import CurrentConfig

app = create_app(config=CurrentConfig)


class CelerySignalType:
    """
    Celery worker signal types
    """

    BEFORE_PUBLISH = "BEFORE_PUBLISH"
    AFTER_PUBLISH = "AFTER_PUBLISH"
    BEFORE_RUN = "BEFORE_RUN"
    AFTER_RUN = "AFTER_RUN"
    RECEIVED = "RECEIVED"


@before_task_publish.connect
def task_before_publish(sender=None, headers=None, body=None, **kwargs):
    info = headers if "task" in headers else body
    with app.app_context():
        current_app.logger.info(
            "Celery '{0}' signal received with task name '{1}', id '{2}'".format(
                CelerySignalType.BEFORE_PUBLISH, info["task"], info["id"]
            )
        )


@after_task_publish.connect
def task_after_publish(sender=None, headers=None, body=None, **kwargs):
    info = headers if "task" in headers else body
    with app.app_context():
        current_app.logger.info(
            "Celery '{0}' signal received with task name '{1}', id '{2}'".format(
                CelerySignalType.AFTER_PUBLISH, info["task"], info["id"]
            )
        )

@task_prerun.connect
def task_pre_run_handler(task_id=None, task=None, **kwargs):
    with app.app_context():
        current_app.logger.info(
            "Celery '{0}' signal received with task name '{1}', id '{2}'".format(
                CelerySignalType.BEFORE_RUN, task.name, task_id
            )
        )


@task_postrun.connect
def task_post_run_handler(task_id=None, task=None, **kwargs):
    with app.app_context():
        current_app.logger.info(
            "Celery '{0}' signal received with task name '{1}', id '{2}'".format(
                CelerySignalType.AFTER_RUN, task.name, task_id
            )
        )
