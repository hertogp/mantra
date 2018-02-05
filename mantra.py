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

# pylint: disable=block-comment-should-start-with-#, E265

#-- LAYOUT

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
    [dd.Input('app-url', 'pathname')])
def app_nav(pathname):
    'set pathname, page_id, cache_id & test_id based on pathname'
    pathname = pathname if pathname else '/'

    if pathname.startswith('/{}/'.format(CONFIG['quizdir'])):
        parts = pathname.split('/')
        page_id = '/'.join(parts[0:3])
        test_id = parts[-1]
    else:
        page_id = pathname
        test_id = ''

    cache_id = 'app-cache-{}'.format(page_id)
    app_nav = {
        'pathname': pathname,
        'test_id': test_id,
        'cache_id': cache_id,
        'page_id': page_id
    }
    print('app-nav', app_nav)
    return json.dumps(app_nav)


@app.callback(
    dd.Output('app-page', 'children'),
    [dd.Input('app-nav', 'children')],
    [dd.State('app-cache', 'children')])
def goto_page(app_nav, app_cache):
    app_nav = json.loads(app_nav)
    pathname = app_nav.get('pathname', '/')
    page_id = app_nav.get('page_id', '/')
    cache_id = app_nav.get('cache_id', '')
    print('goto_page', pathname)

    all_caches = [x['props'] for x in app_cache]
    page_cache = None
    for cache in all_caches:
        if cache['id'] == cache_id:
            kids = cache.get('children', None)
            if kids and len(kids) > 0:
                page_cache = json.loads(kids)
                print('cache_id', cache_id, page_cache)

    page = PAGES.get(page_id, None)
    if page is None:
        return html.Div('404 - {!r} - not found'.format(pathname))
    return page.layout(app_nav, page_cache)


@app.callback(
    dd.Output('app-menu-content', 'children'),
    [dd.Input('app-menu-content', 'n_clicks'),
     dd.Input('app-nav', 'children')],
    [dd.State('app-menu-content', 'children')])
def set_active_link(clicks, app_nav, menu_items):
    app_nav = json.loads(app_nav)
    pathname = app_nav.get('pathname', '/')
    print('set_active_link', pathname)
    # pathname = '/' if pathname is None else pathname
    page = PAGES.get(pathname, None)
    page_path = '' if page is None else page.path
    for item in menu_items:
        prop = item['props']
        href = prop.get('href', None)
        prop['className'] = 'active' if href == page_path else ''
    return menu_items


if __name__ == '__main__':
    app.run_server(debug=True)
