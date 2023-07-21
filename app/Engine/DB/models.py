from app import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask import g
import json
from datetime import datetime
import os
from zoneinfo import ZoneInfo


def now():
    now_dt = datetime.now(tz=ZoneInfo(os.environ["TZ"])).replace(tzinfo=None).replace(microsecond=0)
    result = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    return now_dt


class Game(db.Model):
    __tablename__ = 'Game'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    day_no = db.Column(db.Integer)
    phase = db.Column(db.Integer)
    status_id = db.Column(db.Integer, ForeignKey('Status.id'), default=1)
    owner_id = db.Column(db.Integer, ForeignKey('User.id'))
    start_time = db.Column(db.DateTime(timezone=True))
    game_type_id = db.Column(db.Integer, ForeignKey('GameType.id'))
    owner = relationship("User", uselist=False)
    status = relationship("Status", uselist=False)
    game_players = relationship("GamePlayer", back_populates='game')
    roles = relationship("Game_Roles")
    phases = relationship("Game_Phases")
    game_config = relationship("Game_Configuration")
    game_type = relationship("GameType")

    def lynch_day(self):
        lynch_day = self.day_no - 1 + self.phase
        return lynch_day

    def get_configuration(self, cfg_name):

        cfg_time_offset = [int(c) for c in db_api.get_configuration('time_offset').split(";")]


class GameType(db.Model):
    __tablename__ = 'GameType'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

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
    winner = db.Column(db.Integer)
    game = relationship("Game", back_populates='game_players')


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
    default_value = db.Column(db.String(50))


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
    timestamp = db.Column(db.DateTime(), default=now())
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
    priority = db.Column(db.Integer, default=100)
    source_id = db.Column(db.Integer, default=None)


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


class UserAttributeType(db.Model):
    __tablename__ = 'UserAttributeType'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    visible_name = db.Column(db.String(50))


class UserAttribute(db.Model):
    __tablename__ = 'UserAttribute'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('User.id'))
    attribute_id = db.Column(db.Integer, ForeignKey('UserAttributeType.id'))
    attribute = relationship('UserAttributeType')
    expiration_time = db.Column(db.DateTime(timezone=True))


class Topic(db.Model):
    __tablename__ = 'Topic'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), default=now())
    lastActivity = db.Column(db.DateTime(timezone=True), default=now())
    author = db.Column(db.Integer, ForeignKey('User.id'))
    game_id = db.Column(db.Integer, ForeignKey('Game.id'))
    replies = db.Column(db.Integer, default=0)


class Reply(db.Model):
    __tablename__ = 'Reply'
    id = db.Column(db.Integer, primary_key=True)
    reply_id = db.Column(db.Integer)
    content = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), default=now())
    author_id = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    inReplyTo = db.Column(db.Integer, ForeignKey('Topic.id'))
    author = relationship("GamePlayer")


class Achievements(db.Model):
    __tablename__ = 'Achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('User.id'))
    player_id = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    player = relationship("GamePlayer")
    achievement_id = db.Column(db.Integer, ForeignKey('AchievementTypes.id'))
    achievement = relationship("AchievementTypes")


class AchievementTypes(db.Model):
    __tablename__ = 'AchievementTypes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    visible_name = db.Column(db.String(50))
    description = db.Column(db.String(500))


class Notification(db.Model):
    __tablename__ = 'Notification'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, ForeignKey('GamePlayer.id'))
    time = db.Column(db.DateTime(timezone=True), default=now())
    template_id = db.Column(db.Integer, ForeignKey('NotificationTemplate.id'))
    template = relationship("NotificationTemplate")
    parameters = db.Column(db.String(500))
    read = db.Column(db.Integer, default=0)


class NotificationTemplate(db.Model):
    __tablename__ = 'NotificationTemplate'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    content = db.Column(db.String(500))


class GameJudgement(db.Model):
    __tablename__ = 'GameJudgement'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    day_no = db.Column(db.Integer)
    judgement = db.Column(db.Integer)


class UserToken(db.Model):
    __tablename__ = 'UserToken'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('User.id'))
    token = db.Column(db.String(100))
    time = db.Column(db.DateTime(timezone=True), default=now())

