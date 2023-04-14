from flask import url_for, redirect, render_template, flash, g
from flask_login import login_user, logout_user, current_user
from app import app, lm, db
from app.forms import LoginForm
from app.Engine.DB.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import app.alert_notifications as alert


@app.route('/')
def index():
    return render_template('index.html')

# === User login methods ===

@app.before_request
def before_request():
    g.user = current_user


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data

        user = User.query.filter_by(user=name).first()

        if not user or not check_password_hash(user.password, password):
            alert.login_incorrect()
            return render_template('login.html',
                                   title='Sign In',
                                   form=form)
        else:
            if login_user(user):
                g.user = user
            alert.login_correct(user.name)
            return redirect(url_for('index'))
    return render_template('login.html',
                           title='Sign In',
                           form=form)


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        password = form.password.data

        user = User.query.filter_by(user=name).first()
        user_mail = User.query.filter_by(email=email).first()
        if user or user_mail:  # if a user is found, we want to redirect back to signup page so user can try again
            if user:
                alert.user_already_exists()
            else:
                alert.email_already_taken()
            return render_template('signup.html',
                           title='Sign Up',
                           form=form)
        new_user = User(email=email, user=name, password=generate_password_hash(password, method='sha256'), name=name)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        alert.account_created()
        return redirect(url_for('login'))
    return render_template('signup.html',
                           title='Sign Up',
                           form=form)

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ====================
