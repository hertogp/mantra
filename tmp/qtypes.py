'''
Showing different question types
'''

import json
import dash
import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html

# globs

# pylint disable: E265
#-- 1 app instance

app = dash.Dash()
app.config['suppress_callback_exceptions'] = True
app.css.append_css(
    {"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

#-- 2 app layout

PAGE = [
    dcc.Dropdown(
        options=[
            {'label': 'Multiple choice', 'value': 'mchoice'},
            {'label': 'Multiple response', 'value': 'mresponse'},
            {'label': 'True/False', 'value': 'yesno'},
            {'label': 'Pick list', 'value': 'plist'},
            {'label': 'Order list', 'value': 'olist'},
            {'label': 'Match lists', 'value': 'mlist'},
            {'label': 'Fill blank', 'value': 'fblank'}
        ],
        value='',
        id='select-qtype'
    ),

    html.Div(id='page-content'),
    html.Hr(),
    html.Div(id='response-output')
    ]

app.layout = html.Div(PAGE)

#-- Question types
QTYPE = {
    'mchoice': [
        html.H3('Multiple choice'),

        dcc.Markdown('A multiple *choice* question requires only 1 answer '
                     'and is created using a `dcc.RadioItems` element.'
                     '- check its `value` property'),

        dcc.RadioItems(
            options=[
                {'value': 'A', 'label': 'A. Complete nonsense'},
                {'value': 'B', 'label': 'B. That is entirely correct'},
                {'value': 'C', 'label': 'C. Only half true'},
            ],
            value='',
            id='response'
        )

    ],

    'mresponse': [
        html.H3('Multiple response'),

        dcc.Markdown('A multiple *response* question can have multiple answers '
                     'and is created using a `dcc.Checklist` element.'
                     '- check its `values` property'),

        dcc.Checklist(
            options=[
                {'value': 'A', 'label': 'A. Complete nonsense'},
                {'value': 'B', 'label': 'B. That is entirely correct'},
                {'value': 'C', 'label': 'C. Only half true'},
            ],
            values=[],
            id='response',
            className='mresponse'
        )

    ],

    'yesno': [
        html.H3('True or False'),

        dcc.Markdown('A *True or False* question requires only 1 answer '
                     'and is created using a `dcc.RadioItems` element.'
                     '- check its `value` property'),

        dcc.RadioItems(
            options=[
                {'value': 'A', 'label': 'A. True'},
                {'value': 'B', 'label': 'B. False'},
            ],
            value='',
            id='response',
            className='yesno'
        )
    ],

    'plist': [
        html.H3('Pick list'),

        dcc.Markdown('A Pick list is a question where you select 1 value from '
                     'one or more dropdown lists to match/complete a sentence '
                     'or statement and is created with Dropdown\'s.'),

        html.Div(['To be, or not to ',

                  html.Div([
                      dcc.Dropdown(
                          id='response',
                          options=[
                              {'value': 'A', 'label': 'are'},
                              {'value': 'B', 'label': 'be'},
                              {'value': 'C', 'label': 'been'}
                          ],
                          value='',
                          )],
                           style={'display': 'inline-block',
                                  'height': '23px',
                                  'width': '110px'}),
                  ',that\'s the ',

                  html.Div([
                      dcc.Dropdown(
                          id='response-2',
                          options=[
                              {'value': 'A', 'label': 'answer'},
                              {'value': 'B', 'label': '42'},
                              {'value': 'C', 'label': 'question'},
                          ],
                          value='',
                      )],
                      style={'display': 'inline-block',
                             'height': '23px',
                             'width': '110px'}),
                  ])

    ],

    'olist': [
        html.H3('Order list'),

        dcc.Markdown('Order a list is a question where you get to rearrange '
                     'the order of the entries in a list.  In the question text '
                     'you just give the correct order, rendering the question '
                     'takes care of randomizing the given order before '
                     'displaying it on the page.  It is created using a simple '
                     'unordered list and a special js-script that will allow '
                     'dragging and dropping of items in the list'),

        html.Ul([
            html.Li('The unordered list', draggable=True),
            html.Li('is not handy to', draggable=True),
            html.Li('to wield in this case', draggable=True)
        ], id='reponse'),

        dcc.Markdown('So all the list dragndrop stuff probably requires a new '
                     'dcc component to be built via de dash plugin system that '
                     'allow extensions of dash via react components'),


    ],

    'mlist': [
        html.H3('Match lists'),

        dcc.Markdown('See **Order list**, same applies here'),

    ],

    'fblank': [
        html.H3('Fill in the blank'),

        dcc.Markdown('This question type allows the user to fill in '
                     'a word in order to complete a sentence'),

        html.P(['To be or not to ',
                dcc.Input(value='',
                          placeholder='type an answer',
                          type='text'),
                'That\'s the question.'
                ]),

        dcc.Markdown('Apparently, you can inline a dcc.Component by listing it '
                     'as a child in the list of children of a html container'),
    ],

}
#-- 3 interaction

# subscribe to all possible triggers, even though they donot exist all
# at the same time (qresponse has either a values or a value trigger,
# but not both).  This requires to disable the callback exceptions in app.config

# register answer with current question before setting new question idx
@app.callback(
    dd.Output('page-content', 'children'),
    [dd.Input('select-qtype', 'value')])
def setPageContent(value):
    'show the new question'
    # Notes:
    qstn = QTYPE.get(value, value)
    return qstn

@app.callback(
    dd.Output('response-output', 'children'),
    [dd.Input('response', 'value'),
     dd.Input('response', 'values')])
def setResponseOutput(*kids):
    k1 = '{}'.format(kids[0])
    k2 = '{}'.format(repr(kids[1]))
    return html.Div([
        html.P('response value ' + k1),
        html.P('response values ' + k2)
    ])

#-- 4 run the server

if __name__ == '__main__':
    app.run_server(debug=True)

