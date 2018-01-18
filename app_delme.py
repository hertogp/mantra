'''
Mantra - delme page
'''

import dash_html_components as html
import dash.dependencies as dd

from app import app


app.pages['/delme'] = html.Div([
    'this is the delme page',
    html.Button('Click me not',
                id='delme-button',
                n_clicks=0),
    html.Pre('this will get updated',
             id='delme-output')
])


@app.callback(
    dd.Output('delme-output', 'children'),
    [dd.Input('delme-button', 'n_clicks')])
def set_output(clicks):
    print('delme button clicked', clicks)
    return html.Pre('delme was clicked {} times'.format(clicks))
