# coding: utf-8


class SNMP_IFPort():
    def __init__(self, idx, snmp_service):
        self._snmp = snmp_service
        self._portidx = int(idx)
        self._portalias = ''
        self._portdescr = ''
        self._porttype = 0
        self._portstatus = 2  # down=2, up=1
        self._get_port_info()

    def _get_port_info(self):
        self._portdescr = self._snmp.get('.1.3.6.1.2.1.2.2.1.2.{}'.format(self._portidx)).value
        self._porttype = int(self._snmp.get('IF-MIB::ifType.{}'.format(self._portidx)).value)
        self._portstatus = int(self._snmp.get('.1.3.6.1.2.1.2.2.1.8.{}'.format(self._portidx)).value)
        self._portalias = self._snmp.get('IF-MIB::ifAlias.{}'.format(self._portidx)).value

    def descr(self):
        return self._portdescr

    def alias(self):
        return self._portalias

    def is_up(self):
        return self._portstatus == 1

    def is_vlan(self):
        return self._porttype == 53  # propvirtual

    def is_interface(self):
        if int(self._snmp.get('IF-MIB::ifAdminStatus.{}'.format(self._portidx)).value) != 1:
            return False
        return self._porttype == 6   # ethernetCsmacd

    def is_loopback(self):
        return self._porttype == 24   # ethernetCsmacd

    def is_trunk(self):
        return self._porttype == 54  # propMultiplexor

    def idx(self):
        return self._portidx

    def has_port_auth(self):
        return int(self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx)).value) == 1

    def set_port_auth(self, active, auth_vlan=None, unauth_vlan=None):
        if unauth_vlan is not None:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid.{}'.format(self._portidx), unauth_vlan)
        if auth_vlan is not None:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid.{}'.format(self._portidx), auth_vlan)
        if active:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx), 1)
        else:
            self._snmp.set('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xPaePortAuth.{}'.format(self._portidx), 2)

    def port_access_info(self):
        ret = dict(
            enabled=self.has_port_auth(),
            auth_vlan=int(self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthAuthVid.{}'.format(self._portidx)).value),
            unauth_vlan=int(self._snmp.get('HP-DOT1X-EXTENSIONS-MIB::hpicfDot1xAuthUnauthVid.{}'.format(self._portidx)).value)
            )
        return ret
