from .snmp_port import SNMP_IFPort
from app.services import SNMP_Service


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

    def vlans(self):
        interfaces = self._snmp.getall('IF-MIB::ifIndex')
        for interface in interfaces:
            if int(self._snmp.get('IF-MIB::ifType.{}'.format(interface.value)).value) == 53:
                pass

        vlan_ids = self._snmp.getall('Q-BRIDGE-MIB::dot1qVlanStaticRowStatus')
        ret = {}
        for vlan_id in vlan_ids:
            vlan_name = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(vlan_id.value)).value
            ret[vlan_id.value] = vlan_name
        return ret

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
