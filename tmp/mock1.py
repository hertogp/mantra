'''
setting layout
'''

import json
import dash
import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html


# pylint disable: E265
#-- 1 app instance

app = dash.Dash()
app.config['suppress_callback_exceptions'] = True
app.css.append_css(
    {"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

#-- 2 app layout

p_LEFT = html.Div([
    'left',
])

p_MIDDLE = html.Div([
    'middle',
])

p_RIGHT = html.Div([
    'right',
])

p_HIDDEN = html.Div(['hidden'],
                    style={'display': 'none'})


PAGE = [
    html.Div(p_LEFT,
             id='p_left',
             className="three columns"),

    html.Div(p_MIDDLE,
             id='p_middle',
             className='seven columns'),

    html.Div(p_RIGHT,
             id='p_right',
             className='two columns'),

    html.Div(p_HIDDEN,
             id='p_hidden',
             style={'display': 'none'}),
]

app.layout = html.Div(PAGE,
                      id='content',
                      className='row')


#-- 3 interaction

#-- 4 run the server

if __name__ == '__main__':
    app.run_server(debug=True)

