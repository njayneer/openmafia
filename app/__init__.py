# -*- encoding: utf-8 -*-
"""
Python Aplication Template
Licence: GPLv3
"""

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import time

os.environ["TZ"] = "Europe/Warsaw"
#time.tzset()

app = Flask(__name__)

#Configuration of application, see configuration.py, choose one and uncomment.
#app.config.from_object('app.configuration.ProductionConfig')
app.config.from_object('app.configuration.DevelopmentConfig')
#app.config.from_object('app.configuration.TestingConfig')

bs = Bootstrap(app) #flask-bootstrap
db = SQLAlchemy(app, session_options={"expire_on_commit": False}) #flask-sqlalchemy

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

dbcreation = False  # change when you run dbcreation.py
if dbcreation:
    import app.Engine.DB.dbcreation
else:
    from app.AdminPanel import AdminModule as adminmodule_blueprint
    from app.SetupGameModule import SetupGameModule as setupgamemodule_blueprint

    app.register_blueprint(adminmodule_blueprint)
    app.register_blueprint(setupgamemodule_blueprint)

    from app import views
    from app.Engine.DB import models
    from app import Engine
