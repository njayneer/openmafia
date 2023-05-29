from flask import flash, redirect, url_for
from functools import wraps
from flask_login import current_user

def administrator_privileges_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.name != 'admin':
            flash('User ' + current_user.name + ' nie ma uprawnień do wykonania tej operacji!', 'alert-danger')
            redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function
