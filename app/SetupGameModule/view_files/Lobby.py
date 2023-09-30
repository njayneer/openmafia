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


class Lobby():

    def view(self, game_id):
        game_id = int(game_id)
        lynch_vote_day = request.args.get('lynch_vote_day', default=None)
        game_scheduler = GameScheduler()
        game_scheduler.check_jobs_and_run(game_id)

        forum_form = ForumForm()
        db_api = GameApi()
        game = db_api.get_game(game_id)
        event_api = GameEventApi()

        # privileges
        you = db_api.get_player_object_for_user_id(current_user.id)

        # roles visibility after death
        try:
            roles_not_visible_after_death = json.loads(db_api.get_configuration('roles_not_visible_after_death'))
        except json.decoder.JSONDecodeError:
            roles_not_visible_after_death = []  # configuration does not exists yet

        your_privileges = judge_privileges(you, game)

        #if v.user_in_game() and v.game_is_started():
        if your_privileges['show_lobby'].granted:
            # day and night duration
            day_duration = game.phases[0].phase_duration
            night_duration = game.phases[1].phase_duration

            # alive players list
            alive_players = db_api.get_alive_players()
            alive_players_names = [player.name for player in alive_players]
            form = CreateEventForm()
            form.target.choices = ['-'] + alive_players_names
            time_form = DurationForm()

            # dead players list
            dead_players = db_api.get_dead_players()

            # dead players list
            special_players = db_api.get_special_players()

            # mafiosos
            mafiosos = db_api.get_players_with_role('mafioso')

            # actual your mafioso vote if you are in mafia
            if your_privileges['mafia_tab_visible'].granted:
                mafia_actual_target = check_target_from_events(db_api, event_api=event_api)
                if mafia_actual_target is not None:
                    mafia_actual_target = [player for player in game.game_players if player.id == mafia_actual_target][0]
            else:
                mafia_actual_target = None

            # citizen votes, your actual vote and actual results
            citizen_votes = event_api.get_all_events_for_actual_day(game, 'citizen_vote', day_no=lynch_vote_day)
            citizen_votes = sorted(citizen_votes, key=lambda d: d.timestamp)
            for citizen_vote in citizen_votes:  # change UTC timestamp to local time
                citizen_vote.timestamp = utc_to_local(citizen_vote.timestamp)

            last_citizen_votes = event_api.get_last_events_for_actual_day(game, 'citizen_vote', day_no=lynch_vote_day)
            try:
                your_citizen_vote = last_citizen_votes['citizen_vote'][you.id]
                your_citizen_vote = [player for player in game.game_players if player.id == your_citizen_vote.target][0]
            except (KeyError, IndexError):
                your_citizen_vote = None

            # Count votes
            vote_results_id = {}
            vote_results = {}
            if len(last_citizen_votes) > 0:
                for vote in last_citizen_votes['citizen_vote']:
                    target_id = last_citizen_votes['citizen_vote'][vote].target
                    source_id = last_citizen_votes['citizen_vote'][vote].player_id
                    source_name = db_api.get_player_name_for_id(source_id)
                    if target_id not in vote_results_id.keys():
                        vote_results_id[target_id] = [source_name]
                    else:
                        vote_results_id[target_id].append(source_name)
                vote_results_len = {k: len(vote_results_id[k]) for k in vote_results_id}
                vote_results_len = {k: v for k, v in
                                    sorted(vote_results_len.items(), key=lambda item: item[1], reverse=True)}
                vote_results_id = {k: vote_results_id[k] for k in vote_results_len}

                for vote in vote_results_id:
                    if vote:
                        target_name = [player for player in game.game_players if player.id == vote][0]
                        target_value = vote_results_id[vote]
                        target_value.sort()
                        vote_results[target_name] = target_value

            # get all events for history
            history_events = list(event_api.get_all_events_for_whole_game(game, 'lynch'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'mafia_kill'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'gun_shot_kill'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'citizens_win'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'mafiosos_win'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_kill'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_revive'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_block_lynch'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_block_mafia_kill'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'mvp_chosen'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'mvp2_chosen'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'mvp3_chosen'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'lynch_draw_noone'))
            history_events += list(event_api.get_all_events_for_whole_game(game, 'lynch_draw_mafia_choice'))
            history_events.sort(key=lambda x: (x.day_no, x.phase_no))
            # for ev in history_events:
            #      ev.timestamp = utc_to_local(ev.timestamp)

            # any winner?
            winners = event_api.check_if_someone_wins(game)

            # current time
            current_time = datetime.datetime.now(tz=ZoneInfo(os.environ["TZ"])).replace(tzinfo=None).replace(microsecond=0)

            try:
                all_your_events = event_api.get_last_your_events_for_actual_day(game, you.id)
            except AttributeError:
                all_your_events = {}


            # notifications
            self._display_your_notifications(you)

            # roles
            roles_data = None
            if 'detective' in [r.name for r in db_api.get_user_roles(you.user_id)]:  # role:detective
                notification_api = NotificationApi()
                your_notifications = notification_api.read_player_notifications(you.id, unread_only=False,
                                                                                specific='detective_check')
                roles_data = self._parse_notifications(your_notifications)

            if 'spy' in [r.name for r in db_api.get_user_roles(you.user_id)]:  # role:spy
                notification_api = NotificationApi()
                your_notifications = notification_api.read_player_notifications(you.id, unread_only=False,
                                                                                specific='spy_check')
                roles_data = self._parse_notifications(your_notifications)

            # judgements
            current_judgements = db_api.get_judgements_for_actual_day(you.id, game.lynch_day())
            print(db_api.game.lynch_day())

            # time offset (game speed up)
            cfg_time_offset = [int(c) for c in db_api.get_configuration('time_offset').split(";")]

            data = {
                'day_end': game.start_time + timedelta(
                    seconds=game.day_no * (day_duration + night_duration) - night_duration,
                    hours=cfg_time_offset[0],
                    minutes=cfg_time_offset[1]),
                'night_end': game.start_time + timedelta(seconds=game.day_no * (day_duration + night_duration),
                                                         hours=cfg_time_offset[0],
                                                         minutes=cfg_time_offset[1]),
                'you': you,
                'role_ready_to_use': True,
                'alive_players': alive_players,
                'dead_players': dead_players,
                'special_players': special_players,
                'mafia_actual_target': mafia_actual_target,
                'your_actual_citizen_vote': your_citizen_vote,
                'citizen_votes': citizen_votes,
                'winners': winners,
                'now': current_time,
                'your_privileges': your_privileges,
                'mafiosos': mafiosos,
                'vote_results': vote_results,
                'history_events': history_events,
                'lynch_vote_day': lynch_vote_day,
                'your_events': all_your_events,
                'roles_data': roles_data,
                'current_judgements': current_judgements,
                'roles_not_visible_after_death': roles_not_visible_after_death
            }
            return render_template('SetupGameModule_lobby.html',
                                   game=game,
                                   data=data,
                                   form=form,
                                   forum_form=forum_form,
                                   time_form=time_form)
        else:
            return redirect(url_for('SetupGameModule.game_list'))


    def _parse_notifications(self, notifications):
        result = None
        if notifications:
            result = []
            for n in notifications:
                parameters = n.parameters.split(';;')
                notification = n.template.content
                for p in parameters:
                    notification = Markup(notification.replace("%s", p, 1))
                result.append(notification)
        return result

    def _display_your_notifications(self, you):
        notification_api = NotificationApi()
        your_notifications = notification_api.read_player_notifications(you.id)
        if your_notifications:
            for n in your_notifications:
                parameters = n.parameters.split(';;')
                notification = n.template.content
                for p in parameters:
                    notification = Markup(notification.replace("%s", p, 1))
                flash(notification, 'alert-notification')
                notification_api.set_notification_read(n)