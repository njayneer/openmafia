# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.


# # generate event types
    event_types = [db_models.EventType(name="lynch_draw_mafia_chose",
                                      description="Mafia wybrała cel linczu"),
                   db_models.EventType(name="lynch_draw_mafia_choice_vote",
                                       description="Głos mafii na cel linczu")
                   ]
    for event_type in event_types:
        db.session.add(event_type)
    db.session.commit()
