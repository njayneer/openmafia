from . import UserModule
from flask_login import current_user, login_required
from flask import render_template
from app.Engine.DB.db_api import UserApi, GameApi


@UserModule.route('/<user_id>', methods=['GET', 'POST'])
@UserModule.route('', methods=['GET', 'POST'])
@login_required
def user_main(user_id=None):
    if user_id is None:
        user_id = current_user.id
    else:
        user_id = int(user_id)
    achievements = None
    classic_creations = None
    classic_games = None

    user_api = UserApi()
    user = user_api.get_user_for_user_id(user_id)
    if user:
        game_api = GameApi()
        achievements = user_api.get_user_achievements()
        my_finished_games = [game for game in game_api.list_games('my_games', user) if game.status.name == 'finished']
        classic_games = [game for game in my_finished_games if game.game_type.name == 'classic']
        classic_creations = []
        for g in classic_games:
            game_api.game = g
            classic_creations.append(game_api.get_player_object_for_user_id(user_id))

    return render_template('User_index.html',
                           user=user,
                           achievements=achievements,
                           classic_creations=classic_creations)


@UserModule.route('/list', methods=['GET', 'POST'])
@UserModule.route('/list/<page>', methods=['GET', 'POST'])
@login_required
def user_list(page=1):
    page = int(page)
    user_api = UserApi()
    users = user_api.get_all_users(page, 10)

    return render_template('User_list.html',
                           users=users)


@UserModule.route('/toplist', methods=['GET', 'POST'])
@UserModule.route('/toplist/<page>', methods=['GET', 'POST'])
@login_required
def user_toplist(page=1):
    page = int(page)
    game_api = GameApi()
    game_players = game_api.get_game_players()
    users = extract_users_data_from_db_game_players(game_players)
    users = add_calculated_users_data(users)
    users = {k: v for k, v in sorted(users.items(), key=lambda item: item[1]['OM_points'], reverse=True)}

    return render_template('User_toplist.html',
                           users=users)


def add_calculated_users_data(users):
    for user in users:
        users[user]['won_percentage'] = round(users[user]['games_won'] / users[user]['games_played'] * 100, 2)
        users[user]['OM_points'] = users[user]['games_played'] + users[user]['games_won'] * 2 + users[user]['games_mvp'] * 7
    return users


def extract_users_data_from_db_game_players(game_players):
    users = {}
    for gp in game_players:
        if gp.status != 'special':
            if gp.user_id not in users:
                users[gp.user_id] = {}

            if 'games_played' not in users[gp.user_id]:
                users[gp.user_id]['games_played'] = 1
            else:
                users[gp.user_id]['games_played'] += 1

            won = int(gp.winner)
            if 'games_won' not in users[gp.user_id]:
                users[gp.user_id]['games_won'] = won
            else:
                users[gp.user_id]['games_won'] += won

            mvp = 'mvp' in [a.achievement.name for a in gp.achievements]
            if mvp:
                mvp = 1
            else:
                mvp = 0
            if 'games_mvp' not in users[gp.user_id]:
                users[gp.user_id]['games_mvp'] = mvp
            else:
                users[gp.user_id]['games_mvp'] += mvp

            users[gp.user_id]['user_name'] = gp.user.name

    return users
