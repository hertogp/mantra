'''
Mantra - upload page
'''

import dash_html_components as html

from app import app

PATH = '/upload'

def layout(nav, controls):
    return _layout

_layout = html.Div([
     __doc__
])


# @app.callback(
#     dd.Output('delme-output', 'children'),
#     [dd.Input('delme-button', 'n_clicks')])
# def set_output(clicks):
#     print('delme button clicked', clicks)
#     return html.Pre('delme was clicked {} times'.format(clicks))
