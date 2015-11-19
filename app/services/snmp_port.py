# coding: utf-8


class SNMP_IFPort():
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
        #try:
        #    CONFIG-MIB::hpSwitchPortTrunkGroup
        #    self._trunk_group = int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.8.{}'.format(self._portidx)).value)
        #except:
        #    pass
        # max(CONFIG-MIB::hpSwitchPortTrunkGroup)
        # first propMultiplexor(54) or ieee8023adLag(161)

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
        return int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1.{}'.format(self._portidx)).value) == 1

    def set_port_auth(self, active, auth_vlan=None, unauth_vlan=None):
        if unauth_vlan is not None:
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid
            self._snmp.set('1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.2.{}'.format(self._portidx), unauth_vlan)
        if auth_vlan is not None:
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid
            self._snmp.set('1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.1.{}'.format(self._portidx), auth_vlan)
        if active:
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth
            self._snmp.set('1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1.{}'.format(self._portidx), 1)
        else:
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth
            self._snmp.set('1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1.{}'.format(self._portidx), 2)

    def port_access_info(self):
        ret = dict(
            enabled=self.has_port_auth(),
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid
            auth_vlan=int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.1.{}'.format(self._portidx)).value),
            # HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid
            unauth_vlan=int(self._snmp.get('1.3.6.1.4.1.11.2.14.11.5.1.25.1.2.1.1.2.{}'.format(self._portidx)).value)
            )
        return ret
