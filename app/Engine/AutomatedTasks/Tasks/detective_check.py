
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi, NotificationApi, RolesApi
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
            source = game_api.get_player_object_for_player_id(source_id)
            if source:
                if source.status == 'alive' and game_api.game.status.name == 'in_progress':
                    roles_api = RolesApi()
                    target_roles = [r.name for r in game_api.get_all_players_roles(target)]
                    # target_roles = [r.role.name for r in target.roles]
                    if ('mafioso' in target_roles or 'suspect' in target_roles) and 'godfather' not in target_roles:
                        # role:suspect show to detective as mafioso
                        # role:godfather show to detective as citizen
                        res_role = roles_api.get_role_visible_name_from_name('mafioso')
                    elif 'citizen' in target_roles or 'godfather' in target_roles:
                        res_role = roles_api.get_role_visible_name_from_name('citizen')
                    else:
                        res_role = 'Frakcja neutralna'
                    notif_api = NotificationApi()
                    notif_api.add_new_notification(source_id, 'detective_check', game_api.get_player_name_for_id(target), res_role)


def check_target_from_events(game_api, event_api, source_id):
    # day_no - 1 due to be fired after mafia kill
    events = event_api.get_last_events_for_actual_day(game_api.game, 'detective_check', day_no=game_api.game.day_no-1)
    if events is None or events == {}:
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
