'''
Mantra - compile-a-test page
'''

import json
import dash_html_components as html
import dash.dependencies as dd

from app import app
from app_tests import TESTS

path = '/_mantra/compile'


def layout(cached):
    if cached is None:
        return _layout
    print('compile.layout(cached), cached:', cached)
    for ctl_id, attr, value in cached:
        setattr(_layout[ctl_id], attr, value)
    return _layout

_layout = html.Div([
    html.Div(id='compile-target',
             children='no target'),
    html.Div(id='compile-display'),
])


#-- Page Cache
@app.callback(
    dd.Output('app-cache-{}'.format(path), 'children'),
    [dd.Input('app-url', 'pathname')])
def cache_page(url):
    url = str(url)  # None becomes 'None' if applicable
    cached = json.dumps(
        [('compile-target', 'children', 'target is {}'.format(url))]
    )

    print('compile.cache_page:', cached)
    return str(cached)
