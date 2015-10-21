# coding: utf-8

from flask import render_template, Blueprint

from app.services import switch_db as db

mod = Blueprint('views', __name__,
                template_folder='templates')


@mod.route("/", methods=['GET'])
def index():
    devices = db.all()
    return render_template('index.html', devices=devices)

@mod.route("/switch/<hostname>", methods=['GET'])
def detail(hostname):
    device = db.get_or_404(hostname)
    return render_template('detail.html', device=device)
