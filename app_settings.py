'''
Mantra - settings page
'''
import logging
import json

import dash_html_components as html
import dash_core_components as dcc
import dash.dependencies as dd

from app import app
from config import cfg
import utils

# - Module logger
log = logging.getLogger(cfg.app_name)
# log = getlogger(__name__)
log.debug('logging via %s', log.name)

# - PAGE globals
PATH = '/settings'
ID = '{}-{{}}'.format(__name__).format  # use as id=ID('elem_id')
CONTROLS = utils.get_domid('controls', PATH)
DISPLAY = utils.get_domid('display', PATH)


def layout(nav, controls):
    log.debug('nav %s', nav)
    log.debug('controls %r', controls)
    return utils.set_controls(_layout, controls)

_layout = html.Div(
    className='row',
    id=ID('page'),
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
                        id=ID('mode'),
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
                        id=ID('limit-maxq'),
                        options=[{'value': 'yes', 'label': ' '}],
                        values=[],
                        style={'display': 'inline-block'},
                        labelStyle={'display': 'inline-block'},
                    ),
                    html.B('Max '),
                    dcc.Input(
                        id=ID('max'),
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
                        id=ID('limit-time'),
                        options=[{'value': 'yes', 'label': ' '}],
                        values=[],
                        style={'display': 'inline-block'},
                        labelStyle={'display': 'inline-block'},
                    ),
                    html.B('Max '),
                    dcc.Input(
                        id=ID('max-time'),
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
                        id=ID('options'),
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
                    )]),

                ]),

                html.Div(
                    className='eight columns',
                    id=DISPLAY,
                    children=['loading ...']
                ),

])

# -- Page controls
@app.callback(
    dd.Output(CONTROLS, 'children'),
    [dd.Input(ID('mode'), 'value'),
     dd.Input(ID('max'), 'value'),
     dd.Input(ID('options'), 'values'),
     dd.Input(ID('limit-maxq'), 'values'),
     dd.Input(ID('limit-time'), 'values'),
     dd.Input(ID('max-time'), 'value'),
     ])
def controls(mode, maxq, options, limit_maxq, limit_time, max_time):
    'store page state in cache and controls for revisits'
    controls = json.dumps([
        (ID('mode'), 'value', mode),
        (ID('max'), 'value', maxq),
        (ID('options'), 'values', options),
        (ID('limit-maxq'), 'values', limit_maxq),
        (ID('limit-time'), 'values', limit_time),
        (ID('max-time'), 'value', max_time),
    ])
    return controls
