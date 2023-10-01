
def do(game_id, source_id):
    from app.Engine.DB.db_api import GameApi, GameEventApi
    from app import app
    from app.Engine.AutomatedTasks.scheduler import GameScheduler
    import random
    with app.app_context():
        game_api = GameApi()
        game_api.get_game(game_id)
        event_api = GameEventApi()
        events = event_api.get_last_events_for_actual_day(game_api.game, 'citizen_vote')
        # game_admin can create event to block lynch. If so, kill noone and proces to next phase
        admin_blocks = len(event_api.get_last_events_for_actual_day(game_api.game, 'admin_block_lynch')) > 0
        if admin_blocks:
            # remove vote events
            citien_vote_type_id = event_api.get_eventtype_id_from_name('citizen_vote')
            event_api.remove_event_for_type_and_day(citien_vote_type_id, game_api.game.day_no)
        elif (not admin_blocks) and game_api.game.status.name == 'in_progress':
            if events == {}:
                winners = [player.id for player in game_api.game.game_players if player.status == 'alive']
            else:
                # Count votes
                vote_results = {}
                for event in events['citizen_vote']:
                    if events['citizen_vote'][event].target:
                        if events['citizen_vote'][event].target not in vote_results.keys():
                            vote_results[events['citizen_vote'][event].target] = 0
                        vote_results[events['citizen_vote'][event].target] += 1
                if vote_results == {}:
                    winners = [player.id for player in game_api.game.game_players if player.status == 'alive']
                else:
                    max_vote_value = max(vote_results.values())
                    winners = [candidate for candidate in vote_results if vote_results[candidate] == max_vote_value]
            if len(winners) > 1:
                lynch_draw_config = game_api.get_configuration('lynch_draw')
                if lynch_draw_config == 'random':
                    winner = random.choice(winners)
                    event_api.create_new_event(game=game_api.game,
                                               event_name='lynch',
                                               player_id=None,
                                               target_id=winner)
                    game_api.kill_player(winner)
                elif lynch_draw_config == 'noone':
                    event_api.create_new_event(game=game_api.game,
                                               event_name='lynch_draw_noone',
                                               player_id=None,
                                               target_id=None)
                elif lynch_draw_config == 'mafia_choice':
                    event_api.create_new_event(game=game_api.game,
                                               event_name='lynch_draw_mafia_choice',
                                               player_id=None,
                                               target_id=None)
                    #TODO new voting system for mafia, not available yet. Use "noone" and manual kill
            else:
                winner = winners[0]
                event_api.create_new_event(game=game_api.game,
                                           event_name='lynch',
                                           player_id=None,
                                           target_id=winner)
                game_api.kill_player(winner)

        game_api.process_to_next_phase()
        
        # Winning conditions
        finished = game_api.check_winning_condition()


if __name__ == "__main__":
    do(1)
