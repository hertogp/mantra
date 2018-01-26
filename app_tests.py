'''
Mantra - test selection page
'''
import os
import time
import json
import dash_html_components as html
import dash.dependencies as dd
import dash_core_components as dcc

from app import app
from config import CONFIG
from utils import find_files

TEST_TYPES = [
    'md', 'markdown', 'pd'
]


#-- helpers
def get_tests():
    root = CONFIG['tests']
    rv = []
    for f in find_files(root, CONFIG['test-types']):
        ctime = time.strftime('%Y-%m-%d', time.localtime(os.path.getctime(f)))
        atime = time.strftime('%Y-%m-%d', time.localtime(os.path.getatime(f)))
        cat = os.path.relpath(f, root).split(os.sep)[0:1][0]
        rv.append({'cat': cat,
                   'file': f,
                   'created': ctime,
                   'attempted': atime})

    return rv

TESTS = get_tests()


def test_options(tests, cats):
    rv = []
    cats = [] if cats is None else cats
    cats = cats if len(cats) else [t['cat'] for t in TESTS]
    cats = [cat.lower() for cat in cats]
    for test in tests:
        if test['cat'].lower() in cats:
            rv.append(
                {'label': ': '.join([test['created'],
                                    os.path.basename(test['file'])]),
                 'value': test['file']
                 })
    return rv


def category_options(tests):
    rv = []
    for cat in sorted(set([test['cat'] for test in tests])):
        rv.append({'label': cat, 'value': cat})
    return rv

#-- PAGE
path = '/tests'


def layout(cached):
    # fill static layout with cached settings, if any
    print('app-tests, cached', cached)
    if cached is None:
        return _layout
    for ctl_id, attr, value in cached:
        setattr(_layout[ctl_id], attr, value)
    return _layout

_layout = html.Div(
    className='row',
    id='app-tests',
    children=[
        # Selection Row
        html.Div(
            className='row',
            children=[
                html.Div(
                    className='four columns',
                    children=[
                        dcc.Dropdown(
                            id='tests-category',
                            value=[],
                            multi=True,
                            placeholder='Category ...',
                            options=category_options(TESTS)
                                )]),
                html.Div(
                    className='eight columns',
                    children=[
                        dcc.Dropdown(
                            id='tests-filename',
                            placeholder='Select a Test ...',
                            multi=False,
                            value='',
                            options=test_options(TESTS, None)
                        )
                    ]),
            ]),

        html.Hr(),

        # Controls | Preview Row
        html.Div(
            className='row',
            children=[
                html.Div(
                    className='four columns',
                    # style={
                        # 'margin-left' : 0
                    # },
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
                        ]),

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
                        ],
                                 style={'width': '100%'}
                                 ),

                        # limit time for test run
                        html.Div([
                            dcc.Checklist(
                                id='tests-limit-time',
                                options=[{'value': 'yes', 'label': ' '}],
                                values=[],
                                style={'display': 'inline-block'},
                                labelStyle={'display': 'inline-block'},
                            ),
                            html.B('Limit to '),
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
                        ],
                                 style={'width': '100%'}
                                 ),

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

                        html.Br(),

                        html.Button(
                            id='tests-btn-start',
                            className='btn-awesome',
                            children=[
                                html.I(className='far fa-play-circle fa-2x',
                                       style={'color': 'green'}),
                            ]),

                    ]),

                    html.Div(
                        className='eight columns',
                        id='tests-display',
                        children=[
                            'preview'
                        ]),
            ]),
])


# -- Page Cache
@app.callback(
    dd.Output('app-cache-/tests', 'children'),
    [dd.Input('tests-category', 'value'),
     dd.Input('tests-filename', 'value'),
     dd.Input('tests-mode', 'value'),
     dd.Input('tests-max', 'value'),
     dd.Input('tests-options', 'values'),
     dd.Input('tests-limit-maxq', 'values'),
     dd.Input('tests-limit-time', 'values'),
     dd.Input('tests-max-time', 'value'),
     ])
def cache_page(cats, fname, mode, maxq, options,
               limit_maxq, limit_time, max_time):
    'store page state in cache and controls for revisits'
    return json.dumps(
        [('tests-category', 'value', cats),
         ('tests-filename', 'value', fname),
         ('tests-mode', 'value', mode),
         ('tests-max', 'value', maxq),
         ('tests-options', 'values', options),
         ('tests-limit-maxq', 'values', limit_maxq),
         ('tests-limit-time', 'values', limit_time),
         ('tests-max-time', 'value', max_time),
         ])


# -- Cache display (temporary)
@app.callback(
    dd.Output('tests-display', 'children'),
    [dd.Input('app-cache-/tests', 'children')])
def display_cache(cached):
    print('display cache', cached, type(cached))
    if cached is None:
        return html.Pre('no cached information')
    return html.Pre(json.dumps(json.loads(cached), indent=4))


# -- Page controls
@app.callback(
    dd.Output('tests-filename', 'options'),
    [dd.Input('tests-category', 'value')])
def ctl_filter_to_category(cats):
    'limit tests in dropdown by categories'
    return test_options(TESTS, cats)


@app.callback(
    dd.Output('tests-filename', 'value'),
    [dd.Input('tests-category', 'value')],
    [dd.State('tests-filename', 'value')])
def ctl_set_tests_filename(cats, fname):
    'possibly clear filename when category changes'
    allowed = [t['value'] for t in test_options(TESTS, cats)]
    if fname in allowed:
        return fname
    return ''

