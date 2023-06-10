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
        classic_games = [game for game in game_api.list_games('my_games', user) if game.game_type.name == 'classic' and game.status.name == 'finished']
        classic_creations = []
        for g in classic_games:
            game_api.game = g
            classic_creations.append(game_api.get_player_object_for_user_id(user_id))

    return render_template('User_index.html',
                           user=user,
                           achievements=achievements,
                           classic_creations=classic_creations)
