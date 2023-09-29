from app.Engine.DB.models import GamePlayer, Game
from app.Engine.DB.db_api import GameApi, UserApi
from flask_login import current_user
def _player_roles(player):
    return [role.role.name for role in player.roles]




def _get_all_privileges(player, game):
    return {
        'graveyard_visible': GraveyardVisible(player, game),
        'graveyard_forum_read': GraveyardForumRead(player, game),
        'graveyard_forum_write': GraveyardForumWrite(player, game),
        'initial_thread_forum_read': InitialThreadForumRead(player, game),
        'initial_thread_forum_write': InitialThreadForumWrite(player, game),
        'mafioso_forum_read': MafiosoForumRead(player, game),
        'mafioso_forum_write': MafiosoForumWrite(player, game),
        'citizen_forum_read': CitizenForumRead(player, game),
        'citizen_forum_write': CitizenForumWrite(player, game),
        'citizen_vote': CitizenVote(player, game),
        'mafia_kill_vote': MafiaKillVote(player, game),
        'mafia_tab_visible': MafiaTabVisible(player, game),
        'see_roles_of_alive_players': SeeRolesOfAlivePlayers(player, game),
        'see_roles_of_dead_players': SeeRolesOfDeadPlayers(player, game),
        'kill_a_player_at_any_time': KillAPlayerAtAnyTime(player, game),
        'revive_a_player_at_any_time': ReviveAPlayerAtAnyTime(player, game),
        'see_detailed_lynch_results': SeeDetailedLynchResults(player, game),
        'see_history_of_lynch_voting': SeeHistoryOfLynchVoting(player, game),
        'block_lynch': BlockLynch(player, game),
        'block_mafia_kill': BlockMafiaKill(player, game),
        'adding_game_guest': AddingGameGuest(player, game),
        'reverting_game': RevertingGame(player, game),
        'see_list_of_dead_people': SeeListOfDeadPeople(player, game),
        'see_user_names_of_players': SeeUserNamesOfPlayers(player, game),
        'see_enrolled_user_list': SeeEnrolledUserList(player, game),
        'see_creations_form': SeeCreationsForm(player, game),
        'detective_check': DetectiveCheck(player, game),
        'judge_players': JudgePlayers(player, game),
        'speeding_up_game': SpeedingUpGame(player, game),
        'priest_prayer': PriestPrayer(player, game),
        'gun_shot': GunShot(player, game),
        'event_history_read': EventHistoryRead(player, game),
        'event_remove': EventRemove(player, game),
        'choose_mvp': ChooseMVP(player, game),
        'choose_mvp2': ChooseMVP2(player, game),
        'choose_mvp3': ChooseMVP3(player, game),
        'show_judgement_summary': ShowJudgementSummary(player, game),
        'see_list_of_special_people': SeeListOfSpecialPeople(player, game),
        'show_lobby': ShowLobby(player, game)
    }


def judge_privileges(player, game):
    privileges = _get_all_privileges(player, game)
    for privilege in privileges:
        privileges[privilege].judge_if_deserved()
    return privileges


