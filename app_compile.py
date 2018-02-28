# -*- encoding: utf8 -*-
'''
Mantra - compile-a-test page
'''

import os
import json
import time
import threading
import dash_html_components as html
import dash_core_components as dcc
import dash.dependencies as dd

from log import getlogger
from app import app
from config import cfg
from qparse import Quiz
import utils


# - PAGE globals
#   ensure uniq names across all layouts
PATH = '/compile'
CONTROLS = utils.get_domid('controls', PATH)
DISPLAY = utils.get_domid('display', PATH)
PROGRESS = '{}-progress'.format(DISPLAY)
TIMER = '{}-timer'.format(DISPLAY)

# - Module logger
log = getlogger(__name__)
log.debug('logger created')

# - Module functionality

# use a logger to dump progress info to test_dir/mtr.log
# use an interval to dump its contents to display until done
# then show results ala app_tests with action to play the test
# and use threading to separate out the compiler process


def compiler(nav):
    'worker func to compile test in separate thread'
    if nav.test_id is None:
        log.error('invalid test_id (None)')
        return False

    # get src details (MtrIdx tuple) to compile
    master_idx = utils.mtr_idx_read()
    idx = master_idx.get(nav.test_id, None)
    if idx is None or len(idx) < 1:
        log.error('no index entry for %s', nav.test_id)
        return False

    log.debug('starting on %s' % nav.test_id)

    # get dest dir for compiler output
    # - or put dst_root = cfg.dst_dir in idx?
    qz = Quiz(idx, cfg)

    # log any errors in qz to app log
    # display qparse log results in case of errors
    log.debug('%s tags: %s', nav.test_id, qz.tags)
    log.debug('%s meta: %s', nav.test_id, qz.meta)
    log.debug('%s qstn: %s', nav.test_id, len(qz.questions))

    del qz

    return True


# - Page Layout
_layout = html.Div([
    dcc.Interval(interval=250, id=TIMER, n_intervals=0),
    html.Div(id=DISPLAY),
    html.Div(id=PROGRESS),
])


def layout(nav, controls):
    'update controls to cached settings and return layout'
    log.debug('nav %s', nav)
    log.debug('controls %s', controls)
    return utils.set_controls(_layout, controls)


# - Controls Cacheing
@app.callback(
    dd.Output(CONTROLS, 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State(CONTROLS, 'children')])
def controls(nav, controls):
    controls = json.loads(controls) if controls else []
    log.debug('save controls: %s', controls)
    return json.dumps(controls)


# - Display
@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input('app-nav', 'children'),
     dd.Input(CONTROLS, 'children')],
    [dd.State(DISPLAY, 'children')])
def display(nav, controls, display):
    nav = utils.UrlNav(*json.loads(nav))
    controls = json.loads(controls) if controls else []
    log.debug('nav %s', nav.href)
    log.debug('display %s', display)
    return ''


# - Progress (timed)
@app.callback(
    dd.Output(TIMER, 'interval'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children')])
def terminate(n_intervals, nav):
    OFF = '86400000'  # str(24*60*60*1000) update once per day
    ON = '1000'  # str(1*1000) update every second
    nav = utils.UrlNav(*json.loads(nav))
    log.debug('interval %s for nav %s', n_intervals, nav)

    # callbacks are in random order, so donot terminate unless
    # we've had <n>-interval cycles...
    if n_intervals < 2:
        return ON

    if nav.test_id is None:
        return OFF

    logfile = os.path.join(cfg.dst_dir, nav.test_id, 'mtr.log')
    # with threading.Lock():
    if not os.path.isfile(logfile):
        log.debug('TERMINATE!')
        return OFF

    return ON


@app.callback(
    dd.Output(PROGRESS, 'children'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children'),
     dd.State(PROGRESS, 'children')])
def progress(intervals, nav, progress):
    'display compiler log file periodically'
    nav = utils.UrlNav(*json.loads(nav))
    log.debug('interval=%s', intervals)
    if nav.test_id is None:
        return html.Div('No Compile target: {}?'.format(nav.test_id))
    dst_dir = os.path.join(cfg.dst_dir, nav.test_id)
    logfile = os.path.join(dst_dir, 'mtr.log')

    if intervals == 0:
        with threading.Lock():
            if not os.path.isfile(logfile):
                t = threading.Thread(target=compiler, args=(nav,))
                os.makedirs(dst_dir, exist_ok=True)
                with open(logfile, 'w') as fh:
                    msg = '{} compiled by {}'.format(nav.test_id, t.name)
                    fh.write(msg)
                    fh.write(time.strftime(' %Y%m%d %H:%M:%S\n',
                                           time.localtime()))
                t.start()
                log.debug(msg)
                return html.Div(msg)
            else:
                log.debug('joining running compile thread for %s', nav.test_id)
                return html.Div('Joining ...')

    # Display compiler results until done!
    if not os.path.isfile(logfile):
        return html.Div(children=[
            progress,
            'link to play results if all went ok']
                        )
    with open(logfile, 'r') as fh:
        rv = fh.readlines()

    return html.Div(html.Pre(''.join(rv)))
