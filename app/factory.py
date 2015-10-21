# coding: utf-8

# from .assets import create_assets

from flask import Flask, send_from_directory

# from . import db, mail, security, babel, user_datastore

# from flask.ext.security import SQLAlchemyUserDatastore

import logging

def create_app(package_name, package_path, settings_override=None, **kwargs):
    app = Flask(__name__, **kwargs)
    app.config.from_object('app.config.Config')
    app.config.from_object(settings_override)
    app.config.from_pyfile('settings.cfg', silent=True)

    # mail.init_app(app)
    # db.init_app(app)
    # babel.init_app(app)
    # user_datastore.init(db, User, Role)
    # security.init_app(app, SQLAlchemyUserDatastore(db, User, Role),
    #                  register_form=Extended_Register_Form,
    #                  confirm_register_form=Extended_Register_Form)

    logging.basicConfig()
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    return app
