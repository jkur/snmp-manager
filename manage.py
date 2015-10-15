#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask.ext.script import Server, Manager

from app import create_app
from manager import *

application = create_app(__name__, '/', settings_override="app.config.Development")

'''
All the commands that you can call by ./manage.py command
'''
manager = Manager(application)

manager.add_command("runserver", Server())


if __name__ == "__main__":
    with application.app_context():
        # db.create_all()
        pass
    manager.run()
