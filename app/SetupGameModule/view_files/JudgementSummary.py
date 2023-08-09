from flask import render_template, g, redirect, url_for, request, flash, Markup
from ..forms import CreateEventForm, ForumForm, DurationForm
from app.Engine.DB.db_api import GameApi, GameEventApi, utc_to_local, NotificationApi
from flask_login import current_user
from ..validators import Validator
import datetime
from app.Engine.AutomatedTasks.scheduler import GameScheduler
from datetime import timedelta
from app.Engine.AutomatedTasks.Tasks.mafia_kill import check_target_from_events
from ..privileges import judge_privileges
import json
import os
from zoneinfo import ZoneInfo


class JudgementSummary:

    def view(self, game_id):
        db_api = GameApi()
        game = db_api.get_game(game_id)
        you = db_api.get_player_object_for_user_id(current_user.id)
        your_privileges = judge_privileges(you, game)
        if your_privileges['show_judgement_summary'].granted:
            player_id_list = [p.id for p in game.game_players]
            player_fractions = db_api.get_players_fraction()  # result = {player_id: 'mafioso'}
            player_names = {p.id: p.name for p in game.game_players}

            # get all judgements of the game
            # format-> all_judgements = {day_id: {player_no: {target_id: judgement_db_object}}}
            all_judgements = db_api.get_all_judgements(player_id_list)

            # players count for each day (based on players per vote) - type = []
            mafioso_count = self.get_player_count(all_judgements, player_fractions, 'mafioso')
            citizen_count = self.get_player_count(all_judgements, player_fractions, 'citizen')
            all_player_count = [m + c for m, c in zip(mafioso_count, citizen_count)]  # not everyone due to GM and observers

            # due to dividing by 0 danger. If such a situation happens, result is not important, so we can simply change to 1
            if mafioso_count == 0:
                mafioso_count = 1
            if citizen_count == 0:
                citizen_count = 1

            # multiplied by 5 due to "1" for full mafia, "1" for full city, we want range -10 to 10, not -2 to 2
            mafioso_points = [5 / m for m in mafioso_count]
            citizen_points = [-5 / c for c in citizen_count]

            judgement_lookup_table = {10: 1, 5: 0, 1: -1} # mafioso, neutral, citizen
            color_lookup_table = {10: 'czerwony', 5: 'żółty', 1: 'zielony'}
            faction_lookup_table = {'mafioso': mafioso_points, 'unspecified': 0.0, 'citizen': citizen_points}

            #calculate points
            # format-> all_judgements = {day_id: {player_no: {target_id: judgement_db_object}}}
            # format-> judgement_results = {day_no: {'player_id': x, 'player_name': y, 'points': z, 'fraction': t}}
            judgement_results = {}
            for i, (day, player_votes) in enumerate(all_judgements.items()):
                actual_mafioso_points = mafioso_points[i]
                actual_citizen_points = citizen_points[i]

                self.rewrite_judgement_for_day(all_judgements, day, player_fractions, player_votes, player_id_list)

                # rewrite points if there is no vote that day
                self.initialize_judgement_result_for_day(day, game, judgement_results, player_fractions)

                # we are counting for one specific day now. Calculate sum of points value for all players in loop
                for player, votes in player_votes.items():
                    if votes:
                        for target, vote in votes.items():
                            points_from_vote = judgement_lookup_table[vote.judgement]
                            wage_from_fraction = faction_lookup_table[player_fractions[vote.target_id]][i]
                            step_points = points_from_vote * wage_from_fraction
                            if step_points == -0.0:
                                step_points = 0.0

                            # points for citizen
                            info_string = player_names[target]\
                                          + ': '\
                                          + str(round(step_points, 2))\
                                          + 'p ('\
                                          + color_lookup_table[vote.judgement]\
                                          + ') <br />'
                            if judgement_results[day][player]['info'] in ('Brak oceny', 'Brak nowej oceny'):
                                judgement_results[day][player]['info'] = info_string
                                judgement_results[day][player]['points'] = step_points
                            else:
                                judgement_results[day][player]['info'] += info_string
                                judgement_results[day][player]['points'] += step_points

                            # points for mafioso
                            if player_fractions[vote.target_id] == 'mafioso':
                                self.give_points_for_mafioso(actual_citizen_points, actual_mafioso_points,
                                                             color_lookup_table, day, judgement_results,
                                                             player_names, vote)

                        # round value after each vote result addition
                        judgement_results[day][player]['points'] = round(judgement_results[day][player]['points'], 1)
                        if judgement_results[day][player]['points'] == -0.0:
                            judgement_results[day][player]['points'] = 0.0

            for d, pr in judgement_results.items():
                first = next(iter(all_judgements[d]))
                alive_players = [p for p in all_judgements[d][first]]
                for p, p_dict in pr.items():
                    if p in alive_players:
                        p_dict['player_status'] = 'alive'
                    else:
                        p_dict['player_status'] = 'dead'


            judgement_citizen_results = {}
            judgement_mafioso_results = {}
            for d, jr in judgement_results.items():
                judgement_citizen_results[d] = {p: j for p, j in jr.items() if player_fractions[p] == 'citizen'}
                judgement_mafioso_results[d] = {p: j for p, j in jr.items() if player_fractions[p] == 'mafioso'}

            data = {'judgement_results': judgement_results,
                    'judgement_citizen_results': judgement_citizen_results,
                    'judgement_mafioso_results': judgement_mafioso_results,
                    'judgement_full': all_judgements
                    }

            return render_template('SetupGameModule_judgementsummary.html',
                                   data=data,
                                   game_id=game_id)
        else:
            return redirect(url_for('SetupGameModule.lobby', game_id=game_id))

    def rewrite_judgement_for_day(self, all_judgements, day, player_fractions, player_votes, all_players):
        first = next(iter(player_votes))
        players = [p for p in player_votes[first]]  # all alive players of the day
        players_without_votes = [p for p in all_players if p not in player_votes and player_fractions[p] != 'mafioso']
        for p in players_without_votes:
            j = None
            for d in range(day - 1, 0, -1):
                try:
                    j = {t: ju for t, ju in all_judgements[d][p].items() if
                         t in players}  # last judgment of player without vote
                    break
                except:
                    continue
            player_votes[p] = j

    def give_points_for_mafioso(self, actual_citizen_points, actual_mafioso_points, color_lookup_table, day,
                                judgement_results, player_names, vote):
        # if accurate vote, subtract mafioso points, if not accurate, add citizen points
        if color_lookup_table[vote.judgement] == 'czerwony':
            mafioso_step_points = - actual_mafioso_points
        elif color_lookup_table[vote.judgement] == 'zielony':
            mafioso_step_points = - actual_citizen_points
        else:
            mafioso_step_points = 0
        info_string = player_names[vote.player_id] \
                      + ': ' \
                      + str(round(mafioso_step_points, 2)) \
                      + 'p ( ' \
                      + color_lookup_table[vote.judgement] \
                      + ') <br />'
        if judgement_results[day][vote.target_id]['info'] in ('Brak oceny', 'Brak nowej oceny'):
            judgement_results[day][vote.target_id]['info'] = info_string
            judgement_results[day][vote.target_id]['points'] = mafioso_step_points
        else:
            judgement_results[day][vote.target_id]['info'] += info_string
            judgement_results[day][vote.target_id]['points'] += mafioso_step_points

    def initialize_judgement_result_for_day(self, day, game, judgement_results, player_fractions):

        previous_day_judgement = None
        for d in range(day - 1, 0, -1):
            if d in judgement_results:
                previous_day_judgement = judgement_results[d]
                break
        judgement_results[day] = {gp.id: {'player_id': gp.id,
                                          'fraction': player_fractions[gp.id],
                                          'player_name': gp.name,
                                          'points': previous_day_judgement[gp.id]['points'] if previous_day_judgement else 0.0,
                                          'info': 'Brak oceny'} for gp in game.game_players}

    def get_player_count(self, all_judgements, player_fractions, fraction):
        mafioso_count = []
        for day in all_judgements:
            first = next(iter(all_judgements[day]))
            m_c = len([p for p in all_judgements[day][first] if player_fractions[p] == fraction])
            mafioso_count.append(m_c)
        return mafioso_count
