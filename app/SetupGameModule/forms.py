from flask_wtf import FlaskForm
from wtforms  import StringField, FieldList, SelectField, FormField
from wtforms.validators import DataRequired
from wtforms.fields import DateField, TimeField


class SetupGameForm(FlaskForm):
	name = StringField(u'Nazwa', validators=[DataRequired()])


class RoleForm(FlaskForm):
	role = SelectField('Rola', choices=['a','b','c'], validators=[DataRequired()])


class ChooseRolesForm(FlaskForm):
	roles = FieldList(FormField(RoleForm), min_entries=2)

	def set_form_parameters(self, entries, choices):
		# overriding forms to workaround dymanic form configuration
		class LocalRoleForm(RoleForm):
			pass
		LocalRoleForm.role = SelectField('Rola', choices=choices, validators=[DataRequired()])

		class LocalChooseRolesForm(ChooseRolesForm):
			pass

		LocalChooseRolesForm.roles = FieldList(FormField(LocalRoleForm), min_entries=entries, max_entries=entries)
		return LocalChooseRolesForm()


class DurationForm(FlaskForm):
	duration = TimeField('Time', format='%H:%M', validators=[DataRequired()])


class ChooseStartTimeForm(FlaskForm):
	date_posted = DateField('Data startu', format='%Y-%m-%d', validators=[DataRequired()])
	time_posted = TimeField('Godzina startu', format='%H:%M', validators=[DataRequired()])
	phases = FieldList(FormField(DurationForm), min_entries=2)


class CreateEventForm(FlaskForm):
	target = SelectField('Żywy gracz', choices=[])