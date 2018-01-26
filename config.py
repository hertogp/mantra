# -*- encoding: utf-8 -*-
import os
import pathlib
import utils

CONFIG = {
    # directories
    'root': '/home/dta/mantra',
    'static': 'static',
    'tests': 'docs',

    # test file suffixes
    'test-types': ['md', 'pd', 'markdown'],

    # /static resources ...
    # favicon and logo
    'logo': '/static/img/mantra-space-age.png',
    'favicon': 'img/favicon.ico',  # no /static/.. (due to GET /favicon.ico)

    # css stuff
    'stylesheets': [
        '/static/css/chriddyp.css',
        '/static/css/fontawesome-all.css',
        '/static/css/mantra.css',
    ],

    # javaScripts
    'scripts': [
    ]

}

update = utils.load_config('mantra.yaml') or {}
CONFIG.update(update)

# create absolute full paths

try:
    CONFIG['root'] = pathlib.Path(CONFIG['root']).expanduser().resolve().absolute()
    CONFIG['static'] = str((CONFIG['root'] / CONFIG['static']).resolve())
    CONFIG['tests'] = str((CONFIG['root'] / CONFIG['tests']).resolve())
    CONFIG['root'] = str(CONFIG['root'])

except Exception as e:
    print('failed to load the configuration')
    print('-', e)
    raise SystemExit(1)

print(CONFIG)
