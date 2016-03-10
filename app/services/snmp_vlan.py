# coding: utf-8
import math


# Factory
class SNMP_Vlan():
    @classmethod
    def create(cls, id, snmp_service):
        if id == 1:
            return SNMP_Default_Vlan(id, snmp_service)
        else:
            return SNMP_Vlan_Base(id, snmp_service)


class Hex_Array():
    def __init__(self, array, inverted=False):
        if isinstance(array, str):
            # print("creating hexarray from string")
            hexvalue = ''.join(["%02X" % ord(x) for x in array if x not in ['\n', ' ']]).strip()
            print(hexvalue)
            self._data = bytearray.fromhex(hexvalue)
        elif isinstance(array, bytearray):
            # print("creating hexarray from bytearray")
            self._data = array
        self._inverted = inverted

    def __repr__(self):
        return ''.join(["%02X " % x for x in self._data]).strip()

    def __getitem__(self, idx):
        byte_idx, portvalue = self._read_byte(idx)
        return (self._data[byte_idx] & portvalue) == portvalue

    def __setitem__(self, idx, value):
        byte_idx, portvalue = self._read_byte(idx)
        if self._inverted:
            if not value:
                self._data[byte_idx] = self._data[byte_idx] | portvalue
            else:
                self._data[byte_idx] = self._data[byte_idx] & ~portvalue
            return (self._data[byte_idx] & portvalue) == portvalue
        # regular setting
        else:
            if value:
                self._data[byte_idx] = self._data[byte_idx] | portvalue
            else:
                self._data[byte_idx] = self._data[byte_idx] & ~portvalue
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
        # print("DEBUG: Port {}, byteidx {}, subidx {}, portvalue {}({})".format(portnum, byte_idx, sub_idx, portvalue, hex(portvalue)))
        return int(byte_idx), int(portvalue)


class SNMP_Vlan_Base(object):
    def __init__(self, vlan_id, snmp_service=None):
        self._table_tagged = Hex_Array(bytearray())

        self._table_untagged = Hex_Array(bytearray())

        self._table_forbidden = Hex_Array(bytearray())

        self._dirty = True
        self._snmp = snmp_service
        self._vlan_id = int(vlan_id)
        self._vlan_name = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticName.{}'.format(vlan_id)).value
        self._refresh()

    def _refresh(self):
        # untagged
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticUntaggedPorts.{}'.format(self._vlan_id))
        self._table_untagged = Hex_Array(result.value)

        # tagged
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanStaticEgressPorts.{}'.format(self._vlan_id))
        self._table_tagged = Hex_Array(result.value)

        # forbidden
        result = self._snmp.get('Q-BRIDGE-MIB::dot1qVlanForbiddenEgressPorts.{}'.format(self._vlan_id))
        self._table_forbidden = Hex_Array(result.value)
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
        print ("==== DEBUG ====")
        print("Untagged: ", self._table_untagged)
        print("Tagged:   ", self._table_tagged)
        print("Forbid:   ", self._table_forbidden)
        print ("==== END ====")

    def _write_untagged_default(self):
        # the default vlan is dependent of the other untagged vlan ports
        # we need to wirte this too.
        # BROKEN: untagged_default_vlan = [0xff - (x|y|z) for x, y, z in zip(self._table_untagged [...])
        pass

#    def port_table(self):
#        self._refresh()
#        return (self._table_untagged_raw, self._table_tagged_raw, self._table_forbidden_raw)

    def is_dirty(self):
        return self._dirty

    def dirty(self):
        self._dirty = True

    def clean(self):
        self._dirty = False

    def get_port_status(self, portnum):
        if self._table_untagged[portnum]:
            return ("UNTAGGED", 'u')
        if self._table_forbidden[portnum]:
            return ("FORBIDDEN", 'f')
        if self._table_tagged[portnum]:
            return ("TAGGED", 't')
        return ("NO", '')

    def set_port_status(self, portnum, status_code):
        if status_code == 't':
            self._table_tagged[portnum] = True
            self._table_untagged[portnum] = False
            self._table_forbidden[portnum] = False

            self._snmp.set_multiple([('Q-BRIDGE-MIB::dot1qVlanStaticUntaggedPorts.{}'.format(self._vlan_id), str(self._table_untagged)),
                                     ('Q-BRIDGE-MIB::dot1qVlanStaticForbiddenPorts.{}'.format(self._vlan_id), str(self._table_forbidden)),
                                     ('Q-BRIDGE-MIB::dot1qVlanStaticEgressPorts.{}'.format(self._vlan_id), str(self._table_tagged))])
        else:
            raise Exception("NOT yet implemented")

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
        #if self._vlans is None or self._vlans_dirty:
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
