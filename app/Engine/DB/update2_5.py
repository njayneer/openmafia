# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.

# generate roles
    roles = [db_models.Role(name="priest",
                            visible_name='Ksiądz',
                            description='Rola księdza polega na modleniu się za mieszkańców. Każdego dnia wybiera cel modłów, który jest chroniony na wypadek mafijnego mordu w danym dniu.'),
             db_models.Role(name="sniper",
                            visible_name='Snajper',
                            description='Snajper na początku gry otrzymuje strzelbę. Może jej używać w celu samodzielnego zabijania innych zawodników.')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# generate configurations
    roles = [db_models.Configuration(name="time_offset",
                                     description='Przesunięcie czasowe wszystkich zdarzeń w grze. Przyspiesza lub opóźnia lincz, mord, itd. Format HH;MM.',
                                     default_value='0;0'),
             db_models.Configuration(name="sniper_shots",
                                     description='Konfiguracja określa, ile strzałów będzie miał pistolet, który na wstępie otrzyma snajper.',
                                     default_value='1')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# generate event types
    event_types = [db_models.EventType(name="priest_prayer",
                                      description="Modlitwa księdza"),
                   db_models.EventType(name="gun_shot",
                                       description="Snajperski strzał"),
                   db_models.EventType(name="gun_shot_kill",
                                       description="Zabójstwo wykonane przez strzał z pistoletu.")
                   ]
    for event_type in event_types:
        db.session.add(event_type)
    db.session.commit()

# generate notification types
    notifications = [db_models.NotificationTemplate(name="priest_prayer_result",
                                                    content="Twoja modlitwa za  <b>%s</b>  okazała się  <b>%s</b>.")
                     ]
    for notif in notifications:
        db.session.add(notif)
    db.session.commit()


# generate items
    items = [db_models.Items(name="gun",
                             visible_name="pistolet",
                             description="Pistolet służy do zabijania innych graczy. Wybór celu następuje w dowolnej chwili, ale cel zostaje zabity dopiero w momencie mordu.")
                     ]
    for notif in notifications:
        db.session.add(notif)
    db.session.commit()
