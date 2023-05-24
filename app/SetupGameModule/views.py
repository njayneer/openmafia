from . import SetupGameModule
from flask import render_template, g, redirect, url_for, request, flash
from .forms import SetupGameForm, ChooseRolesForm, ChooseStartTimeForm, CreateEventForm, ForumForm
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi, ForumApi
from flask_login import current_user, login_required
from .validators import Validator
import datetime
from app.Engine.AutomatedTasks.scheduler import GameScheduler
from datetime import timedelta
import app.alert_notifications as alert
from app.Engine.AutomatedTasks.Tasks.mafia_kill import check_target_from_events
from .decorators import handle_jobs



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
    v = Validator(game, current_user)
    form = SetupGameForm()
    forum_form = ForumForm()
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
            'initial_thread': initial_chat_page_content
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
    v = Validator(game, current_user)
    form = ChooseRolesForm()
    form = form.set_form_parameters(entries=len(game.game_players), choices=[role.visible_name for role in roles_api.roles])

    if v.user_is_game_admin() and v.enrollment_is_closed():
        if not form.is_submitted():
            return render_template('SetupGameModule_choose_roles.html', game=game, form=form)
        else:
            # placeholder for form handler
            roles = [role.name for role in roles_api.roles]
            role_ids = []
            for entry in form.roles.entries:
                print(entry.data['role'])
                role_index = [role.visible_name for role in roles_api.roles].index(entry.data['role'])
                role_ids.append(roles_api.roles[role_index].id)
                db_api.remove_roles_from_game()
                db_api.set_roles_to_game(role_ids)

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
            game = db_api.set_start_time(start_datetime)
            game_scheduler.create_game_start(game)

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

    if form.is_submitted():
        post_content = form.content.data
        post_content = (post_content[:998] + '..') if len(post_content) > 998 else post_content
        topic_name = form.topic_name.raw_data[1]

        if v.user_can_write_in_forum(topic_name) and v.user_in_game():

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
            if datetime.datetime.utcnow() - last_reply_date < timedelta(seconds=60): # TODO: remove hardcoded confituration
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
def lobby(game_id):
    game_id = int(game_id)

    game_scheduler = GameScheduler()
    game_scheduler.check_jobs_and_run(game_id)

    forum_form = ForumForm()
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)
    event_api = GameEventApi()

    your_privileges = []
    if v.user_in_game() and v.game_is_started():
        # day and night duration
        day_duration = game.phases[0].phase_duration
        night_duration = game.phases[1].phase_duration

        # alive players list
        alive_players = db_api.get_alive_players()
        alive_players_names = [player.name for player in alive_players]
        form = CreateEventForm()
        form.target.choices = alive_players_names

        # dead players list
        dead_players = db_api.get_dead_players()

        # mafiosos
        mafiosos = db_api.get_players_with_role('mafioso')

        # you db object
        you = [player for player in game.game_players if player.user_id == current_user.id][0]
        if you in dead_players:
            your_privileges.append('graveyard')
        # actual your mafioso vote if you are in mafia
        if 'mafioso' in [role.name for role in db_api.get_user_roles(current_user.id)]:
            your_privileges.append('mafioso')
            mafia_actual_target = check_target_from_events(db_api, event_api=event_api)
            if mafia_actual_target is not None:
                mafia_actual_target = [player for player in game.game_players if player.id == mafia_actual_target][0]
        else:
            mafia_actual_target = None

        # citizen votes and your actual vote
        citizen_votes = event_api.get_all_events_for_actual_day(game, 'citizen_vote')
        citizen_votes = sorted(citizen_votes, key=lambda d: d.timestamp)

        try:
            your_citizen_vote = event_api.get_last_events_for_actual_day(game, 'citizen_vote')['citizen_vote'][you.id]
            your_citizen_vote = [player for player in game.game_players if player.id == your_citizen_vote.target][0]
        except KeyError:
            your_citizen_vote = None

        # any winner?
        winners = event_api.check_if_someone_wins(game)

        # current time
        current_time = datetime.datetime.now()


        data = {
            'day_end': game.start_time + timedelta(seconds=game.day_no * (day_duration + night_duration) - night_duration),
            'night_end': game.start_time + timedelta(seconds=game.day_no * (day_duration + night_duration)),
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
            'mafiosos': mafiosos
        }
        return render_template('SetupGameModule_lobby.html',
                               game=game,
                               data=data,
                               form=form,
                               forum_form=forum_form)
    else:
        return redirect(url_for('SetupGameModule.game_list'))


@SetupGameModule.route('<game_id>/create_event/<event_name>', methods=['GET', 'POST'])
@login_required
@handle_jobs
def create_event(game_id, event_name):
    game_id = int(game_id)
    db_api = GameApi()
    game = db_api.get_game(game_id)
    v = Validator(game, current_user)
    if v.user_in_game() and v.user_can_do_event(event_name) and v.game_in_progress() and v.user_is_alive():
        alive_players = db_api.get_alive_players()
        alive_players_names = [player.name for player in alive_players]
        form = CreateEventForm()
        form.target.choices = alive_players_names
        if form.validate_on_submit():
            game_event_api = GameEventApi()
            game_event_api.create_new_event(game,
                                            event_name,
                                            db_api.get_player_id_for_user_id(current_user.id),
                                            db_api.get_player_id_for_name(form.target.data))

    return redirect(url_for('SetupGameModule.lobby', game_id=game_id))


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
    privileges = []
    if v.user_is_allowed_for_forum(forum_name):
        #privileges
        privileges.append('user_can_read')
        if v.user_can_write_in_forum(forum_name):
            privileges.append('user_can_write')

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
            'privileges': privileges
        }
        return render_template('SetupGameModule_forum.html',
                               game=game,
                               data=data,
                               forum_form=forum_form)
    else:
        return redirect(url_for('SetupGameModule.lobby', game_id=game_id))
