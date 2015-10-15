from flask.ext.testing import TestCase

# from app import assets, db
from app.frontend import create_app as app_factory
from app.config import Testing

'''
All tests will be run when calling nosetests from the projects root directoy
You can set options in setup.cfg under [nosetests]
'''


class FlaskAppTest(TestCase):
    '''Tries to create and destroy the api'''
    def create_app(self):
        return app_factory(settings_override=Testing())

    def setUp(self):
        # db.create_all()
        pass

    def tearDown(self):
        # db.session.remove()
        # db.drop_all()
        pass
