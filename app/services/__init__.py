from easysnmp import Session
from flask import abort


class SNMP_Service():
    def __init__(self, hostname, **kwargs):
        self.switch = hostname
        self.version = kwargs.get('version', 2)
        if self.version < 3:
            self.community = kwargs.get('community', 'public')
            self.session = Session(hostname=self.switch, community=self.community, version=self.version)
        else:
            self.security_level = kwargs.get('security_level', 'authNoPriv')
            self.security_username = kwargs.get('security_username', 'opro')
            self.auth_protocol = kwargs.get('auth_protocol', 'SHA')
            self.auth_password = kwargs.get('auth_password', '')
            self.privacy_protocol = kwargs.get('privacy_protocol', 'aes')
            self.privacy_password = kwargs.get('privacy_password', '')
            self.session = Session(hostname=self.switch,
                                   security_level=self.security_level,
                                   security_username=self.security_username,
                                   auth_protocol=self.auth_protocol,
                                   auth_password=self.auth_password,
                                   privacy_protocol=self.privacy_protocol,
                                   privacy_password=self.privacy_password,
                                   version=self.version)

    def sys_descr(self):
        d = self.session.get('sysDescr.0')
        [descr, fw, rom] = d.value.split(',')
        return (self.switch, descr, fw, rom)

    def num_ports(self):
        d = self.session.get('')
        [descr, fw, rom] = d.value.split(',')

    def model(self):
        d = self.session.get('ENTITY-MIB::entPhysicalModelName.1')
        return d

    def firmware(self):
        d = self.session.get('ENTITY-MIB::entPhysicalSoftwareRev.1')
        return d

    def get(self, oid):
        return self.session.get(oid)

    def getfirst(self, oid):
        ret = self.session.get_next(oid)
        while ret is not None and not len(ret.value):
            ret = self.session.get_next(ret.oid)
        return ret

    def getall(self, oid):
        ret = self.session.walk(oid)
        return ret

    def set(self, oid, value, snmp_type=None):
        return self.session.set(oid, value, snmp_type)


class SNMP_IFPort():
    def __init__(self, idx, snmp_service):
        self._snmp = snmp_service
        self._portidx = int(idx)
        self._portalias = ''
        self._portdescr = ''
        self._porttype = 0
        self._portstatus = 2  # down=2, up=1
        self._get_port_info()

    def _get_port_info(self):
        self._portdescr = self._snmp.get('.1.3.6.1.2.1.2.2.1.2.{}'.format(self._portidx)).value
        self._porttype = int(self._snmp.get('IF-MIB::ifType.{}'.format(self._portidx)).value)
        self._portstatus = int(self._snmp.get('.1.3.6.1.2.1.2.2.1.8.{}'.format(self._portidx)).value)
        self._portalias = self._snmp.get('IF-MIB::ifAlias.{}'.format(self._portidx)).value

    def descr(self):
        return self._portdescr

    def alias(self):
        return self._portalias

    def is_up(self):
        return self._portstatus == 1

    def is_vlan(self):
        return self._porttype == 53  # propvirtual

    def is_interface(self):
        if int(self._snmp.get('IF-MIB::ifAdminStatus.{}'.format(self._portidx)).value) != 1:
            return False
        return self._porttype == 6   # ethernetCsmacd

    def is_loopback(self):
        return self._porttype == 24   # ethernetCsmacd

    def is_trunk(self):
        return self._porttype == 54  # propMultiplexor

    def idx(self):
        return self._portidx

    def has_port_auth(self):
        return int(self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx)).value) == 1

    def set_port_auth(self, active, auth_vlan=None, unauth_vlan=None):
        if unauth_vlan is not None:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid.{}'.format(self._portidx), unauth_vlan)
        if auth_vlan is not None:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid.{}'.format(self._portidx), auth_vlan)
        if active:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx), 1)
        else:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx), 2)

    def port_access_info(self):
        ret = dict(
            enabled=self.has_port_auth(),
            auth_vlan=int(self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid.{}'.format(self._portidx)).value),
            unauth_vlan=int(self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid.{}'.format(self._portidx)).value)
            )
        return ret


class SNMP_Device():
    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        self._portlist = None
        self._snmp = SNMP_Service(self.hostname, **kwargs)

    def get_sysdescr(self):
        return self._snmp.sys_descr().value

    def get_number_ports(self):
        return self._snmp.num_ports().value

    def model(self):
        return self._snmp.getfirst('ENTITY-MIB::entPhysicalModelName.1').value

    def firmware(self):
        return self._snmp.getfirst('ENTITY-MIB::entPhysicalSoftwareRev.1').value

    def port_auth_enabled(self):
        return int(self._snmp.get('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0').value) == 1

    def set_port_auth_enabled(self, enable):
        if enable:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 1)
        else:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 2)

    def get_ports(self):
        if self._portlist is None:
            self._portlist = [SNMP_IFPort(idx.value, self._snmp) for idx in self._snmp.getall('.1.3.6.1.2.1.2.2.1.1')]
        return self._portlist

    def get_port(self, idx):
        if self._portlist is None:
            self.get_ports()
        for port in self._portlist:
            if port.idx() == idx:
                return port
        return None


class SwitchDB():
    _switches = {}

    def __init__(self):
        pass

    def init_app(self, app):
        # if self._initialized: return
        self._switches = {}
        if 'SWITCHES' in app.config:
            for switchname, values in app.config['SWITCHES'].items():
                self._switches.update({switchname: SNMP_Device(switchname, **values)})

    def get(self, name):
        return self._switches[name]

    def get_or_404(self, name):
        try:
            s = self._switches[name]
            return s
        except KeyError:
            abort(404)

    def all(self):
        ret = []
        for k, v in self._switches.items():
            ret.append(v)
        return ret


switch_db = SwitchDB()
