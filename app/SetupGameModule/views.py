from . import SetupGameModule
from flask import render_template, g, redirect, url_for, request, flash, Markup
from .forms import SetupGameForm, ChooseRolesForm, ChooseStartTimeForm, CreateEventForm, ForumForm, ConfigurationForm, DurationForm
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi, ForumApi, utc_to_local, UserApi, JobApi, NotificationApi
from flask_login import current_user, login_required
from .validators import Validator
import datetime
from app.Engine.AutomatedTasks.scheduler import GameScheduler
from datetime import timedelta
import app.alert_notifications as alert
from app.Engine.AutomatedTasks.Tasks.mafia_kill import check_target_from_events
from .decorators import handle_jobs
from .privileges import judge_privileges
from app.Engine.DB.game_config import GameConfiguration
import json
import os
from zoneinfo import ZoneInfo


def now():
    now_dt = datetime.datetime.now(tz=ZoneInfo(os.environ["TZ"])).replace(tzinfo=None).replace(microsecond=0)
    result = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    return now_dt


@SetupGameModule.route('', methods=['GET', 'POST'])
@SetupGameModule.route('create', methods=['GET', 'POST'])
@login_required
def setup_game():
    form = SetupGameForm()
    if form.validate_on_submit():
        db_api = GameApi()
        game_id = db_api.create_game(form.name.data)
        player_id = db_api.join_user_as_player(g.user.id, g.user.name)
        return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))
    else:
        return render_template('SetupGameModule_index.html', form=form)


@SetupGameModule.route('list', methods=['GET', 'POST'])
@SetupGameModule.route('list/<game_type>', methods=['GET', 'POST'])
@login_required
def game_list(game_type='open_games'):
    db_api = GameApi()
    games = db_api.list_games(game_type)
    return render_template('SetupGameModule_list.html', games=games)


