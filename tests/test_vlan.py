from unittest import TestCase

from app.services import SwitchDB
from app.services.snmp_device import SNMP_Vlan


class Test_Vlan(TestCase):
    def setUp(self):
        self.confv3 = {'version': 3,
                       'security_username': 'pm',
                       'auth_protocol': 'SHA',
                       'auth_password': 'eighoi7Yuuno',
                       'privacy_protocol': 'DEFAULT',
                       'privacy_password': 'io0chuigi6Ot',
                       'security_level': 'authPriv'}
        class AppMock():
            def __init__(self, conf):
                self.conf = conf
                self.config = dict(SWITCHES={'switch-loft4-2': self.conf})
        appmock = AppMock(self.confv3)
        self.db = SwitchDB()
        self.db.init_app(appmock)
        self.device = self.db.all()[0]

    def test_snmp_vlans(self):
        device = self.device
        self.assertEqual(len(device.vlans()), 4)
        self.assertEqual(device.vlans()[0][1], "DEFAULT_VLAN")
        self.assertEqual(device.vlans()[1][1], "WLAN")
        self.assertEqual(device.vlans()[2][1], "WLANGAST")
        self.assertEqual(device.vlans()[3][1], "VOIP")

    def test_vlan_list(self):
        device = self.device
        self.assertIn((15, 't'), device.get_port_membership(7))
        self.assertNotIn((15, 'u'), device.get_port_membership(7))
        
    def test_vlan_port_assignment(self):
        vlan15 = SNMP_Vlan(15, self.device._snmp)
        vlan1 = SNMP_Vlan(1, self.device._snmp)
        vlan1.print_tables()
        vlan15.print_tables()

        self.assertFalse(vlan15.is_dirty())
        self.assertEqual('WLAN (15)', str(vlan15))

        self.assertTrue(vlan15.get_port_tagged(1))
        self.assertTrue(vlan15.get_port_tagged(5))
        self.assertTrue(vlan15.get_port_tagged(7))

        self.assertTrue(vlan15.get_port_untagged(2))
        self.assertFalse(vlan15.get_port_tagged(3))
        self.assertFalse(vlan15.get_port_tagged(4))

        self.assertTrue(vlan1.get_port_untagged(1))
        self.assertFalse(vlan1.get_port_untagged(2))

        self.assertTrue(vlan1.get_port_tagged(3))
        self.assertFalse(vlan1.get_port_untagged(3))

        ### strange!

        self.assertTrue(vlan1.get_port_tagged(27))
        self.assertFalse(vlan1.get_port_untagged(27))

        self.assertTrue(vlan1.get_port_untagged(28))
        self.assertFalse(vlan1.get_port_tagged(28))

        self.assertTrue(vlan1.get_port_untagged(26))
        self.assertFalse(vlan1.get_port_tagged(26))
