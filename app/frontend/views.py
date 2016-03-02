# coding: utf-8

from flask import render_template, Blueprint, request, redirect, url_for, flash

from app.services import switch_db as db
import re


mod = Blueprint('views', __name__,
                template_folder='templates')


@mod.route("/", methods=['GET'])
def index():
    devices = db.all()
    return render_template('index.html', devices=devices)


@mod.route("/switch/<hostname>", methods=['GET', 'POST'])
def detail(hostname):
    device = db.get_or_404(hostname)
    device.ports().update()
    if request.method == 'POST':
        if request.form.get('802.1x-enabled', False):
            value = request.form.get('802.1x-enabled')
            setauth = True if value == "1" else False
            print ("setting port auth", setauth)
            device.set_port_auth_enabled(setauth)
        for key, value in request.form.items():
            if key.startswith('port-auth-'):
                idx = int(key.split('-')[-1])
                port_auth_enabled = True if value == "true" else False
                port = device.ports().port(idx)
                port.set_port_auth(port_auth_enabled)
                if port.has_port_auth() and not port_auth_enabled:
                    port.set_port_auth(False)
                    print("Set port {} to NOAUTH".format(port.idx()))
                if not port.has_port_auth() and port_auth_enabled:
                    port.set_port_auth(True)
                    print("Set port {} to AUTH".format(port.idx()))
        return redirect("/switch/{}".format(hostname))
    return render_template('detail.html', device=device)


@mod.route("/switch/<hostname>/vlan/<id>/edit", methods=['POST'])
def vlan_edit(hostname, id):
    device = db.get_or_404(hostname)
    if request.method == "POST":
        vlan_id = request.form.get('VLAN_ID_TO_RENAME', None)
        vlan_name = request.form.get('VLAN_NEW_NAME', None)
        if vlan_id == id and vlan_name:
            try:
                device.vlan_rename(int(vlan_id), vlan_name)
            except:
                flash("rename failed")
    return redirect(url_for('.detail', hostname=hostname))


@mod.route("/switch/<hostname>/vlan/<id>/delete", methods=['POST'])
def vlan_delete(hostname, id):
    device = db.get_or_404(hostname)
    if request.method == "POST":
        vlan_id = request.form.get('VLAN_ID_TO_REMOVE', None)
        if vlan_id == id:
            try:
                device.vlan_remove(vlan_id)
            except:
                flash("remove failed")
    return redirect(url_for('.detail', hostname=hostname))


@mod.route("/switch/<hostname>/vlan/create", methods=['POST'])
def vlan_create(hostname):
    device = db.get_or_404(hostname)
    if request.method == "POST":
        vlan_name = request.form.get('VLAN_NAME', None)
        vlan_id = request.form.get('VLAN_ID', None)
        if vlan_name and vlan_id:
            try:
                device.vlan_create(vlan_id, vlan_name)
            except:
                flash("Failed to add VLAN")
        else:
            flash("Wrong input")
    return redirect(url_for('.detail', hostname=hostname))


@mod.route("/vlan/all/vlan/create", methods=['POST'])
def vlan_create_all():
    if request.method == 'POST':
        devices = db.all()
        vlan_name = request.form.get('VLAN_NAME', None)
        vlan_id = request.form.get('VLAN_ID', None)
        for device in devices:
            try:
                device.vlan_create(vlan_id, vlan_name)
            except:
                flash("Failed to create vlan {} on {}".format(vlan_id, device.hostname()))
        return redirect(url_for('.index'))


@mod.route("/vlan/all/vlan/delete", methods=['POST'])
def vlan_remove_all():
    if request.method == 'POST':
        devices = db.all()
        vlan_id = request.form.get('VLAN_ID', None)
        for device in devices:
            try:
                device.vlan_remove(vlan_id)
            except:
                flash("Failed to remove vlan {} on {}".format(vlan_id, device.hostname))
        return redirect(url_for('.index'))


@mod.route("/vlan/<hostname>")
def vlan_member(hostname):
    device = db.get_or_404(hostname)
    interfaces = device.get_interfaces()
    vlans = device.vlans()
    return render_template('vlan.html', hostname=hostname, device=device, vlans=vlans, interfaces=interfaces)


@mod.route("/vlan/<hostname>/savetable", methods=["POST"])
def vlan_member_save(hostname):
    if request.method == 'POST':
        device = db.get_or_404(hostname)
        # sanity checks
        # len(form) == num_of_ports * num_of_vids
        interfaces = device.get_interfaces()
        vlans = device.vlans()
        num_of_vids = len(vlans)
        num_of_ports = len(vlans)
    return redirect(url_for('.vlan_member', hostname=hostname))


@mod.route("/port/<hostname>/<int:idx>", methods=["GET"])
def port_detail(hostname, idx):
    device = db.get_or_404(hostname)
    vlans = device.vlans()
    port = device.get_port(idx)
    vlan_membership = vlans.get_port_membership(idx)
    return render_template('port.html', hostname=hostname, device=device, vlans=vlans, port=port, vlan_membership=vlan_membership)


@mod.route("/port/<hostname>/<int:idx>/save", methods=["POST"])
def port_save(hostname, idx):
    device = db.get_or_404(hostname)
    port = device.get_port(idx)
    if request.method == 'POST':
        auth_vid = request.form.get('AUTHVID', None)
        unauth_vid = request.form.get('UNAUTHVID', None)
        port_auth = True if request.form.get('802.1x-enabled', 2) == '1' else False
        port.set_port_auth(port_auth, auth_vid, unauth_vid)
        # set alias
        if request.form.get('ifalias', None) is not None:
            port.set_alias(request.form.get('ifalias', None))
        flash("Port Auth saved")
    return redirect(url_for('.port_detail', hostname=hostname, idx=idx))


@mod.route("/search/mac/", methods=["GET", "POST"])
def search_mac():
    result = None
    device = None
    mac = '00:00:00:00:00:00'
    if request.method == 'POST':
        mac = request.form.get('mac', None)
        if mac is not None:
            # validate input
            if not re.match('([A-F0-9]{2}:){5}[A-F0-9]{2}', mac.upper()):
                flash("Bad Mac Address")
            else:
                result = db.global_search_mac2(mac)
                if result is None:
                    flash("Mac ({0}) not found".format({'mac': mac}))
    return render_template('search_mac.html', result=result, mac=mac, device=device)

@mod.route("/auth", methods=["GET"])
def auth_index():
    devices = db.all()
    auth_info = {}
    for device in devices:
        users_and_port = device.get_auth_users_and_port()
        auth_info.update({device.hostname: users_and_port})
    return render_template('auth.html', devices=devices, auth_info=auth_info)
