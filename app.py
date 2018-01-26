# -*- encoding: utf8 -*-
import os
import dash
from flask import send_from_directory
from config import CONFIG

# pylint disable: E265
app = dash.Dash('__MANTRA__')
app.config['suppress_callback_exceptions'] = True
app.title = 'Mantra'
# app.css.config.serve_locally = True


@app.server.route('/static/<path:path>')
def serve_static(path):
    # root-dir is <some-path>/static
    return send_from_directory(CONFIG['static'], path)


@app.server.route('/favicon.ico')
def serve_favicon():
    # the browser does GET /favicon.ico
    # - favicon: png, gif or ico; 15x16 or 32x32; 8- or 24-bit colors
    return send_from_directory(CONFIG['static'], CONFIG['favicon'])
