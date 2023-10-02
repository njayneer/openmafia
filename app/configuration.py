import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config(object):
	"""
	Configuration base, for all environments.
	"""
	DEBUG = False
	TESTING = False
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')
	BOOTSTRAP_FONTAWESOME = True
	SECRET_KEY = "ALVKELDJFMEAKASFFGR"
	CSRF_ENABLED = True
	SQLALCHEMY_TRACK_MODIFICATIONS = True

	MAIL_SERVER = 'smtp.gmail.com'
	MAIL_PORT = 465
	MAIL_USE_SSL = True
	MAIL_USERNAME = 'playopenmafia@gmail.com'
	MAIL_PASSWORD = 'dkenfiei9fn493fjwl0g82245'
	EMAIL_PASSWORD_RESET = 'playopenmafia@gmail.com'


	JOB_PRIORITIES = {
		'start_game': 10,
		'lynch': 100,
		'barman_getting_drunk': 160,  # before every other night functionality (possibly after role blocking)
		'gun_shot': 190,
		'mafia_kill': 200,
		'detective_check': 210,
		'spy_check': 220
	}



	#Get your reCaptche key on: https://www.google.com/recaptcha/admin/create
	#RECAPTCHA_PUBLIC_KEY = "6LffFNwSAAAAAFcWVy__EnOCsNZcG2fVHFjTBvRP"
	#RECAPTCHA_PRIVATE_KEY = "6LffFNwSAAAAAO7UURCGI7qQ811SOSZlgU69rvv7"

class ProductionConfig(Config):
	# SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:admin@localhost/test'
	SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user='openmafia',
																						password='haslojebacjaslo',
																						server='openmafia.mysql.pythonanywhere-services.com',
																						database='openmafia$default')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):

	DEBUG = True


class TestingConfig(Config):
	SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user='njayneer',
																									password='haslojebacjaslo',
																									server='njayneer.mysql.pythonanywhere-services.com',
																									database='njayneer$default')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