@SetupGameModule.route('<game_id>/game_configuration', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration(game_id):
    try:
        page = int(request.args.get('p'))
    except:
        page = 1
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    if game is None:
        flash('Nieprawidłowy numer gry!', 'alert-danger')
        return redirect(url_for('SetupGameModule.game_list'))
    v = Validator(game, current_user)
    form = SetupGameForm()
    forum_form = ForumForm()

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    if v.game_is_not_started():
        user_ids = []
        for player in game.game_players:
            user_ids.append(player.user_id)

        if game.owner_id == current_user.id:
            user_type = 'admin'
        elif g.user.id in user_ids:
            user_type = 'player'
        else:
            user_type = 'guest'

        # forums
        forum_api = ForumApi(game.id, current_user.id)
        forums = forum_api.get_or_create_topics_for_game()

        # initial forum
        # if request.form['citizen_chat_page'] is None:
        initial_chat_page = int(page)
        initial_chat_page_content = forum_api.get_thread_page(forums['initial_thread'].id, initial_chat_page)

        data = {
            'initial_thread': initial_chat_page_content,
            'your_privileges': your_privileges,
            'you': you
        }

        return render_template('SetupGameModule_game_configuration.html',
                               game=game,
                               user_type=user_type,
                               form=form,
                               data=data,
                               forum_form=forum_form
                               )
    else:
        return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/join', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_join(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    if v.enrollment_is_open() and v.user_not_in_game():
        game = db_api.join_user_as_player(g.user.id, g.user.name)
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/sign-off', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_sign_off(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    if v.enrollment_is_open() and v.user_in_game():
        db_api.sign_off_as_player(g.user.id)
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/throw-user/<user_id>', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_throw_user(game_id, user_id):
    game_id = int(game_id)
    user_id = int(user_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)
    if v.user_is_game_admin() and v.enrollment_is_open() and v.user_in_game(user_id) and v.thrown_user_is_not_game_admin(user_id):
        db_api.sign_off_as_player(user_id)
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/enrollment_open', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_enrollment_open(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    if v.user_is_game_admin() and v.enrollment_can_be_opened() and v.user_in_game():
        db_api.enrollment_open()
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/enrollment_close', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_enrollment_close(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    if v.user_is_game_admin() and v.enrollment_is_open():
        db_api.enrollment_close()
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/set_player_name', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_set_player_name(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)
    form = SetupGameForm()
    if v.user_in_game() and v.game_is_not_started():
        if form.validate_on_submit():
            db_api.set_player_name(current_user.id, form.name.data)
            alert.player_name_set(form.name.data)
        else:
            alert.player_name_not_set()

    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/remove', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_remove(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game_scheduler = GameScheduler()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    if v.user_is_game_admin() and v.game_is_not_started():
        db_api.cancel_game()
        game_scheduler.remove_jobs_for_game(game)
        return redirect(url_for('SetupGameModule.game_list'))
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/choose_roles', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_choose_roles(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    roles_api = RolesApi()
    game_config = GameConfiguration(game)

    v = Validator(game, current_user)
    form = ChooseRolesForm()
    players_count = len(game.game_players)
    game_admin_activated = db_api.get_configuration_value_boolean('game_admin')
    if game_admin_activated:
        players_count -= 1
    form = form.set_form_parameters(entries=players_count, choices=[role.visible_name for role in roles_api.roles])
    if v.user_is_game_admin() and v.enrollment_is_closed():
        if not form.is_submitted():
            return render_template('SetupGameModule_choose_roles.html',
                                   game=game,
                                   form=form,
                                   game_admin_activated=game_admin_activated,
                                   roles=[role.name for role in roles_api.roles])
        else:
            # placeholder for form handler
            roles = [role.name for role in roles_api.roles]
            role_ids = []
            # choosen roles to DB
            for entry in form.roles.entries:
                role_index = [role.visible_name for role in roles_api.roles].index(entry.data['role'])
                role_ids.append(roles_api.roles[role_index].id)
                db_api.remove_roles_from_game()
                db_api.set_roles_to_game(role_ids)

            # role visibility to DB configuration
            roles_not_visible = []
            for role_id, entry in enumerate(form.role_visibility_after_death.entries):
                if not entry.data['role_visible_after_death']:
                    roles_not_visible.append(role_id+1) #  +1 due to DB iteration from 1
            roles_not_visible = json.dumps(roles_not_visible)
            db_api.update_game_configuration({'roles_not_visible_after_death': roles_not_visible})

            # role configurations
            if [r.id for r in roles_api.roles if r.name == 'sniper'][0] in role_ids:  # if sniper is chosen
                db_api.update_game_configuration({'sniper_shots': str(form.sniper_shots.data)})

            if game_admin_activated:
                admin_player_id = db_api.get_player_id_for_user_id(current_user.id)
                db_api.assign_game_admin(admin_player_id)

    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/game_configuration/plan_starting_game', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_plan_starting_game(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    game_scheduler = GameScheduler()
    v = Validator(game, current_user)
    form = ChooseStartTimeForm()

    if v.user_is_game_admin() and v.enrollment_is_closed() and v.roles_no_equals_players_no():
        if not form.is_submitted():
            return render_template('SetupGameModule_plan_starting.html', form=form)
        else:
            start_datetime = datetime.datetime.combine(form.date_posted.data,
                                                       form.time_posted.data)
            db_api.set_phases(form.phases.data)
            db_api.set_start_time(start_datetime)
            game = db_api.set_game_type()
            game_scheduler.create_game_start(game)

    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


def _boolean_to_string(var: bool):
    if var:
        return '1'
    else:
        return '0'


@SetupGameModule.route('<game_id>/game_configuration/configuration', methods=['GET', 'POST'])
@login_required
@handle_jobs
def game_configuration_configuration(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    form = ConfigurationForm()
    v = Validator(game, current_user)

    if v.user_is_game_admin():
        if form.validate_on_submit():
            game_admin = _boolean_to_string(form.game_admin.data)
            detailed_lynch_results = _boolean_to_string(form.detailed_lynch_results.data)
            lynch_voting_history = _boolean_to_string(form.lynch_voting_history.data)
            see_enrolled_user_list = _boolean_to_string(form.see_enrolled_user_list.data)
            citizen_forum_turned_on = _boolean_to_string(form.citizen_forum_turned_on.data)
            initial_forum_turned_on = _boolean_to_string(form.initial_forum_turned_on.data)
            creations_on = _boolean_to_string(form.creations_on.data)
            configuration = {
                'game_admin': game_admin,
                'detailed_lynch_results': detailed_lynch_results,
                'lynch_voting_history': lynch_voting_history,
                'see_enrolled_user_list': see_enrolled_user_list,
                'citizen_forum_turned_on': citizen_forum_turned_on,
                'initial_forum_turned_on': initial_forum_turned_on,
                'creations_on': creations_on
            }
            db_api.update_game_configuration(configuration)
            flash('Konfiguracja zapisana!', 'alert-success')
        else:
            form.game_admin.data = db_api.get_configuration_value_boolean('game_admin')
            form.detailed_lynch_results.data = db_api.get_configuration_value_boolean('detailed_lynch_results')
            form.lynch_voting_history.data = db_api.get_configuration_value_boolean('lynch_voting_history')
            form.see_enrolled_user_list.data = db_api.get_configuration_value_boolean('see_enrolled_user_list')
            form.citizen_forum_turned_on.data = db_api.get_configuration_value_boolean('citizen_forum_turned_on')
            form.initial_forum_turned_on.data = db_api.get_configuration_value_boolean('initial_forum_turned_on')
            form.creations_on.data = db_api.get_configuration_value_boolean('creations_on')
        return render_template('SetupGameModule_config.html',
                               game=game,
                               form=form
                               )
    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))



