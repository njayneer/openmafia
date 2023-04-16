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



	#Get your reCaptche key on: https://www.google.com/recaptcha/admin/create
	#RECAPTCHA_PUBLIC_KEY = "6LffFNwSAAAAAFcWVy__EnOCsNZcG2fVHFjTBvRP"
	#RECAPTCHA_PRIVATE_KEY = "6LffFNwSAAAAAO7UURCGI7qQ811SOSZlgU69rvv7"

class ProductionConfig(Config):
	# SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:admin@localhost/test'
	SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user='njayneer',
																						password='haslojebacjaslo',
																						server='njayneer.mysql.pythonanywhere-services.com',
																						database='njayneer$default')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):

	DEBUG = True


class TestingConfig(Config):
	TESTING = True
