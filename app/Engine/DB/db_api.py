from app.Engine.DB.models import *
import random
from flask_login import current_user
from sqlalchemy import desc
from datetime import datetime, timezone

import os
from dateutil import tz
def utc_to_local(utc_dt):
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(os.environ["TZ"])
    utc_dt = utc_dt.replace(tzinfo=from_zone)
    localized_tz = utc_dt.astimezone(to_zone)
    return localized_tz

class GameApi:
    def __init__(self):
        self.game = None

    def list_games(self, game_type='all', user=None):
        if game_type == 'all':
            return Game.query.all()
        elif game_type == 'all_but_cancelled':
            status_id = self._get_status_id('cancelled')
            return Game.query.filter(Game.status_id != status_id).all()
        elif game_type == 'open_games':
            status_id = self._get_status_id('enrollment_open')
            return Game.query.filter(Game.status_id == status_id).all()
        elif game_type == 'my_games':
            games = Game.query.all()
            return [game for game in games if current_user.id in [player.user_id for player in game.game_players]]
        # elif game_type == 'my_last_game':
        #     games = Game.query.order_by(desc(Game.id))
        #     return [game for game in games if current_user.id in [player.user_id for player in game.game_players]][0]
        else:
            return None

    def create_game(self, name):
        self.game = Game(name=name,
                    owner_id=g.user.id)
        db.session.add(self.game)
        db.session.commit()
        return self.game.id

    def cancel_game(self):
        self._set_status('cancelled')
        db.session.commit()

    def get_game(self, game_id):
        self.game = Game.query.filter_by(id=game_id).first()
        # order players in randomized order due to anonymization
        try:
            self.game.game_players.sort(key=lambda x: x.order_id)
        except TypeError:
            pass
        return self.game

    def set_game(self, game):
        self.game = game

    def join_user_as_player(self, user_id, name):
        game_player = GamePlayer(user_id=user_id, game_id=self.game.id, name=name, status='new')
        db.session.add(game_player)
        db.session.commit()
        return game_player.id

    def sign_off_as_player(self, user_id):
        GamePlayer.query.filter_by(game_id=self.game.id, user_id=user_id).delete()
        db.session.commit()

    def enrollment_open(self):
        self._set_status('enrollment_open')
        db.session.commit()

    def enrollment_close(self):
        self._set_status('enrollment_closed')
        db.session.commit()

    def start_game(self):
        self._set_status('in_progress')
        self.game.day_no = 1
        self.game.phase = 1
        db.session.commit()

    def remove_roles_from_game(self):
        Game_Roles.query.filter_by(game_id=self.game.id).delete()
        db.session.commit()

    def set_roles_to_game(self, role_ids):
        for role_id in role_ids:
            role = Game_Roles(game_id=self.game.id,
                              role_id=role_id)
            db.session.add(role)
        db.session.commit()

    def set_start_time(self, start_datetime):
        self.game.start_time = start_datetime
        self._set_status('waiting_for_start')
        db.session.commit()
        return self.game

    def set_phases(self, phases):
        day_hours = phases[0]['duration_hours']
        day_minutes = phases[0]['duration_minutes']
        day_seconds = (day_hours * 60 + day_minutes) * 60
        day_phase = Game_Phases(game_id=self.game.id, phase_id=1, phase_name='Dzień', phase_duration=day_seconds)
        db.session.add(day_phase)

        night_hours = phases[1]['duration_hours']
        night_minutes = phases[1]['duration_minutes']
        night_seconds = (night_hours * 60 + night_minutes) * 60
        night_phase = Game_Phases(game_id=self.game.id, phase_id=2, phase_name='Noc', phase_duration=night_seconds)
        db.session.add(night_phase)

        db.session.commit()

    def shuffle_roles_to_players(self):
        player_ids = [player.id for player in self.game.game_players]
        random.shuffle(player_ids)
        i_id = iter(player_ids)
        for role in self.game.roles:
            role.player_id = next(i_id)
        db.session.commit()

    def shuffle_order_of_players(self):
        players = [player for player in self.game.game_players]
        random.shuffle(players)
        for i, player in enumerate(players):
            player.order_id = i
        db.session.commit()

    def make_all_players_alive(self):
        for player in self.game.game_players:
            player.status = 'alive'
        db.session.commit()

    def get_alive_players(self):
        players = []
        for player in self.game.game_players:
            if player.status == 'alive':
                players.append(player)
        return players

    def get_dead_players(self):
        players = []
        for player in self.game.game_players:
            if player.status == 'dead':
                players.append(player)
        return players

    def get_players_with_role(self, role_name):
        players = []
        for player in self.game.game_players:
            if role_name in [role.role.name for role in player.roles]:
                players.append(player)
        return players

    def _set_status(self, status_name):
        statuses = Status.query.all()
        self.game.status_id = [status.id for status in statuses if status_name == status.name][0]

    def _get_status_id(self, status_name):
        statuses = Status.query.all()
        return [status.id for status in statuses if status.name == status_name][0]

    def get_user_roles(self, user_id):
        player = [game_player for game_player in self.game.game_players if game_player.user_id == user_id][0]
        user_roles = [role.role for role in player.roles]
        return user_roles

    def get_player_id_for_user_id(self, user_id):
        return [player.id for player in self.game.game_players if player.user_id == user_id][0]

    def get_player_id_for_name(self, name):
        return [player.id for player in self.game.game_players if player.name == name][0]

    def kill_player(self, player_id):
        player = [player for player in self.game.game_players if player.id == player_id][0]
        player.status = 'dead'
        db.session.commit()

    def process_to_next_phase(self):
        if self.game.phase == len(self.game.phases):
            # last phase - process to next day
            self.game.day_no += 1
            self.game.phase = 1
        else:
            self.game.phase += 1
        db.session.commit()

    def set_player_name(self, user_id, player_name):
        player = [player for player in self.game.game_players if player.user_id == user_id][0]
        player.name = player_name
        db.session.commit()

    def check_citizen_winning_condition(self):
        mafioso_ids = self.get_role_owners('mafioso')
        mafioso_ids_alive = [player.id for player in self.game.game_players if player.id in mafioso_ids and player.status == 'alive']
        citizen_ids = self.get_role_owners('citizen')
        citizen_ids_alive = [player.id for player in self.game.game_players if
                             player.id in citizen_ids and player.status == 'alive']
        return len(mafioso_ids_alive) == 0 and len(citizen_ids_alive) > 0

    def check_mafioso_winning_condition(self):
        mafioso_ids = self.get_role_owners('mafioso')
        mafioso_ids_alive = [player.id for player in self.game.game_players if
                             player.id in mafioso_ids and player.status == 'alive']
        citizen_ids = self.get_role_owners('citizen')
        citizen_ids_alive = [player.id for player in self.game.game_players if
                             player.id in citizen_ids and player.status == 'alive']
        return len(mafioso_ids_alive) >= len(citizen_ids_alive)

    def get_role_owners(self, role_name):
        player_ids = []
        for player in self.game.game_players:
            if role_name in [gamerole.role.name for gamerole in player.roles]:
                player_ids.append(player.id)
        return player_ids

    def finish_game(self):
        self._set_status('finished')
        db.session.commit()

