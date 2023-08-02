from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, SelectField, FormField, HiddenField, IntegerField, BooleanField
from wtforms.validators import DataRequired
from wtforms.fields import DateField, TimeField
from wtforms.widgets import TextArea

class SetupGameForm(FlaskForm):
	name = StringField(u'Nazwa', validators=[DataRequired()])


class RoleForm(FlaskForm):
	role = SelectField('Rola', choices=['a','b','c'], validators=[DataRequired()])


class RoleVisibleAfterDeathForm(FlaskForm):
	role_visible_after_death = BooleanField(default=True)


class ChooseRolesForm(FlaskForm):
	roles = FieldList(FormField(RoleForm), min_entries=2)
	role_visibility_after_death = FieldList(FormField(RoleVisibleAfterDeathForm), min_entries=1)

	# here custom fields for roles
	sniper_shots = IntegerField('Dostępnych strzałów', default=1)
	sniper_blocked_after_missed_shot = BooleanField('Blokada i odsłonięcie roli po zabiciu niewinnego.')

	def set_form_parameters(self, entries, choices):
		# overriding forms to workaround dymanic form configuration
		class LocalRoleForm(RoleForm):
			pass
		LocalRoleForm.role = SelectField('Rola', choices=choices, validators=[DataRequired()])

		class LocalRoleVisibleAfterDeathForm(RoleVisibleAfterDeathForm):
			pass
		LocalRoleVisibleAfterDeathForm.role_visible_after_death = BooleanField('Widoczna po śmierci', default=True)

		class LocalChooseRolesForm(ChooseRolesForm):
			pass

		LocalChooseRolesForm.roles = FieldList(FormField(LocalRoleForm), min_entries=entries, max_entries=entries)
		LocalChooseRolesForm.role_visibility_after_death = FieldList(FormField(LocalRoleVisibleAfterDeathForm),
																	 min_entries=len(choices),
																	 max_entries=len(choices))
		return LocalChooseRolesForm()


class DurationForm(FlaskForm):
	#duration = TimeField('Time', format='%H:%M', validators=[DataRequired()])
	duration_hours = IntegerField('Hours', validators=[DataRequired()], default=0)
	duration_minutes = IntegerField('Minutes', validators=[DataRequired()], default=0)


class ChooseStartTimeForm(FlaskForm):
	date_posted = DateField('Data startu', format='%Y-%m-%d', validators=[DataRequired()])
	time_posted = TimeField('Godzina startu', format='%H:%M', validators=[DataRequired()])
	phases = FieldList(FormField(DurationForm), min_entries=2)


class CreateEventForm(FlaskForm):
	target = SelectField('Żywy gracz', choices=[])


class ForumForm(FlaskForm):
	content = StringField(u'Content', validators=[DataRequired()], widget=TextArea())
	topic_name = HiddenField(u'TopicName')


class ConfigurationForm(FlaskForm):
	game_admin = BooleanField()
	detailed_lynch_results = BooleanField()
	lynch_voting_history = BooleanField()
	see_enrolled_user_list = BooleanField()
	citizen_forum_turned_on = BooleanField()
	initial_forum_turned_on = BooleanField()
	creations_on = BooleanField()
