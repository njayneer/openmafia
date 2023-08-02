from . import AdminModule
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from .decorators import administrator_privileges_required
from .forms import RoleForm
from app import db
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi, ForumApi, utc_to_local, UserApi
from app.Engine.DB.models import *
from werkzeug.security import generate_password_hash


@AdminModule.route('', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def admin_index():
    user_api = UserApi()
    achievement_types = user_api.list_achievement_types()
    return render_template('AdminModule_index.html', achievement_types=achievement_types)


@AdminModule.route('update_db', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def update_db():
    import app.Engine.DB.update2_5_1
    flash('Wykonano', 'alert-success')
    return redirect(url_for('AdminModule.admin_index'))


@AdminModule.route('add_role', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def add_role():
    role_form = RoleForm()
    roles_api = RolesApi()

    if role_form.validate_on_submit():

        role_name = role_form.name.data
        visible_name = role_form.visible_name.data
        description = role_form.description.data

        roles_api.add_role(role_name, visible_name, description)

        flash('Dodano rolę '+role_name, 'alert-success')

    roles = roles_api.list_roles()
    return render_template('AdminModule_addrole.html', role_form=role_form, roles=roles)

@AdminModule.route('set_achievement', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def set_achievement():
    user_name = request.args.get("user_name")
    achievement_name = request.args.get("achievement_name")

    if user_name and achievement_name:
        user_api = UserApi()
        user_api.get_user_for_username(user_name)
        if user_api.user:
            user_api.set_achievement_to_user(achievement_name)
            flash('Dodano achievement', 'alert-success')
        else:
            flash('Nie znaleziono takiego loginu', 'alert-danger')
    return redirect(url_for('AdminModule.admin_index'))


@AdminModule.route('create_test_users', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def create_test_users():
    users = [User(email="user1@email.com",
                  user="user1",
                  name="user1",
                  password=generate_password_hash("user1", method='sha256')),
             User(email="user2@email.com",
                  user="user2",
                  name="user2",
                  password=generate_password_hash("user2", method='sha256')),
             User(email="user3@email.com",
                  user="user3",
                  name="user3",
                  password=generate_password_hash("user3", method='sha256')),
             User(email="user4@email.com",
                  user="user4",
                  name="user4",
                  password=generate_password_hash("user4", method='sha256')),
             User(email="user5@email.com",
                  user="user5",
                  name="user5",
                  password=generate_password_hash("user5", method='sha256')),
             User(email="user6@email.com",
                  user="user6",
                  name="user6",
                  password=generate_password_hash("user6", method='sha256')),
             User(email="user7@email.com",
                  user="user7",
                  name="user7",
                  password=generate_password_hash("user7", method='sha256')),
             User(email="user8@email.com",
                  user="user8",
                  name="user8",
                  password=generate_password_hash("user8", method='sha256')),
             User(email="user9@email.com",
                  user="user9",
                  name="user9",
                  password=generate_password_hash("user9", method='sha256')),
             User(email="user10@email.com",
                  user="user10",
                  name="user10",
                  password=generate_password_hash("user10", method='sha256'))]
    for user in users:
        db.session.add(user)
    db.session.commit()
    flash('Dodano', 'alert-success')
    return redirect(url_for('AdminModule.admin_index'))
