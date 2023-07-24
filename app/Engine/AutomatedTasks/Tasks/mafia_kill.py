
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi, NotificationApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    import random
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()

        # game_admin can create event to block lynch. If so, kill noone and proces to next phase
        admin_blocks = len(event_api.get_last_events_for_actual_day(game_api.game, 'admin_block_mafia_kill')) > 0

        if (not admin_blocks) and game_api.game.status.name == 'in_progress':
            target = check_target_from_events(game_api, event_api)

            # role:priest - check if there is no prayer events for current day
            target = check_priest_prayer(event_api, game_api, target)

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

        if game_api.game.status.name == 'in_progress':
            # Winning conditions
            finished = game_api.check_winning_condition()
            if not finished:
                game_api.process_to_next_phase()
                game_scheduler = GameScheduler()
                game_scheduler.create_lynch_for_actual_day(game_api.game)
                game_scheduler.create_mafia_kill_for_actual_day(game_api.game)


def check_priest_prayer(event_api, game_api, target):
    priest_prayer = event_api.get_last_events_for_actual_day(game_api.game, 'priest_prayer')
    if len(priest_prayer) > 0:
        priest_prayer = priest_prayer['priest_prayer']
        priest_result = False
        for p_source in priest_prayer:
            p = priest_prayer[p_source]
            p_target = p.target
            if p_target == target:  # prayer target equals mafia target
                priest_result = True
        if priest_result:
            target = None
    return target


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
