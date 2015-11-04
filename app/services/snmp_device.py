from .snmp_port import SNMP_IFPort
from app.services import SNMP_Service
from easysnmp import EasySNMPError

class SNMP_Device():
    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        self._portlist = None
        self._portlist_dirty = True
        self._snmp = SNMP_Service(self.hostname, **kwargs)

    def get_sysdescr(self):
        return self._snmp.sys_descr().value

    def get_number_ports(self):
        return self._snmp.num_ports().value

    def model(self):
        return self._snmp.getfirst('ENTITY-MIB::entPhysicalModelName.1').value

    def firmware(self):
        return self._snmp.getfirst('ENTITY-MIB::entPhysicalSoftwareRev.1').value

    def radius_info(self):
        server_ips = self._snmp.getall('RADIUS-AUTH-CLIENT-MIB::radiusAuthServerAddress')
        server_ports = self._snmp.getall('RADIUS-AUTH-CLIENT-MIB::radiusAuthClientServerPortNumber')
        return [(x.value, y.value) for x, y in zip(server_ips, server_ports)]

    def vlans(self):
        ret = []
        vlan_ids = [x.value for x in self._snmp.getall('CONFIG-MIB::hpSwitchIgmpVlanIndex')]
        for vlan_id in vlan_ids:
            vlan_name = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(vlan_id)).value
            ret.append((int(vlan_id), vlan_name))
        return ret

    def vlan_create(self, id, name):
        # cshould we heck if vlans exists?#
        try:
            self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticRowStatus.{}'.format(id), 4)  # create and go
        except EasySNMPError:
            # log the VLAN already exists
            pass
        self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(id), name)  # set name
        self._portlist_dirty = True

    def vlan_remove(self, id):
        self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticRowStatus.{}'.format(id), 6)  # destroy
        self._portlist_dirty = True

    def vlan_rename(self, id, name):
        self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(id), name)  # set name
        self._portlist_dirty = True

    def port_auth_enabled(self):
        return int(self._snmp.get('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0').value) == 1

    def set_port_auth_enabled(self, enable):
        if enable:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 1)
        else:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 2)

    def get_ports(self):
        if self._portlist_dirty:
            self._portlist = [SNMP_IFPort(idx.value, self._snmp) for idx in self._snmp.getall('.1.3.6.1.2.1.2.2.1.1')]
            self._portlist_dirty = False
        return self._portlist

    def get_port(self, idx):
        if self._portlist_dirty:
            self.get_ports()
        for port in self._portlist:
            if port.idx() == idx:
                return port
        return None
