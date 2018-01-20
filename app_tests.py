'''
Mantra - test selection page
'''

import dash_html_components as html
import dash.dependencies as dd

from app import app
from utils import Proxy

path = '/tests'

layout = html.Div([
    __doc__,
    Proxy(
        html.Div([
            'proxied div',
            Proxy(html.Button('click me', id='delme')),
        ], id='blah-blah'))

])


# @app.callback(
#     dd.Output('delme-output', 'children'),
#     [dd.Input('delme-button', 'n_clicks')])
# def set_output(clicks):
#     print('delme button clicked', clicks)
#     return html.Pre('delme was clicked {} times'.format(clicks))
