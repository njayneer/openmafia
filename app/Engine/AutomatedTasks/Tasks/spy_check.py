
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
                    # do not consider mafioso and citizen roles, only others
                    try:
                        target_roles.remove('mafioso')
                    except ValueError:
                        pass
                    try:
                        target_roles.remove('citizen')
                    except ValueError:
                        pass
                    if len(target_roles) == 0:
                        res_role = 'bezrolny'
                    else:
                        res_role = 'rolny (posiada rolę)'

                    notif_api = NotificationApi()
                    notif_api.add_new_notification(source_id, 'spy_check', game_api.get_player_name_for_id(target), res_role)


def check_target_from_events(game_api, event_api, source_id):
    # day_no - 1 due to be fired after mafia kill
    events = event_api.get_last_events_for_actual_day(game_api.game, 'spy_check', day_no=game_api.game.day_no-1)
    if events is None:
        target = None
    elif source_id not in events['spy_check']:
        target = None
    else:
        # result = {'event_name1': {1: Event(), 2: Event()},
        #           'event_name2': {5: Event(), 18: Event()}
        #           }
        # Get last event
        last_event = events['spy_check'][source_id]
        target = last_event.target
    return target


if __name__ == "__main__":
    do(2)
