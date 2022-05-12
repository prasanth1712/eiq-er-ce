# -*- coding: utf-8 -*-

from polylogyx.application import create_app
from polylogyx.settings import CurrentConfig
from polylogyx.tasks import celery  # noqa

from celery.signals import task_prerun, task_postrun, before_task_publish, after_task_publish
from flask import current_app

app = create_app(config=CurrentConfig)


class CelerySignalType:
    """
    Celery worker signal types
    """
    BEFORE_PUBLISH = 'BEFORE_PUBLISH'
    AFTER_PUBLISH = 'AFTER_PUBLISH'
    BEFORE_RUN = 'BEFORE_RUN'
    AFTER_RUN = 'AFTER_RUN'
    RECEIVED = 'RECEIVED'
    TASK_WAIT_TIME = 'TASK_WAIT_TIME'
    TASK_COMPLETION_TIME = 'TASK_COMPLETION_TIME'


@before_task_publish.connect
def task_before_publish(sender=None, headers=None, body=None, **kwargs):
    info = headers if 'task' in headers else body
    with app.app_context():
        current_app.logger.info("Celery '{0}' signal received with task name '{1}', id '{2}'".format(
            CelerySignalType.BEFORE_PUBLISH, info['task'], info['id']))


@after_task_publish.connect
def task_after_publish(sender=None, headers=None, body=None, **kwargs):
    info = headers if 'task' in headers else body
    with app.app_context():
        current_app.logger.info("Celery '{0}' signal received with task name '{1}', id '{2}'".format(
            CelerySignalType.AFTER_PUBLISH, info['task'], info['id']))


# @task_received.connect
# def task_received(request=None, **kwargs):
#     with app.app_context():
#         current_app.logger.info("Celery '{0}' signal received with task name '{1}', id '{2}'".format(
#             CelerySignalType.RECEIVED, request.task_name, request.task_id))
#         current_app.logger.debug("Payload received to the celery task '{0}' and task id '{1}' is:\n{2}".format(
#             request.task_name, request.task_id, request.body))


@task_prerun.connect
def task_pre_run_handler(task_id=None, task=None,  **kwargs):
    with app.app_context():
        current_app.logger.info("Celery '{0}' signal received with task name '{1}', id '{2}'".format(
            CelerySignalType.BEFORE_RUN, task.name, task_id))


@task_postrun.connect
def task_post_run_handler(task_id=None, task=None,  **kwargs):
    with app.app_context():
        current_app.logger.info("Celery '{0}' signal received with task name '{1}', id '{2}'".format(
            CelerySignalType.AFTER_RUN, task.name, task_id))
