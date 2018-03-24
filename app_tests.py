# -*- encoding: utf8 -*-
'''
Mantra - test selection page
'''
import os
import json
import shutil
import threading
import time
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
# def test_actions(idx):
#     'return array of dcc.Links for possible actions on idx'
#     buttons = {
#         utils.F_PLAYABLE: ('far fa-play-circle fa-1x', 'play'),
#         utils.F_OUTDATED: ('fas fa-recycle fa-1x', 'compile'),
#         utils.F_DSTERROR: ('fas fa-times-circle', 'clear'),
#         utils.F_SRCERROR: ('fas fa-question-circle', 'error'),
#     }

#     rv = []
#     for flag in buttons.keys():
#         if idx.cflags & flag:
#             button, action = buttons.get(flag)
#             rv.append(
#                 dcc.Link(
#                     html.I(className=button),
#                     href='/{};{}'.format(action, idx.test_id),
#                     className='btn-awesome',
#                 )
#             )

#     return rv

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
    # links = [dcc.Link(x, href='/{};{}'.format(x, test_id)) for x in act]
    # U(pdatable) -> run, (re)compile, preview, delete
    # P(layable)  -> run, (re)compile, preview, delete
    # C(reatable) -> compile, no dsts files yet: cannot run, preview, delete
    # O(rphaned)  -> run, preview, delete, revert, missing source files
    flagged = [
        # new pages
        ('UPO', dcc.Link('run', href='/run;{}'.format(test_id))),
        ('UPC', dcc.Link('compile', href='/compile;{}'.format(test_id))),
        # in-page actions
        ('UPO', dcc.Link('preview',
                         href='{};{}?action=preview'.format(PATH, test_id))),
        ('O', dcc.Link('revert',
                       href='{};{}?action=revert'.format(PATH, test_id))),
        ('UPO', dcc.Link('delete',
                         href='{};{}?action=delete'.format(PATH, test_id)))
    ]
    # not all links make sense all the time
    links = [link for flags, link in flagged if flag in flags]
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
    for idx in idxs:
        if len(categories) and idx.category not in categories:
            continue

        # 'no_op' disables the link -> see mantra.css
        # link inactive if dsts has yet to be created
        linkClassName = 'no_op' if idx.flag == 'C' else ''
        row = html.Tr([
            html.Td(action_icon(idx.test_id, idx.flag)),
            html.Td(html.A(href='/run;{}'.format(idx.test_id),
                           children=os.path.basename(idx.src),
                           className=linkClassName,
                           )),
            html.Td(idx.category),
            html.Td(action_menu(idx.test_id, idx.flag)),
        ])  # , title=rowTitle)
        rows.append(row)

    return html.Table(rows)


# def test_table(categories):
#     'load mantra.idx from disk and return as html.Table'
#     idxs = []
#     try:
#         idxs = utils.mtr_idx_read(cfg.dst_dir).values()
#     except FileNotFoundError:
#         pass
#     rows = [
#         # Header row
#         html.Tr([
#             html.Th('Category'),
#             html.Th('Test'),
#             html.Th('Score'),
#             html.Th('Test ID'),
#             html.Th('#Q\'s'),
#             html.Th('Actions'),
#         ])
#     ]
#     idxs = sorted(idxs, key=attrgetter('category', 'score'))
#     for idx in idxs:
#         if len(categories) and idx.category not in categories:
#             continue

#         # see mantra.css for no_op to flag inactive link
#         linkClassName = '' if idx.cflags & utils.F_PLAYABLE else 'no_op'
#         row = html.Tr([
#             html.Td(idx.category),
#             html.Td(html.A(href='/play;{}'.format(idx.test_id),
#                            children=os.path.basename(idx.src_file),
#                            className=linkClassName,
#                            )),
#             html.Td('{}%'.format(idx.score)),
#             html.Td(idx.test_id),
#             html.Td(idx.numq),
#             html.Td(test_actions(idx)),
#         ])  # , title=rowTitle)
#         rows.append(row)

#     return html.Table(rows)


def category_options():
    'setup categories for category filter on test table'
    try:
        tests = utils.MantraIdx(cfg.src_dir, cfg.dst_dir).idx.values()
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
            className='four columns',
            children=[
                html.Div(dcc.Dropdown(
                    id=ID('category'),
                    value=[],
                    multi=True,
                    placeholder='Category ...',
                    options=category_options()
                    ),
                         style={'display': 'block'}),

                html.Div('loading ...', id=DISPLAY)
            ]),

        html.Progress(
            max=100, value=60
        ),

        # modal display
        html.Div(
            html.Div(
                html.Div([
                    html.Div([
                        html.I(id=ID('modal-close'),
                               n_clicks=0,
                               className='fas fa-times w3-button w3-display-topright'),
                        html.H1('  ', id=ID('modal-header')),
                    ],
                             className='w3-container w3-teal'),
                    html.Div([
                        dcc.Interval(interval=500, id=ID('modal-timer'),
                                     n_intervals=0),
                        html.Div([], id=ID('modal-text'),
                                 className='w3-container')
                    ]),
                ],
                    className='w3-modal-content w3-animate-top w3-card-4'),
                className='w3-modal',
                style={'display': 'none'},
                id=ID('modal-1')),
            className='seven columns')
        ])


