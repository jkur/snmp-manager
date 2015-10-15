from . import FlaskAppTest


class Test_App(FlaskAppTest):
    def test_app(self):
        self.assertIsNotNone(self.app)
