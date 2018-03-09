# -*- encoding: utf8 -*-
import dash
from flask import send_from_directory
import logging

# App imports
from config import cfg

# pylint disable: E265
app = dash.Dash('__{}__'.format(cfg.app_name.upper()))
app.config['suppress_callback_exceptions'] = True
app.title = cfg.app_name.upper()

log = logging.getLogger(cfg.app_name)
log.debug('setting up static routes')
log.debug('/static/<path> -> %s/<path>', cfg.static)
log.debug('/mantra/<path> -> %s/mantra/<path>', cfg.root)


# - STATIC ROUTES
@app.server.route('/static/<path:path>')
def serve_static(path):
    # root-dir is <some-path>/static
    # log.debug(path)
    return send_from_directory(cfg.static, path)

@app.server.route('/mantra/<path:path>')
def serve_quiz(path):
    if path.lower().endswith('png'):
        return send_from_directory(cfg.root, path)

@app.server.route('/favicon.ico')
def serve_favicon():
    # the browser does GET /favicon.ico
    # - favicon: png, gif or ico; 15x16 or 32x32; 8- or 24-bit colors
    log.debug('serving %s', cfg.favicon)
    return send_from_directory(cfg.static, cfg.favicon)
