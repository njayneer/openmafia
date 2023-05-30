def _player_roles(player):
    return [role.role.name for role in player.roles]

def get_all_privileges():
    return {
        'graveyard_visible': GraveyardVisible(),
        'graveyard_forum_read': GraveyardForumRead(),
        'graveyard_forum_write': GraveyardForumWrite(),
        'initial_thread_forum_read': InitialThreadForumRead(),
        'initial_thread_forum_write': InitialThreadForumWrite(),
        'mafioso_forum_read': MafiosoForumRead(),
        'mafioso_forum_write': MafiosoForumWrite(),
        'citizen_forum_read': CitizenForumRead(),
        'citizen_forum_write': CitizenForumWrite(),
        'citizen_vote': CitizenVote(),
        'mafia_kill_vote': MafiaKillVote(),
        'mafia_tab_visible': MafiaTabVisible(),
        'see_roles_of_alive_players': SeeRolesOfAlivePlayers(),
        'see_roles_of_dead_players': SeeRolesOfDeadPlayers()
    }


def judge_privileges(privileges, player, game):
    for privilege in privileges:
        privileges[privilege].judge_if_deserved(player, game)
    return privileges

class Privilege:
    description = 'This is generic privilege and should not be used in practical situations.'
    def __init__(self):
        self.granted = False

    def grant(self):
        self.granted = True

    def revoke(self):
        self.granted = False

    def judge_if_deserved(self, player=None, game=None):
        self.granted = False
        return self.granted


class GraveyardVisible(Privilege):
    description = 'You are able to see whole graveyard tab with all that content.'

    def judge_if_deserved(self, player=None, game=None):
        dead_citizen = player.status == 'dead' and 'citizen' in _player_roles(player)
        game_finished = game.status.name == 'finished'
        if dead_citizen or game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GraveyardForumRead(Privilege):
    description = 'You are able read in graveyard forum.'

    def judge_if_deserved(self, player=None, game=None):
        dead_citizen = player.status == 'dead' and 'citizen' in _player_roles(player)
        game_finished = game.status.name == 'finished'
        if dead_citizen or game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class GraveyardForumWrite(Privilege):
    description = 'You are able write in graveyard forum.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        dead_citizen = player.status == 'dead' and 'citizen' in _player_roles(player)
        if player_in_game and dead_citizen:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class InitialThreadForumRead(Privilege):
    description = 'You are able read in initial thread forum.'

    def judge_if_deserved(self, player=None, game=None):
        game_not_in_progress = game.status.name != 'in_progress'
        if game_not_in_progress:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class InitialThreadForumWrite(Privilege):
    description = 'You are able write in initial thread forum.'

    def judge_if_deserved(self, player=None, game=None):
        game_not_in_progress = game.status.name != 'in_progress'
        if game_not_in_progress:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiosoForumRead(Privilege):
    description = 'You are able read in mafioso forum.'

    def judge_if_deserved(self, player=None, game=None):
        player_is_mafioso = 'mafioso' in _player_roles(player)
        game_finished = game.status.name == 'finished'
        if player_is_mafioso or game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiosoForumWrite(Privilege):
    description = 'You are able write in mafioso forum.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        player_is_mafioso = 'mafioso' in _player_roles(player)
        if player_in_game and player_is_mafioso:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenForumRead(Privilege):
    description = 'You are able read in citizen forum.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        if player_in_game:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenForumWrite(Privilege):
    description = 'You are able write in citizen forum.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        alive_player = player.status == 'alive'
        if player_in_game and alive_player:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class CitizenVote(Privilege):
    description = 'You are able to vote choosing player to be lynch.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        alive_player = player.status == 'alive'
        current_phase_is_day = game.phase == 1
        if player_in_game and alive_player and current_phase_is_day:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiaKillVote(Privilege):
    description = 'You are able to choose target for mafia murder.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        player_is_mafioso = 'mafioso' in _player_roles(player)
        alive_player = player.status == 'alive'
        if player_in_game and player_is_mafioso and alive_player:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class MafiaTabVisible(Privilege):
    description = 'You are able to see content from mafia tab.'

    def judge_if_deserved(self, player=None, game=None):
        player_in_game = player.game_id == game.id
        player_is_mafioso = 'mafioso' in _player_roles(player)
        if player_in_game and player_is_mafioso:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeRolesOfAlivePlayers(Privilege):
    description = 'You are able to see all roles owned by alive players.'

    def judge_if_deserved(self, player=None, game=None):
        game_finished = game.status.name == 'finished'
        if game_finished:
            self.granted = True
        else:
            self.granted = False
        return self.granted


class SeeRolesOfDeadPlayers(Privilege):
    description = 'You are able to see all roles owned by dead players.'

    def judge_if_deserved(self, player=None, game=None):
        self.granted = True
        return self.granted

    
class SeeRolesOfDeadPlayers(Privilege):
    description = 'You are able to see all roles owned by dead players.'

    def judge_if_deserved(self, player=None, game=None):
        self.granted = True
        return self.granted