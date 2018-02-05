'''
Mantra - compile-a-test page
'''

import json
import dash_html_components as html
import dash.dependencies as dd

from app import app
from app_tests import TESTS

path = '/_mantra/compile'
PATH = path
CACHE = 'app-cache-{}'.format(PATH)
DISPLAY = 'app-display-{}'.format(PATH)


# - Page Layout
_layout = html.Div([
    html.Div(
        [html.Div('Compiling: '),
         html.Div('no tgt', id='compile-target'),
         ]
    ),
    html.Div(id=DISPLAY),
    html.Div(id='compile-display'),
])


def layout(app_nav, cached):
    print('compile layout:')
    print('  <--reads--', cached, type(cached))
    print('  <--reads--', app_nav, type(app_nav))
    tgt = app_nav.get('test_id', 'No TaRgeT')
    obj = _layout.get('compile-target', None)
    if obj:
        setattr(obj, 'children', tgt)
    if cached is None:
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
    cache = json.loads(cache) if cache else [
        ('id', 'property', 'value')
    ]
    app_nav = json.loads(app_nav)
    print('compile cache')
    print('  --store-->', cache)
    print('  --saw---->', app_nav)
    return json.dumps(cache)


@app.callback(
    dd.Output(DISPLAY, 'children'),
    [dd.Input('app-nav', 'children'),
     dd.Input(CACHE, 'children')])
def display(app_nav, cached):
    print('compile display')
    print('   <--read--', cached, type(cached))
    print('   <--read--', app_nav, type(app_nav))
    app_nav = json.loads(app_nav)
    cached = json.loads(cached)
    tgt = app_nav.get('test_id', None)
    if tgt is None:
        return html.Div('target {} is unknown'.format(tgt))
    rv = []
    for test in TESTS:
        if test['test_id'] == tgt:
            rv.append(test)
    return html.Div(json.dumps(rv))