class Privilege:
    description = 'This is generic privilege and should not be used in practical situations.'

    def __init__(self, player=None, game=None):
        self.game_api = GameApi()
        self.game_api.set_game(game)
        self.user_api = UserApi()
        self.user_api.user = current_user
        self.user_attributes = [ua.attribute.name for ua in self.user_api.get_user_attributes()]
        self.granted = False
        if player:
            self.player = player
        else:
            self.player = GamePlayer()
        if game:
            self.game = game
        else:
            self.game = Game()
        self.calculate_conditions()

    def grant(self):
        self.granted = True

    def revoke(self):
        self.granted = False

    def judge_if_deserved(self):
        self.granted = False
        return self.granted

    def calculate_conditions(self):
        self.dead_citizen = self.player.status == 'dead' and 'citizen' in _player_roles(self.player)
        self.game_finished = self.game.status.name == 'finished'
        self.game_admin = 'game_admin' in _player_roles(self.player)
        self.player_in_game = self.player.game_id == self.game.id
        self.game_not_in_progress = self.game.status.name != 'in_progress'
        self.game_started = self.game.status.name in ['in_progress', 'finished']
        self.player_is_mafioso = 'mafioso' in _player_roles(self.player)
        self.alive_player = self.player.status == 'alive'
        self.current_phase_is_day = self.game.phase == 1
        self.cfg_see_detailed_lynch_results = self.game_api.get_configuration('detailed_lynch_results') == '1'
        self.cfg_see_history_of_lynch_voting = self.game_api.get_configuration('lynch_voting_history') == '1'
        self.game_guest = 'game_guest' in _player_roles(self.player)
        self.cfg_see_enrolled_user_list = self.game_api.get_configuration('see_enrolled_user_list') == '1'
        self.cfg_game_admin = self.game_api.get_configuration('game_admin') == '1'
        self.cfg_citizen_forum_turned_on = self.game_api.get_configuration('citizen_forum_turned_on') == '1'
        self.cfg_initial_forum_turned_on = self.game_api.get_configuration('initial_forum_turned_on') == '1'
        self.cfg_creations_on = self.game_api.get_configuration('creations_on') == '1'
        self.role_detective = 'detective' in _player_roles(self.player)
        self.role_priest = 'priest' in _player_roles(self.player)
        self.item_gun = len(self.game_api.select_game_items('gun', self.player.id, not_consumed_only=True)) > 0
        self.admin = 'administrator' in self.user_attributes
        self.mvp_not_asigned = 'mvp' not in [a.achievement.name for a in self._get_achievements()]
        self.mvp2_not_asigned = 'mvp2' not in [a.achievement.name for a in self._get_achievements()]
        self.mvp3_not_asigned = 'mvp3' not in [a.achievement.name for a in self._get_achievements()]

    def _get_achievements(self):
        return self.user_api.get_game_achievements([gp.id for gp in self.game.game_players])
class GraveyardVisible(Privilege):
    description = 'You are able to see whole graveyard tab with all that content.'

    def judge_if_deserved(self):
        if self.dead_citizen or self.game_finished or self.game_admin or self.game_guest or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GraveyardForumRead(Privilege):
    description = 'You are able read in graveyard forum.'

    def judge_if_deserved(self):
        if self.dead_citizen or self.game_finished or self.game_admin or self.game_guest or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GraveyardForumWrite(Privilege):
    description = 'You are able write in graveyard forum.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.dead_citizen) or self.game_admin or self.game_guest or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class InitialThreadForumRead(Privilege):
    description = 'You are able read in initial thread forum.'

    def judge_if_deserved(self):
        if (self.game_not_in_progress and self.cfg_initial_forum_turned_on) or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class InitialThreadForumWrite(Privilege):
    description = 'You are able write in initial thread forum.'

    def judge_if_deserved(self):
        if (self.game_not_in_progress and self.cfg_initial_forum_turned_on) or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiosoForumRead(Privilege):
    description = 'You are able read in mafioso forum.'

    def judge_if_deserved(self):
        if self.player_is_mafioso or self.game_finished or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiosoForumWrite(Privilege):
    description = 'You are able write in mafioso forum.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.player_is_mafioso) or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenForumRead(Privilege):
    description = 'You are able read in citizen forum.'

    def judge_if_deserved(self):
        if self.cfg_initial_forum_turned_on or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenForumWrite(Privilege):
    description = 'You are able write in citizen forum.'

    def judge_if_deserved(self):
        if ((self.player_in_game and self.alive_player) or self.game_admin or self.admin) and self.cfg_citizen_forum_turned_on:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenVote(Privilege):
    description = 'You are able to vote choosing player to be lynch.'

    def judge_if_deserved(self):
        if self.player_in_game and self.alive_player and self.current_phase_is_day and not self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiaKillVote(Privilege):
    description = 'You are able to choose target for mafia murder.'

    def judge_if_deserved(self):
        if self.player_in_game and self.player_is_mafioso and self.alive_player and not self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiaTabVisible(Privilege):
    description = 'You are able to see content from mafia tab.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.player_is_mafioso) or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeRolesOfAlivePlayers(Privilege):
    description = 'You are able to see all roles owned by alive players.'

    def judge_if_deserved(self):
        if self.game_finished or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeRolesOfDeadPlayers(Privilege):
    description = 'You are able to see all roles owned by dead players.'

    def judge_if_deserved(self):
        self.granted = True
        return self.granted


