
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
                    target_events = event_api.get_last_your_events_for_actual_day(game_api.game, target, game_api.game.day_no)

                    if 'mafioso' in target_roles:
                        mafia_events = event_api.get_last_events_for_actual_day(game_api.game, 'mafia_kill_vote', game_api.game.day_no)
                        if 'mafia_kill_vote' in mafia_events.keys():
                            if target_events['mafia_kill_vote'].target != None:
                                possible_targets = [p.id for p in game_api.get_players_with_role('citizen')]
                                try:  # remove previous target from possible options
                                    possible_targets.remove(mafia_events['mafia_kill_vote'].target_player.id)
                                except:
                                    pass

                                new_random_target = random.choice(possible_targets)
                                event_api.create_new_event(game=game_api.game,
                                                           event_name='mafia_kill_vote',
                                                           player_id=target,
                                                           target_id=new_random_target)
                    if game_api.get_configuration('barman_town_roles_drunk') == 'True':
                        get_role_drunk('detective_check', event_api, game_api, target, target_events)
                        get_role_drunk('priest_prayer', event_api, game_api, target, target_events)
                        get_role_drunk('gun_shot', event_api, game_api, target, target_events, not_me=True)
                        get_role_drunk('spy_check', event_api, game_api, target, target_events)
                        get_role_drunk('barman_getting_drunk', event_api, game_api, target, target_events)


def get_role_drunk(event_type_name, event_api, game_api, target, target_events, not_me=False):
    import random
    # Check if role event exists and if so, create new one with random target
    if event_type_name in target_events.keys():
        if target_events[event_type_name].target != None:
            possible_targets = [p.id for p in game_api.get_game_players_for_game() if p.status == 'alive']
            try:  # remove previous target from possible options
                possible_targets.remove(target_events[event_type_name].target_player.id)
            except:
                pass
            if not_me:  # not-me means role cannot choose themself as a new target
                try:
                    possible_targets.remove(target_events[event_type_name].source_player.id)
                except:
                    pass
            new_random_target = random.choice(possible_targets)
            event_api.create_new_event(game=game_api.game,
                                       event_name=event_type_name,
                                       player_id=target,
                                       target_id=new_random_target)


def check_target_from_events(game_api, event_api, source_id):
    events = event_api.get_last_events_for_actual_day(game_api.game, 'barman_getting_drunk', day_no=game_api.game.day_no)
    if events is None or events == {}:
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
