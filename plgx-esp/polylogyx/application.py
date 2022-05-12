# -*- coding: utf-8 -*-
import os

from flask import Flask, render_template
from flask_cors import CORS

from polylogyx.api.api import blueprint as api
from polylogyx.celery.tasks import celery
from polylogyx.extensions import (
    cache,
    csrf,
    db,
    log_tee,
    mail,
    make_celery,
    migrate,
    rule_manager,
    threat_intel
)
from polylogyx.settings import ProdConfig


def create_app(config=ProdConfig):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)
    app.config.from_envvar("POLYLOGYX_SETTINGS", silent=True)

    register_blueprints(app)
    register_loggers(app)
    register_extensions(app)
    

    return app


def register_blueprints(app):
    app.register_blueprint(api)
    csrf.exempt(api)


def register_extensions(app):
    csrf.init_app(app)
    db.init_app(app)

    migrate.init_app(app, db)

    log_tee.init_app(app)
    rule_manager.init_app(app)
    threat_intel.init_app(app)

    mail.init_app(app)
    make_celery(app, celery)
    cache.init_app(app)


def register_loggers(app):
    import logging
    import sys
    from logging.handlers import RotatingFileHandler,TimedRotatingFileHandler
    import pathlib
    from datetime import datetime

    logfile = app.config["POLYLOGYX_LOGGING_FILENAME"]

    if logfile == "-":
        handler = logging.StreamHandler(sys.stdout)
    else:
        log_dir = pathlib.Path(app.config['POLYLOGYX_LOGGING_DIR'])
        logfile = log_dir.joinpath(logfile)
        max_size = app.config["POLYLOGYX_LOGFILE_SIZE"]
        backup_cnt = app.config["POLYLOGYX_LOGFILE_BACKUP_COUNT"]
        handler = RotatingFileHandler(logfile, maxBytes=max_size, backupCount=backup_cnt)
        #handler = TimedRotatingFileHandler(logfile,"midnight",1,10,'utf-8')
        namer = lambda fn : str(fn).split(".")[0]+"_"+ datetime.now().strftime("%Y-%m-%d_%H-%M")
        handler.namer=namer

    level_name = app.config["POLYLOGYX_LOGGING_LEVEL"]

    if level_name in ("DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"):
        app.logger.setLevel(getattr(logging, level_name))

    formatter = logging.Formatter(app.config["POLYLOGYX_LOGGING_FORMAT"])
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    