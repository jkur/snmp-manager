# SNMP-Manager
## Small Web Frontend for simple tasks on switch management.


This application can talk to switches (mainly HP ProCurve) via SNMP (v2,v3) and configure switch behaviour like VLAN, radius auth, port access control (802.1x).

## Motivation

Configuring HP ProCurve switches in a small business environment is done usually by invoking the ssh, connecting to each switch and running commands via command line (CLI) or the menu.

Having a good overview about configured VLANS, ports, port aliases, etc. might be useful if you have more then 2 or 3 switches around.

Your setup may be on the other too small for the expensive ProCurve Manager software. Or even better you like the idea of free software.


Then the snmp-manager might be a good base for your own management system.

## Features
 * Easy configurable through settings.cfg
 * Create, rename, destroy VLANs
 * Enable port-auth on switch and configure ports to use 802.1x
 * Have switch information (like firmware revision or model) readily available on overview page
 * See connected (up) or unused ports (down)

## Install
```shell
git clone https://github.com/jkur/snmp-manager.git
cd snmp-manager
virtualenv -p /usr/bin/python3 env
env/bin/pip install -r requirements.txt
env/bin/python wsgi.py
```


## Technology used
 * snmp-manager is developed with Python3.x (needed for easysnmp)
 * It uses easysnmp for SNMP handling. 
 * The web application part is based on Flask.

