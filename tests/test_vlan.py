from unittest import TestCase

from app.services import SwitchDB
from app.services.snmp_device import SNMP_Vlan, SNMP_Vlan_Base
from app.services.snmp_device import SNMP_Vlanlist


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
        self.assertEqual(device.vlans()[0].name(), "DEFAULT_VLAN")
        self.assertEqual(device.vlans()[1].name(), "WLAN")
        self.assertEqual(device.vlans()[2].name(), "WLANGAST")
        self.assertEqual(device.vlans()[3].name(), "VOIP")

    def test_vlan_portmembership(self):
        device = self.device
        self.assertIn((15, 't'), device.get_port_membership(7))
        self.assertNotIn((15, 'u'), device.get_port_membership(7))

    def test_vlan_list(self):
        vlist = SNMP_Vlanlist(self.device._snmp)
        self.assertIsNotNone(vlist._vlans)
        self.assertIn((1, 'DEFAULT_VLAN'), vlist)
        self.assertIn((15, 'WLAN'), vlist)
        self.assertIn((20, 'WLANGAST'), vlist)
        vlan_list_test = [(1, 'DEFAULT_VLAN'), (15, 'WLAN'), (20, 'WLANGAST'), (25, 'VOIP')]
        # iterator
        for test_vlan, vlist_item in zip(vlan_list_test, vlist):
            self.assertEqual(test_vlan, vlist_item)
        for vlan in vlist:
            print ("Type: ", type(vlan))
            self.assertIs(type(vlan.vid()), int)
        self.assertEqual(len(vlist), 4)

    def test_create_delete_vlan(self):
        device = self.device
        device.vlan_remove(7)
        self.assertNotIn((7, 'test'), device.vlans())
        device.vlan_create(7, 'test')
        self.assertIn((7, 'test'), device.vlans())
        device.vlan_remove(7)
        self.assertNotIn((7, 'test'), device.vlans())

    def test_vlan_cmp(self):
        vlan15 = SNMP_Vlan.create(15, self.device._snmp)
        vlan1 = SNMP_Vlan.create(1, self.device._snmp)
        vlan1_1 = SNMP_Vlan.create(1, self.device._snmp)
        # compare vlan objects
        self.assertEqual(vlan1, vlan1_1)
        self.assertNotEqual(vlan15, vlan1_1)
        # compare by vlan_id
        self.assertEqual(1, vlan1)
        self.assertNotEqual(15, vlan1)
        # compare by VLAN-Tuple
        self.assertEqual((1, 'DEFAULT_VLAN'), vlan1)
        self.assertNotEqual((15, 'WLAN'), vlan1)

    def test_vlan_port_assignment(self):
        vlan15 = SNMP_Vlan.create(15, self.device._snmp)
        vlan20 = SNMP_Vlan.create(20, self.device._snmp)
        vlan25 = SNMP_Vlan.create(25, self.device._snmp)
        vlan1 = SNMP_Vlan.create(1, self.device._snmp)
        vlan1.print_tables()
        vlan15.print_tables()

        self.assertFalse(vlan15.is_dirty())
        self.assertEqual('WLAN (15)', str(vlan15))

        # Port 1 (u,t,t,t)
        self.assertTrue(vlan1.is_untagged(1))
        self.assertFalse(vlan1.is_tagged(1))
        self.assertTrue(vlan15.is_tagged(1))
        self.assertFalse(vlan15.is_untagged(1))

        self.assertTrue(vlan20.is_tagged(1))
        self.assertFalse(vlan20.is_untagged(1))

        self.assertTrue(vlan25.is_tagged(1))
        self.assertFalse(vlan25.is_untagged(1))

        
        # Port 3 (u,n,n,n)
        self.assertTrue(vlan1.is_untagged(3))
        self.assertFalse(vlan1.is_tagged(3))
        self.assertFalse(vlan15.is_tagged(3))
        self.assertFalse(vlan15.is_untagged(3))

        # port 17 (n,u,n,n,n)
        self.assertFalse(vlan1.is_untagged(17))
        self.assertFalse(vlan1.is_tagged(17))
        self.assertTrue(vlan15.is_untagged(17))
        self.assertFalse(vlan15.is_tagged(17))

        # port 21 (n,t,n,n,n)
        self.assertFalse(vlan1.is_untagged(21))
        self.assertFalse(vlan1.is_tagged(21))
        self.assertFalse(vlan15.is_untagged(21))
        self.assertTrue(vlan15.is_tagged(21))
