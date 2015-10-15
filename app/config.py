# coding: utf-8

# import flask.ext.uploads
import os.path
_basedir = os.path.abspath(os.path.dirname(__file__))

'''
Configuration settings that always apply
'''


class Config(object):
    DEBUG = True
    TESTING = False
    SITEURL = 'https://test.lan'
    # PROPAGATE_EXCEPTIONS = True
    SECRET_KEY = "changemeplease"
    SESSION_COOKIE_NAME = "flasksession"
    LOGGER_NAME = 'flask-app'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'entropy.db')
    # BABEL_DEFAULT_LOCALE = 'de_DE.UTF-8'
    # BABEL_DEFAULT_TIMEZONE = "Europe/Berlin"

    # SECURITY_CONFIRMABLE = True     # We still need to provice an url for confirmation
    # SECURITY_REGISTERABLE = True    # We still need to provide an url for user creation
    # SECURITY_RECOVERABLE = True     # We still need to provice the reset url
    # SECURITY_TRACKABLE = False
    # SECURITY_CHANGEABLE = True      # We still need to provide an url for password change
    # SECURITY_USER_IDENTITY_ATTRIBUTES = ('email', 'username')
    # SECURITY_PASSWORD_HASH = 'plaintext'
    # SECURITY_TOKEN_AUTHENTICATION_HEADER = "Auth-Token"


class Development(Config):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'entropy_dev.db')
    SITEURL = 'http://localhost:5000'
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    SECURITY_PASSWORD_SALT = "radmonchangeme"
    ASSETS_DEBUG = True


class Testing(Config):
    ASSETS_DEBUG = True
    DEBUG = True
    TESTING = True
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    SITEURL = 'http://localhost:5000'
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    SECURITY_PASSWORD_SALT = "radmonchangeme"
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
