# -*- encoding: utf8 -*-
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

PAGES = {
    '/': app_tests,
    app_tests.path: app_tests,
    app_review.path: app_review,
    app_upload.path: app_upload,
    app_settings.path: app_settings,
}


app.layout = html.Div([
    # HEADER, same across all pages
    html.Div([
        dcc.Location(id='mtr-url'),

        html.Div([
            html.Link(rel='stylesheet',
                      href=x) for x in CONFIG['stylesheets']
        ]),

        html.I(
            className='fab fa-themeisle fa-2x',
            style={
                'color': 'black',
                'display': 'inline-block',
            }
        ),

        html.Pre('    ', style={'display': 'inline-block'}),
        html.Img(
            src=CONFIG['logo'],
            style={'max-height': '30px',
                   'max-width': '400px',
                   'display': 'inline-block'}
        ),

        html.Div(
            className="dropdown",
            id='mtr-menu',
            children=[
                html.I(className='fa fa-bars fa-3x dropbtn'),
                html.Div(
                    className='dropdown-content',
                    id='mtr-menu-content',
                    children=[
                        dcc.Link('tests', href='/tests'),
                        dcc.Link('review', href='/review'),
                        dcc.Link('upload', href='/upload'),
                        dcc.Link('settings', href='/settings'),
                    ]
                ),
            ]
        ),

        html.Div(
            id='mtr-cache',
            style={'display': 'none'}
        )

    ], className='row'),

    # BODY
    html.Div(
        html.Div(id='mtr-page'),
        className='row')
])


# -- dropdown menu
@app.callback(
    dd.Output('mtr-page', 'children'),
    [dd.Input('mtr-url', 'pathname')])
def goto_page(pathname):
    page = PAGES.get(pathname, None)
    if page is None:
        return html.Div('404, {} - not found'.format(pathname))
    return page.layout


@app.callback(
    dd.Output('mtr-menu-content', 'children'),
    [dd.Input('mtr-menu-content', 'n_clicks')],
    [dd.State('mtr-url', 'pathname'),
     dd.State('mtr-menu-content', 'children')])
def set_active_link(clicks, pathname, menu_items):
    page = PAGES.get(pathname, None)
    page_path = '' if page is None else page.path
    for item in menu_items:
        prop = item['props']
        href = prop.get('href', None)
        prop['className'] = 'active' if href == page_path else ''
    return menu_items


if __name__ == '__main__':
    app.run_server(debug=True)