@SetupGameModule.route('<game_id>/add_forum_reply/<topic_name>', methods=['GET', 'POST'])
@SetupGameModule.route('<game_id>/add_forum_reply', methods=['GET', 'POST'])
@login_required
@handle_jobs
def add_forum_reply(game_id, topic_name='citizen_thread'):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)

    v = Validator(game, current_user)
    form = ForumForm()

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    forum_privileges = {
        'read': {
            'citizen_thread': your_privileges['citizen_forum_read'].granted,
            'mafioso_thread': your_privileges['mafioso_forum_read'].granted,
            'graveyard_thread': your_privileges['graveyard_forum_read'].granted,
            'initial_thread': your_privileges['initial_thread_forum_read'].granted
        },
        'write': {
            'citizen_thread': your_privileges['citizen_forum_write'].granted,
            'mafioso_thread': your_privileges['mafioso_forum_write'].granted,
            'graveyard_thread': your_privileges['graveyard_forum_write'].granted,
            'initial_thread': your_privileges['initial_thread_forum_write'].granted
        }
    }

    if form.is_submitted():
        post_content = form.content.data
        post_content = (post_content[:998] + '..') if len(post_content) > 998 else post_content
        topic_name = form.topic_name.raw_data[1]

        if forum_privileges['write'][topic_name]:

            # you db object
            you = [player for player in game.game_players if player.user_id == current_user.id][0]

            forum_api = ForumApi(game.id, current_user.id)
            forums = forum_api.get_or_create_topics_for_game()

            # check if it is not too early
            last_reply = forum_api.read_last_reply(forums[topic_name].id, you.id)
            if last_reply is None:
                last_reply_date = datetime.datetime(1970, 1, 1)
            else:
                last_reply_date = last_reply.date
            if now() - last_reply_date < timedelta(seconds=60): # TODO: remove hardcoded confituration
                flash('Nie możesz tak szybko pisać kolejnych postów (blokada trwa 60 sekund). Spróbuj ponownie za chwilę.', 'alert-danger')
            else:
                forum_api.create_reply(forums[topic_name].id, post_content, you.id)
        else:
            return redirect(url_for('SetupGameModule.lobby', game_id=game_id))
    if topic_name == 'initial_thread':
        return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))
    else:
        return redirect(url_for('SetupGameModule.forum', game_id=game_id, forum_name=topic_name))


