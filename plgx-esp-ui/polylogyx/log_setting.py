from typing import Set
from polylogyx.models import Settings
from flask import current_app


def _get_log_level_from_db(name="er_ui_log_level"):
    log_level_setting = Settings.query.filter(
            Settings.name == name
        ).first()
    if log_level_setting:
        return log_level_setting.setting
    else:
        return "WARNING"

def _check_log_level_exists(name="er_ui_log_level"):
    log_level_setting = Settings.query.filter(
        Settings.name == name
    ).first()
    return log_level_setting

def _set_log_level_to_db(log_level):
    from polylogyx.cache import refresh_log_level
    esp_ui_log_level_setting = _check_log_level_exists()

    if esp_ui_log_level_setting:
        current_app.logger.info("Log level is already set to {0} , Updating it..."
                                .format(esp_ui_log_level_setting.setting))
        esp_ui_log_level_setting.update(setting=log_level)
    else:
        current_app.logger.info("Setting up Log level to {0} ".format(log_level))
        esp_ui_log_level_setting=Settings.create(name='er_ui_log_level', setting=log_level)
        esp_ui_log_level_setting.save()
    refresh_log_level()

def set_app_log_level(level):
    current_app.logger.setLevel(level)


import requests
import urllib3
urllib3.disable_warnings()
import socket
import json
def set_another_server_log_level(server_name,log_level):
    headers = {
                'Content-Type': 'application/json'
                }
    payload = json.dumps({"log_level":log_level,"host":socket.gethostname()})
    resp={"status":"success","message":"Log level update failed"}    
    if server_name=="ER":
        host = current_app.config.get("ER_ADDRESS",None)
        if host: 
            url = host+"/log_setting"
            resp = requests.put(url=url,data=payload,headers=headers)
            resp = resp.json()
    return resp["status"],resp["message"]