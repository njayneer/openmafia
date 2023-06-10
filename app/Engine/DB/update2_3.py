# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.


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
