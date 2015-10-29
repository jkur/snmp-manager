from unittest import TestCase

from app.services import SwitchDB, SNMP_Device, SNMP_Service


class Test_SwitchDB(TestCase):
    def setUp(self):
        self.confv3 = {'version': 3,
                       'security_username': 'pm',
                       'auth_protocol': 'SHA',
                       'auth_password': 'eighoi7Yuuno',
                       'privacy_protocol': 'DEFAULT',
                       'privacy_password': 'io0chuigi6Ot',
                       'security_level': 'authPriv'}

    def test_snmp_service(self):
        # version 2
        s = SNMP_Service('switch-loft4-2', community='public', version=2)
        self.assertIsNotNone(s)
        # version 3
        s = SNMP_Service('switch-loft4-2', **self.confv3)
        self.assertIsNotNone(s)

    def test_snmp_device(self):
        s = SNMP_Device('switch-loft4-2', community='public', version=2)
        self.assertIsNotNone(s)
        # v3
        s = SNMP_Device('switch-loft4-2', **self.confv3)
        self.assertIsNotNone(s)

    def test_snmp_db(self):
        class AppMock():
            def __init__(self, conf):
                self.conf = conf
                self.config = dict(SWITCHES={'switch-loft4-2': self.conf})
        appmock = AppMock(self.confv3)
        s = SwitchDB()
        s.init_app(appmock)
        self.assertIsNotNone(s)
        for i in s.all():
            print (i.hostname)
        self.assertEqual( len(s.all()), 1)
        self.assertEqual(s.get('switch-loft4-2').hostname, 'switch-loft4-2')
        snmpdev = s.get('switch-loft4-2')
        self.assertEqual(snmpdev.model().upper(), 'J9020A')
        modelname = snmpdev._snmp.getfirst('ENTITY-MIB::entPhysicalModelName').value
        self.assertEqual(modelname.upper(), 'J9020A')

    def test_snmp_device_vlans(self):
        class AppMock():
            def __init__(self, conf):
                self.conf = conf
                self.config = dict(SWITCHES={'switch-loft4-2': self.conf})
        appmock = AppMock(self.confv3)
        s = SwitchDB()
        s.init_app(appmock)
        self.assertIsNotNone(s)
        device = s.all()[0]
        self.assertEqual(len(device.vlans()), 3)
        self.assertEqual(device.vlans()[0][1], "DEFAULT_VLAN")
        self.assertEqual(device.vlans()[1][1], "WLAN")
        self.assertEqual(device.vlans()[2][1], "VOIP")
        
        


        
    #def test_portlist(self):
    #    s = SNMP_Device('switch-loft4-2')
    #    self.assertIsNotNone(s)
    #    ports = s.get_ports()
    #    self.assertNotEqual(len(ports), 0)
    #    self.assertEqual(ports[0].alias(), 'UPLINK-c05')
    #    self.assertEqual(ports[0].descr(), '1')
    #    self.assertTrue(s.get_port(1).is_interface())
    #    #self.assertFalse(s.get_port(99).is_interface())
    #    #self.assertTrue(s.get_port(49).is_trunk())
    #    self.assertTrue(s.get_port(17).is_up())
    #    self.assertFalse(s.get_port(15).has_port_auth())
    #    self.assertTrue(s.get_port(18).has_port_auth())
    # 
    #def test_port_auth_set(self):
    #    s = SNMP_Device('switch-loft4-2', **self.confv3)
    #    self.assertIsNotNone(s)
    #    portauth = s.get_port(21).has_port_auth()
    #    if portauth:
    #        self.assertTrue(s.get_port(21).has_port_auth())
    #    else:
    #        self.assertFalse(s.get_port(21).has_port_auth())
    # 
    #    s.get_port(21).set_port_auth(True, 30, 15)
    # 
    #    portinfo = s.get_port(21).port_access_info()
    #    self.assertTrue(portinfo['enabled'])
    #    self.assertEqual(portinfo['auth_vlan'], 30)
    #    self.assertEqual(portinfo['unauth_vlan'], 15)