class RolesApi:
    def __init__(self):
        self.roles = self.list_roles()

    def list_roles(self):
        return Role.query.all()

    def get_role_id_from_name(self, name):
        return Role.query.filter_by(name=name).first().id

    def add_role(self, name, visible_name, description):
        role = Role(name=name, visible_name=visible_name, description=description)
        db.session.add(role)
        db.session.commit()
    

class GameEventApi:

    def create_new_event(self, game, event_name, player_id, target_id):
        new_event = Event(game_id=game.id,
                          event_type=self._get_event_id(event_name),
                          player_id=player_id,
                          target=target_id,
                          day_no=game.day_no,
                          phase_no=game.phase)
        db.session.add(new_event)
        db.session.commit()

    def get_eventtype_id_from_name(self, name):
        return EventType.query.filter_by(name=name).first().id

    def get_event_name_from_id(self, id):
        return EventType.query.filter_by(id=id).first().name

    def _get_event_id(self, event_name):
        e = EventType.query.filter_by(name=event_name).first()
        return e.id

    def get_last_events_for_actual_day(self, game, event_name=None, day_no=None):
        '''
        result = {'event_name1': {1: Event(), 2: Event()},
                  'event_name2': {5: Event(), 18: Event()}
                 }
        Numbers are players
        '''
        if day_no is None:
            day_no = game.day_no
        if event_name is None:
            events = Event.query.filter_by(game_id=game.id, day_no=day_no)
        else:
            event_type = self._get_event_id(event_name)
            events = Event.query.filter_by(game_id=game.id, day_no=day_no, event_type=event_type)

        # get last event for each player - newer overrides older one
        event_dict = {}
        for ev in events:
            event_name = self.get_event_name_from_id(ev.event_type)
            if event_name not in event_dict.keys():
                event_dict[event_name] = {}
            event_dict[event_name][ev.player_id] = ev
        return event_dict

    def get_all_events_for_actual_day(self, game, event_name=None, day_no=None):
        '''
        result = [Event(), Event(), ...]
        '''
        if day_no is None:
            day_no = game.day_no
        if event_name is None:
            events = Event.query.filter_by(game_id=game.id, day_no=day_no)
        else:
            event_type = self._get_event_id(event_name)
            events = Event.query.filter_by(game_id=game.id, day_no=day_no, event_type=event_type)

        return events

    def get_all_events_for_whole_game(self, game, event_name=None):
        '''
            result = [Event(), Event(), ...]
        '''
        if event_name is None:
            events = Event.query.filter_by(game_id=game.id)
        else:
            event_type = self._get_event_id(event_name)
            events = Event.query.filter_by(game_id=game.id, event_type=event_type).order_by(Event.timestamp)
        return events

    def check_if_someone_wins(self, game):
        event_citizens_win = self._get_event_id('citizens_win')
        event_mafiosos_win = self._get_event_id('mafiosos_win')
        events = Event.query.filter_by(game_id=game.id).all()
        winners = []
        for event in events:
            if event.event_type_tbl.name == 'citizens_win':
                winners.append('citizen')
            if event.event_type_tbl.name == 'mafiosos_win':
                winners.append('mafioso')
        return winners


