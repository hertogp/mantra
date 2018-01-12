import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd

from utils import Jsonify

from config import CONFIG

#-- HEADER

stylesheets = html.Div([
    html.Link(rel='stylesheet', href=x) for x in CONFIG['stylesheets']
])


HEADER = html.Div(
    # ROW with themeisle and logo
    [
        html.I(className='fab fa-themeisle fa-2x',
               style={
                   'color': 'black',
                   'display': 'inline-block',
               }),
        html.Pre(' ', style={'display': 'inline-block'}),
        html.Img(src=CONFIG['logo'],
                 # className='eight columns',
                 style={'max-height': '30px',
                        'max-width': '400px',
                        'display': 'inline-block'})
    ], className='row')


#-- BODY

BODY = html.Div([

    html.Div(
        html.Table([
            html.Tr([html.Td(x) for x in ['a', 'b', 'c']],
                    id='myt-0', n_clicks=0, className='row-selected'),
            html.Tr([html.Td(x) for x in [1, 2, 3]],
                    id='myt-1', n_clicks=0, className=''),
            html.Tr([html.Td(x) for x in [4, 5, 6]],
                    id='myt-2', n_clicks=0, className='')
        ], id='my-table', className='five columns'),
        className='row'),

    html.Hr(),

    html.Div('[0, [0, 0, 0]]',
             id='stash-qz-choice', style={'display': 'none'}),
])


#-- LAYOUT

LAYOUT = html.Div(
    [
        stylesheets,
        HEADER,
        BODY
    ])

print('-'*80, 'LAYOUT')
jsondump = Jsonify(indent=4).encode
print(jsondump(LAYOUT))