@SetupGameModule.route('<game_id>/lobby', methods=['GET', 'POST'])
@login_required
@handle_jobs
def lobby(game_id):
    game_id = int(game_id)
    lynch_vote_day = request.args.get('lynch_vote_day', default=None)
    game_scheduler = GameScheduler()
    game_scheduler.check_jobs_and_run(game_id)

    forum_form = ForumForm()
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)
    event_api = GameEventApi()

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)

    # roles visibility after death
    try:
        roles_not_visible_after_death = json.loads(db_api.get_configuration('roles_not_visible_after_death'))
    except json.decoder.JSONDecodeError:
        roles_not_visible_after_death = []  # configuration does not exists yet

    your_privileges = judge_privileges(you, game)

    if v.user_in_game() and v.game_is_started():
        # day and night duration
        day_duration = game.phases[0].phase_duration
        night_duration = game.phases[1].phase_duration

        # alive players list
        alive_players = db_api.get_alive_players()
        alive_players_names = [player.name for player in alive_players]
        form = CreateEventForm()
        form.target.choices = alive_players_names
        time_form = DurationForm()

        # dead players list
        dead_players = db_api.get_dead_players()

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
        for citizen_vote in citizen_votes: # change UTC timestamp to local time
            citizen_vote.timestamp = utc_to_local(citizen_vote.timestamp)

        last_citizen_votes = event_api.get_last_events_for_actual_day(game, 'citizen_vote', day_no=lynch_vote_day)
        try:
            your_citizen_vote = last_citizen_votes['citizen_vote'][you.id]
            your_citizen_vote = [player for player in game.game_players if player.id == your_citizen_vote.target][0]
        except KeyError:
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
            vote_results_len = {k: v for k, v in sorted(vote_results_len.items(), key=lambda item: item[1], reverse=True)}
            vote_results_id = {k: vote_results_id[k] for k in vote_results_len}

            for vote in vote_results_id:
                target_name = [player for player in game.game_players if player.id == vote][0]
                target_value = vote_results_id[vote]
                vote_results[target_name] = target_value

        # get all events for history
        history_events = list(event_api.get_all_events_for_whole_game(game, 'lynch'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'mafia_kill'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'gun_shot_kill'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'citizens_win'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'mafiosos_win'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_kill'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_block_lynch'))
        history_events += list(event_api.get_all_events_for_whole_game(game, 'admin_block_mafia_kill'))
        history_events.sort(key=lambda x: (x.day_no, x.phase_no))
        # for ev in history_events:
        #      ev.timestamp = utc_to_local(ev.timestamp)

        # any winner?
        winners = event_api.check_if_someone_wins(game)

        # current time
        current_time = datetime.datetime.now(tz=ZoneInfo(os.environ["TZ"])).replace(tzinfo=None).replace(microsecond=0)

        all_your_events = event_api.get_last_your_events_for_actual_day(game, you.id)

        #notifications
        _display_your_notifications(you)

        # roles
        roles_data = None
        if 'detective' in [r.name for r in db_api.get_user_roles(you.user_id)]: # role:detective
            notification_api = NotificationApi()
            your_notifications = notification_api.read_player_notifications(you.id, unread_only = False, specific='detective_check')
            roles_data = _parse_notifications(your_notifications)

        # judgements
        current_judgements = db_api.get_judgements_for_actual_day(you.id, game.lynch_day())
        print(db_api.game.lynch_day())

        # time offset (game speed up)
        cfg_time_offset = [int(c) for c in db_api.get_configuration('time_offset').split(";")]

        data = {
            'day_end': game.start_time + timedelta(seconds=game.day_no * (day_duration + night_duration) - night_duration,
                                                   hours=cfg_time_offset[0],
                                                   minutes=cfg_time_offset[1]),
            'night_end': game.start_time + timedelta(seconds=game.day_no * (day_duration + night_duration),
                                                     hours=cfg_time_offset[0],
                                                     minutes=cfg_time_offset[1]),
            'you': you,
            'role_ready_to_use': True,
            'alive_players': alive_players,
            'dead_players': dead_players,
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


def _parse_notifications(notifications):
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

def _display_your_notifications(you):
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


@SetupGameModule.route('<game_id>/create_event/<event_name>', methods=['GET', 'POST'])
@login_required
@handle_jobs
def create_event(game_id, event_name):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    #if v.user_in_game() and v.user_can_do_event(event_name) and v.game_in_progress() and v.user_is_alive():
    if your_privileges[event_name].granted:
        alive_players = db_api.get_alive_players()
        alive_players_names = [player.name for player in alive_players]
        form = CreateEventForm()
        form.target.choices = alive_players_names
        if form.validate_on_submit():
            game_event_api = GameEventApi()
            form_target = form.target.data

            event_validated = validate_event(event_name, form_target, game, you, game_event_api)

            if event_validated:
                game_event_api.create_new_event(game,
                                                event_name,
                                                you.id,
                                                db_api.get_player_id_for_name(form_target))

                create_job_for_event(event_name, game, you)

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


def create_job_for_event(event_name, game, you):
    # events sometimes needs to create a job
    # events that triggers at mafia kill time
    if event_name in ['detective_check', 'gun_shot']:
        job_api = JobApi()
        # check if the job for your player already exists. If no, create new one.
        try:
            dummy = job_api.get_time_of_active_job(game.id, event_name, you.id)
        except:
            trigger_time = job_api.get_time_of_active_job(game.id, 'mafia_kill')
            job_api.add_job(event_name, game, trigger_time, you.id)


def validate_event(event_name, form_target, game, you, game_event_api):
    """ some events have additional conditions
    """
    event_validated = True
    if event_name == 'priest_prayer':  # role:priest check if the last time target wasnt the same
        last_event = game_event_api.get_last_events_for_actual_day(game, 'priest_prayer', game.day_no - 1)
        if last_event:
            if last_event['priest_prayer'][you.id].target_player.name == form_target:
                event_validated = False
                flash('Nie możesz dwa razy z rzędu modlić się za tę samą osobę!', 'alert-danger')
    return event_validated


# @SetupGameModule.route('<game_id>/forum/<forum_name>/<page>', methods=['GET', 'POST'])
@SetupGameModule.route('<game_id>/forum/<forum_name>', methods=['GET', 'POST'])
# @SetupGameModule.route('<game_id>/forum', methods=['GET', 'POST'])
@login_required
@handle_jobs
def forum(game_id, forum_name='citizen_thread'):
    game_id = int(game_id)
    page = int(request.args.get('page', default='1'))
    forum_form = ForumForm()
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    forum_privileges = {
        'read': {
            'citizen_thread': your_privileges['citizen_forum_read'].granted,
            'mafioso_thread': your_privileges['mafioso_forum_read'].granted,
            'graveyard_thread': your_privileges['graveyard_forum_read'].granted,
            'initial_thread': your_privileges['initial_thread_forum_read'].granted
        },
        'write': {
            'citizen_thread': your_privileges['citizen_forum_write'].granted,
            'mafioso_thread': your_privileges['mafioso_forum_write'].granted,
            'graveyard_thread': your_privileges['graveyard_forum_write'].granted,
            'initial_thread': your_privileges['initial_thread_forum_write'].granted
        }
    }

    if forum_privileges['read'][forum_name]:

        # forums
        forum_api = ForumApi(game.id, current_user.id)
        forums = forum_api.get_or_create_topics_for_game()

        # forum
        if forum_name == 'citizen_thread':
            page_content = forum_api.get_thread_page(forums['citizen_thread'].id, page)
            thread_description = 'Oto główny wątek dyskusyjny miasta.'
        elif forum_name == 'mafioso_thread':
            page_content = forum_api.get_thread_page(forums['mafioso_thread'].id, page)
            thread_description = 'Witamy w mafijnym zakątku...'
        elif forum_name == 'graveyard_thread':
            page_content = forum_api.get_thread_page(forums['graveyard_thread'].id, page)
            thread_description = 'Cmentarne forum - miejsce życia po śmierci.'
        else:
            return redirect(url_for('SetupGameModule.lobby', game_id=game_id))
        data = {
            'thread_content': page_content,
            'thread_description': thread_description,
            'forum_name': forum_name,
            'privileges': forum_privileges
        }
        return render_template('SetupGameModule_forum.html',
                               game=game,
                               data=data,
                               forum_form=forum_form)
    else:
        return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


@SetupGameModule.route('<game_id>/kill_player/<player_id>', methods=['GET', 'POST'])
@login_required
def kill_player(game_id, player_id):
    game_id = int(game_id)
    db_api = GameApi()
    event_api = GameEventApi()

    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    # if v.user_is_game_admin() and v.game_is_started():
    if your_privileges['kill_a_player_at_any_time'].granted:
        db_api.kill_player(int(player_id))
        event_api.create_new_event(game, 'admin_kill', you.id, int(player_id))
        flash('Pomyślnie zabito gracza.', 'alert-success')

        # Winning conditions
        finished = db_api.check_winning_condition()

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


@SetupGameModule.route('<game_id>/block_event/<event_type>', methods=['GET', 'POST'])
@login_required
def block_lynch(game_id, event_type):
    game_id = int(game_id)
    db_api = GameApi()
    event_api = GameEventApi()

    game = db_api.get_game(game_id)
    v = Validator(game, current_user)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    if event_type == 'lynch' and your_privileges['block_lynch'].granted:
        event_api.create_new_event(game, 'admin_block_lynch', you.id, None)
        flash('Pomyślnie zablokowano dzisiejszy lincz.', 'alert-success')
    elif event_type == 'mafia_kill' and your_privileges['block_mafia_kill'].granted:
        event_api.create_new_event(game, 'admin_block_mafia_kill', you.id, None)
        flash('Pomyślnie zablokowano dzisiejszy mord.', 'alert-success')

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


@SetupGameModule.route('<game_id>/add_game_guest', methods=['GET', 'POST'])
@login_required
def add_game_guest(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    user_name = request.args.get('user_name', default=None)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    if your_privileges['adding_game_guest'].granted and user_name is not None:
        user_api = UserApi()
        user_added = user_api.get_user_for_username(user_name)
        if user_added is None:
            flash('Użytkownik o podanym loginie nie istnieje!', 'alert-danger')
        else:
            user_id = user_added.id
            player_id = db_api.get_player_id_for_user_id(user_id)
            if player_id is None:
                added_player_id = db_api.join_user_as_player(user_id, user_name, 'special')
                db_api.assign_game_guest(added_player_id)
                flash('Pomyślnie dodano gościa ' + user_name, 'alert-success')
            else:
                flash('Użytkownik jest już w grze!', 'alert-danger')

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))

