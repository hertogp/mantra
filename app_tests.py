# -*- encoding: utf8 -*-
'''
Mantra - test selection page
'''
import os
import json
import csv
from operator import attrgetter
import logging
import dash_html_components as html
import dash.dependencies as dd
import dash_core_components as dcc

from app import app
from config import cfg
import utils

# - Module logger
log = logging.getLogger(cfg.app_name)
# log = getlogger(__name__)
log.debug('logging via %s', log.name)

# - PAGE globals
PATH = '/tests'
CONTROLS = utils.get_domid('controls', PATH)
DISPLAY = utils.get_domid('display', PATH)
TESTS = []  # Global list of available tests


#-- helpers
def test_actions(idx):
    'return array of dcc.Links for possible actions on idx'
    buttons = {
        utils.F_PLAYABLE: ('far fa-play-circle fa-1x', 'play'),
        utils.F_OUTDATED: ('fas fa-recycle fa-1x', 'compile'),
        utils.F_DSTERROR: ('fas fa-times-circle', 'clear'),
        utils.F_SRCERROR: ('fas fa-question-circle', 'error'),
    }

    rv = []
    for flag in buttons.keys():
        if idx.cflags & flag:
            button, action = buttons.get(flag)
            rv.append(
                dcc.Link(
                    html.I(className=button),
                    href='/{};{}'.format(action, idx.test_id),
                    className='btn-awesome',
                )
            )

    return rv


def test_table(categories):
    'load mantra.idx from disk and return as html.Table'
    idxs = []
    try:
        idxs = utils.mtr_idx_read().values()
    except FileNotFoundError:
        pass
    rows = [
        # Header row
        html.Tr([
            html.Th('Category'),
            html.Th('Test'),
            html.Th('Score'),
            html.Th('Test ID'),
            html.Th('#Q\'s'),
            html.Th('Actions'),
        ])
    ]
    idxs = sorted(idxs, key=attrgetter('category', 'score'))
    for idx in idxs:
        if len(categories) and idx.category not in categories:
            continue

        # see mantra.css for no_op to flag inactive link
        linkClassName = '' if idx.cflags & utils.F_PLAYABLE else 'no_op'
        row = html.Tr([
            html.Td(idx.category),
            html.Td(html.A(href='/play;{}'.format(idx.test_id),
                           children=os.path.basename(idx.src_file),
                           className=linkClassName,
                           )),
            html.Td('{}%'.format(idx.score)),
            html.Td(idx.test_id),
            html.Td(idx.numq),
            html.Td(test_actions(idx)),
        ])  # , title=rowTitle)
        rows.append(row)

    return html.Table(rows)


def category_options():
    'setup categories for category filter on test table'
    try:
        tests = utils.mtr_idx_read().values()  # only need idx values
    except OSError:
        tests = []
    rv = []
    for cat in sorted(set([test.category for test in tests])):
        rv.append({'label': cat, 'value': cat})
    return rv


_layout = html.Div(
    className='row',
    id='app-tests',
    children=[
        # Controls | Html table
        html.Div(
            className='four columns',
            # style={ 'margin-left' : 0 },
            children=[

                # test mode
                html.Div([
                    html.B('Mode:'),
                    dcc.RadioItems(
                        id='tests-mode',
                        options=[
                            {'value': 'exam', 'label': 'Exam'},
                            {'value': 'train', 'label': 'Train'},
                            {'value': 'flash', 'label': 'Flash'}
                        ],
                        value='train',
                        style={'display': 'inline-block'},
                        labelStyle={'display': 'inline'},
                    ),
                ], style={'display': 'block'}),

                # test take MAX QUESTIONs
                html.Div([
                    dcc.Checklist(
                        id='tests-limit-maxq',
                        options=[{'value': 'yes', 'label': ' '}],
                        values=[],
                        style={'display': 'inline-block'},
                        labelStyle={'display': 'inline-block'},
                    ),
                    html.B('Max '),
                    dcc.Input(
                        id='tests-max',
                        type='number',
                        min=0,
                        value=10,
                        style={'display': 'inline-block',
                               'width': '5em',
                               'height': '1.2em'
                               },
                    ),
                    html.Spacer(' '),
                    html.Label('questions',
                               style={'display': 'inline-block'}
                               )
                ], style={'width': '100%'}),

                # limit time for test run
                html.Div([
                    dcc.Checklist(
                        id='tests-limit-time',
                        options=[{'value': 'yes', 'label': ' '}],
                        values=[],
                        style={'display': 'inline-block'},
                        labelStyle={'display': 'inline-block'},
                    ),
                    html.B('Max '),
                    dcc.Input(
                        id='tests-max-time',
                        type='number',
                        min=0,
                        value=20,
                        style={'display': 'inline-block',
                               'width': '5em',
                               'height': '1.2em'
                               },
                    ),
                    html.Spacer(' '),
                    html.Label('minutes',
                               style={'display': 'inline-block'}
                               )
                ], style={'width': '100%'}),

                html.Div([
                    html.B('Options: ',
                           style={'display': 'inline-block'}
                           ),
                    dcc.Checklist(
                        id='tests-options',
                        options=[
                            {'value': 'opt-skip-known',
                             'label': 'skip easy questions'},
                            {'value': 'opt-random-q',
                             'label': 'randomize questions'},
                            {'value': 'opt-random-a',
                             'label': 'randomize answers'},
                            {'value': 'opt-show-p',
                             'label': 'show progress'},
                            {'value': 'opt-show-score',
                             'label': 'show running score'},
                        ],
                        values=['opt-random-q', 'opt-random-a'],
                        style={'display': 'block'},
                        labelStyle={'display': 'block'},
                    )
                ]),

                # category dropdown filter
                html.Div(
                    # className='three columns',
                    children=[
                        dcc.Dropdown(
                            id='tests-category',
                            value=[],
                            multi=True,
                            placeholder='Category ...',
                            options=category_options()
                        )], style={'display': 'block'}),

                ]),

                html.Div(
                    className='eight columns',
                    id=DISPLAY,
                    children=['loading ...']
                ),

])


def layout(nav, controls):
    # return static layout with cached controls settings, if any
    log.debug('nav %s', nav)
    return utils.set_controls(_layout, controls)


# -- Page controls
@app.callback(
    dd.Output(CONTROLS, 'children'),
    [dd.Input('tests-category', 'value'),
     dd.Input('tests-mode', 'value'),
     dd.Input('tests-max', 'value'),
     dd.Input('tests-options', 'values'),
     dd.Input('tests-limit-maxq', 'values'),
     dd.Input('tests-limit-time', 'values'),
     dd.Input('tests-max-time', 'value'),
     ])
def controls(cats, mode, maxq, options, limit_maxq, limit_time, max_time):
    'store page state in cache and controls for revisits'
    controls = json.dumps([
        ('tests-category', 'value', cats),
        ('tests-mode', 'value', mode),
        ('tests-max', 'value', maxq),
        ('tests-options', 'values', options),
        ('tests-limit-maxq', 'values', limit_maxq),
        ('tests-limit-time', 'values', limit_time),
        ('tests-max-time', 'value', max_time),
    ])
    log.debug('save controls %s', controls)
    return controls


# - display html table, trigger is page cache
@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input(CONTROLS, 'children')])
def display(controls):
    log.debug('tests display %s', controls)
    controls = json.loads(controls)
    categories = []
    for id_, attr, val in controls:
        if id_ == 'tests-category':
            categories = val
    return test_table(categories)