def layout(nav, controls):
    # return static layout with cached controls settings, if any
    log.debug('nav %s', nav)
    log.debug('controls %s', controls)
    if len(nav.query):
        _layout[ID('modal-1')].style = {'display': 'block'}
        _layout[ID('modal-timer')].interval = 500  # refresh 1/second
        _layout[ID('modal-header')].children = [
            html.I(className='far fa-file-code'),
            ' {}'.format(nav.test_id)
        ]
        # handle query in diff. thread
        QueryHandler(nav.test_id).start(nav, cfg)
    else:
        _layout[ID('modal-1')].style = {'display': 'none'}
        _layout[ID('modal-timer')].interval = 1000*3600*24  # refresh 1/day
    return utils.set_controls(_layout, controls)


# -- process nav.query
class QueryHandler(metaclass=utils.Cached):
    def __init__(self, job):
        self.job = job
        self.msgs = []
        self.running = False

    def start(self, nav, cfg):
        self.nav = nav
        self.cfg = cfg
        threading.Thread(target=self._run, name=self.job).start()
        return self

    @classmethod
    def find(cls, *args):
        'find instance for args or return None'
        return cls._Cached__cache.get(args, None)

    def _run(self):
        self.running = True
        log.debug('QueryHandler(%s) - started', self.job)
        for action in self.nav.query.get('action', []):
            meth = getattr(self, 'do_{}'.format(action), None)
            if meth is None:
                self.msgs.append('ignore unknown action {}'.format(action))
                continue
            else:
                self.msgs.append('-> {}'.format(action))
            meth()
            time.sleep(2)  # give modal update callback time to fire

    def do_delete(self):
        'delete compiled output files'
        dst_dir = os.path.join(self.cfg.dst_dir, self.nav.test_id)
        for fname in utils.glob_files(dst_dir, ['*']):
            fullname = os.path.join(dst_dir, fname)
            log.debug('del %s', fullname)
            os.remove(fullname)
            self.msgs.append('rm {}'.format(fullname))
        shutil.rmtree(dst_dir)
        self.msgs.append('rmtree {}'.format(dst_dir))
        return self

    def do_clear_history(self):
        'clear logged history of tests'
        pass



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


@app.callback(
    dd.Output('app-url', 'search'),
    [dd.Input('app-url', 'href')])
def reset_url(pathname):
    'clear query/search from url'
    log.debug('resetting path %s', pathname)
    return ''


@app.callback(
    dd.Output(ID('modal-1'), 'style'),
    [dd.Input(ID('modal-close'), 'n_clicks'),
     dd.Input(ID('modal-text'), 'n_clicks')],
    [dd.State(ID('modal-1'), 'style')])
def toggle_modal(n_close, n_modal, style):
    'modal close button was clicked, so hide the modal'
    n_close = 0 if n_close is None else n_close
    n_modal = 0 if n_modal is None else n_modal
    clicks = n_close + n_modal
    style = {'display': 'none'} if clicks > 0 else style
    return style
    log.debug('[%s] <- %s', n_close, style)
    style = {'display': 'none'} if n_close > 0 else style
    log.debug('[%s] -> %s', n_close, style)
    # return style
    if n_close is None:  # in case n_clicks was not specified in _layout
        return style     # - this is a no-op (initial callback on load)
    elif n_close == 0:   # same case, but with initial n_clicks=0 in layout
        return style     # - again a no-op
    else:
        style = {'display': 'none'}
    log.debug('[%s] -> %s', n_close, style)
    return style


@app.callback(
    dd.Output(ID('modal-timer'), 'interval'),
    [dd.Input(ID('modal-1'), 'style'),
     dd.Input(ID('modal-timer'), 'n_intervals')],
    [dd.State('app-nav', 'children')])
def toggle_updates(style, nvals, nav):
    'stop updating if there is no QueryHandler for nav anymore'
    ON = '500'       # once/second
    OFF = '86400000'  # once/day
    nav = utils.UrlNav(*json.loads(nav))
    qh = QueryHandler.find(nav.test_id)
    rv = ON if qh and qh.running else OFF
    msg = 'running -> ON' if qh and qh.running else 'not found -> OFF'
    log.debug('QueryHandler(%s) - %s', nav.test_id, msg)
    return rv


@app.callback(
    dd.Output(ID('modal-text'), 'children'),
    [dd.Input(ID('modal-timer'), 'n_intervals')],
    [dd.State('app-nav', 'children'),
     dd.State(ID('modal-text'), 'children')])
def update_modal(nvals, nav, kids):
    'display QueryHandler.msgs while it is running'
    nav = utils.UrlNav(*json.loads(nav))
    log.debug('[%s] update_modal', nvals)
    qh = QueryHandler.find(nav.test_id)
    if qh and qh.running:
        log.debug(' - return %s QueryHandler.msgs', len(qh.msgs))
        return html.Pre('\n'.join(qh.msgs))
    log.debug(' - returning %s kids', len(kids))
    return kids



