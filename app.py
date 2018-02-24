# -*- encoding: utf8 -*-
import dash
from flask import send_from_directory
from log import getlogger, TITLE
from config import cfg

# pylint disable: E265
app = dash.Dash('__MANTRA__')
app.config['suppress_callback_exceptions'] = True
app.title = TITLE
log = getlogger(__name__)
log.debug('setting up static routes')

# - STATIC ROUTES
@app.server.route('/static/<path:path>')
def serve_static(path):
    # root-dir is <some-path>/static
    # log.debug(path)
    return send_from_directory(cfg.static, path)


@app.server.route('/favicon.ico')
def serve_favicon():
    # the browser does GET /favicon.ico
    # - favicon: png, gif or ico; 15x16 or 32x32; 8- or 24-bit colors
    log.debug('serving %s', cfg.favicon)
    return send_from_directory(cfg.static, cfg.favicon)
