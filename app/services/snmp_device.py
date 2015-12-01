from .snmp_port import SNMP_Portlist
from .snmp_vlan import SNMP_Vlanlist
from app.services import SNMP_Service


class SNMP_Entity_List(object):
    # make this the super class for portlist and vlanlist
    pass


class SNMP_Device():
    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        self._snmp = SNMP_Service(self.hostname, **kwargs)
        self._vlan = SNMP_Vlanlist(self._snmp)
        self._ports = SNMP_Portlist(self._snmp)

    def get_sysdescr(self):
        return self._snmp.sys_descr().value

    def get_number_ports(self):
        return len(self._ports)

    def model(self):
        return self._snmp.getfirst('ENTITY-MIB::entPhysicalModelName.1').value

    def firmware(self):
        return self._snmp.getfirst('ENTITY-MIB::entPhysicalSoftwareRev.1').value

    def radius_info(self):
        server_ips = self._snmp.getall('RADIUS-AUTH-CLIENT-MIB::radiusAuthServerAddress')
        server_ports = self._snmp.getall('RADIUS-AUTH-CLIENT-MIB::radiusAuthClientServerPortNumber')
        return [(x.value, y.value) for x, y in zip(server_ips, server_ports)]

    def vlans(self):
        return self._vlan

    def ports(self):
        return self._ports

    def vlan_create(self, id, name):
        self._vlan.vlan_create(id, name)

    def vlan_remove(self, id):
        self._vlan.vlan_remove(id)

    def vlan_rename(self, id, name):
        self._vlan.vlan_rename(id, name)

    def get_port_membership(self, portidx):
        return self._vlan.get_port_membership(portidx)

    def get_membership_per_vlan(self, portidx, vlan_id):
        return self._vlan.get_membership_per_vlan(portidx, vlan_id)

    def port_auth_enabled(self):
        return int(self._snmp.get('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0').value) == 1

    def set_port_auth_enabled(self, enable):
        if enable:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 1)
        else:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 2)

    def get_ports(self):
        return self._ports

    def get_auth_users_and_port(self):
        auth_list = self._snmp.getall('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionUserName')
        ret = []
        for entry in auth_list:
            user = entry.value
            port = int(entry.oid_index.split('.')[0])
            ret.append((user, port))
        # print (auth_list)
        return ret

    def get_interfaces(self):
        return [x for x in self._ports if x.is_interface()]

    def get_vlan(self, vlan_id):
        return self._vlan.get_vlan(vlan_id)

    def get_port(self, idx):
        return self._ports.port(idx)