class JobApi:
    def add_job(self, job_name, game, trigger_time):
        new_job = Job(job_name=job_name,
                        game_id=game.id,
                        trigger_time=trigger_time)
        db.session.add(new_job)
        db.session.commit()

    def list_jobs(self):
        return Job.query.filter(Job.status != 'done').all()

    def list_jobs_for_game(self, game_id, for_update=False):
        if for_update:
            return Job.query.filter(Job.status != 'done', Job.game_id == game_id).with_for_update().all()
        else:
            return Job.query.filter(Job.status != 'done', Job.game_id == game_id).all()

    def remove_job(self, job_id):
        job = Job.query.filter(Job.id == job_id).first()
        job.delete()
        db.session.commit()

    def update_job_status(self, job_id, status):
        job = Job.query.filter(Job.id == job_id).first()
        job.status = status
        db.session.commit()

    def lock_table(self):
        db.session.begin_nested()
        db.session.execute('LOCK TABLE ' + Job.__tablename__ + ' IN ACCESS EXCLUSIVE MODE;')

    def unlock_table(self):
        db.session.commit()


class ForumApi:
    def __init__(self, game_id, current_user_id):
        self.game_id = game_id
        self.current_user_id = current_user_id

    def create_topic(self, title, content, author_is_none = True):
        if author_is_none:
            author = 1  # admin
        else:
            author = self.current_user_id
        topic = Topic(
            title=title,
            content=content,
            author=author,
            game_id=self.game_id,
        )
        db.session.add(topic)
        db.session.commit()


    def read_last_reply(self, topic_id, player_id):
        last_reply = Reply.query.filter_by(inReplyTo=topic_id, author_id=player_id).order_by(Reply.date.desc()).first()
        if last_reply is not None:
            utc_to_local(last_reply.date)
        return last_reply

    def create_reply(self, topic_id, content, player_id):
        topic = Topic.query.filter(Topic.id == topic_id).first()
        topic.replies += 1
        thread_reply = Reply(
            reply_id=int(topic.replies),
            content=content,
            author_id=int(player_id),
            inReplyTo=int(topic.id)
        )  # Add the reply
        db.session.add(thread_reply)
        db.session.commit()

    def get_topic(self, game_id, topic_title):
        topic = Topic.query.filter(Topic.game_id == game_id, Topic.title == topic_title).first()
        return topic

    def get_or_create_topics_for_game(self):

        citizen_thread = self.get_topic(self.game_id, 'citizen_thread')
        if citizen_thread is None:
            self.create_topic(title='citizen_thread',
                              content='Oto główny wątek dyskusyjny miasta. Rozpoczynamy grę!')
            citizen_thread = self.get_topic(self.game_id, 'citizen_thread')

        mafioso_thread = self.get_topic(self.game_id, 'mafioso_thread')
        if mafioso_thread is None:
            self.create_topic(title='mafioso_thread',
                              content='To jest tajny wątek tylko dla mafii. Wszystkie informacje tu zawarte będą poufne tylko dla mafii.')
            mafioso_thread = self.get_topic(self.game_id, 'mafioso_thread')

        graveyard_thread = self.get_topic(self.game_id, 'graveyard_thread')
        if graveyard_thread is None:
            self.create_topic(title='graveyard_thread',
                              content='Cmentarz to wątek życia po życiu. Żywi go nie widzą. Możesz tu porozmawiać z innymi zmarłymi.')
            graveyard_thread = self.get_topic(self.game_id, 'graveyard_thread')

        initial_thread = self.get_topic(self.game_id, 'initial_thread')
        if initial_thread is None:
            self.create_topic(title='initial_thread',
                              content='Wątek wstępny.')
            initial_thread = self.get_topic(self.game_id, 'initial_thread')

        return {'citizen_thread': citizen_thread,
                'mafioso_thread': mafioso_thread,
                'graveyard_thread': graveyard_thread,
                'initial_thread': initial_thread
                }

    def get_thread_page(self, thread_id, page):
        replies = Reply.query.filter(Reply.inReplyTo == thread_id).order_by(Reply.reply_id.asc()).paginate(page=page, per_page=15)
        for reply in replies.items:
            reply.date = utc_to_local(reply.date)
        return replies
