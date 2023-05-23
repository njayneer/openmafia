from . import AdminModule
from flask import render_template, redirect, url_for, flash
from flask_login import login_required


@AdminModule.route('update_db', methods=['GET', 'POST'])
@login_required
def update_db():
    from app import db
    db.create_all()
    flash('Wykonano', 'alert-success')
    return redirect(url_for('index'))

