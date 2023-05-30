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
                            description='Członek mafii. Razem z innymi mafiozami może dokonywać zabójstw.')]
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
                                       description="Mafia wygrywa!")
                   ]
    for event_type in event_types:
        db.session.add(event_type)
    db.session.commit()
