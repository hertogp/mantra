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

from app import app
from app_tests import TESTS
from config import CONFIG
from qparse import Quiz

path = '/compile'
PATH = path
# ensure uniq names across all layouts
CACHE = 'app-cache-{}'.format(PATH)
DISPLAY = 'app-display-{}'.format(PATH)
PROGRESS = 'app-display2-{}'.format(PATH)
TIMER = 'app-timer-{}'.format(PATH)

# - Module logger
log = app.getlogger(__name__)
log.debug('logger created')

# - Module functionality

# use a logger to dump progress info to test_dir/compile.log
# use an interval to dump its contents to display until done
# then show results ala app_tests with action to play the test
# and use threading to separate out the compiler process

def compiler(app_nav):
    'worker func to compile test in separate thread'
    parms = app_nav['search']
    test_id = parms.get('test_id', None)
    log.debug('starting on %s' % test_id)
    test_dir = os.path.join(CONFIG['dst_dir'], test_id)
    if test_id is None:
        return False
    os.makedirs(test_dir, exist_ok=True)
    logfile = os.path.join(test_dir, 'qc.log')
    src_test = {}
    for test in TESTS:
        if test['test_id'] == test_id:
            src_test = test
    src_file = test.get('filepath', None)
    assert src_file is not None

    # start a new logfile
    with open(logfile, 'w') as fh:
        fh.write('Compile target: %s\n' % test_id)
        fh.write('Source:\n')
        for k, v in src_test.items():
            fh.write('- %-9s: %s\n' % (k, str(v)))

    for i in range(5):
        time.sleep(1)
        with open(logfile, 'a') as fh:
            fh.write('.%s' % i)
            log.debug('working .. %s', i)

    # signal termination of compile process
    with open(logfile, 'a') as fh:
        fh.write('\ndone!')

    return True


# - Page Layout
_layout = html.Div([
    dcc.Interval(interval=500, id=TIMER, n_intervals=0),
    html.Div(id=DISPLAY),
    html.Div(id=PROGRESS),
])


def layout(app_nav, cached):
    log.debug('app_nav %s', app_nav['search'])
    log.debug('cache %s', cached)

    if cached is None or len(cached) < 1:
        return _layout
    for id_, attr, value in cached:
        obj = _layout.get(id_, None)
        if obj is None:
            continue
        setattr(obj, attr, value)
    return _layout


# - Page Cache
@app.callback(
    dd.Output(CACHE, 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State(CACHE, 'children')])
def cache(app_nav, cache):
    cache = json.loads(cache) if cache else []
    app_nav = json.loads(app_nav)
    log.debug('to cache: %s', cache)
    log.debug('app_nav %s', app_nav['search'])
    return json.dumps(cache)


# - Display
@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input('app-nav', 'children'),
     dd.Input(CACHE, 'children')])
def display(app_nav, cached):
    app_nav = json.loads(app_nav)
    cached = json.loads(cached) if cached else []
    log.debug('app-nav %s', app_nav['search'])
    return '' # html.Div(html.Pre('waiting on results ...'))


# - Progress (timed)
@app.callback(
    dd.Output(TIMER, 'interval'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children'),
     dd.State(TIMER, 'interval')])
def terminate(n_intervals, app_nav, t):
    # XXX: a better sentinel is needed here, this is a test
    OFF = str(24*60*60*1000)  # once per day
    ON = str(1*1000)
    log.debug('n_intervals %s', n_intervals)
    app_nav = json.loads(app_nav)
    parms = app_nav['search']
    log.debug('app_nav', parms)
    test_id = parms.get('test_id', None)
    if test_id is None:
        return ON

    test_dir = os.path.join(CONFIG['dst_dir'], test_id)
    logfile = os.path.join(test_dir, 'qc.log')
    if not os.path.isfile(logfile):
        return ON
    with open(logfile, 'r') as fh:
        rv = fh.readlines()

    log.debug('last line is %s', rv[-1])
    if 'done!' in rv[-1].lower():
        log.debug('TERMINATE!')
        return OFF
    return ON

@app.callback(
    dd.Output(PROGRESS, 'children'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children'),
     dd.State(PROGRESS, 'children')])
def progress(intervals, app_nav, progress):
    'display compiler log file periodically'
    app_nav = json.loads(app_nav)
    log.debug('interval=%s', intervals)

    if intervals == 0:
        t = threading.Thread(target=compiler, args=(app_nav,))
        t.start()
        log.debug('started thread %s', t.name)
        return html.Div('Started compiler %s' % t.name)

    # log.debug('progress %s, %s', type(progress), progress)
    # progress = progress if progress else html.Div()
    # progress['props']['children'] += '.'
    # return progress

    # Display compiler results until done!

    parms = app_nav['search']
    test_id = parms.get('test_id', None)
    if test_id is None:
        return html.Div('No Compile target: {}?'.format(test_id))

    test_dir = os.path.join(CONFIG['dst_dir'], test_id)
    logfile = os.path.join(test_dir, 'qc.log')
    if not os.path.isfile(logfile):
        return html.Div('No compiler results ... (yet)')
    rv = ['No news yet\n']
    with open(logfile, 'r') as fh:
        rv = fh.readlines()

    return html.Div(html.Pre(''.join(rv)))


