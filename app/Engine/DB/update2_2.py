# Run this file only once while server setup.

from app import app, db
import app.Engine.DB.models as db_models
from werkzeug.security import generate_password_hash
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi

with app.app_context():
    db.create_all()  # pass the create_app result so Flask-SQLAlchemy gets the configuration.

    # generate roles
    roles = [db_models.Role(name="game_admin",
                            visible_name='Mistrz gry',
                            description='Mistrz gry nie bierze udziału w rozgrywce, ale ma możliwość zarządzania graczami. Ma dostęp do wszystkich czatów, może w nich pisać i zna wszystkie role w grze.'),
             db_models.Role(name="game_guest",
                            visible_name='Gość',
                            description='Gość może jedynie obserwować grę, nie bierze czynnego udziału w rozgrywce.')
             ]
    for role in roles:
        db.session.add(role)
    db.session.commit()

    # generate event types
    event_types = [db_models.EventType(name="admin_kill",
                                      description="Administrator zabił gracza."),
                   db_models.EventType(name="admin_block_lynch",
                                      description="Administrator zablokował dzisiejszy lincz."),
                   db_models.EventType(name="admin_block_mafia_kill",
                                      description="Administrator zablokował dzisiejszy mord.")
                   ]
    for event_type in event_types:
        db.session.add(event_type)
    db.session.commit()

    # generate configuration
    configs = [db_models.Configuration(name="game_admin",
                                       description="Twórca zostaje administratorem (mistrzem) gry"),
               db_models.Configuration(name="detailed_lynch_results",
                                       description="Wyniki po linczu szczegółowe (kto na kogo)"),
               db_models.Configuration(name="lynch_voting_history",
                                       description="Głosowanie do linczu jawne na żywo"),
                   ]
    for config in configs:
        db.session.add(config)
    db.session.commit()
