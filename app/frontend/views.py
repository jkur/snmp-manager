# coding: utf-8

from flask import render_template, Blueprint, request, redirect

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
        for key, value in request.form.items():
            if key.startswith('port-auth-'):
                idx = int(key.split('-')[-1])
                # port_auth_enabled = bool(value)
                # port = device.get_port(idx)
                # if port.has_port_auth() and not port_auth_enabled:
                #     port.set_port_auth(False)
                # if not port.has_port_auth() and port_auth_enabled:
                #     port.set_port_auth(True)
        redirect("/switch/{}".format(hostname))
    return render_template('detail.html', device=device)
