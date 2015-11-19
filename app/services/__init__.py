from easysnmp import Session


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

    def getall(self, oid, filter_by_value=False):
        ret = self.session.walk(oid)
        if filter_by_value:
            return [lambda x: x.value for x in ret]
        return ret

    def set(self, oid, value, snmp_type=None):
        return self.session.set(oid, value, snmp_type)


from .snmp_db import SwitchDB

switch_db = SwitchDB()

from .snmp_device import SNMP_Device
from .snmp_port import SNMP_IFPort
