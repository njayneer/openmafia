from app.Engine.DB.models import *
import random
from flask_login import current_user
from sqlalchemy import desc

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
        day_dt = phases[0]['duration']
        day_seconds = (day_dt.hour * 60 + day_dt.minute) * 60 + day_dt.second
        day_phase = Game_Phases(game_id=self.game.id, phase_id=1, phase_name='Dzień', phase_duration=day_seconds)
        db.session.add(day_phase)

        night_dt = phases[1]['duration']
        night_seconds = (night_dt.hour * 60 + night_dt.minute) * 60 + night_dt.second
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
        return len(mafioso_ids_alive) == 0

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

    def get_last_events_for_actual_day(self, game, event_name=None):
        '''
        result = {'event_name1': {1: Event(), 2: Event()},
                  'event_name2': {5: Event(), 18: Event()}
                 }
        Numbers are players
        '''
        if event_name is None:
            events = Event.query.filter_by(game_id=game.id, day_no=game.day_no)
        else:
            event_type = self._get_event_id(event_name)
            events = Event.query.filter_by(game_id=game.id, day_no=game.day_no, event_type=event_type)

        # get last event for each player - newer overrides older one
        event_dict = {}
        for ev in events:
            event_name = self.get_event_name_from_id(ev.event_type)
            if event_name not in event_dict.keys():
                event_dict[event_name] = {}
            event_dict[event_name][ev.player_id] = ev
        return event_dict

    def get_all_events_for_actual_day(self, game, event_name=None):
        '''
        result = [Event(), Event(), ...]
        '''
        if event_name is None:
            events = Event.query.filter_by(game_id=game.id, day_no=game.day_no)
        else:
            event_type = self._get_event_id(event_name)
            events = Event.query.filter_by(game_id=game.id, day_no=game.day_no, event_type=event_type)

        return events
