# -*- encoding: utf8 -*-

import json
import dash
import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html
from flask import send_from_directory

# mantra imports
import utils
import config
import layout
jsondump = utils.Jsonify(indent=4).encode

# pylint disable: E265


# -- 0 config
CONFIG = config.CONFIG

# -- 1 app instance
app = dash.Dash('__MANTRA__')
app.config['suppress_callback_exceptions'] = True
# app.css.config.serve_locally = True
# - not needed due to app.server.route
print('-'*80, 'APP')
print(dir(app))
print('- config', app.config)
print('-'*80)

# -- 2 app layout

app.layout = layout.LAYOUT

# -- 3 routing url's

# the app.server.route('/static/<path:path>') eats the '/static/':
# - path won't have the leading static part
# - but app.server.route('/<path:path>' won't work
# - so root dir needs to end with ../static
@app.server.route('/static/<path:path>')
def serve_static(path):
    print('serve_static', path)
    return send_from_directory(CONFIG['root'], path)


@app.server.route('/favicon.ico')
def serve_favicon():
    # browser GET /favicon.ico for every page refresh/load
    # - favicon must exist as a real file (png, gif or ico)
    # - must be 16x16 or 32x32 pixels with 8- or 24-bit colors
    print('favicon')
    print('returning', CONFIG['favicon'])
    return send_from_directory(CONFIG['root'], CONFIG['favicon'])

# -- 4 interaction

@app.callback(
    dd.Output('stash-qz-choice', 'children'),
    [dd.Input('myt-{}'.format(x), 'n_clicks') for x in range(3)],
    [dd.State('stash-qz-choice', 'children')])
def _stash_qz_choice(*args):
    cur, prev = json.loads(args[-1])
    now = args[0:-1]
    for idx, (p, n) in enumerate(zip(prev, now)):
        if n > p:
            cur = idx
            break

    print('stash', cur, prev, '-', now)
    return json.dumps([cur, now])

# - qz-choice --> row selection callbacks
#   click on row and change its class (+/- row-selected)
def _row_selection_callback(row):
    def callback(choice, cname):
        print('selection_callback', row)
        cur, prev = json.loads(choice)
        if cur == row:
            if 'row-selected' not in cname:
                return (cname + ' row-selected').strip()
            return cname
        else:
            return cname.replace('row-selected', '').strip()
    return callback

# create table row callbacks
for ROW in range(3):
    app.callback(
        dd.Output('myt-{}'.format(ROW), 'className'),
        [dd.Input('stash-qz-choice', 'children')],
        [dd.State('myt-{}'.format(ROW), 'className')])(
            _row_selection_callback(ROW))

print(jsondump(app.callback_map))

if __name__ == '__main__':
    app.run_server(debug=True)
