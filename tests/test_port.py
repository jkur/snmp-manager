from unittest import TestCase

from app.services import SwitchDB
from app.services.snmp_device import SNMP_Portlist
# from app.services.snmp_port import SNMP_IFPort


class Test_Ports(TestCase):
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

    def test_port_list_isolated(self):
        portlist = SNMP_Portlist(self.device._snmp)
        self.assertIsNotNone(portlist)
        self.assertTrue(len(portlist) > 20)
        self.assertEqual(portlist.port(1).idx(), 1)
        self.assertTrue(portlist.trunk(40).is_part_of_trunk())
        self.assertTrue(portlist.trunk(41).is_part_of_trunk())
        self.assertTrue(portlist.trunk(42).is_part_of_lacp())
        self.assertTrue(portlist.trunk(43).is_part_of_lacp())

    def test_port_list(self):
        device = self.device
        self.assertTrue(len(device.ports()) > 49)
