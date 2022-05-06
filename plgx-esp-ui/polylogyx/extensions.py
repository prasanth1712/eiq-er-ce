# -*- coding: utf-8 -*-

from flask_bcrypt import Bcrypt
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_authorize import Authorize
from werkzeug.exceptions import HTTPException
from flask import g
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal
from raven.contrib.flask import Sentry


def make_celery(app, celery):
    """ From http://flask.pocoo.org/docs/0.10/patterns/celery/ """
    # Register our custom serializer type before updating the configuration.
    from kombu.serialization import register
    from polylogyx.celery_serializer import djson_dumps, djson_loads

    register(
        'djson', djson_dumps, djson_loads,
        content_type='application/x-djson',
        content_encoding='utf-8'
    )

    # Actually update the config
    celery.config_from_object(app.config)

    # Register Sentry client
    if 'SENTRY_DSN' in app.config and app.config['SENTRY_DSN']:
        client = Client(app.config['SENTRY_DSN'])
        # register a custom filter to filter out duplicate logs
        register_logger_signal(client)
        # hook into the Celery error handler
        register_signal(client)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def get_current_user():
    """
    Returns current user being saved from 'require_api_key' decorator into the global variable 'g'
    """
    return g.user


class MyUnauthorizedException(HTTPException):
    """
    Custom exception to be raised when user is not allowed to access a resource
    """
    code = 403
    description = 'Access to this resource is Forbidden!'


bcrypt = Bcrypt()
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
cache = Cache()
authorize = Authorize(current_user=get_current_user, exception=MyUnauthorizedException, strict=False)
ldap_manager = LDAP3LoginManager()
login_manager = LoginManager()
sentry = Sentry()
