# -*- encoding: utf-8 -*-
"""
Python Aplication Template
Licence: GPLv3
"""

from flask import Flask, g
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)

#Configuration of application, see configuration.py, choose one and uncomment.
#app.config.from_object('configuration.ProductionConfig')
app.config.from_object('app.configuration.DevelopmentConfig')
#app.config.from_object('configuration.TestingConfig')

bs = Bootstrap(app) #flask-bootstrap
db = SQLAlchemy(app) #flask-sqlalchemy

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

dbcreation = False  # change when you run dbcreation.py
if not dbcreation:
    # start scheduler
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    game_scheduler = GameScheduler()
    with app.app_context():
        game_scheduler.app_start()

    from app.AdminPanel import AdminModule as adminmodule_blueprint
    from app.SetupGameModule import SetupGameModule as setupgamemodule_blueprint

    app.register_blueprint(adminmodule_blueprint)
    app.register_blueprint(setupgamemodule_blueprint)

from app import views
from app.Engine.DB import models
from app import Engine
