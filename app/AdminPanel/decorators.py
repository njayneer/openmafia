from flask import flash, redirect, url_for, abort
from functools import wraps
from flask_login import current_user

def administrator_privileges_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.name != 'admin':
            return abort(404)

        return f(*args, **kwargs)
    return decorated_function
