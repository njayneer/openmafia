# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.

    # generate admin account
    admin_user = db_models.User(email="email@email.com",
                                user="admin",
                                name="admin",
                                password=generate_password_hash("admin22", method='sha256'))
    db.session.add(admin_user)
    db.session.commit()

    # generate game statuses
    statuses = [db_models.Status(name="new", visible_name="Nowa gra"),
                db_models.Status(name="enrollment_open", visible_name="Zapisy otwarte"),
                db_models.Status(name="enrollment_closed", visible_name="Zapisy zamknięte"),
                db_models.Status(name="waiting_for_start", visible_name="Oczekiwanie na start"),
                db_models.Status(name="in_progress", visible_name="Gra w trakcie"),
                db_models.Status(name="finished", visible_name="Gra zakończona"),
                db_models.Status(name="cancelled", visible_name="Gra anulowana")]
    for st in statuses:
        db.session.add(st)
    db.session.commit()

    # generate roles
    roles = [db_models.Role(name="citizen",
                            visible_name='Mieszkaniec',
                            description='Niewinny mieszkaniec miasta, jego rola polega na głosowaniu w linczu.'),
             db_models.Role(name="mafioso",
                            visible_name='Mafiozo',
                            description='Członek mafii. Razem z innymi mafiozami może dokonywać zabójstw.'),
             db_models.Role(name="game_admin",
                            visible_name='Mistrz gry',
                            description='Mistrz gry nie bierze udziału w rozgrywce, ale ma możliwość zarządzania graczami. Ma dostęp do wszystkich czatów, może w nich pisać i zna wszystkie role w grze.'),
             db_models.Role(name="game_guest",
                            visible_name='Gość',
                            description='Gość może jedynie obserwować grę, nie bierze czynnego udziału w rozgrywce.'),
             db_models.Role(name="detective",
                            visible_name='Detektyw',
                            description='Detektyw każdego dnia może wybrać jednego żyjącego gracza, którego szpieguje. Na koniec nocy otrzymuje informację, czy szpiegowana osoba jest członkiem mafii.')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

    # generate event types
    event_types = [db_models.EventType(name="citizen_vote",
                                       description="Głos mieszkańca w kandydata do linczu"),
                   db_models.EventType(name="mafia_kill_vote",
                                       description="Głos na cel zabójstwa mafii"),
                   db_models.EventType(name="lynch",
                                       description="Miasto dopuściło się linczu."),
                   db_models.EventType(name="mafia_kill",
                                       description="Zabójstwo mafii"),
                   db_models.EventType(name="citizens_win",
                                       description="Miasto wygrywa!"),
                   db_models.EventType(name="mafiosos_win",
                                       description="Mafia wygrywa!"),
                   db_models.EventType(name="admin_kill",
                                      description="Administrator zabił gracza."),
                   db_models.EventType(name="admin_block_lynch",
                                      description="Administrator zablokował dzisiejszy lincz."),
                   db_models.EventType(name="admin_block_mafia_kill",
                                      description="Administrator zablokował dzisiejszy mord."),
                   db_models.EventType(name="detective_check",
                                       description="Detektyw sprawdza przynależność gracza."),
                   ]
    for event_type in event_types:
        db.session.add(event_type)
    db.session.commit()

    # generate configuration
    configs = [db_models.Configuration(name="game_admin",
                                       description="Twórca zostaje administratorem (mistrzem) gry",
                                       default_value="1"),
               db_models.Configuration(name="detailed_lynch_results",
                                       description="Wyniki po linczu szczegółowe (kto na kogo)",
                                       default_value="1"),
               db_models.Configuration(name="lynch_voting_history",
                                       description="Głosowanie do linczu jawne na żywo",
                                       default_value="0"),
               db_models.Configuration(name="see_enrolled_user_list",
                                       description="Pokazywanie całej listy zapisanych do gry przed rozpoczęciem.",
                                       default_value="0"),
               db_models.Configuration(name="citizen_forum_turned_on",
                                       description="Włącza forum miasta.",
                                       default_value="1"),
               db_models.Configuration(name="initial_forum_turned_on",
                                       description="Włącza forum przed startem gry.",
                                       default_value="0"),
               db_models.Configuration(name="creations_on",
                                       description="Włącza ustawianie indywidualnych dla rozgrywki nazw użytkowników w celu zanonimizowania graczy.",
                                       default_value="1")
                   ]
    for config in configs:
        db.session.add(config)
    db.session.commit()

    # generate achievements
    achievements = [db_models.AchievementTypes(name="tester",
                                               description="Użytkownik zasłużył się jako testujący nowe wersje OpenMafii."),
                    db_models.AchievementTypes(name="pioneer",
                                               description="Użytkownik jest z nami od początków istnienia OpenMafii."),
                    db_models.AchievementTypes(name="mvp",
                                               description="Gracz został wybrany na najlepszego zawodnika gry!"),
                    db_models.AchievementTypes(name="classic_winner",
                                               description="Gracz wygrał grę w trybie klasycznym."),
                    db_models.AchievementTypes(name="administrator",
                                               description="Użytkownik administruje OpenMafię."),
                    db_models.AchievementTypes(name="game_master",
                                               description="Gracz był mistrzem gry w trybie klasycznym."),
                    db_models.AchievementTypes(name="patron",
                                               description="Użytkownik aktywnie wspiera rozwój OpenMafii, dziękujemy!")
                    ]
    for achievement in achievements:
        db.session.add(achievement)
    db.session.commit()

    # game types
    gametypes = [db_models.GameType(name="classic"),
                 db_models.GameType(name="blitz"),
                 db_models.GameType(name="short")]
    for gametype in gametypes:
        db.session.add(gametype)
    db.session.commit()
