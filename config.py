# -*- encoding: utf-8 -*-
import pathlib
import utils

CONFIG = {
    'root': '/home/dta/mantra/docs/static',
    'logo': '/static/img/mantra-space-age.png',
    'favicon': '/img/favicon-themeisle-black.ico',
    'stylesheets': [
        '/static/css/chriddyp.css',
        '/static/css/fontawesome-all.css',
        '/static/css/mantra.css',
    ],
    'scripts': [
    ]

}

CONFIG.update(utils.load_config('mantra.yaml'))

# create absolute full paths

try:
    CONFIG['root'] = str(
        pathlib.Path(CONFIG['root']).expanduser().resolve().absolute()
    )
    print('root', CONFIG['root'])

except Exception as e:
    print('failed to load the configuration')
    print('-', e)
    raise SystemExit(1)

print('-'*80, 'CONFIG')
jsondump = utils.Jsonify(indent=3).encode
print(jsondump(CONFIG))
print('^'*80)
print()

