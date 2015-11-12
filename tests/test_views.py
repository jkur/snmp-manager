from . import FlaskAppTest
from app.services import switch_db as db

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

    def  test_create_delete_vlan(self):
        device = db.all()[0]
        self.assertNotIn( (7, 'test'), device.vlans())
        data = dict(VLAN_NAME="test", VLAN_ID=7)
        r = self.client.post('/vlan/all/vlan/create', data=data, follow_redirects=False)
        self.assertEqual(302, r.status_code)
        self.assertIn( (7, 'test'), device.vlans())
        data = dict(VLAN_ID=7)
        r = self.client.post('/vlan/all/vlan/delete', data=data, follow_redirects=False)
        self.assertEqual(302, r.status_code)


 #   def test_detail_port(self):
 #       data = 
 #       r = self.client.post("/switch/switch-loft4-1")
 #       self.assert_200(r)
