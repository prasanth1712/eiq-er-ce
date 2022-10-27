# -*- coding: utf-8 -*-
import base64
import os
from pathlib import Path

import werkzeug
from flask import Flask, current_app
from flask_cors import CORS
from flask.json import jsonify

from polylogyx.blueprints.v1.external_api import blueprint as external_api_v1
from polylogyx.extensions import (
    bcrypt, db, ldap_manager, login_manager,
    mail, make_celery, migrate, sentry, authorize, redis_client
)
from polylogyx.models import Settings
from polylogyx.settings import ProdConfig
from polylogyx.tasks import celery
from datetime import datetime


def create_app(config=ProdConfig):
    app = Flask(__name__, template_folder='templates')
    CORS(app)
    app.config.from_object(config)

    app.config.from_envvar('POLYLOGYX_SETTINGS', silent=True)

    register_blueprints(app)
    register_loggers(app)
    register_extensions(app)
    register_auth_method(app)
    register_errorhandlers(app)
    return app


def register_blueprints(app):
    # if the POLYLOGYX_NO_MANAGER environment variable isn't set,
    # register the backend blueprint. This is useful when you want
    # to only deploy the api as a standalone service.
    #app.register_blueprint(external_api, url_prefix="/services/api/v0", name="external_api")
    app.register_blueprint(external_api_v1, url_prefix="/services/api/v1", name="external_api")


def register_extensions(app):
    bcrypt.init_app(app)
    db.init_app(app)

    migrate.init_app(app, db)
    try:
        set_email_sender(app)
    except Exception as e:
        print('No email address configured')

    mail.init_app(app)
    make_celery(app, celery)
    login_manager.init_app(app)
    sentry.init_app(app)
    authorize.init_app(app)
    mail.init_app(app)
    redis_client.init_app(app)
    if app.config['ENFORCE_SSL']:
        # Due to architecture of flask-sslify,
        # its constructor expects to be launched within app context
        # unless app is passed.
        # As a result, we cannot create sslify object in `extensions` module
        # without getting an error.
        from flask_sslify import SSLify
        SSLify(app)


def register_loggers(app):
    from logging.handlers import RotatingFileHandler,TimedRotatingFileHandler
    import logging
    import sys
    import pathlib

    logfile = app.config['POLYLOGYX_LOGGING_FILENAME']
    
    if logfile == '-':
        handler = logging.StreamHandler(sys.stdout)
    else:
        log_dir = pathlib.Path(app.config['POLYLOGYX_LOGGING_DIR'])
        logfile = log_dir.joinpath(logfile)
        max_size = app.config["POLYLOGYX_LOGFILE_SIZE"]
        backup_cnt = app.config["POLYLOGYX_LOGFILE_BACKUP_COUNT"]
        handler = RotatingFileHandler(logfile, maxBytes=max_size, backupCount=backup_cnt)
        namer = lambda fn : str(fn).split(".")[0]+"_"+ datetime.now().strftime("%Y-%m-%d_%H-%M")
        handler.namer=namer
        #handler = TimedRotatingFileHandler(logfile,"midnight",1,10,'utf-8')
        

    level_name = app.config['POLYLOGYX_LOGGING_LEVEL']

    if level_name in ('DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL'):
        app.logger.setLevel(getattr(logging, level_name))

    formatter = logging.Formatter(app.config['POLYLOGYX_LOGGING_FORMAT'])
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        if 'POLYLOGYX_NO_MANAGER' in os.environ:
            return '', 400
        return '', error_code

    @app.errorhandler(werkzeug.exceptions.Unauthorized)
    def handle_unauthorised(e):
        return jsonify({'status':"failure", 'message':'Username/Password is/are wrong!'}), 200

    app.register_error_handler(401, handle_unauthorised)


def register_auth_method(app):
    login_manager.login_view = 'users.login'
    login_manager.login_message_category = 'warning'

    if app.config['POLYLOGYX_AUTH_METHOD'] == 'ldap':
        ldap_manager.init_app(app)
        return

    # no other authentication methods left, falling back to OAuth

    if app.config['POLYLOGYX_AUTH_METHOD'] != 'polylogyx':
        login_manager.login_message = None
        login_manager.needs_refresh_message = None


def set_email_sender(app):
    with app.app_context():
        email_sender = db.session.query(Settings).filter(Settings.name == 'email').first().setting
        email_password = base64.b64decode(
            db.session.query(Settings).filter(Settings.name == 'password').first().setting)
        smtp_port = db.session.query(Settings).filter(Settings.name == 'smtpPort').first().setting
        smtp_address = db.session.query(Settings).filter(Settings.name == 'smtpAddress').first().setting
        current_app.config['MAIL_USERNAME'] = email_sender
        current_app.config['MAIL_PASSWORD'] = email_password
        current_app.config['MAIL_SERVER'] = smtp_address
        current_app.config['MAIL_PORT'] = int(smtp_port)
