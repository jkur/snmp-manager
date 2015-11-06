from .snmp_port import SNMP_IFPort
from app.services import SNMP_Service
from easysnmp import EasySNMPError
import math

class SNMP_Portlist():
    pass


class SNMP_Vlan():
    def __init__(self, vlan_id, snmp_service):
        self._table_tagged = bytearray()
        self._table_untagged = bytearray()
        self._table_forbidden = bytearray()
        self._dirty = True
        self._snmp = snmp_service
        self._vlan_id = vlan_id
        self._vlan_name = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(vlan_id)).value
        self._refresh()

    def _refresh(self):
        # tagged
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticEgressPorts.{}'.format(self._vlan_id))
        table = ''.join(["%02X " % ord(x) for x in result.value]).strip()
        self._table_tagged = bytearray.fromhex(table)

        # untagged
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticUntaggedPorts.{}'.format(self._vlan_id))
        table = ''.join(["%02X " % ord(x) for x in result.value]).strip()
        self._table_untagged = bytearray.fromhex(table)

        # forbidden
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanForbiddenEgressPorts.{}'.format(self._vlan_id))
        table = ''.join(["%02X " % ord(x) for x in result.value]).strip()
        self._table_forbidden = bytearray.fromhex(table)

        #if self._vlan_id == 1:
        #    #print(self._table_tagged.decode("utf-8"))
        #    self._table_tagged = bytearray([0xff - x for x in self._table_tagged])
        #    self._table_untagged = bytearray([0xff - x for x in self._table_untagged])
        self._dirty = False

    def __repr__(self):
        return '{} ({})'.format(self._vlan_name, self._vlan_id)

    def print_tables(self):
        print(self)
        print("Untagged: ", ' '.join(["%02X" % x for x in self._table_untagged]))
        print("Tagged:   ", ' '.join(["%02X" % x for x in self._table_tagged]))
        print("Forbid:   ", ' '.join(["%02X" % x for x in self._table_forbidden]))

    def _write_untagged_default(self):
        # the default vlan is dependent of the other untagged vlan ports
        # we need to wirte this too.
        # BROKEN: untagged_default_vlan = [0xff - (x|y|z) for x, y, z in zip(self._table_untagged [...])
        pass

    def is_dirty(self):
        return self._dirty

    def dirty(self):
        self._dirty = True

    def clean(self):
        self._dirty = False

    def get_tagged(self):
        return self._table_tagged

    def get_untagged(self):
        return self._table_untagged

    def get_forbidden(self):
        return self._table_forbidden

    def _read_byte(self, portnum):
        # byteweise stehen die Port drin
        # pro byte:
        # port  :     1   2   3   4   5   6   7   8
        # subidx:     0   1   2   3   4   5   6   7
        # portvalue: 128 64  32  16   8   4   2   1
        byte_idx = math.floor((portnum-1) / 8)
        sub_idx = (portnum - 1) % 8
        portvalue = 128 >> sub_idx
        print("DEBUG: Port {}, byteidx {}, subidx {}, portvalue {}".format(portnum, byte_idx, sub_idx, portvalue))
        return byte_idx, portvalue

    def get_port_tagged(self, portnum):
        byte_idx, portvalue = self._read_byte(portnum)
        return (self._table_tagged[byte_idx] & portvalue) == portvalue

    def get_port_untagged(self, portnum):
        byte_idx, portvalue = self._read_byte(portnum)
        return (self._table_untagged[byte_idx] & portvalue) == portvalue


class SNMP_Vlanlist():
    def __init__(self, snmp_service):
        self._snmp = snmp_service
        self._vlan = None
        self._vlan_dirty = True
        self.vlans()
        self._vlan_port_assignment = None
        self._refresh_vlan_port_assignment()

    def _refresh_vlan_port_assignment(self):
        self._vlan_port_assignment = []
        for vlan_id, vlan_name in self._vlan:
            self._vlan_port_assignment.append(SNMP_Vlan(vlan_id, self._snmp))

    def vlans(self):
        if self._vlan is None or self._vlan_dirty:
            self._vlan = []
            vlan_ids = [x.value for x in self._snmp.getall('CONFIG-MIB::hpSwitchIgmpVlanIndex')]
            for vlan_id in vlan_ids:
                vlan_name = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(vlan_id)).value
                self._vlan.append((int(vlan_id), vlan_name))
                self._vlan_dirty = False
        return self._vlan

    def get_port_membership(self, portidx):
        ret = []
        for (vlan_id, vlan_name), vlan in zip(self._vlan, self._vlan_port_assignment):
            if vlan.get_port_tagged(portidx):
                ret.append((vlan_id, 't'))
            if vlan.get_port_untagged(portidx):
                ret.append((vlan_id, 'u'))
        return ret

class SNMP_Device():
    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        self._portlist = None
        self._portlist_dirty = True
        self._snmp = SNMP_Service(self.hostname, **kwargs)
        self._vlan = SNMP_Vlanlist(self._snmp)

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
        return self._vlan.vlans()

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

    def get_port_membership(self, portidx):
        return self._vlan.get_port_membership(portidx)

    def get_vlan_ports(self, vlan_id):
        if vlan_id not in self._vlan_port_assignment or self._vlan_port_assignment[vlan_id][1]:
            table = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticEgressPorts.{}'.format(vlan_id))
            table = ''.join(["%02X " % ord(x) for x in table.value]).strip()
            table = bytearray.fromhex(table)
            self._vlan_port_assignment.update({vlan_id: (table, False)})
        return table

    def port_auth_enabled(self):
        return int(self._snmp.get('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0').value) == 1

    def set_port_auth_enabled(self, enable):
        if enable:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 1)
        else:
            self._snmp.set('IEEE8021-PAE-MIB::dot1xPaeSystemAuthControl.0', 2)

    def get_ports(self):
        if self._portlist_dirty:
            self._portlist = [SNMP_IFPort(idx.value, self._snmp, self) for idx in self._snmp.getall('.1.3.6.1.2.1.2.2.1.1')]
            self._portlist_dirty = False
        return self._portlist

    def get_interfaces(self):
        return filter(lambda x: x.is_interface(), self.get_ports())

    def get_port(self, idx):
        if self._portlist_dirty:
            self.get_ports()
        for port in self._portlist:
            if port.idx() == idx:
                return port
        return None
