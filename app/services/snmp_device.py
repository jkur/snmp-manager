from .snmp_port import SNMP_IFPort
from app.services import SNMP_Service
from easysnmp import EasySNMPError
import math


class SNMP_Entity_List(object):
    # make this the super class for portlist and vlanlist
    pass


class SNMP_Portlist():
    def __init__(self, snmp_service):
        self._snmp = snmp_service
        self._ports = None
        self._port_mapping = None
        self._trunks = None
        self._trunks_start = 0
        self._trunks_stop = 0
        self._first_trunk_group = 0
        self._last_trunk_group = 0
        self._ports_dirty = True
        self._refresh()

    def _refresh(self):
        self._ports = []
        # IF-MIB::ifIndex
        ifidx = [int(x.value) for x in self._snmp.getall('1.3.6.1.2.1.2.2.1.1')]
        # IF-MIB::ifType
        iftype = [int(x.value) for x in self._snmp.getall('1.3.6.1.2.1.2.2.1.3')]
        self._trunks = [x for x in zip(ifidx, iftype) if x[1] == 54 or x[1] == 161]
        if len(self._trunks):
            self._trunks_start = min(self._trunks, key=lambda x: x[0])
            self._trunks_stop = max(self._trunks, key=lambda x: x[0])
            # trunk_numbers = filter(lambda x: x > 0, self._snmp.getall('CONFIG-MIB::hpSwitchPortTrunkGroup', filter_by_value=True))
            # CONFIG-MIB::hpSwitchPortTrunkGroup
            trunk_numbers = [int(x.value) for x in self._snmp.getall('1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.8') if int(x.value) > 0]
            self._first_trunk_group = min(trunk_numbers)
            self._last_trunk_group = min(trunk_numbers)

        # self._ports = [SNMP_IFPort(idx.value, self._snmp, self) for idx in self._snmp.getall('.1.3.6.1.2.1.2.2.1.1')]
        self._ports = [SNMP_IFPort(idx, self._snmp, self, iftype=iftype) for (idx, iftype) in zip(ifidx, iftype)]
        self._ports_dirty = False

    def port(self, idx):
        for port in self._ports:
            if port.idx() == idx:
                return port
        raise IndexError

    def trunk(self, idx):
        return self.port(idx + self._trunks_start)

    def __repr__(self):
        return str(self._ports)

    def __len__(self):
        return len(self._ports)

    def __contains__(self, a):
        for port in self._ports:
            if port == a:
                return True
        return False
        # return a in self._vlans

    def __getitem__(self, idx):
        return self._ports[idx]

    def __next__(self):
        if self._iteridx != len(self._ports):
            r = self._ports[self._iteridx]
            self._iteridx += 1
            return r
        else:
            raise StopIteration()

    def __iter__(self):
        self._iteridx = 0
        return self


# Factory
class SNMP_Vlan():
    @classmethod
    def create(cls, id, snmp_service):
        if id == 1:
            return SNMP_Default_Vlan(id, snmp_service)
        else:
            return SNMP_Vlan_Base(id, snmp_service)


class Hex_Array():
    def __init__(self, array):
        if type(array) is bytearray:
            self._data = array

    def __repr__(self):
        return str(self._data)

    def __getitem__(self, idx):
        byte_idx, portvalue = self._read_byte(idx)
        return (self._data[byte_idx] & portvalue) == portvalue

    def __setitem__(self, idx, unset=False):
        byte_idx, portvalue = self._read_byte(idx)
        if unset:
            self._data[byte_idx] = self._data[byte_idx] & ~portvalue
            return (self._data[byte_idx] & portvalue) == portvalue
        else:
            self._data[byte_idx] = self._data[byte_idx] | portvalue
            return (self._data[byte_idx] & portvalue) == portvalue

    def _read_byte(self, portnum):
        # byteweise stehen die Port drin
        # pro byte:
        # port  :     1   2   3   4   5   6   7   8
        # subidx:     0   1   2   3   4   5   6   7
        # portvalue: 128 64  32  16   8   4   2   1
        byte_idx = math.floor((portnum-1) / 8)
        sub_idx = (portnum - 1) % 8
        portvalue = 128 >> sub_idx
        #print("DEBUG: Port {}, byteidx {}, subidx {}, portvalue {}({})".format(portnum, byte_idx, sub_idx, portvalue, hex(portvalue)))
        return byte_idx, portvalue


