from functools import wraps

from flask import g

from app.api.error import error_response
from app.models import Permission


def permission_required(permission):
    """检查常规权限"""
    def decorator(f):
        @wraps(f)
        def decorator_function(*args,**kwargs):
            if not g.current_user.can(permission):
                return error_response(403)
            else:
                return f(*args,**kwargs)
        return decorator_function

    return decorator

def admin_required(f):
    """检查管理员权限"""
    return permission_required(Permission.ADMIN)(f)