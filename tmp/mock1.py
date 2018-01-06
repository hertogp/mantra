'''
mockup of mantra layout
'''

import json
import dash
import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html

# to serve fontawesome locally
import os
from flask import send_from_directory

# pylint disable: E265
#-- 1 app instance

#<link href="https://use.fontawesome.com/releases/v5.0.2/css/all.css" rel="stylesheet">
#<script defer src="https://use.fontawesome.com/releases/v5.0.2/js/all.js"></script>


app = dash.Dash()
app.config['suppress_callback_exceptions'] = True
# app.css.append_css({
#     'external_url': 'https://use.fontawesome.com/releases/v5.0.2/css/all.css'
# })
app.css.config.serve_locally = True

stylesheets = html.Div([
    html.Link(rel='stylesheet', href='/static/css/chriddyp.css'),
    html.Link(rel='stylesheet', href='/static/css/fontawesome-all.css'),
])
#-- 2 app layout

content_top = [
    html.Div([html.I(className='fab fa-themeisle fa-3x',
                     style={
                        'color': 'midnightblue',
                        'display': 'inline-block',
                     }),
              html.Label(['__MANTRA__'],
                         style={
                             'display': 'inline-block',
                             'font-family': 'Monaco, Monospace',
                             'font-size': '32px'
                             # 'float': 'right'
                         }),
              ]),

    html.Div([
        html.Div([
            # html.B('Filter tests'),
            dcc.Dropdown(
                id='quiz-filter-exams',
                options=[
                    {'value': 'any', 'label': 'Any'},
                    {'value': 'cisco', 'label': 'Cisco'},
                    {'value': 'ccna', 'label': 'CCNA'},
                    {'value': 'ccnp', 'label': 'CCNP'},
                    {'value': 'ccnq', 'label': 'CCNQ'},
                    {'value': 'ccn3', 'label': 'CCNR'},
                    {'value': 'ccns', 'label': 'CCNS'},
                    {'value': 'ccnt', 'label': 'CCNT'},
                ],
                value=[],
                multi=True,
                placeholder='Filter available tests ...',
            )],
                 style={'display': 'inline-block'},
                 className='four columns'
                 )
    ]),

    html.Div([
        # html.B('Select a test'),
        dcc.Dropdown(
            id='quiz_select',
            options=[
                {'value': 't1', 'label': 'test-1'},
                {'value': 't2', 'label': 'test-2'},
            ],
            value='',
            placeholder='Select a test ...'
        )],
             style={'display': 'inline-block'},
             className='eight columns'
    ),

    html.Div(
        className='twelve columns',
        style={'height': '5px',
               'background-color': 'powderblue'},)
]

pane_TOP = html.Div(
    id='pane-top',
    className='twelve columns',
    style={
        'height': '100%',
        'border-style': 'dashed',
        'border-width': '1px',
        'border-color': 'black',
        'background-color': 'powderblue'
    },
    children=content_top
)

content_left = [
    # Settings
    html.Label(
        html.B('Settings'),
        style={'margin': '0 0 5px 0',
               'border-style': 'solid',
               'border-width': '0 0 1px 0',
               'border-color': 'light-grey'}
    ),

    # EXAM MODE
    html.Div([
        html.Label('Exam mode',
               style={
                   'display': 'inline-block',
                   'width': '50%',
                   }
               ),
        dcc.RadioItems(
            id='quiz-mode',
            options=[
                {'value': 'exam', 'label': 'Exam'},
                {'value': 'train', 'label': 'Train'},
                {'value': 'flash', 'label': 'Flash'}
            ],
            value='train',
            style={
                'display': 'inline-block',
                'width': '50%',
                # 'height': '1.1em',
                },
            labelStyle={'display': 'inline'},
        ),
    ]),

    # MAX QUESTIONs
    html.Div([
        html.Label('Max questions',
               style={'display': 'inline-block', 'width': '50%'}
               ),
        dcc.Input(
            id='quiz-max-questions',
            type='number',
            min=0,
            value=10,
            style={'display': 'inline-block',
                   'width': '5em',
                   'height': '1.5em'
                   },
            placeholder='Max #questions',
        )
    ]),

    html.Div([
        html.Label('Randomize questions',
               style={'display': 'inline-block', 'width': '50%'}
               ),
        dcc.RadioItems(
            id='quiz-randomize-questions',
            options=[
                {'value': 'True', 'label': 'True'},
                {'value': 'False', 'label': 'False'}],
            value='True',
            style={'display': 'inline-block'},
            labelStyle={'display': 'inline'},
        )
    ]),

    html.Div([
        html.Label('Randomize responses',
                   style={'display': 'inline-block', 'width': '50%'}
                  ),
        dcc.RadioItems(
            id='qz-random-responses',
            options=[
                {'value': 'True', 'label': 'True'},
                {'value': 'False', 'label': 'False'}],
            value='True',
            style={'display': 'inline-block',
                   'height': '1.5em'
                   },
            labelStyle={'display': 'inline'}
        )
    ]),


    html.Div([
        # html.B('Filter Sections'),
        html.Div([
            dcc.Dropdown(
                id='quiz-filter-sections',
                options=[
                    {'value': 'any', 'label': 'Any'},
                    {'value': 'basics', 'label': 'Basics'},
                    {'value': 'switch', 'label': 'Swtich'},
                    {'value': 'routing', 'label': 'Routing'},
                    {'value': 'bgp', 'label': 'Bgp'},
                    {'value': 'ospf', 'label': 'Ospf'},
                    {'value': 'eigrp', 'label': 'Eigrp'},
                ],
                value=[],
                multi=True,
            placeholder='Select test sections ...')
        ]),
    ])
]