class SNMP_Vlan_Base(object):
    def __init__(self, vlan_id, snmp_service=None):
        self._table_tagged = Hex_Array(bytearray())
        self._table_tagged_raw = None

        self._table_untagged = Hex_Array(bytearray())
        self._table_untagged_raw = None

        self._table_forbidden = Hex_Array(bytearray())
        self._table_forbidden_raw = None

        self._dirty = True
        self._snmp = snmp_service
        self._vlan_id = int(vlan_id)
        self._vlan_name = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(vlan_id)).value
        self._refresh()

    def _refresh(self):
        # untagged
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticUntaggedPorts.{}'.format(self._vlan_id))
        table = ''.join(["%02X " % ord(x) for x in result.value]).strip()
        self._table_untagged_raw = bytearray.fromhex(table)
        self._table_untagged = Hex_Array(bytearray.fromhex(table))

        # tagged
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticEgressPorts.{}'.format(self._vlan_id))
        table = ''.join(["%02X " % ord(x) for x in result.value]).strip()
        self._table_tagged_raw = bytearray.fromhex(table)
        self._table_tagged = Hex_Array(bytearray.fromhex(table))

        # forbidden
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanForbiddenEgressPorts.{}'.format(self._vlan_id))
        table = ''.join(["%02X " % ord(x) for x in result.value]).strip()
        self._table_forbidden_raw = bytearray.fromhex(table)
        self._table_forbidden = Hex_Array(bytearray.fromhex(table))
        self._dirty = False

    def __repr__(self):
        return '{} ({})'.format(self._vlan_name, self._vlan_id)

    def __lt__(self, other):
        if type(other) is int:
            return self._vlan_id < other
        if isinstance(other, SNMP_Vlan_Base):
            return self._vlan_id < other._vlan_id
        return False

    def __eq__(self, other):
        if type(other) is int:
            return self._vlan_id == other
        if type(other) is tuple:
            return other == (self._vlan_id, self._vlan_name)
        if isinstance(other, SNMP_Vlan_Base):
            return self._vlan_id == other._vlan_id
        return False

    def name(self):
        return self._vlan_name

    def vid(self):
        return self._vlan_id

    def print_tables(self):
        print(self)
        print("Untagged: ", ' '.join(["%02X" % x for x in self._table_untagged._data]))
        print("Tagged:   ", ' '.join(["%02X" % x for x in self._table_tagged._data]))
        print("Forbid:   ", ' '.join(["%02X" % x for x in self._table_forbidden._data]))

    def _write_untagged_default(self):
        # the default vlan is dependent of the other untagged vlan ports
        # we need to wirte this too.
        # BROKEN: untagged_default_vlan = [0xff - (x|y|z) for x, y, z in zip(self._table_untagged [...])
        pass

    def port_table(self):
        self._refresh()
        return (self._table_untagged_raw, self._table_tagged_raw, self._table_forbidden_raw)

    def is_dirty(self):
        return self._dirty

    def dirty(self):
        self._dirty = True

    def clean(self):
        self._dirty = False

    def is_tagged(self, portnum):
        if self._table_untagged[portnum]:
            return False
        return self._table_tagged[portnum]

    def is_forbidden(self, portnum):
        if self._table_untagged[portnum]:
            return False
        return self._table_forbidden[portnum]

    def is_untagged(self, portnum):
        return self._table_untagged[portnum]


