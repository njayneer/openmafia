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

# generate configurations
    configurations = [db_models.Configuration(name="lynch_blocked_days",
                                              description='Dni, w których lincz będzie zablokowany.',
                                              default_value=''),
                      db_models.Configuration(name="mafia_kill_blocked_days",
                                              description='Dni, w których mord będzie zablokowany.',
                                              default_value=''),
                      db_models.Configuration(name="godfather_allow_change_owner",
                                              description='Właściciel roli Ojca Chrzestnego może być zmieniony do końca pierwszego dnia."',
                                              default_value='False'),
             ]
    for config in configurations:
        db.session.add(config)
    db.session.commit()

# generate roles
    roles = [db_models.Role(name="godfather",
                            visible_name='Ojciec Chrzestny',
                            description='Ojciec Chrzestny to pasywna rola. Jeśli detektyw sprawdzi OC, wynik będzie niewinny, jeśli barman upije OC, upicie będzie nieskuteczne. Jeśli ksiądz będzie się modlił za OC, OC dostanie informację z nickiem księdza.')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# generate notification types
    notifications = [db_models.NotificationTemplate(name="prayer_for_godfather",
                                                    content="Ksiądz <b>%s</b> wybrał ciebie jako cel modlitwy!")
                     ]
    for notif in notifications:
        db.session.add(notif)
    db.session.commit()