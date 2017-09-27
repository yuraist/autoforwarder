import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']
    SECURITY_REGISTERABLE = True
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SECURITY_PASSWORD_SALT = os.environ['SECURITY_PASSWORD_SALT']
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