pane_LEFT = html.Div(
    id='pane-left',
    className='four columns',
    style={
        'height': '100%',
        'border-style': 'dashed',
        'border-width': '1px',
        'border-color': 'black',
    },
    children=content_left
)

pane_RIGHT = html.Div(
    id='pane-right',
    className='eight columns',
    style={
        'height': '100%',
        'border-style': 'dashed',
        'border-width': '1px',
        'border-color': 'black',
    },
    children=[
        'right-pane',
    ])


content_bottom = [
    html.Div([
        html.Button([
            html.I(className='far fa-play-circle fa-2x',
                   style={'color': 'green'}),
            ' Start']),

        html.Button([
            html.I(className='far fa-stop-circle fa-2x',
                   style={'color': 'green'}),
            ' Stop']),

        html.Button([
            html.I(className='far fa-pause-circle fa-2x',
                   style={'color': 'green'}),
            ' Pause'
        ]),

        html.Button([
            html.I(className='fas fa-step-backward fa-2x',
                   style={'color': 'green'}),
            ' Back'
        ]),

        html.Button([
            html.I(className='fas fa-step-forward fa-2x',
                   style={'color': 'green'}),
            ' Next'
        ]),

        html.Button([
            html.I(className='far fa-times-circle fa-2x',
                   style={'color': 'green'}),
            ' Quit'
        ]),

        html.Button([
            html.I(className='far fa-arrow-alt-circle-down fa-2x',
                   style={'color': 'green'}),
            ' Finish'
        ]),

        html.Button([
            html.I(className='fas fa-toggle-on fa-2x',
                   style={'color': 'green'})
        ]),

        html.Button([
            html.I(className='fas fa-toggle-off fa-2x',
                   style={'color': 'green'})
        ]),


    ]),


]

pane_BOTTOM = html.Div(
    id='pane-bottom',
    className='twelve columns',
    style={
        'height': '100%',
        'border-style': 'dashed',
        'border-width': '1px',
        'border-color': 'black',
    },
    children=content_bottom
)

pane_HIDDEN = html.Div(
    id='pane-hidden',
    style={'display': 'none'})


PAGE = [
    stylesheets,
    html.Div(pane_TOP,
             className='row',
             style={}),

    html.Div([pane_LEFT, pane_RIGHT],
             className='row',
             style={'height': '70vh'}),  #, 'display': 'block'}),
    html.Div([pane_BOTTOM],
             className='row',
             style={'height': '10vh'}),  #, 'display': 'block'}),
    pane_HIDDEN
]


app.layout = html.Div(PAGE, id='content',
                      style={'height': '100%'})


#-- 3 interaction

#-- 4 run the server

@app.server.route('/static/<path:path>')
def static_file(path):
    print('server route', path)
    static_folder = os.path.join(os.getcwd(), 'static')
    print('static_folder', static_folder)
    return send_from_directory(static_folder, path)


if __name__ == '__main__':
    app.run_server(debug=True)

