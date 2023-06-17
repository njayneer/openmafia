
def do(game_id, source_id):

    from app.Engine.DB.db_api import GameApi, ForumApi, NotificationApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    from flask_login import current_user
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        game_api.shuffle_roles_to_players()
        game_api.shuffle_order_of_players()
        game_api.make_all_players_alive()
        game_api.make_special_players_status_special()
        game_api.start_game()
        forum_api = ForumApi(game_api.game.id, current_user.id)
        forum_api.get_or_create_topics_for_game()


        # notifications with roles
        roles_dictionary = game_api.get_all_players_roles(visible=True)
        for player in game_api.game.game_players:
            roles = roles_dictionary[player.id]
            roles_string = roles[0]
            for role in roles[1:]:
                roles_string += ', ' + role
            notif_api = NotificationApi()
            notif_api.add_new_notification(player.id, 'game_started', roles_string)

        game_scheduler = GameScheduler()
        game_scheduler.create_lynch_for_actual_day(game_api.game)
        game_scheduler.create_mafia_kill_for_actual_day(game_api.game)
