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
        'see_detailed_lynch_results': SeeDetailedLynchResults(player, game),
        'see_history_of_lynch_voting': SeeHistoryOfLynchVoting(player, game),
        'block_lynch': BlockLynch(player, game),
        'block_mafia_kill': BlockMafiaKill(player, game),
        'adding_game_guest': AddingGameGuest(player, game),
        'reverting_game': RevertingGame(player, game),
        'see_list_of_dead_people': SeeListOfDeadPeople(player, game),
        'see_user_names_of_players': SeeUserNamesOfPlayers(player, game)
    }


def judge_privileges(player, game):
    privileges = _get_all_privileges(player, game)
    for privilege in privileges:
        privileges[privilege].judge_if_deserved()
    return privileges

class Privilege:
    description = 'This is generic privilege and should not be used in practical situations.'

    def __init__(self, player, game):
        self.granted = False
        self.player = player
        self.game = game
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
        self.player_is_mafioso = 'mafioso' in _player_roles(self.player)
        self.alive_player = self.player.status == 'alive'
        self.current_phase_is_day = self.game.phase == 1
        self.cfg_see_detailed_lynch_results = self.game.get_configuration('detailed_lynch_results') == '1'
        self.cfg_see_history_of_lynch_voting = self.game.get_configuration('lynch_voting_history') == '1'
        self.game_guest = 'game_guest' in _player_roles(self.player)

class GraveyardVisible(Privilege):
    description = 'You are able to see whole graveyard tab with all that content.'

    def judge_if_deserved(self):
        if self.dead_citizen or self.game_finished or self.game_admin or self.game_guest:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GraveyardForumRead(Privilege):
    description = 'You are able read in graveyard forum.'

    def judge_if_deserved(self):
        if self.dead_citizen or self.game_finished or self.game_admin or self.game_guest:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GraveyardForumWrite(Privilege):
    description = 'You are able write in graveyard forum.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.dead_citizen) or self.game_admin or self.game_guest:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class InitialThreadForumRead(Privilege):
    description = 'You are able read in initial thread forum.'

    def judge_if_deserved(self):
        if self.game_not_in_progress:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class InitialThreadForumWrite(Privilege):
    description = 'You are able write in initial thread forum.'

    def judge_if_deserved(self):
        if self.game_not_in_progress:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiosoForumRead(Privilege):
    description = 'You are able read in mafioso forum.'

    def judge_if_deserved(self):
        if self.player_is_mafioso or self.game_finished or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiosoForumWrite(Privilege):
    description = 'You are able write in mafioso forum.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.player_is_mafioso) or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenForumRead(Privilege):
    description = 'You are able read in citizen forum.'

    def judge_if_deserved(self):
        if self.player_in_game:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenForumWrite(Privilege):
    description = 'You are able write in citizen forum.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.alive_player) or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenVote(Privilege):
    description = 'You are able to vote choosing player to be lynch.'

    def judge_if_deserved(self):
        if self.player_in_game and self.alive_player and self.current_phase_is_day:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiaKillVote(Privilege):
    description = 'You are able to choose target for mafia murder.'

    def judge_if_deserved(self):
        if self.player_in_game and self.player_is_mafioso and self.alive_player:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiaTabVisible(Privilege):
    description = 'You are able to see content from mafia tab.'

    def judge_if_deserved(self):
        if (self.player_in_game and self.player_is_mafioso) or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeRolesOfAlivePlayers(Privilege):
    description = 'You are able to see all roles owned by alive players.'

    def judge_if_deserved(self):
        if self.game_finished or self.game_admin:
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
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeDetailedLynchResults(Privilege):
    description = 'You can see who voted to who in previous days'

    def judge_if_deserved(self):
        if self.cfg_see_detailed_lynch_results or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeHistoryOfLynchVoting(Privilege):
    description = 'You can see all votes, also changed and outdated, also in current day.'

    def judge_if_deserved(self):
        if self.cfg_see_history_of_lynch_voting or self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class BlockLynch(Privilege):
    description = 'You can block this day lynch.'

    def judge_if_deserved(self):
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class BlockMafiaKill(Privilege):
    description = 'You can block this day mafia kill.'

    def judge_if_deserved(self):
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class AddingGameGuest(Privilege):
    description = 'You can add an user as a game guest.'

    def judge_if_deserved(self):
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted

class RevertingGame(Privilege):
    description = 'You can revert the game to state before shuffling roles and start.'

    def judge_if_deserved(self):
        if self.game_admin:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeListOfDeadPeople(Privilege):
    description = 'You can see a list of dead people in lobby of the game.'

    def judge_if_deserved(self):
        if self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted

    
class SeeUserNamesOfPlayers(Privilege):
    def judge_if_deserved(self):
        if self.game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted
