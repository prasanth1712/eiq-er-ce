from typing import Set
from polylogyx.models import Settings
from flask import current_app

import requests
import socket
import json
import urllib3
urllib3.disable_warnings()


def get_log_level_setting(name='er_ui_log_level'):
    setting = Settings.query.filter(Settings.name == name).first()
    return setting


def update_log_level_setting(name='er_ui_log_level', value='WARNING'):
    settings = Settings.query.filter(Settings.name == name).first()
    if settings:
        settings.update(setting=value)
    else:
        settings = Settings.create(name=name, setting=value)
    return settings


def set_app_log_level(level):
    current_app.logger.setLevel(level)


def set_another_server_log_level(server_name, log_level):
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({"log_level": log_level, "host": socket.gethostname()})
    resp = {"status": "success", "message": "Log level update failed"}
    if server_name == "ER":
        host = current_app.config.get("ER_ADDRESS", None)
        if host:
            url = host+"/log_setting"
            resp = requests.put(url=url, data=payload, headers=headers)
            resp = resp.json()
    return resp["status"], resp["message"]