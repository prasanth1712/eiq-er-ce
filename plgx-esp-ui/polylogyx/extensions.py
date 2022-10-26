# -*- coding: utf-8 -*-

from flask_bcrypt import Bcrypt
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_authorize import Authorize
from werkzeug.exceptions import HTTPException
from flask import g
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal
from raven.contrib.flask import Sentry

import redis


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


class RedisClient(object):
    def __init__(self, app=None, **kwargs):
        self._redis_client = None
        self.provider_class = redis.Redis
        self.provider_kwargs = kwargs

        if app is not None:
            self.init_app(app)

    @classmethod
    def from_custom_provider(cls, provider, app=None, **kwargs):
        assert provider is not None, "your custom provider is None, come on"

        # We never pass the app parameter here, so we can call init_app
        # ourselves later, after the provider class has been set
        instance = cls(**kwargs)

        instance.provider_class = provider
        if app is not None:
            instance.init_app(app)
        return instance

    def init_app(self, app, **kwargs):
        self.provider_kwargs.update(kwargs)
        self._redis_client = self.provider_class(host=app.config.get('REDIS_HOST'), 
                                                port=app.config.get('REDIS_PORT'), 
                                                password=app.config.get('REDIS_PASSWORD'), 
                                                db=0, 
                                                **self.provider_kwargs
                                            )

    def __getattr__(self, name):
        return getattr(self._redis_client, name)

    def __getitem__(self, name):
        return self._redis_client[name]

    def __setitem__(self, name, value):
        self._redis_client[name] = value

    def __delitem__(self, name):
        del self._redis_client[name]


bcrypt = Bcrypt()
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
authorize = Authorize(current_user=get_current_user, exception=MyUnauthorizedException, strict=False)
ldap_manager = LDAP3LoginManager()
login_manager = LoginManager()
sentry = Sentry()
redis_client = RedisClient()