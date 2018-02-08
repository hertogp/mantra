# -*- encoding: utf8 -*-
import logging
import dash
from flask import send_from_directory
from config import CONFIG

# pylint disable: E265
app = dash.Dash('__MANTRA__')
app.config['suppress_callback_exceptions'] = True
app.title = 'Mantra'

# - LOGGING
logger = logging.getLogger(app.title)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('{}.log'.format(app.title))
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# available also: %(filename)s, %(lineno)
msgfmt = '%(asctime)s %(name)-20s %(levelname)-8s %(funcName)10s: %(message)s'
datefmt = '%Y%m%d %H:%m:%S'
formatter = logging.Formatter(fmt=msgfmt, datefmt=datefmt)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
logger.debug('app logger created')
logger.debug('dir(app)=%s', dir(app))


def getlogger(name):
    return logging.getLogger('{}.{}'.format(app.title, name))

app.getlogger = getlogger


# - STATIC ROUTES
@app.server.route('/static/<path:path>')
def serve_static(path):
    # root-dir is <some-path>/static
    return send_from_directory(CONFIG['static'], path)


@app.server.route('/favicon.ico')
def serve_favicon():
    # the browser does GET /favicon.ico
    # - favicon: png, gif or ico; 15x16 or 32x32; 8- or 24-bit colors
    return send_from_directory(CONFIG['static'], CONFIG['favicon'])
