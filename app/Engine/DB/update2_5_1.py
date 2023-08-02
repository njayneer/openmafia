# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.

# generate configurations
    roles = [db_models.Configuration(name="sniper_blocked_after_missed_shot",
                                     description='Po zabiciu nie-mafii snajper traci broń i jego rola jest odsłaniana.',
                                     default_value='False')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# # generate event types
#     event_types = [db_models.EventType(name="priest_prayer",
#                                       description="Modlitwa księdza"),
#                    db_models.EventType(name="gun_shot",
#                                        description="Snajperski strzał"),
#                    db_models.EventType(name="gun_shot_kill",
#                                        description="Zabójstwo wykonane przez strzał z pistoletu.")
#                    ]
#     for event_type in event_types:
#         db.session.add(event_type)
#     db.session.commit()

