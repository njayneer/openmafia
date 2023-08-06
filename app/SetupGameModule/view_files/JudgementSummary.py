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
            all_player_count = mafioso_count + citizen_count  # not everyone due to GM and observers

            # due to dividing by 0 danger. If such a situation happens, result is not important, so we can simply change to 1
            if mafioso_count == 0:
                mafioso_count = 1
            if citizen_count == 0:
                citizen_count = 1

            # multiplied by 5 due to "1" for full mafia, "1" for full city, we want range -10 to 10, not -2 to 2
            mafioso_points = [a / m * 5 for a, m in zip(all_player_count, mafioso_count)]
            citizen_points = [a / c * (-5) for a, c in zip(all_player_count, citizen_count)]

            judgement_lookup_table = {10: 1, 5: 0, 1: -1} # mafioso, neutral, citizen
            color_lookup_table = {10: 'czerwony', 5: 'żółty', 1: 'zielony'}
            faction_lookup_table = {'mafioso': mafioso_points, 'unspecified': 0.0, 'citizen': citizen_points}

            #calculate points
            # format-> judgements = {day_id: {player_no: {target_id: judgement_db_object}}}
            # format-> judgement_results = {day_no: {'player_id': x, 'player_name': y, 'points': z, 'fraction': t}}
            judgement_results = {}
            for i, (day, player_votes) in enumerate(all_judgements.items()):
                # rewrite points if there is no vote that day
                self.initialize_judgement_result_for_day(day, game, judgement_results, player_fractions)

                # we are counting for one specific day now. Calculate sum of points value for all players in loop
                for player, votes in player_votes.items():
                    for target, vote in votes.items():
                        points_from_vote = judgement_lookup_table[vote.judgement]
                        wage_from_fraction = faction_lookup_table[player_fractions[vote.target_id]][i]
                        step_points = points_from_vote * wage_from_fraction
                        if step_points == -0.0:
                            step_points = 0.0

                        # points for citizen
                        judgement_results[day][player]['points'] += step_points
                        info_string = player_names[target]\
                                      + ': '\
                                      + str(round(step_points, 1))\
                                      + 'p ('\
                                      + color_lookup_table[vote.judgement]\
                                      + ') <br />'
                        if judgement_results[day][player]['info'] in ('Brak oceny', 'Brak nowej oceny'):
                            judgement_results[day][player]['info'] = info_string
                        else:
                            judgement_results[day][player]['info'] += info_string

                        # points for mafioso
                        if player_fractions[vote.target_id] == 'mafioso':
                            # if accurate vote, subtract mafioso points, if not accurate, add citizen points
                            if color_lookup_table[vote.judgement] == 'czerwony':
                                mafioso_step_points = - mafioso_points[i]
                            elif color_lookup_table[vote.judgement] == 'zielony':
                                mafioso_step_points = - citizen_points[i]
                            else:
                                mafioso_step_points = 0

                            judgement_results[day][vote.target_id]['points'] += mafioso_step_points
                            info_string = player_names[player] \
                                          + ': ' \
                                          + str(round(mafioso_step_points, 1)) \
                                          + 'p ( ' \
                                          + color_lookup_table[vote.judgement] \
                                          + ') <br />'
                            if judgement_results[day][vote.target_id]['info'] in ('Brak oceny', 'Brak nowej oceny'):
                                judgement_results[day][vote.target_id]['info'] = info_string
                            else:
                                judgement_results[day][vote.target_id]['info'] += info_string

                    # round value after each vote result addition
                    judgement_results[day][player]['points'] = round(judgement_results[day][player]['points'], 1)
                    if judgement_results[day][player]['points'] == -0.0:
                        judgement_results[day][player]['points'] = 0.0

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
                                   data=data)
        else:
            return redirect(url_for('SetupGameModule.lobby', game_id=game_id))

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
