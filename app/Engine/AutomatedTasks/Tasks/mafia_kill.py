
def do(game_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    import random
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()

        # game_admin can create event to block lynch. If so, kill noone and proces to next phase
        admin_blocks = len(event_api.get_last_events_for_actual_day(game_api.game, 'admin_block_mafia_kill')) > 0

        if not admin_blocks:
            target = check_target_from_events(game_api, event_api)

            # Kill the target
            if target is not None:
                event_api.create_new_event(game=game_api.game,
                                           event_name='mafia_kill',
                                           player_id=None,
                                           target_id=target)
                game_api.kill_player(target)
            else:
                event_api.create_new_event(game=game_api.game,
                                           event_name='mafia_kill',
                                           player_id=None,
                                           target_id=None)

        # Winning conditions
        if game_api.check_citizen_winning_condition():
            # city win
            game_api.finish_game()
            event_api.create_new_event(game=game_api.game,
                                       event_name='citizens_win',
                                       player_id=None,
                                       target_id=None)
        elif game_api.check_mafioso_winning_condition():
            game_api.finish_game()
            event_api.create_new_event(game=game_api.game,
                                       event_name='mafiosos_win',
                                       player_id=None,
                                       target_id=None)
            # mafia win
        else:
            game_api.process_to_next_phase()
            game_scheduler = GameScheduler()
            game_scheduler.create_lynch_for_actual_day(game_api.game)


def check_target_from_events(game_api, event_api):
    events = event_api.get_last_events_for_actual_day(game_api.game, 'mafia_kill_vote')
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


if __name__ == "__main__":
    do(2)
