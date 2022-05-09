from polylogyx.models import db, Role
from sqlalchemy import asc
from polylogyx.extensions import cache
from flask import current_app


@cache.cached(timeout=86400, key_prefix='all_roles')
def get_all_cached_roles_from_db():
    """
    Method to cache all the roles being created from 'plgx-esp' service,
    so that it doesn't need to query on every request

    Usually the roles being cached will be queried from db unless the situation that 'plgx-esp' service is in progress
    creating the roles and other stuff needed.

    Returns the list of tuples with access level and role name for further easy usage
    """
    roles_dict = {}
    try:
        roles = db.session.query(Role).order_by(asc(Role.access_level)).all()
        db.session.commit()
        for role in roles:
            roles_dict[role.access_level] = role.name
        if not roles_dict:
            current_app.logger.warning("Roles aren't added to database yet! Taking them from settings.py")
            roles_dict = current_app.config['DEFAULT_ROLES']
    except Exception as e:
        current_app.logger.info(
            """Unable to cache the roles - {}""".format(str(e)))
    role_tuples_array = list(roles_dict.items())
    role_tuples_array.sort(key=lambda y: y[0])
    return role_tuples_array


def get_admin_role_name():
    """
    Returns the name of the role with highest access i.e min access_level column value set
    Usually the first item in the cached array(in the method 'get_all_cached_roles_from_db') will be the admin role
    """
    role_tuples_array = get_all_cached_roles_from_db()
    if role_tuples_array:
        return role_tuples_array[0][1]


from polylogyx.log_setting import _get_log_level_from_db

@cache.cached(key_prefix="er_ui_log_level")
def get_log_level():
    level = _get_log_level_from_db()
    return level

def refresh_log_level():
    level = _get_log_level_from_db()
    cache.set("er_ui_log_level", level)
