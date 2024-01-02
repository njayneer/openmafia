
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi, NotificationApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    import random
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()

        if game_api.game.status.name == 'in_progress':
            target = check_target_from_events(game_api, event_api)

            # Kill the target
            if target is not None:
                event_api.create_new_event(game=game_api.game,
                                           event_name='lynch_draw_mafia_chose',
                                           player_id=None,
                                           target_id=target)
                game_api.kill_player(target)
            else:
                event_api.create_new_event(game=game_api.game,
                                           event_name='lynch_draw_mafia_chose',
                                           player_id=None,
                                           target_id=None)


def check_target_from_events(game_api, event_api):
    events = event_api.get_last_events_for_actual_day(game_api.game, 'lynch_draw_mafia_choice_vote')
    if events == {}:
        target = None
    else:
        # Get last event
        last_event = None
        for event_user in events:
            for event in events[event_user]:
                if last_event is None:
                    last_event = events[event_user][event]
                else:
                    if last_event.id < events[event_user][event].id:
                        last_event = events[event_user][event]
        target = last_event.target
    return target
