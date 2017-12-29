'''
try getting the response only when clicking on the next button
'''

import json
import dash
import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html

from quiz_bridge import QUESTIONS
# globso
QUIZ_ID = 0
QUESTIONz = [
    {'title': '### Multiple *correct*',
     'text': 'Which flavors of **Markdown** are *not* supported by dash?',
     'type': 'mcorrect',
     'choices': ['*Commonmarkdown*',
                 '*Github* markdown',
                 '*Multimarkdown*',
                 ],
     'answer': ['B', 'C'],
     'response': []
     },
    {'title': '### Multiple-choice',
     'text': 'Which flavor of **Markdown** is supported by dash?',
     'type': 'mchoice',
     'choices': ['**All** markdown-flavors',
                 '*Commonmarkdown*',
                 '*Github Markdown*',
                 '*Multi-markdown*'
                 ],
     'answer': ['B'],
     'response': []
     },
]

# pylint disable: E265
#-- 1 app instance

app = dash.Dash()
app.config['suppress_callback_exceptions'] = True
app.css.append_css(
    {"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

#-- 2 app layout

PAGE = [
    html.Div(
        dcc.Markdown('<title>'), id='qtitle'),

    html.Div(
        dcc.Markdown('<text>'), id='qtext'),

    html.Div(
        html.Div(id='qresponse'),  # placeholder for state in callback
        id='qchoices'),            # container for response element

    html.Button('prev', id='qprev'),     # user controls
    html.Button('Finish', id='qfinish'),
    html.Button('next', id='qnext'),

    html.Div(
        json.dumps([0, 0, 0]),
        id='qidx',
        style={'display': 'none'}),  # [prevs, nxts, curidx]

    html.Div(
        id='qscore',
        style={'display': 'block'}),     # display score

    html.Div(
        json.dumps([0, {}]),
        id='qtrack',
        style={'display': 'none'}),      # (quiz_id, {qidx: answer})
    ]

app.layout = html.Div(PAGE)


#-- 3 interaction

def _idx(n):
    'turn n_clicks into offset into QUESTIONS'
    return 0 if n is None else abs(int(n % len(QUESTIONS)))


# subscribe to all possible triggers, even though they donot exist all
# at the same time (qresponse has either a values or a value trigger,
# but not both).  This requires to disable the callback exceptions in app.config

# register answer with current question before setting new question idx
@app.callback(
    dd.Output('qidx', 'children'),
    [dd.Input('qprev', 'n_clicks'),
     dd.Input('qnext', 'n_clicks')],
    [
        dd.State('qidx', 'children'),
        dd.State('qresponse', 'values'),
        dd.State('qresponse', 'value'),
    ])
def setQidx(prev, nxt, curidx, *vals):
    'set the new question index'
    # Notes:
    # - this will trigger the update of the screen
    # - n_clicks is None of nr of times the button was clicked
    # - `-> is always provided when callback fires, even if the
    #   button wasn't pressed.
    # - so you need to compare the current n_clicks with the
    #   previous value to see if it has changed, which means this
    #   is the button actually pressed.
    prevs, nxts, curidx = json.loads(curidx)
    curidx += 1 if nxts != nxt else 0    # maybe nxt was clicked
    curidx -= 1 if prevs != prev else 0  # or prev was clicked
    curidx = max(curidx, 0)
    curidx = min(curidx, len(QUESTIONS)-1)
    return json.dumps([prev, nxt, curidx])


@app.callback(
    dd.Output('qtrack', 'children'),
    [dd.Input('qresponse', 'values'),
     dd.Input('qresponse', 'value')],
    [dd.State('qidx', 'children'),
     dd.State('qtrack', 'children')])
def setQtrack(val1, val2, idx, track):
    'keep track of responses given'
    # Notes:
    # - 'subscribe' to all possible qresponse-triggers
    # - only 1 of value/values will actually exist
    # - Div qidx to get current question idx
    # - Div track to record values as soon as clicked, otherwise we would need
    #   to do this work in multiple places (for all buttons)
    response = [] if val1 is None else val1
    if val2 is not None:
        response.append(val2)
    response = sorted(response)
    _, _, curidx = json.loads(idx)
    qid, responses = json.loads(track)
    responses[str(curidx)] = response
    return json.dumps([qid, responses])


# goto next question
@app.callback(
    dd.Output('qchoices', 'children'),
    [dd.Input('qidx', 'children')],
    [dd.State('qtrack', 'children')])
def setQchoices(val, track):
    'set choices part of the question'
    # Notes:
    # - get curidx from Div qidx
    # - get previous response (if any) from Div track
    prevs, nxts, curidx = json.loads(val)
    q = QUESTIONS[curidx]
    quiz_id, responses = json.loads(track)
    options = [{'label': v,
                'value': chr(65+k)} for k, v in enumerate(q['choices'])]
    response = responses.get(str(curidx), [])
    if q['type'] == 'mcorrect':
        return dcc.Checklist(options=options,
                             values=response,
                             id='qresponse')
    else:
        response = response[0] if len(response) else None
        return dcc.RadioItems(options=options,
                              value=response,
                              id='qresponse')


# set the score board based on answers given
@app.callback(
    dd.Output('qscore', 'children'),
    [dd.Input('qfinish', 'n_clicks')],
    [dd.State('qtrack', 'children')])
def setQscore(n_clicks, track):
    'update end score of the quiz'
    score = 0
    quiz_id, responses = json.loads(track)
    for idx, q in enumerate(QUESTIONS):
        curidx = str(idx)
        if q['answer'] != responses.get(curidx, []):
            print(q['answer'], '!=', responses.get(curidx,[]), '!!')
            continue
        score += 1
    return 'Your score is {}/{} ({}%)'.format(score,
                                              len(QUESTIONS),
                                              int(100*(score/len(QUESTIONS))))


# next question's title
@app.callback(
    dd.Output('qtitle', 'children'),
    [dd.Input('qidx', 'children')])
def setQtitle(val):
    print('setQtitle', val)
    prevs, nxts, curidx = json.loads(val)
    return dcc.Markdown(QUESTIONS[curidx].get('title', '<title>'))

# next question's text
@app.callback(
    dd.Output('qtext', 'children'),
    [dd.Input('qidx', 'children')])
def setQtext(val):
    prevs, nxts, curidx = json.loads(val)
    return dcc.Markdown(QUESTIONS[curidx].get('text', '<oops>'))

#-- 4 run the server

if __name__ == '__main__':
    app.run_server(debug=True)

