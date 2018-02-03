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

        html.Div(
            id='app-cache',
            style=STYLES['header-cache'],
            children=[
                html.Div(id='app-cache-{}'.format(
                    page.path)) for page in set(PAGES.values())
            ]),

    ], className='row'),
    html.Hr(),

    # BODY
    html.Div(
        html.Div(id='app-page'),
        className='row')
])


# -- Page Navigation
@app.callback(
    dd.Output('app-page', 'children'),
    [dd.Input('app-url', 'pathname')],
    [dd.State('app-cache', 'children')])
def goto_page(pathname, app_cache):
    print('goto_page', pathname)
    page_cache = []
    # set appropiate page_id as index into PAGES

    pathname = pathname if pathname else '/'
    if pathname.startswith('/_mantra/'):
        page_id = '/'.join(pathname.split('/')[0:3])
    else:
        page_id = pathname
    cache_id = 'app-cache-{}'.format(page_id)

    all_caches = [x['props'] for x in app_cache]
    for cache in all_caches:
        print('cache', cache)
        if cache['id'] == cache_id:
            kids = cache['children']  # might be None
            print('--> page_cache', cache_id, '=', kids)
            if kids and len(kids) > 0:
                page_cache = json.loads(kids)
                print('page_cache', page_cache)

    page = PAGES.get(page_id, None)
    if page is None:
        print('page mis', page_id, 'not found in', PAGES.keys())
        return html.Div('404 - {!r} - not found'.format(pathname))
    return page.layout(page_cache)


@app.callback(
    dd.Output('app-menu-content', 'children'),
    [dd.Input('app-menu-content', 'n_clicks'),
     dd.Input('app-url', 'pathname')],
    [dd.State('app-menu-content', 'children')])
def set_active_link(clicks, pathname, menu_items):
    pathname = '/' if pathname is None else pathname
    page = PAGES.get(pathname, None)
    page_path = '' if page is None else page.path
    for item in menu_items:
        prop = item['props']
        href = prop.get('href', None)
        prop['className'] = 'active' if href == page_path else ''
    return menu_items


if __name__ == '__main__':
    app.run_server(debug=True)
