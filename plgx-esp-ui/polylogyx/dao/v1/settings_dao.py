from polylogyx.models import Settings
import json


def get_settings_by_name(name):
    return Settings.query.filter(Settings.name == name).first()


def create_settings(name, setting):
    return Settings.create(name=name, setting=setting)


def update_or_create_setting(name, setting):
    settings_obj = Settings.query.filter(Settings.name == name).first()
    if settings_obj:
        settings_obj.setting = setting
        return settings_obj.update(settings_obj)
    else:
        return Settings.create(name=name, setting=setting)


def get_sso_configuration():
    setting = None
    setting_obj = get_settings_by_name('sso_configuration')
    if setting_obj:
        setting = json.loads(setting_obj.setting)
    return setting


def get_sso_enabled_status():
    setting_obj = get_settings_by_name('sso_enable')
    if setting_obj:
        setting = setting_obj.setting
        if setting == 'false':
            return False
        return True
    return