@SetupGameModule.route('<game_id>/revert_game', methods=['GET', 'POST'])
@login_required
def revert_game(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    user_name = request.args.get('user_name', default=None)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    if your_privileges['reverting_game'].granted:
        db_api.revert_game()

    return redirect(url_for('SetupGameModule.game_configuration', game_id=game_id))


@SetupGameModule.route('<game_id>/judge', methods=['GET', 'POST'])
@login_required
def judge(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    if your_privileges['judge_players'].granted:
        # format -> judgements =  {target_id: judgement}
        your_judgements = {}
        alive_players = db_api.get_alive_players()
        for p in alive_players:
            your_judgements[p.id] = request.args.get(str(p.id), default=5)
        db_api.set_player_judgement(you.id, game.lynch_day(), your_judgements)
        flash('Ocena zapisana!', 'alert-success')

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


@SetupGameModule.route('<game_id>/speed_up_game', methods=['GET', 'POST'])
@login_required
@handle_jobs
def speed_up_game(game_id):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    roles_api = RolesApi()
    game_config = GameConfiguration(game)

    # privileges
    you = db_api.get_player_object_for_user_id(current_user.id)
    your_privileges = judge_privileges(you, game)

    form = DurationForm()
    hour = int(form.duration_hours.data)
    minute = int(form.duration_minutes.data)

    if your_privileges['speeding_up_game'].granted:

        cfg_time_offset = [int(c) for c in db_api.get_configuration('time_offset').split(";")]

        new_time_offset = []
        new_time_offset.append(cfg_time_offset[0] + hour)
        new_time_offset.append(cfg_time_offset[1] + minute)

        new_cfg_time_offset = str(new_time_offset[0]) + ";" + str(new_time_offset[1])
        db_api.update_game_configuration({'time_offset': new_cfg_time_offset})

        job_api = JobApi()
        job_api.update_unhandled_jobs_time(datetime.timedelta(hours=hour, minutes=minute))

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))
