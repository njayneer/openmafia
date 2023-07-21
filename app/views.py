from flask import url_for, redirect, render_template, flash, g
from flask_login import login_user, logout_user, current_user
from app import app, lm, db
from app.forms import LoginForm, EmailForm, NewPasswordForm
from app.Engine.DB.models import User, UserToken
from werkzeug.security import generate_password_hash, check_password_hash
import app.alert_notifications as alert
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
import os

def now():
    now_dt = datetime.now(tz=ZoneInfo(os.environ["TZ"])).replace(tzinfo=None).replace(microsecond=0)
    result = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    return now_dt


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


@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    form = EmailForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = secrets.token_urlsafe(64)
            new_token = UserToken(user_id=user.id,
                                  token=token,
                                  time=now()+timedelta(hours=1))
            db.session.add(new_token)
            db.session.commit()

            content = 'Witaj ' + user.name + '! Na podany adres email została wysłana prośba resetu hasła do twojego ' \
                                            'konta OpenMafia. Jeśli to nie ty, nie przejmuj się, nikt nie przejął ' \
                                            'twojego konta. Prosimy nie odpowiadać na ten email. ' \
                                             'Aby zresetować hasło, kliknij poniższy link: ' \
                                            + url_for('new_password', token=token, _external=True)

            msg = MIMEText(content)

            msg['Subject'] = 'OpenMafia - przypomnienie hasła'
            msg['From'] = app.config['EMAIL_PASSWORD_RESET']
            msg['To'] = user.email

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            s = smtplib.SMTP(app.config['MAIL_SERVER'])
            s.sendmail(msg['From'], [msg['To']], msg.as_string())
            s.quit()
        flash('Link do resetu hasła został wysłany na adres email podany w formularzu (o ile jest prawidłowy).',
              'alert-success')
    return render_template('password_reset.html',
                           title='Reset hasła',
                           form=form)

@app.route('/new_password/<token>')
def new_password(token):
    pass
    return redirect(url_for('index'))