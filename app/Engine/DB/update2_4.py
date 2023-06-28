# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.

# generate roles
    roles = [db_models.Role(name="suspect",
                            visible_name='Opryszek',
                            description='Opryszek nie jest świadomy swojej roli. W momencie sprawdzania jego przynależności, ujawnia się jako mafiozo.')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

# generate configurations
    roles = [db_models.Configuration(name="roles_not_visible_after_death",
                                     description='Wybrane role nie będą pojawiać się w wynikach po śmierci właściciela',
                                     default_value='[]')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()
