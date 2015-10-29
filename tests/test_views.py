from . import FlaskAppTest


class Test_View(FlaskAppTest):
    def test_index(self):
        r = self.client.get("/")
        self.assert_200(r)

    def test_detail_404(self):
        r = self.client.get("/switch/testnotexists")
        self.assert_404(r)

    def test_detail_200(self):
        r = self.client.get("/switch/switch-loft4-2")
        self.assert_200(r)

    def test_detail_200_v3(self):
        r = self.client.get("/switch/switch-loft4-2")
        self.assert_200(r)


 #   def test_detail_port(self):
 #       data = 
 #       r = self.client.post("/switch/switch-loft4-1")
 #       self.assert_200(r)
