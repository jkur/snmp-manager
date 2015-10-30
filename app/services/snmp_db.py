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
