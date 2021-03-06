from .snmp_port import SNMP_Portlist, SNMP_IFPort
from .snmp_vlan import SNMP_Vlanlist
from app.services import SNMP_Service
from .snmp_vlan import Hex_Array
import re

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

    def find_mac(self, macstring):
        allmacs = self._snmp.getall('1.3.6.1.2.1.17.4.3.1.2')
        mac_on_port = []
        for mac in allmacs:
            oid = '1.3.6.1.2.1.17.4.3.1.1.'+mac.oid_index
            hexstring = ':'.join(["%02X" % ord(x) for x in self._snmp.get(oid).value]).strip().upper()
            if macstring.upper() == hexstring:
                mac_on_port.append((self.hostname, SNMP_IFPort(mac.value, self._snmp)))
        return mac_on_port

    def find_ports_with_vlan(self, vlanid):
        snmpresult = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticEgressPorts.'+str(vlanid))
        table = ''.join(["%02X " % ord(x) for x in snmpresult.value]).strip()
        egress = Hex_Array(bytearray.fromhex(table))

        snmpresult = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticUntaggedPorts.'+str(vlanid))
        table = ''.join(["%02X " % ord(x) for x in snmpresult.value]).strip()
        untagged = Hex_Array(bytearray.fromhex(table))

        snmpresult = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanForbiddenEgressPorts.'+str(vlanid))
        table = ''.join(["%02X " % ord(x) for x in snmpresult.value]).strip()
        forbidden = Hex_Array(bytearray.fromhex(table))

        ports_found = {'untagged': [], 'tagged': []}
        for port in range(1, len(self._ports)+1):
            try:
                port = int(port)
            except ValueError:
                continue
            if untagged[port]:
                ports_found['untagged'].append(SNMP_IFPort(port, self._snmp))
            elif forbidden[port]:
                pass
            elif egress[port]:
                ports_found['tagged'].append(SNMP_IFPort(port, self._snmp))
        return (self, ports_found)

    def find_connected_host(self, hostname):
        allhost = self._snmp.getall('.1.0.8802.1.1.2.1.4.1.1.9.0')
        result = []
        for host in allhost:
            if re.match(hostname+'.*', host.value):
                port_idx = host.oid.split('.')[-2]
                result.append({'host': host.value,
                               'port': SNMP_IFPort(port_idx, self._snmp)})
        return (self, result)
