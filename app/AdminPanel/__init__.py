from flask import Blueprint

AdminModule = Blueprint('AdminModule',
                           __name__,
                           static_folder='static',
                           url_prefix='/admin',
                           template_folder='templates'
                           )
from . import views