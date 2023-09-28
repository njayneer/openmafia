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
                                       description="vice MVP został wybrany")
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