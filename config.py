# -*- encoding: utf-8 -*-
import pathlib
import yaml

CONFIG = {
    # directories
    'root': '/home/dta/mantra',
    'static': 'static',
    'src_dir': 'docs',
    'dst_dir': '_mantra',

    # test file suffixes
    'test_types': ['md', 'pd', 'markdown'],

    # index of tests stored in json file located in dst_dir:
    # - (re)created at startup
    # - refreshable via gui
    'index_tests': 'idx.json',

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

try:
    path = pathlib.Path('mantra.yaml').expanduser().resolve()
    if not path.exists() or not path.is_file():
        update = {}
    else:
        print('path.name', path.name)
        update = yaml.safe_load(open(path.name, 'rt')) or {}
except FileNotFoundError:
    update = {}
except ValueError as e:
    print('Error in yaml config')
    print(repr(e))
    raise SystemExit(1)

# update = utils.load_config('mantra.yaml') or {}
CONFIG.update(update)

# create absolute full paths

try:
    CONFIG['root'] = pathlib.Path(CONFIG['root']).expanduser().resolve().absolute()
    CONFIG['static'] = str((CONFIG['root'] / CONFIG['static']).resolve())
    CONFIG['src_dir'] = str((CONFIG['root'] / CONFIG['src_dir']).resolve())
    CONFIG['dst_dir'] = str((CONFIG['root'] / CONFIG['dst_dir']).resolve())
    CONFIG['root'] = str(CONFIG['root'])

except Exception as e:
    print('failed to load the configuration')
    print('-', e)
    raise SystemExit(1)

print(CONFIG)
