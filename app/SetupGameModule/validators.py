from flask import flash


class Validator:
    def __init__(self, game, current_user):
        self.game = game
        self.current_user = current_user

    def user_is_game_admin(self, user_id=None):
        if user_id is None:
            user_id = self.current_user.id
        if self.game.owner.id == user_id:
            return True
        else:
            flash('Nie jesteś administratorem gry.', 'alert-danger')
            return False

    def enrollment_can_be_opened(self):
        if self.game.status.name == 'new' or self.game.status.name == 'enrollment_closed':
            return True
        else:
            flash('Zapisy nie mogą zostać otwarte na tym etapie.', 'alert-danger')
            return False

    def enrollment_is_closed(self):
        if self.game.status.name == 'enrollment_closed':
            return True
        else:
            flash('Zapisy nie są, a muszą być zamknięte.', 'alert-danger')
            return False
    def enrollment_is_open(self):
        if self.game.status.name == 'enrollment_open':
            return True
        else:
            flash('Zapisy nie są otwarte.', 'alert-danger')
            return False

    def user_in_game(self, user_id=None):
        if user_id is None:
            user_id = self.current_user.id
        if user_id in [player.user_id for player in self.game.game_players]:
            return True
        else:
            flash('Gracz nie jest zapisany do gry.', 'alert-danger')
            return False

    def user_not_in_game(self, user_id=None):
        if user_id is None:
            user_id = self.current_user.id
        if user_id not in [player.user_id for player in self.game.game_players]:
            return True
        else:
            flash('Gracz jest już zapisany do gry.', 'alert-danger')
            return False

    def thrown_user_is_not_game_admin(self, user_id=None):
        if user_id is None:
            user_id = self.current_user.id
        if self.game.owner.id != user_id:
            return True
        else:
            flash('Nie możesz wyrzucić administratora gry.', 'alert-danger')
            return False

    def game_is_not_started(self):
        if self.game.status.name in ['new', 'enrollment_open', 'enrollment_closed', 'waiting_for_start']:
            return True
        else:
            return False

    def game_is_started(self):
        if self.game.status.name in ['in_progress', 'finished']:
            return True
        else:
            flash('Gra jeszcze nie wystartowała.', 'alert-danger')
            return False

    def game_in_progress(self):
        if self.game.status.name == 'in_progress':
            return True
        else:
            flash('Nie jesteś w trakcie gry!', 'alert-danger')

    def roles_no_equals_players_no(self):
        if len(self.game.roles) == len(self.game.game_players):
            return True
        else:
            flash('Liczba ról nie zgadza się z liczbą graczy. Skonfiguruj role ponownie.', 'alert-danger')
            return False

    def user_has_role(self, role):
        user_roles = [game_player.roles for game_player in self.game.game_players if game_player.user_id == self.current_user.id][0]
        if role in [r.role.name for r in user_roles]:
            return True
        else:
            flash('Nie posiadasz odpowiedniej roli!', 'alert-danger')
            return False

    def user_can_do_event(self, event_name):
        user_roles = [game_player.roles for game_player in self.game.game_players if game_player.user_id == self.current_user.id][0]
        user_events = [user_role.role.events for user_role in user_roles]
        if event_name in [ue.eventtype.name for ue in user_events[0]]:
            return True
        else:
            flash('Nie posiadasz odpowiedniej roli.', 'alert-danger')
            return False

    def user_is_alive(self):
        user_status = [game_player.status for game_player in self.game.game_players if game_player.user_id == self.current_user.id][0]
        if user_status == 'alive':
            return True
        else:
            flash('Nie możesz tego zrobić, bo nie żyjesz!', 'alert-danger')
            return False

    def user_is_allowed_for_forum(self, forum_name):
        if forum_name == 'initial_thread':
            if self.game.status.name not in ['in_progress']:
                return True
            else:
                flash('Nie masz uprawnień do tego forum!', 'alert-danger')
                return False
        elif forum_name == 'graveyard_thread':
            user_status = [game_player.status for game_player in self.game.game_players if
                           game_player.user_id == self.current_user.id][0]
            if (user_status == 'dead' and self.user_has_role('citizen')) or self.game.status.name == 'finished':
                return True
            else:
                flash('Nie masz uprawnień do tego forum!', 'alert-danger')
                return False
        elif forum_name == 'mafioso_thread':
            return self.user_has_role('mafioso') or self.game.status.name == 'finished'
        elif forum_name == 'citizen_thread':
            return True # anyone can see citizen thread

    def user_can_write_in_forum(self, forum_name):
        if forum_name == 'initial_thread':
            return self.game.status.name not in ['in_progress']

        elif forum_name == 'graveyard_thread':
            user_status = [game_player.status for game_player in self.game.game_players if
                           game_player.user_id == self.current_user.id][0]
            return user_status == 'dead' and self.user_has_role('citizen')

        elif forum_name == 'mafioso_thread':
            return self.user_has_role('mafioso')
        elif forum_name == 'citizen_thread':
            try:
                user_status = [game_player.status for game_player in self.game.game_players if
                               game_player.user_id == self.current_user.id][0]
            except:
                user_status = 'unknown'
            return user_status == 'alive'
