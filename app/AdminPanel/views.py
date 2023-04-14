from . import AdminModule
from flask import render_template
from flask_login import login_required
from app import game_scheduler


@AdminModule.route('list_jobs', methods=['GET', 'POST'])
@login_required
def setup_game():
    jobs = game_scheduler.get_jobs()
    return render_template('AdminModule_index.html', jobs=jobs)

@AdminModule.route('create_dummy_job', methods=['GET', 'POST'])
@login_required
def create_dummy_fun():
    game_scheduler.create_dummy_job()
    return render_template('AdminModule_index.html')
