
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    import random
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()

        target = check_target_from_events(game_api, event_api, source_id)

        # Check the target
        if target is not None:
            #game_api.kill_player(target)
            pass # TODO: create notification here


def check_target_from_events(game_api, event_api, source_id):
    # day_no - 1 due to be fired after mafia kill
    events = event_api.get_last_events_for_actual_day(game_api.game, 'detective_check', day_no=game_api.game.day_no-1)
    if events is None:
        target = None
    elif source_id not in events['detective_check']:
        target = None
    else:
        # result = {'event_name1': {1: Event(), 2: Event()},
        #           'event_name2': {5: Event(), 18: Event()}
        #           }
        # Get last event
        last_event = events['detective_check'][source_id]
        target = last_event.target
    return target


if __name__ == "__main__":
    do(2)