class KillAPlayerAtAnyTime(Privilege):
    description = 'You can kill any player at any time'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class ReviveAPlayerAtAnyTime(Privilege):
    description = 'You can revive any player at any time'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class SeeDetailedLynchResults(Privilege):
    description = 'You can see who voted to who in previous days'

    def judge_if_deserved(self):
        if self.cfg_see_detailed_lynch_results or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeHistoryOfLynchVoting(Privilege):
    description = 'You can see all votes, also changed and outdated, also in current day.'

    def judge_if_deserved(self):
        if self.cfg_see_history_of_lynch_voting or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class BlockLynch(Privilege):
    description = 'You can block this day lynch.'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class BlockMafiaKill(Privilege):
    description = 'You can block this day mafia kill.'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class AddingGameGuest(Privilege):
    description = 'You can add an user as a game guest.'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class RevertingGame(Privilege):
    description = 'You can revert the game to state before shuffling roles and start.'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeListOfDeadPeople(Privilege):
    description = 'You can see a list of dead people in lobby of the game.'

    def judge_if_deserved(self):
        #if self.game_finished or self.game_admin:
        if True:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class SeeListOfSpecialPeople(Privilege):
    description = 'You can see a list of other people than players in lobby of the game.'

    def judge_if_deserved(self):
        if self.game_finished or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeUserNamesOfPlayers(Privilege):
    description = 'You can see user name next to player name in game list of players.'
    def judge_if_deserved(self):
        if self.game_finished or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeEnrolledUserList(Privilege):
    description = 'You can see full list of user names before game start. If no, you can see only number of enrolled people.'

    def judge_if_deserved(self):
        # only with configuration or if you are to be GM.
        if self.cfg_see_enrolled_user_list or (self.cfg_game_admin and self.game.owner_id == self.player.user_id) or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeCreationsForm(Privilege):
    description = 'You can see form to choose your creation name for incomming game.'

    def judge_if_deserved(self):
        # only with configuration or if you are to be GM.
        if self.cfg_creations_on and self.player_in_game:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class DetectiveCheck(Privilege):
    description = 'You can use detective ability.'

    def judge_if_deserved(self):
        # only with configuration or if you are to be GM.
        if self.role_detective and self.alive_player and not self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class PriestPrayer(Privilege):
    description = 'You can use priest ability.'

    def judge_if_deserved(self):
        # only with configuration or if you are to be GM.
        if self.role_priest and self.alive_player and not self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class JudgePlayers(Privilege):
    description = 'You can send judgement of all alive players.'

    def judge_if_deserved(self):
        if self.alive_player and not self.game_finished and not self.player_is_mafioso:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SpeedingUpGame(Privilege):
    description = 'You can speed up game to have configured lynch, murder and all game component earlier/later.'

    def judge_if_deserved(self):
        if self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GunShot(Privilege):
    description = 'You can shot from gun'

    def judge_if_deserved(self):
        if self.item_gun:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class EventHistoryRead(Privilege):
    description = 'You can read event history for the game'

    def judge_if_deserved(self):
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class EventRemove(Privilege):
    description = 'You can remove any event from the game'

    def judge_if_deserved(self):
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class ChooseMVP(Privilege):
    description = 'You can asign a player the MVP badge'

    def judge_if_deserved(self):
        if self.game_admin and self.mvp_not_asigned and self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class ChooseMVP2(Privilege):
    description = 'You can asign a player the vice MVP badge'

    def judge_if_deserved(self):
        if self.game_admin and self.mvp2_not_asigned and self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class ChooseMVP3(Privilege):
    description = 'You can asign a player the 2nd vice MVP badge'

    def judge_if_deserved(self):
        if self.game_admin and self.mvp3_not_asigned and self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class ShowJudgementSummary(Privilege):
    description = 'You can see judgement summary of whole game'

    def judge_if_deserved(self):
        if self.game_finished or self.game_admin or self.admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class ShowLobby(Privilege):
    description = 'You can see lobby of a game'

    def judge_if_deserved(self):
        if (self.player_in_game or self.game_admin or self.admin) and self.game_started:
            self.granted = True
        else:
            self.granted = False
        return self.granted
