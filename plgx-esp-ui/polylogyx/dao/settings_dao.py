from polylogyx.models import Settings


def get_settings_by_name(name):
    return Settings.query.filter(Settings.name == name).first()


def create_settings(name, setting):
    Settings.create(name=name, setting=setting)

