
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi, NotificationApi
    from app import app
    import random

    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()

        target = check_target_from_events(game_api, event_api, source_id)

        # Check the target
        if target is not None:
            source = game_api.get_player_object_for_player_id(source_id)
            if source:
                role_player_ids = [p.id for p in game_api.get_players_with_role('barman')]
                if source.status == 'alive' and game_api.game.status.name == 'in_progress' and source.id in role_player_ids:
                    target_roles = [r.name for r in game_api.get_all_players_roles(target)]

                    if 'mafioso' in target_roles:
                        possible_targets = [p.id for p in game_api.get_players_with_role('citizen')]
                        new_random_target = random.choice(possible_targets)
                        event_api.create_new_event(game=game_api.game,
                                                   event_name='mafia_kill_vote',
                                                   player_id=target,
                                                   target_id=new_random_target)
                        notif_api = NotificationApi()
                        notif_api.add_new_notification(target, 'barman_get_drunk')


def check_target_from_events(game_api, event_api, source_id):
    events = event_api.get_last_events_for_actual_day(game_api.game, 'barman_getting_drunk', day_no=game_api.game.day_no)
    if events is None:
        target = None
    elif source_id not in events['barman_getting_drunk']:
        target = None
    else:
        # result = {'event_name1': {1: Event(), 2: Event()},
        #           'event_name2': {5: Event(), 18: Event()}
        #           }
        # Get last event
        last_event = events['barman_getting_drunk'][source_id]
        target = last_event.target
    return target


if __name__ == "__main__":
    do(2)
