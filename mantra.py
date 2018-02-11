# -*- encoding: utf8 -*-
import os
import json
import urllib.parse

import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html

# mantra imports
import utils
from config import CONFIG
# Mantra app and pages: app_<page>'s
from app import app
import app_tests
import app_review
import app_upload
import app_settings
import app_compile


# - Module logger
log = app.getlogger(__name__)
log.debug('logger enabled')


# - Helpers
def urlparms(href):
    'turn href into dict with mantra-fields'
    # Mantra uses the following scheme:
    # - url = scheme://usr:pwd@netloc:8050/path;param?query=arg#frag
    #   - parts after path are optional
    #   - param, if present, is always a unique test_id
    #   - qry=arg[;q2=arg2,..], if any, is meaningful only to app_<path>
    #   - frag, if any, is a single fragment, meaningful only to app_<path>
    # - examples:
    #   - /compile;test_id
    #   - /run;test_id?q=qid
    # - parsed.query := dict, repeated <param>=arg collapse into last one seen
    href = href if href else '/'
    log.debug('href %s', href)
    parsed = urllib.parse.urlparse(href)
    nav = {
        'href': href,
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path if parsed.path else '/',
        'param': parsed.params if parsed.params else '',
        'query': dict(urllib.parse.parse_qs(parsed.query)),
        'fragments': parsed.fragment,
        'username': parsed.username,
        'password': parsed.password,
        'hostname': parsed.hostname,
        'port': parsed.port,
    }

    # mantra specifics
    test_id = parsed.params if parsed.params else ''
    test_dir = os.path.join(CONFIG['dst_dir'], test_id)

    nav['page_id'] = parsed.path if parsed.path else '/'
    nav['test_id'] = test_id
    nav['test_dir'] = os.path.join(CONFIG['dst_dir'], test_id)
    nav['test_log'] = os.path.join(test_dir, 'cmp.log')
    nav['test_lock'] = os.path.join(test_dir, 'cmp.lock')
    nav['controls'] = utils.get_domid('controls', parsed.path)  # 'app-controls-{}'.format(parsed.path)
    nav['vars'] = utils.get_domid('vars', parsed.path)  # 'app-variables-{}'.format(parsed.path)
    log.debug('nav %s', nav)
    return nav


# pylint: disable=block-comment-should-start-with-#, E265

# -- LAYOUT

PAGES = {
    '/': app_tests,
    app_tests.PATH: app_tests,
    app_review.PATH: app_review,
    app_upload.PATH: app_upload,
    app_settings.PATH: app_settings,
    app_compile.PATH: app_compile,
}

STYLES = {
    'header-fa': {
        'color': 'black',
        'display': 'inline-block',
    },
    'header-logo': {
        'display': 'inline-block',
        'max-height': '30px',
        'max-width': '400px',
    },
    'header-menu': {},
    'header-spacer': {
        'display': 'inline-block',
    },
    'header-hidden': {
        'display': 'none'
    },
    'header-banner': {
        'border-width': '0px 0px 1px 0px',
        'border-style': 'solid',
        'border-color': 'lightgrey',
        'margin-bottom': '15px',
        'padding-bottom': '0px',
    }

}

STYLESHEETS = [
    html.Link(rel='stylesheet', href=x) for x in CONFIG['stylesheets']
]

app.layout = html.Div([
    # HEADER, same across all pages
    html.Div([
        dcc.Location(id='app-url', refresh=False),
        html.Div(STYLESHEETS),
        html.I(className='fab fa-themeisle fa-2x', style=STYLES['header-fa']),
        html.Pre('  ', style=STYLES['header-spacer']),
        html.Img(src=CONFIG['logo'], style=STYLES['header-logo']),
        html.Div(id='app-menu',
                 className="dropdown",
                 children=[
                     html.I(className='fa fa-bars fa-3x dropbtn'),
                     html.Div(
                         className='dropdown-content',
                         id='app-menu-content',
                         children=[
                             dcc.Link('tests', href='/tests'),
                             dcc.Link('review', href='/review'),
                             dcc.Link('upload', href='/upload'),
                             dcc.Link('settings', href='/settings'),
                         ]
                     ),
                 ]),
        # store current pathname + derived variables for all pages
        html.Div(id='app-nav', style=STYLES['header-hidden']),

        # create page specific caches for controls and variables per page
        html.Div(
            id='app-controls',
            style=STYLES['header-hidden'],
            children=[
                html.Div(id=utils.get_domid('controls', page.PATH)) for page
                in set(PAGES.values())
            ]),

        html.Div(
            id='app-vars',
            style=STYLES['header-hidden'],
            children=[
                html.Div(id=utils.get_domid('vars', page.PATH))
                for page in set(PAGES.values())
            ]),

    ],
             style=STYLES['header-banner'],
             className='row'),

    # BODY
    html.Div(
        html.Div(id='app-page'),
        className='row')
])


# -- Page Navigation
@app.callback(
    dd.Output('app-nav', 'children'),
    [dd.Input('app-url', 'href')])
def app_nav(href):
    'update app-nav with url called'
    log.debug('href %s', href)
    nav = urlparms(href)
    log.debug('app-nav %s', nav)
    return json.dumps(nav)


@app.callback(
    dd.Output('app-page', 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State('app-controls', 'children')])
def goto_page(app_nav, app_controls):
    'navigate to page using app-nav contents'
    app_nav = json.loads(app_nav) if app_nav else {}
    log.debug('goto nav %s', app_nav)
    page_id = app_nav.get('page_id', '/')
    ctrl_id = app_nav.get('controls', '')
    log.debug('goto page_id %s', page_id)

    cache = [x['props'] for x in app_controls if x['props']['id'] == ctrl_id]
    cache = cache[0].get('children', None) if len(cache) else None
    page_cache = json.loads(cache) if cache else None

    page = PAGES.get(page_id, None)
    if page is None:
        return html.Div('404 - {!r} - not found'.format(page_id))
    log.debug('calling layout for page_id %s', page_id)
    return page.layout(app_nav, page_cache)


@app.callback(
    dd.Output('app-menu-content', 'children'),
    [dd.Input('app-menu-content', 'n_clicks'),
     dd.Input('app-nav', 'children')],
    [dd.State('app-menu-content', 'children')])
def set_active_link(clicks, app_nav, menu_items):
    'set active classname on menuitem if its page is current'
    app_nav = json.loads(app_nav)
    page_path = app_nav.get('path', '/')
    for item in menu_items:
        prop = item['props']
        href = prop.get('href', None)
        prop['className'] = 'active' if href == page_path else ''
    log.debug('returning %s', len(menu_items))
    return menu_items


if __name__ == '__main__':
    app.run_server(debug=True)
