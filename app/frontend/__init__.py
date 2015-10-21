# coding: utf-8
from .. import factory

from .views import mod as views
from ..services import switch_db as db


def create_app(settings_override=None):
    app = factory.create_app(__name__, '/',
                             settings_override,
                             static_path="/static",
                             static_url_path="/static",
                             static_folder="static")

    db.init_app(app)

    #app.errorhandler(404)(not_found)
    #app.errorhandler(403)(forbidden)
    #app.errorhandler(401)(unauthorized)

    app.register_blueprint(views)

    print((app.url_map))
    return app

def not_found(error):
    return render_template('404.html'), 404


def forbidden(error, *args, **kwargs):
    return render_template('403.html'), 403


def unauthorized(error):
    return render_template('401.html'), 401
