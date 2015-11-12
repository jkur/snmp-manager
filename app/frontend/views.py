# coding: utf-8

from flask import render_template, Blueprint, request, redirect, url_for, flash

from app.services import switch_db as db

mod = Blueprint('views', __name__,
                template_folder='templates')


@mod.route("/", methods=['GET'])
def index():
    devices = db.all()
    return render_template('index.html', devices=devices)


@mod.route("/switch/<hostname>", methods=['GET', 'POST'])
def detail(hostname):
    device = db.get_or_404(hostname)
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
                port = device.get_port(idx)
                if port.has_port_auth() and not port_auth_enabled:
                    port.set_port_auth(False)
                    print("Set port {} to NOAUTH".format(port.idx()))
                if not port.has_port_auth() and port_auth_enabled:
                    port.set_port_auth(True)
                    print("Set port {} to AUTH".format(port.idx()))
        redirect("/switch/{}".format(hostname))
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
    return render_template('vlan.html', device=device, vlans=vlans, interfaces=interfaces)
