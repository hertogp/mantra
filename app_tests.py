# -*- encoding: utf8 -*-
'''
Mantra - test selection page
'''
import os
import json
import csv
from collections import namedtuple
from operator import itemgetter

import dash_html_components as html
import dash.dependencies as dd
import dash_core_components as dcc

from app import app
from config import CONFIG
from utils import find_files, hashfnv64

# - Module logger
log = app.getlogger(__name__)
log.debug('logger created')

TESTS = []  # Global list of available tests


#-- helpers
def get_tests():
    'find test.md files under configured root'
    # skip files in rootdir, like index.md, which are generated by mkdocs
    # only subdirs can be categories
    src_root = CONFIG['src_dir']                                   # tests.md's
    dst_root = CONFIG['dst_dir']   # compiled
    rv = []
    for fpath in find_files(src_root, CONFIG['test-types']):
        ctime = os.path.getctime(fpath)
        filename = os.path.basename(fpath)
        dirname = os.path.dirname(fpath)
        category = os.path.relpath(dirname, src_root)

        # skip file in src_root itself
        if category == '.':
            continue

        # hash filename with category as salt -> unique dirname as test_id
        # - use category, so if everything is moved to diff rootdir, test_id's
        #   remain the same.
        test_id = hashfnv64(filename, category)
        test_dir = os.path.join(dst_root, test_id)
        statsfile = os.path.join(test_dir, 'stats.csv')
        available = os.path.isfile(statsfile)

        # See if src_file was compiled to questions in the past
        score, numq, action = 0, 0, 'compile'
        if os.path.isdir(test_dir):
            log.debug('searching test_dir %s', test_dir)
            for qstn in find_files(test_dir, ['json']):
                log.debug('found question %s', qstn)
                numq += 1  # maybe check filesize or timestamp

            # read the stats.csv = timestamp,mode,num_questions,score
            # test.md may have been compiled, but never taken, so no stats
            if available:
                with open(statsfile) as fh:
                    fh_csv = csv.reader(fh)
                    head = next(fh_csv)
                    Stats = namedtuple('Stats', head)
                    score, count = 0, 0
                    for r in fh_csv:
                        row = Stats(*r)
                        score += int(row.score)  # 0 - 100
                        count += 1
                score = int(score / count) if count else 0
                if os.path.getctime(statsfile) < ctime:
                    action = 'compile'
                elif numq > 0:
                    action = 'run'

        log.debug('found src file %s in category %s', filename, category)
        rv.append({'category': category,
                   'filename': filename,
                   'filepath': fpath,
                   'test_id': test_id,
                   'test_dir': test_dir,
                   'created': ctime,
                   'available': available,
                   'numq': numq,
                   'score': score,
                   'action': action,
                   })

    return rv


TESTS = get_tests()


def test_table(tests, categories):
    'generate html table for tests to display'
    # tests_specs = get_tests()
    awesome_action = {
        'run': 'far fa-play-circle fa-1x',
        'compile': 'fas fa-recycle fa-1x',
    }
    default_action = 'fas fa-question-circle fa-1x'
    rows = [
        # Header row
        html.Tr([
            html.Th('Category'),
            html.Th('Test'),
            html.Th('Score'),
            html.Th('Test ID'),
            html.Th('#Q\'s'),
            html.Th('Action'),
        ])
    ]
    tests = sorted(tests, key=itemgetter('category', 'created'))
    for test in tests:
        if len(categories) and test['category'] not in categories:
            continue

        linkClassName = '' if test['action'] == 'run' else 'no_op'
        rowTitle = test['action']
        # action = [run, compile, recompile]
        action = dcc.Link(
            html.I(className=awesome_action.get(test['action'],
                                                default_action)),
            href='/{}?test_id={}'.format(test['action'], test['test_id']),
            className='btn-awesome',
            )

        row = html.Tr([
            html.Td(test['category']),
            html.Td(html.A(href=test['test_id'],
                           children=test['filename'],
                           className=linkClassName,
                           )),
            html.Td('{}%'.format(test['score'])),
            html.Td(test['test_id']),
            html.Td(test['numq']),
            html.Td(action),
        ], title=rowTitle)
        rows.append(row)

    return html.Table(rows)


def test_options(tests, cats):
    rv = []
    cats = [] if cats is None else cats
    cats = cats if len(cats) else [t['category'] for t in TESTS]
    cats = [cat.lower() for cat in cats]
    for test in tests:
        if test['category'].lower() in cats:
            rv.append(
                {'label': test['filename'],
                 'value': test['test_id']
                 })
    return rv


def category_options(tests):
    rv = []
    for cat in sorted(set([test['category'] for test in tests])):
        rv.append({'label': cat, 'value': cat})
    return rv

# - PAGE
path = '/tests'


def layout(app_nav, cached):
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
                            options=category_options(TESTS)
                        )], style={'display': 'block'}),

                ]),

                html.Div(
                    className='eight columns',
                    id='tests-display',
                    children=['loading ...']
                ),

])

# can we list all cacheable controls via className e.g.?j
# print(dir(_layout))
# print(_layout.keys())
# print('-'*80)
# print(_layout.values())
# for vistor in _layout.traverse():
#     if hasattr(vistor, 'id'):
#         print(type(vistor), vistor)

# -- Page Cache
# Cache = list of control attribute tuples (id, attr, value)
@app.callback(
    dd.Output('app-cache-/tests', 'children'),
    [dd.Input('tests-category', 'value'),
     dd.Input('tests-mode', 'value'),
     dd.Input('tests-max', 'value'),
     dd.Input('tests-options', 'values'),
     dd.Input('tests-limit-maxq', 'values'),
     dd.Input('tests-limit-time', 'values'),
     dd.Input('tests-max-time', 'value'),
     ])
def cache(cats, mode, maxq, options, limit_maxq, limit_time, max_time):
    'store page state in cache and controls for revisits'
    return json.dumps(
        [('tests-category', 'value', cats),
         ('tests-mode', 'value', mode),
         ('tests-max', 'value', maxq),
         ('tests-options', 'values', options),
         ('tests-limit-maxq', 'values', limit_maxq),
         ('tests-limit-time', 'values', limit_time),
         ('tests-max-time', 'value', max_time),
         ])


# - display html table, trigger is page cache
@app.callback(
    dd.Output('tests-display', 'children'),
    [dd.Input('app-cache-/tests', 'children')])
def display(cached):
    cached = json.loads(cached)
    print('tests display')
    print('   <--reads--', cached)
    cats = []
    for id_, attr, val in cached:
        if id_ == 'tests-category':
            cats = val
    return test_table(TESTS, cats)


