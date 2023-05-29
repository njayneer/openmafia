from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea


class RoleForm(FlaskForm):
    name = StringField(u'Nazwa', validators=[DataRequired()])
    visible_name = StringField(u'Widoczna nazwa', validators=[DataRequired()])
    description = StringField(u'Opis', validators=[DataRequired()], widget=TextArea())
