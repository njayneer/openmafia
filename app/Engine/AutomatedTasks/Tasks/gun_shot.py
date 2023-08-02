
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi, NotificationApi, RolesApi
    from app import app

    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()

        target = check_target_from_events(game_api, event_api, source_id)

        # Check the target
        if target is not None:
            source = game_api.get_player_object_for_player_id(source_id)
            event_source = None # Event source empty if no specific condition
            target_object = game_api.get_player_object_for_player_id(target)
            if source:
                gun_used = game_api.select_game_items('gun', source_id, True)
                if len(gun_used) > 0:
                    gun_used = gun_used[0]
                else:
                    gun_used = None

                source_is_killed = check_if_source_is_killed_by_other_gun_shot(event_api, game_api, source_id)

                if (source.status == 'alive' or source_is_killed) and game_api.game.status.name == 'in_progress' and gun_used:
                    # Kill the target
                    game_api.kill_player(target)
                    game_api.decrease_item_usages(gun_used)

                    # specific conditions for roles
                    source_roles = [role.name for role in game_api.get_user_roles(source.user_id)]
                    if 'sniper' in source_roles:  # role: sniper
                        if game_api.get_configuration('sniper_blocked_after_missed_shot') == 'True':
                            target_roles = [role.name for role in game_api.get_user_roles(target_object.user_id)]
                            if 'mafioso' not in target_roles:
                                game_api.destroy_item(gun_used)
                                event_source = source.id

                    event_api.create_new_event(game=game_api.game,
                                               event_name='gun_shot_kill',
                                               player_id=event_source,
                                               target_id=target)

                    game_api.check_winning_condition()


def check_if_source_is_killed_by_other_gun_shot(event_api, game_api, source_id):
    gun_shot_kill_events = event_api.get_all_events_for_actual_day(game_api.game, 'gun_shot_kill')
    source_is_killed = False
    for gske in gun_shot_kill_events:
        if gske.target == source_id:
            source_is_killed = True
    return source_is_killed


def check_target_from_events(game_api, event_api, source_id):
    # day_no - 1 due to be fired after mafia kill
    events = event_api.get_last_events_for_actual_day(game_api.game, 'gun_shot', day_no=game_api.game.day_no)
    if events is None:
        target = None
    elif source_id not in events['gun_shot']:
        target = None
    else:
        # result = {'event_name1': {1: Event(), 2: Event()},
        #           'event_name2': {5: Event(), 18: Event()}
        #           }
        # Get last event
        last_event = events['gun_shot'][source_id]
        target = last_event.target
    return target



if __name__ == "__main__":
    do(2)