class SNMP_Default_Vlan(SNMP_Vlan_Base):
    def __init__(self, id, snmp_service):
        super().__init__(id, snmp_service)

    def is_tagged(self, portnum):
        if self._table_untagged[portnum]:
            return False
        return self._table_tagged[portnum]

    def is_untagged(self, portnum):
        return self._table_untagged[portnum]


class SNMP_Vlanlist():
    def __init__(self, snmp_service):
        self._snmp = snmp_service
        self._vlans = None
        self._vlans_dirty = True
        self._refresh()

    def _refresh(self):
        self._vlans = []
        vlan_ids = [x.value for x in self._snmp.getall('CONFIG-MIB::hpSwitchIgmpVlanIndex')]
        for vlan_id in vlan_ids:
            self._vlans.append(SNMP_Vlan.create(vlan_id, self._snmp))
        self._vlans_dirty = False

    def __repr__(self):
        return str(self._vlans)

    def __len__(self):
        return len(self._vlans)

    def __contains__(self, a):
        for vlan in self._vlans:
            if vlan == a:
                return True
        return False
        # return a in self._vlans

    def __getitem__(self, idx):
        return self._vlans[idx]

    def __next__(self):
        if self._iteridx != len(self._vlans):
            r = self._vlans[self._iteridx]
            self._iteridx += 1
            return r
        else:
            raise StopIteration()

    def __iter__(self):
        self._iteridx = 0
        return self

    def get_port_membership(self, portidx):
        if self._vlans is None or self._vlans_dirty:
            self._refresh()
        ret = []
        for vlan in self._vlans:
            if vlan.is_forbidden(portidx):
                ret.append((vlan.vid(), 'f'))
            if vlan.is_untagged(portidx):
                ret.append((vlan.vid(), 'u'))
            if vlan.is_tagged(portidx):
                ret.append((vlan.vid(), 't'))
        return ret

    def get_vlan(self, vlan_id):
        for vlan in self._vlans:
            if vlan_id == vlan:
                return vlan
        return None

    def get_membership_per_vlan(self, portidx, vlan_id):
        if self._vlan is None or self._vlan_dirty:
            self._refresh()
        vlan = self._get_vlan(vlan_id)
        if vlan.get_port_forbidden(portidx):
            return 'f'
        if vlan.get_port_untagged(portidx):
            return 'u'
        if vlan.get_port_tagged(portidx):
            return 't'
        return 'n'

    def vlan_create(self, id, name):
        # cshould we heck if vlans exists?#
        try:
            self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticRowStatus.{}'.format(id), 4)  # create and go
        except EasySNMPError:
            # log the VLAN already exists
            pass
        self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(id), name)  # set name
        self._vlan_dirty = True
        self._refresh()

    def vlan_remove(self, id):
        try:
            self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticRowStatus.{}'.format(id), 6)  # destroy
        except:
            print("Could not remove VLAN", id)
        self._vlan_dirty = True
        self._refresh()

    def vlan_rename(self, id, name):
        self._snmp.set('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(id), name)  # set name
        self._vlan_dirty = True
        self._refresh()


class SNMP_Device():
    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        self._portlist = None
        self._portlist_dirty = True
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
        self._portlist_dirty = True

    def vlan_remove(self, id):
        self._vlan.vlan_remove(id)
        self._portlist_dirty = True

    def vlan_rename(self, id, name):
        self._vlan.vlan_rename(id, name)
        self._portlist_dirty = True

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
        if self._portlist_dirty:
            self._portlist = [SNMP_IFPort(idx.value, self._snmp, self) for idx in self._snmp.getall('.1.3.6.1.2.1.2.2.1.1')]
            self._portlist_dirty = False
        return self._portlist

    def get_interfaces(self):
        return filter(lambda x: x.is_interface() or x.is_trunk(), self.get_ports())

    def get_vlan(self, vlan_id):
        return self._vlan.get_vlan(vlan_id)

    def get_port(self, idx):
        if self._portlist_dirty:
            self.get_ports()
        for port in self._portlist:
            if port.idx() == idx:
                return port
        return None
