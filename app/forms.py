from flask_wtf import FlaskForm
from wtforms  import PasswordField, StringField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
	name = StringField(u'Login', validators = [DataRequired()])
	password = PasswordField(u'Hasło', validators = [DataRequired()])
	email = StringField(u'Email')

class SetupGameForm(FlaskForm):
	name = StringField(u'Login', validators=[DataRequired()])
