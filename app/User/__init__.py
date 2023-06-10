from flask import Blueprint

UserModule = Blueprint('User',
                           __name__,
                           static_folder='static',
                           url_prefix='/user',
                           template_folder='templates'
                           )
from . import views
