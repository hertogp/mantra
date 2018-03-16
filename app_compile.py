# -*- encoding: utf8 -*-
'''
Mantra - compile-a-test page
'''

import os
import json
import time
import threading
import logging
import dash_html_components as html
import dash_core_components as dcc
import dash.dependencies as dd

# App imports
from app import app
from config import cfg
import qparse
import utils


# - PAGE globals
#   ensure uniq names across all layouts
PATH = '/compile'
CONTROLS = utils.get_domid('controls', PATH)
DISPLAY = utils.get_domid('display', PATH)
PROGRESS = '{}-progress'.format(DISPLAY)
TIMER = '{}-timer'.format(DISPLAY)

# - Module logger
log = logging.getLogger(cfg.app_name)
log.debug('logging via %s', log.name)

# - Page Layout
_layout = html.Div([
    dcc.Interval(interval=1000, id=TIMER, n_intervals=0),
    html.Div(id=DISPLAY),
    html.Div(id=PROGRESS),
])


def layout(nav, controls):
    'update controls to cached settings and return layout'
    return utils.set_controls(_layout, controls)


# - controls caching
@app.callback(
    dd.Output(CONTROLS, 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State(CONTROLS, 'children')])
def controls(nav, controls):
    controls = json.loads(controls) if controls else []
    return json.dumps(controls)


# - Display
@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input('app-nav', 'children'),
     dd.Input(CONTROLS, 'children')],
    [dd.State(DISPLAY, 'children')])
def display(nav, controls, display):
    controls = json.loads(controls) if controls else []
    return display


# - Progress (timed)
@app.callback(
    dd.Output(TIMER, 'interval'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children')])
def terminate(n_intervals, nav):
    OFF = '86400000'  # str(24*60*60*1000) update once per day
    ON = '500'       # str(1*1000) update every second
    nav = utils.UrlNav(*json.loads(nav))
    if qparse.Compiler(nav.test_id).running:
        log.debug('[%d], %s running, refresh ON', n_intervals, nav.test_id)
        return ON
    log.debug('[%d], %s terminated, refresh OFF', n_intervals, nav.test_id)
    return OFF


@app.callback(
    dd.Output(PROGRESS, 'children'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children'),
     dd.State(PROGRESS, 'children')])
def progress(intervals, nav, progress):
    'display compiler log file periodically'
    nav = utils.UrlNav(*json.loads(nav))
    if nav.test_id is None:
        return html.Div('No Compile target: {}?'.format(nav.test_id))
    c = qparse.Compiler(nav.test_id)
    if not c.running and intervals == 0:
        log.debug('Starting compiler for %s', nav.test_id)
        c.start(nav, cfg)  # first time around, start compiler
        time.sleep(1)      # give thread chance to start

    if c.running:
        log.debug('[%s] %s running', intervals, c.job)
        try:
            with open(c.logfile, 'r') as fh:
                rv = fh.readlines()
                progress = html.Pre(''.join(rv))
        except OSError:
            log.error('%s not found/readable', c.logfile)
            return html.Div('error reading compiler log file %s' % c.logfile)

    return html.Div(children=[progress])
