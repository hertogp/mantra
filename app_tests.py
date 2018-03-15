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
PAGE_ID = 'app-{}'.format(PATH)
ID = '{}-{{}}'.format(__name__).format
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

def action_icon(test_id, flag):
    klass = {
        'U': ('fas fa-sync fa-1x', 'update'),
        'P': ('far fa-play-circle fa-1x', 'run'),
        'C': ('fas fa-wrench fa-1x', 'compile'),
        'O': ('fas fa-child', 'revert')
    }
    button, action = klass.get(flag)
    return dcc.Link(
        html.I(className=button, title=action),
        href='/{};{}'.format(action, test_id),
        className='btn-awesome')


def action_menu(test_id, flag):
    flags = {
        'U': 'run compile preview delete'.split(),
        'P': 'run preview delete'.split(),
        'C': 'compile delete'.split(),
        'O': 'run preview revert delete'.split()
    }
    act = flags.get(flag, ['run', 'compile', 'preview', 'delete'])
    links = [dcc.Link(x, href='/{};{}'.format(x, test_id)) for x in act]
    return html.Div(className="dropdown",
                    children=[
                        html.I(className='fa fa-ellipsis-v dropbtn'),
                        html.Div(
                            className='dropdown-content',
                            id='app-menu-content',
                            children=links)
                    ])


def test_table2(categories):
    'load mantra.idx from disk and return as html.Table'
    idxs = utils.MantraIdx(cfg.src_dir, cfg.dst_dir)
    rows = [
        # Header row
        html.Tr([
            html.Th('Tests'),
            html.Th(),
            html.Th(),
            html.Th(),

        ])
    ]
    for test_id, flag, src, category in idxs:
        if len(categories) and category not in categories:
            continue

        # see mantra.css for no_op to flag inactive link
        linkClassName = '' if flag in 'UPO' else 'no_op'
        row = html.Tr([
            html.Td(action_icon(test_id, flag)),
            html.Td(html.A(href='/run;{}'.format(test_id),
                           children=os.path.basename(src),
                           className=linkClassName,
                           )),
            html.Td(category),
            html.Td(action_menu(test_id, flag)),
        ])  # , title=rowTitle)
        rows.append(row)

    return html.Table(rows)

def test_table(categories):
    'load mantra.idx from disk and return as html.Table'
    idxs = []
    try:
        idxs = utils.mtr_idx_read(cfg.dst_dir).values()
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
        tests = utils.mtr_idx_read(cfg.dst_dir).values()  # only idx values
    except OSError:
        tests = []
    rv = []
    for cat in sorted(set([test.category for test in tests])):
        rv.append({'label': cat, 'value': cat})
    return rv


_layout = html.Div(
    className='row',
    id=PAGE_ID,
    children=[
        # Controls | Html table
        html.Div(
            className='twelve columns',
            # style={ 'margin-left' : 0 },
            children=[
                # category dropdown filter
                html.Div(
                    # className='three columns',
                    children=[
                        dcc.Dropdown(
                            id=ID('category'),
                            value=[],
                            multi=True,
                            placeholder='Category ...',
                            options=category_options()
                        )], style={'display': 'block'}),

                ]),

                html.Div(
                    className='twelve columns',
                    id=DISPLAY,
                    children=[
                        html.Div('loading ...')]
                ),

])


def layout(nav, controls):
    # return static layout with cached controls settings, if any
    log.debug('nav %s', nav)
    return utils.set_controls(_layout, controls)


# -- Page controls
@app.callback(
    dd.Output(CONTROLS, 'children'),
    [dd.Input(ID('category'), 'value')])
def controls(category):
    'store page state in cache and controls for revisits'
    controls = json.dumps([
        (ID('category'), 'value', category),
    ])
    log.debug('save controls %s', controls)
    return controls


# - display html table, trigger is page cache
@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input(CONTROLS, 'children')])
def display(controls):
    controls = json.loads(controls)
    categories = []
    for id_, attr, val in controls:
        if id_ == ID('category'):
            categories = val
    return test_table2(categories)
