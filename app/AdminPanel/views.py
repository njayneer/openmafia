from . import AdminModule
from flask import render_template
from flask_login import login_required


@AdminModule.route('list_jobs', methods=['GET', 'POST'])
@login_required
def setup_game():
    jobs = []
    return render_template('AdminModule_index.html', jobs=jobs)

