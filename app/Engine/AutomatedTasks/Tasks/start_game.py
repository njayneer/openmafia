
def do(game_id):

    from app.Engine.DB.db_api import GameApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        game_api.shuffle_roles_to_players()
        game_api.shuffle_order_of_players()
        game_api.make_all_players_alive()
        game_api.start_game()

        game_scheduler = GameScheduler()
        game_scheduler.create_lynch_for_actual_day(game_api.game)
