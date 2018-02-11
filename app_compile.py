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
import utils

# - PAGE globals
#   ensure uniq names across all layouts
PATH = '/compile'
CONTROLS = utils.get_domid('controls', PATH)
DISPLAY = utils.get_domid('display', PATH)
PROGRESS = '{}-progress'.format(DISPLAY)
TIMER = '{}-timer'.format(DISPLAY)

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
    test_id = app_nav.get('test_id', None)
    log.debug('starting on %s' % test_id)
    test_dir = os.path.join(CONFIG['dst_dir'], test_id)
    if test_id is None:
        return False
    os.makedirs(test_dir, exist_ok=True)
    logfile = os.path.join(test_dir, 'compile.log')
    lockfile = os.path.join(test_dir, '.lock')
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
        time.sleep(4)
        with open(logfile, 'a') as fh:
            fh.write('.%s' % i)
            log.debug('working .. %s', i)

    with open(logfile, 'a') as fh:
        fh.write('\ndone!')

    # signal termination of compile process
    try:
        with threading.Lock():
            os.remove(lockfile)
    except OSError:
        pass
    except Exception:
        raise


    return True


# - Page Layout
_layout = html.Div([
    dcc.Interval(interval=500, id=TIMER, n_intervals=0),
    html.Div(id=DISPLAY),
    html.Div(id=PROGRESS),
])


def layout(app_nav, controls):
    'update controls to cached settings and return layout'
    log.debug('app_nav %s', app_nav)
    log.debug('cached %s', controls)
    return utils.set_layout_controls(_layout, controls)


# - Page Cache
@app.callback(
    dd.Output(CONTROLS, 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State(CONTROLS, 'children')])
def controls(app_nav, controls):
    controls = json.loads(controls) if controls else []
    app_nav = json.loads(app_nav)
    log.debug('restore controls: %s', controls)
    return json.dumps(controls)


# - Display
@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input('app-nav', 'children'),
     dd.Input(CONTROLS, 'children')],
    [dd.State(DISPLAY, 'children')])
def display(app_nav, controls, display):
    app_nav = json.loads(app_nav)
    controls = json.loads(controls) if controls else []
    log.debug('app-nav %s', app_nav['href'])
    log.debug('display %s', display)

    return ''


# - Progress (timed)
@app.callback(
    dd.Output(TIMER, 'interval'),
    [dd.Input(TIMER, 'n_intervals')],
    [dd.State('app-nav', 'children')])
def terminate(n_intervals, app_nav):
    OFF = str(24*60*60*1000)  # once per day
    ON = str(1*1000)
    log.debug('n_intervals %s', n_intervals)
    app_nav = json.loads(app_nav)
    log.debug('app_nav', app_nav)
    test_id = app_nav.get('test_id', None)

    if test_id is None:
        return OFF

    test_dir = os.path.join(CONFIG['dst_dir'], test_id)
    lockfile = os.path.join(test_dir, '.lock')
    with threading.Lock():
        if not os.path.isfile(lockfile):
            log.debug('TERMINATE!')
            return OFF
        else:
            with open(lockfile, 'r') as fh:
                log.debug('locked %s', fh.read())
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
    test_id = app_nav.get('test_id', None)
    if test_id is None:
        return html.Div('No Compile target: {}?'.format(test_id))
    test_dir = os.path.join(CONFIG['dst_dir'], test_id)
    logfile = os.path.join(test_dir, 'compile.log')
    lockfile = os.path.join(test_dir, '.lock')

    if intervals == 0:
        with threading.Lock():
            if not os.path.isfile(lockfile):
                t = threading.Thread(target=compiler, args=(app_nav,))
                t.start()
                with open(lockfile, 'w') as fh:
                    fh.write('{} started '.format(t.name))
                    fh.write(time.strftime('%Y%m%d %H:%M:%S',
                                           time.localtime()))
                log.debug('started thread %s for %s', t.name, test_id)
                return html.Div('Started compiler {}'.format(t.name))
            else:
                log.debug('joining running compile thread for %s', test_id)
                return html.Div('Joining ...')

    # Display compiler results until done!
    if not os.path.isfile(logfile):
        return html.Div('No compiler results ... (yet)')
    rv = ['No news yet\n']
    with open(logfile, 'r') as fh:
        rv = fh.readlines()

    return html.Div(html.Pre(''.join(rv)))


