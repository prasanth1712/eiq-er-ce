from polylogyx.db.models import Settings
from flask import current_app


def _get_log_level_from_db():
    esp_log_level_setting = Settings.query.filter(
            Settings.name == "er_log_level"
        ).first()
    if esp_log_level_setting:
        return esp_log_level_setting.setting
    else:
        return "WARNING"


def _check_log_level_exists():
    esp_log_level_setting = Settings.query.filter(
        Settings.name == "er_log_level"
    ).first()
    return esp_log_level_setting


def _set_log_level_to_db(log_level):
    from polylogyx.utils.cache import update_cached_setting
    esp_log_level_setting = _check_log_level_exists()

    if esp_log_level_setting:
        current_app.logger.info("Log level is already set to {0} , Updating it..."
                                .format(esp_log_level_setting.setting))
        esp_log_level_setting.update(setting=log_level)
    else:
        current_app.logger.info("Setting up Log level to {0} ".format(log_level))
        Settings.create(name='er_log_level', setting=log_level)
    update_cached_setting('er_log_level', log_level)


def set_app_log_level(level):
    current_app.logger.setLevel(level)
