# -*- encoding: utf8 -*-
import json
import dash.dependencies as dd
import dash_core_components as dcc
import dash_html_components as html

# mantra imports
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
def urlparams(fragment):
    'create dict from params in fragments like {?,#}p1=v1&p2=v2&...'
    # ignore parts without an '=' in them
    if fragment is None or len(fragment) < 4:
        return {}
    parts = [x.split('=') for x in fragment[1:].split('&')]
    # ignore fragments that are not param=value
    return dict(x for x in parts if len(x) == 2)

# pylint: disable=block-comment-should-start-with-#, E265

# -- LAYOUT

PAGES = {
    '/': app_tests,
    app_tests.path: app_tests,
    app_review.path: app_review,
    app_upload.path: app_upload,
    app_settings.path: app_settings,
    app_compile.path: app_compile,
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
    'header-cache': {
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
        html.Div(id='app-nav', style=STYLES['header-cache']),
        # create page specific caches for controls amongst others
        html.Div(
            id='app-cache',
            style=STYLES['header-cache'],
            children=[
                html.Div(id='app-cache-{}'.format(
                    page.path)) for page in set(PAGES.values())
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
    [dd.Input('app-url', 'pathname'),
     dd.Input('app-url', 'hash'),
     dd.Input('app-url', 'search')])
def app_nav(pathname, urlhash, urlsearch):
    'set pathname, page_id, cache_id & test_id based on pathname'
    pathname = pathname if pathname else '/'
    log.debug('app_nav pathname %s', pathname)
    log.debug('app_nav hash %s', urlhash)
    log.debug('app_nav search %s', urlsearch)

    app_nav = {
        'cache_id': 'app-cache-{}'.format(pathname),
        'page_id': pathname,
        'url': '{}{}{}'.format(pathname, urlsearch, urlhash),
        'search': urlparams(urlsearch),
        'hash': urlparams(urlhash),
    }
    log.debug('app-nav %s', app_nav)
    return json.dumps(app_nav)


@app.callback(
    dd.Output('app-page', 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State('app-cache', 'children')])
def goto_page(app_nav, app_cache):
    app_nav = json.loads(app_nav)
    page_id = app_nav.get('page_id', '/')
    cache_id = app_nav.get('cache_id', '')
    log.debug('goto page %s', page_id)

    cache = [x['props'] for x in app_cache if x['props']['id'] == cache_id]
    cache = cache[0].get('children', None) if len(cache) else None
    page_cache = json.loads(cache) if cache else None
    log.debug('%s read cache %s', cache_id, page_cache)

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
    app_nav = json.loads(app_nav)
    pathname = app_nav.get('pathname', '/')
    log.debug('active link in menu is %s', pathname)
    page = PAGES.get(pathname, None)
    page_path = '' if page is None else page.path
    for item in menu_items:
        prop = item['props']
        href = prop.get('href', None)
        prop['className'] = 'active' if href == page_path else ''
    log.debug('returning %s', len(menu_items))
    return menu_items


if __name__ == '__main__':
    app.run_server(debug=True)
