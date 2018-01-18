'''
Mantra - delme page
'''

import dash_html_components as html
import dash.dependencies as dd

from app import app

print('>'*45, 'DELME2', app)
path = '/delme2'

layout = html.Div([
    'this is the delme2 page',
    html.Button('Click me please',
                id='please-button',
                n_clicks=0),
    html.Pre('this will get updated',
             id='please-output')
])


@app.callback(
    dd.Output('please-output', 'children'),
    [dd.Input('please-button', 'n_clicks')])
def set_output(clicks):
    print('please button clicked', clicks)
    return html.Pre('please was clicked {} times'.format(clicks))
