from flask import g

from polylogyx.cache import get_admin_role_name
from polylogyx.extensions import authorize, MyUnauthorizedException
from functools import wraps


def admin_required(f):
    """
    Decorator to make sure the user logged in is 'admin'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if authorize.has_role(get_admin_role_name()):
            return f(*args, **kwargs)
        else:
            raise MyUnauthorizedException
    return decorated_function


def is_current_user_an_admin():
    """
    Check if the current logged in user is admin or not
    """
    return authorize.has_role(get_admin_role_name())


def is_admin_or_self(f):
    """
    Decorator to make sure the user logged in is 'admin' or himself
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ('username' in kwargs and g.user.username == kwargs['username']) or \
                authorize.has_role(get_admin_role_name()):
            return f(*args, **kwargs)
        else:
            raise MyUnauthorizedException
    return decorated_function
