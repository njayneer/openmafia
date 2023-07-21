
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
        if (not admin_blocks) and game_api.game.status.name == 'in_progress':
            if events == {}:
                winner = random.choice([player.id for player in game_api.game.game_players if player.status == 'alive'])
            else:
                # Count votes
                vote_results = {}
                for event in events['citizen_vote']:
                    if events['citizen_vote'][event].target not in vote_results.keys():
                        vote_results[events['citizen_vote'][event].target] = 0
                    vote_results[events['citizen_vote'][event].target] += 1

                max_vote_value = max(vote_results.values())
                winners = [candidate for candidate in vote_results if vote_results[candidate] == max_vote_value]
                if len(winners) > 1:
                    winner = random.choice(winners)
                else:
                    winner = winners[0]

            # Kill winner
            event_api.create_new_event(game=game_api.game,
                                       event_name='lynch',
                                       player_id=None,
                                       target_id=winner)
            game_api.kill_player(winner)

        # Winning conditions
        finished = game_api.check_winning_condition()
        if not finished:
            game_api.process_to_next_phase()



if __name__ == "__main__":
    do(1)
