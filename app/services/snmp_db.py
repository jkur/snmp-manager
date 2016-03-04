from flask import abort
from .snmp_device import SNMP_Device


class SwitchDB():
    _switches = {}

    def __init__(self):
        pass

    def init_app(self, app):
        # if self._initialized: return
        self._switches = {}
        if 'SWITCHES' in app.config:
            for switchname, values in app.config['SWITCHES'].items():
                self._switches.update({switchname: SNMP_Device(switchname, **values)})

    def get(self, name):
        return self._switches[name]

    def get_or_404(self, name):
        try:
            s = self._switches[name]
            return s
        except KeyError:
            abort(404)

    def all(self):
        ret = []
        for k, v in self._switches.items():
            ret.append(v)
        return ret

    def global_search_mac(self, mac):
        result = []
        devices = self.all()
        for device in devices:
            result.append(device.find_mac(mac))
        if len(result):
            return [item for sublist in result for item in sublist]
        else:
            return None

    def global_search_vlan(self, vlanid):
        result = []
        devices = self.all()
        for device in devices:
            result.append(device.find_ports_with_vlan(vlanid))
        if len(result):
            #return [item for sublist in result for item in sublist]
            return result
        else:
            return None

    def global_search_byhostname(self, hostname):
        # LLDP INFO is here .1.0.8802.1.1.2.1.4.1.1.9.0
        result = []
        devices = self.all()
        for device in devices:
            result.append(device.find_connected_host(hostname))
        if len(result):
            return result
        else:
            return None
