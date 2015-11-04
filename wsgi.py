#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from app.frontend import create_app

frontend = create_app(settings_override="app.config.Development")

application = DispatcherMiddleware(frontend, {})


if __name__ == "__main__":
    with frontend.app_context():
        # db.create_all()
        pass
    run_simple('127.0.0.1', 5000, application, use_reloader=True, use_debugger=True)
