from app import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask import g
import json


class Game(db.Model):
    __tablename__ = 'Game'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    day_no = db.Column(db.Integer)
    phase = db.Column(db.Integer)
    status_id = db.Column(db.Integer, ForeignKey('Status.id'), default=1)
    owner_id = db.Column(db.Integer, ForeignKey('User.id'))
    start_time = db.Column(db.DateTime(timezone=True))
    owner = relationship("User", uselist=False)
    status = relationship("Status", uselist=False)
    game_players = relationship("GamePlayer")
    roles = relationship("Game_Roles")
    phases = relationship("Game_Phases")
    game_config = relationship("Game_Configuration")

    def get_configuration(self, cfg_name: str):
        privilege = [config.value for config in self.game_config if config.configuration.name == cfg_name]
        if len(privilege) == 1:
            privilege_value = privilege[0]
        else:
            privilege_value = None
        return privilege_value


class GamePlayer(db.Model):
    __tablename__ = 'GamePlayer'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    user_id = db.Column(db.Integer, ForeignKey('User.id'))
    order_id = db.Column(db.Integer)
    roles = relationship("Game_Roles")
    name = db.Column(db.String(500))
    status = db.Column(db.String(500))
    user = relationship("User")


class Game_Roles(db.Model):
    __tablename__ = 'Game_Roles'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    player_id = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    role_id = db.Column(db.Integer, ForeignKey('Role.id'))
    role = relationship("Role")


class Game_Phases(db.Model):
    __tablename__ = 'Game_Phases'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    phase_id = db.Column(db.Integer)
    phase_name = db.Column(db.String(100))
    phase_duration = db.Column(db.Integer)


class Game_Configuration(db.Model):
    __tablename__ = 'Game_Configuration'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    configuration_id = db.Column(db.Integer, ForeignKey('Configuration.id'))
    value = db.Column(db.String(50))
    configuration = relationship("Configuration")


class Configuration(db.Model):
    __tablename__ = 'Configuration'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(100))


class Status(db.Model):
    __tablename__ = 'Status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    visible_name = db.Column(db.String(100))

    def __repr__(self):
        return self.name


class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    visible_name = db.Column(db.String(500))
    description = db.Column(db.String(500))


class Event(db.Model):
    __tablename__ = 'Event'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    player_id = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    event_type = db.Column(db.Integer, ForeignKey('EventType.id'))
    target = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    day_no = db.Column(db.Integer)
    phase_no = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    source_player = relationship("GamePlayer", foreign_keys=[player_id])
    target_player = relationship("GamePlayer", foreign_keys=[target])
    event_type_tbl = relationship("EventType")

class EventType(db.Model):
    __tablename__ = 'EventType'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    description = db.Column(db.String(500))

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(500))
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    trigger_time = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default='new')


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(500))
    name = db.Column(db.String(500))
    email = db.Column(db.String(120), unique=True)
    is_active = db.Column(db.Boolean)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return self.id


class Topic(db.Model):
    __tablename__ = 'Topic'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    lastActivity = db.Column(db.DateTime(timezone=True), server_default=func.now())
    author = db.Column(db.Integer, ForeignKey('User.id'))
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    replies = db.Column(db.Integer, default=0)


class Reply(db.Model):
    __tablename__ = 'Reply'
    id = db.Column(db.Integer, primary_key=True)
    reply_id = db.Column(db.Integer)
    content = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    author_id = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    inReplyTo = db.Column(db.Integer, ForeignKey('Topic.id'))
    author = relationship("GamePlayer")
