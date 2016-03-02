# coding: utf-8


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
        # self._refresh()

    def _refresh(self):

        # IF-MIB::ifIndex
        ifidx = [int(x.value) for x in self._snmp.getall('1.3.6.1.2.1.2.2.1.1')]
        # IF-MIB::ifType
        iftype = [int(x.value) for x in self._snmp.getall('1.3.6.1.2.1.2.2.1.3')]

        # liste aller trunks (idx)
        if_trunk = [x[0] for x in zip(ifidx, iftype) if x[1] == 54 or x[1] == 161]
        # liste der echten ports (idx) ethernet
        if_ether = [x[0] for x in zip(ifidx, iftype) if x[1] == 6]

        # remove trunk interfaces from list of ethnernet interfaces
        if_trunk_members = []
        if_interfaces = []
        for idx in if_ether:
            # CONFIG-MIB::hpSwitchPortTrunkGroup
            t = int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.8.{}'.format(idx)).value)
            if t > 0:
                if_trunk_members.append((idx, t))
            else:
                if_interfaces.append(idx)

        # now we can create the IFPort
        self._ports = [SNMP_IFPort(idx, self._snmp, self) for idx in if_interfaces]

        # now create TrunkPorts
        # group by trunk_group
        trunks = {}
        for idx, trunkgroup in if_trunk_members:
            if trunkgroup in trunks:
                trunks[int(trunkgroup)].append(idx)
            else:
                trunks.update({int(trunkgroup): [idx]})

        trunkports = [SNMP_TrunkPort(idx, self._snmp, self, tm) for tm, idx in zip(list(trunks.values()), if_trunk)]
        print ("DEBUG: Found trunks: ", len(trunkports))
        self._ports += trunkports
        self._ports_dirty = False

    def update(self):
        self._refresh()

    def port(self, idx):
        if self._ports is None or len(self._ports) == 0:
            self._refresh()
        for port in self._ports:
            if port.idx() == idx:
                return port
        raise IndexError

    def __repr__(self):
        return str(self._ports)

    def __len__(self):
        if self._ports is None:
            self._refresh()
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


class SNMP_IFPort(object):
    def __init__(self, idx, snmp_service, device=None):
        self._snmp = snmp_service
        self._portidx = int(idx)
        self._portalias = ''
        self._portdescr = ''
        self._porttype = 0
        self._portstatus = 2  # down=2, up=1
        self._device = device
        self._trunk_group = 0
        self._dirty_flag = True
        self._get_port_info()

    def _get_port_info(self):
        if self._dirty_flag:
            # IF-MIB::ifDescr
            self._portdescr = self._snmp.get('.1.3.6.1.2.1.2.2.1.2.{}'.format(self._portidx)).value
            # IF-MIB::ifType
            self._porttype = int(self._snmp.get('1.3.6.1.2.1.2.2.1.3.{}'.format(self._portidx)).value)
            # IF-MIB::ifOperStatus
            self._portstatus = int(self._snmp.get('.1.3.6.1.2.1.2.2.1.8.{}'.format(self._portidx)).value)
            # IF-MIB::ifAlias
            self._portalias = self._snmp.get('1.3.6.1.2.1.31.1.1.1.18.{}'.format(self._portidx)).value
        # check if we are part of some trunk
        try:
            # CONFIG-MIB::hpSwitchPortTrunkGroup
            self._trunk_group = int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.8.{}'.format(self._portidx)).value)
        except:
            pass
        # max(CONFIG-MIB::hpSwitchPortTrunkGroup)
        # first propMultiplexor(54) or ieee8023adLag(161)

    def parent_device(self):
        return self._device
        
    def vlan_member(self):
        if self.is_interface():
            return self._device.get_port_membership(self._portidx)
        return None

    def descr(self):
        return self._portdescr

    def alias(self):
        return self._portalias

    def alias_or_descr(self):
        ret = self._portalias
        if not len(ret):
            ret = self._portdescr
        return ret

    def set_alias(self, alias):
        self._snmp.set('IF-MIB:ifAlias.{}'.format(self._portidx), str(alias))

    def is_up(self):
        return self._portstatus == 1

    def is_vlan(self):
        return self._porttype == 53  # propvirtual

    def is_interface(self):
        # IF-MIB::ifAdminStatus
        if int(self._snmp.get('1.3.6.1.2.1.2.2.1.7.{}'.format(self._portidx)).value) != 1:
            return False
        return self._porttype == 6   # ethernetCsmacd

    def is_loopback(self):
        return self._porttype == 24   # ethernetCsmacd

    def is_part_of(self):
        return self._trunk_group

    def is_part_of_trunk(self):
        if self._trunk_group > 0:
            pass

    def is_part_of_lacp(self):
        if self._trunk_group > 0:
            pass

    def is_trunk(self):
        return self._porttype == 54  # propMultiplexor

    def is_lacp(self):
        return self._porttype == 161  # ieee8023adLag

    def idx(self):
        return self._portidx

    def has_port_auth(self):
        # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth
        try:
            result = self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1.{}'.format(self._portidx))
            return int(result.value) == 1
        except:
            return False

    def unauth_vid(self):
        if self.has_port_auth():
            return self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid.{}'.format(self._portidx)).value
        else:
            return -1

    def auth_vid(self):
        if self.has_port_auth():
            return self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid.{}'.format(self._portidx)).value
        else:
            return -1

    def set_port_auth(self, active, auth_vlan=None, unauth_vlan=None):
        if active:
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth
            # 1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx), 1)
            if unauth_vlan is not None:
                # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid
                # 1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.2
                self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid.{}'.format(self._portidx), unauth_vlan)
            if auth_vlan is not None:
                # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid
                # 1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.1
                self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid.{}'.format(self._portidx), auth_vlan)
        else:
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx), 2)

    def port_access_info(self):
        ret = dict(
            enabled=self.has_port_auth(),
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid
            auth_vlan=int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.1.{}'.format(self._portidx)).value),
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid
            unauth_vlan=int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.2.{}'.format(self._portidx)).value)
            )
        return ret

    def get_auth_info(self):
        # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionStatsEntry
        auth_info = []
        auth_info += self._snmp.getall('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionVid.{}'.format(self._portidx))
        auth_info += self._snmp.getall('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionUserName.{}'.format(self._portidx))
        auth_info += self._snmp.getall('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionTime.{}'.format(self._portidx))
        auth_info += self._snmp.getall('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionAuthenticMethod.{}'.format(self._portidx))
        auth_info += self._snmp.getall('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthSessionId.{}'.format(self._portidx))
        return auth_info

    def get_macs(self):
        # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xSMAuthMacAddr.32. for auth ports
        allmacs = self._snmp.getall('1.3.6.1.2.1.17.4.3.1.2')
        mac_on_port = []
        for mac in allmacs:
            if int(mac.value) == self._portidx:
                oid = '1.3.6.1.2.1.17.4.3.1.1.'+mac.oid_index
                hexstring = ':'.join(["%02X" % ord(x) for x in self._snmp.get(oid).value]).strip().upper()
                mac_on_port.append(hexstring)
        return mac_on_port


class SNMP_TrunkPort(SNMP_IFPort):
    def __init__(self, idx, snmp_service, device=None, members=[]):
        self._members = [SNMP_IFPort(x, snmp_service, device) for x in members]
        super().__init__(idx, snmp_service, device)

    def members(self):
        return self._members
