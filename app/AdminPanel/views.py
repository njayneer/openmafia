from . import AdminModule
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from .decorators import administrator_privileges_required
from .forms import RoleForm
from app import db
from app.Engine.DB.db_api import GameApi, RolesApi, GameEventApi, ForumApi, utc_to_local
from app.Engine.DB.models import *


@AdminModule.route('', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def admin_index():
    return render_template('AdminModule_index.html')


@AdminModule.route('update_db', methods=['GET', 'POST'])
@login_required
@administrator_privileges_required
def update_db():
    db.create_all()
    flash('Wykonano', 'alert-success')
    return redirect(url_for('admin_index'))


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

