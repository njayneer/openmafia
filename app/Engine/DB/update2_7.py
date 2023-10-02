# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.


# # generate event types
    event_types = [db_models.EventType(name="mvp2_chosen",
                                      description="vice MVP został wybrany"),
                   db_models.EventType(name="mvp3_chosen",
                                       description="vice MVP został wybrany"),
                   db_models.EventType(name="lynch_draw_noone",
                                       description="Przez remis w głosowaniu nikt nie został zlinczowany!"),
                   db_models.EventType(name="lynch_draw_mafia_choice",
                                       description="Przez remis w głosowaniu nikt nie został zlinczowany, cel wybierze mafia!"),
                   db_models.EventType(name="admin_revive",
                                       description="Administrator ożywił gracza!"),
                   db_models.EventType(name="spy_check",
                                       description="Szpieg wybiera cel śledzenia!"),
                   db_models.EventType(name="barman_getting_drunk",
                                       description="Barman wybiera cel upicia.")
                   ]
    for event_type in event_types:
        db.session.add(event_type)
    db.session.commit()
#
# generate achievements
    achievements = [
                    db_models.AchievementTypes(name="mvp2",
                                               description="Gracz został wybrany na wice-najlepszego zawodnika gry."),
                    db_models.AchievementTypes(name="mvp3",
                                               description="Gracz został wybrany na drugiego wice-najlepszego zawodnika gry."),
                    db_models.AchievementTypes(name="best-detective",
                                               description="Gracz został najlepszym detektywem tej edycji!"),
                    db_models.AchievementTypes(name="feelings-master",
                                               description="Gracz został Mistrzem Czutek - najlepszym detektywem pierwszego dnia!"),
                    db_models.AchievementTypes(name="best-troublemaker",
                                               description="Gracz został najlepszym mącicielem tej edycji!"),
                    db_models.AchievementTypes(name="camouflage-master",
                                               description="Gracz został Mistrzem Kamuflażu - najlepszym mącicielem pierwszego dnia!"),
                    db_models.AchievementTypes(name="first-to-find",
                                               description="Gracz jako pierwszy prawidłowo wytypował cały skład mafii!"),
                    db_models.AchievementTypes(name="best-detective2",
                                               description="Gracz został vice-najlepszym detektywem tej edycji!"),
                    db_models.AchievementTypes(name="best-detective3",
                                               description="Gracz został drugim vice-najlepszym detektywem tej edycji!"),
                   ]
    for achievement in achievements:
        db.session.add(achievement)
    db.session.commit()


# generate configurations
    roles = [db_models.Configuration(name="lynch_draw",
                                     description='Algorytm uruchamiany w przypadku remisu w linczu. Możliwe: random, noone, mafia_choice',
                                     default_value='random'),
             db_models.Configuration(name="spy_specific_roles",
                                     description='Szpieg otrzymuje dokładną informację o rolach, zamiast suchego "rolny"/"bezrolny"',
                                     default_value='False'),
             db_models.Configuration(name="spy_allow_change_owner",
                                     description='Właściciel roli szpiega może być zmieniony do końca pierwszego dnia."',
                                     default_value='False')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# generate roles
    roles = [db_models.Role(name="spy",
                            visible_name='Szpieg',
                            description='Szpieg wybiera gracza i sprawdza, czy ma rolę. W zależności od konfiguracji otrzymuje informację o dokładnej roli lub ogólnie - ma/nie ma.'),
             db_models.Role(name="barman",
                            visible_name='Barman',
                            description='Barman codziennie upija jedną osobę, której cele nocne są ustalane całkowicie losowo.')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# generate notification types
    notifications = [db_models.NotificationTemplate(name="spy_check",
                                                    content="Twoje śledztwo szpiega doprowadziło Cię do wniosku, że  <b>%s</b>  posiada rolę  <b>%s</b>."),
                     db_models.NotificationTemplate(name="barman_get_drunk",
                                                    content="Tej nocy zostałeś upity przez barmana.")
                     ]
    for notif in notifications:
        db.session.add(notif)
    db.session.commit()