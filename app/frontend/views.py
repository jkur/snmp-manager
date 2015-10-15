# coding: utf-8

from flask import render_template, abort, current_app, redirect, url_for, request, flash, Blueprint

mod = Blueprint('views', __name__,
                template_folder='templates')

@mod.route("/", methods=['GET'])
def index():
    return render_template('index.html')
