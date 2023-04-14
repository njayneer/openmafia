from flask import Blueprint

SetupGameModule = Blueprint('SetupGameModule',
                           __name__,
                           static_folder='static',
                           url_prefix='/game',
                           template_folder='templates'
                           )
from . import views