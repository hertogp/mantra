# -*- encoding: utf-8 -*-
from collections import namedtuple
import os
import yaml

from log import getlogger
log = getlogger(__name__)

_DEFAULTS = (
    ('root', os.getcwd()),
    ('static', 'static'),
    ('src_dir', 'docs'),
    ('dst_dir', '_mantra'),
    ('tst_ext', 'md pd markdown'.split()),
    ('logo', '/static/img/mantra-space-age.png'),
    ('favicon', 'img/favicon.ico'),  # no /static/.. (GET /favicon.ico)
    ('stylesheets', [
        '/static/css/chriddyp.css',
        '/static/css/fontawesome-all.css',
        '/static/css/mantra.css'
    ]),
    ('scripts', [])
)

Conf = namedtuple('Conf', [item[0] for item in _DEFAULTS])
cfg = Conf(*[item[1] for item in _DEFAULTS])

try:
    with open('mantra.yml', 'rt') as fh:
        usrcfg = yaml.safe_load(fh) or {}
    # only use fields already present in confg
    update = dict((k, v) for (k, v) in usrcfg.items() if hasattr(cfg, k))
    cfg = cfg._replace(**update)
except FileNotFoundError:
    pass
except AttributeError:
    log.error('mantra.yaml does not yield a dict?')
    raise SystemExit(0)
except ValueError as e:
    print('Error in yaml config {!r}'.format(e))

abspaths = {
    'static': os.sep.join([cfg.root, cfg.static]),
    'src_dir': os.sep.join([cfg.root, cfg.src_dir]),
    'dst_dir': os.sep.join([cfg.root, cfg.dst_dir])
}

cfg = cfg._replace(**abspaths)

# sanity check configuration settings
errors = []
warn = []
if not os.access(cfg.static, os.R_OK):
    errors.append('dir missing or unreadable {!r}'.format(cfg.static))
else:
    # check availability of files in static subdir
    for item in [cfg.logo, cfg.favicon, *cfg.stylesheets]:
        if not os.access(os.sep.join([cfg.root, item]), os.R_OK):
            warn.append('cannot access {!r}'.format(item))

    for item in cfg.scripts:
        if not os.access(os.sep.join([cfg.root, item]), os.R_OK):
            errors.append('cannot access {!r}'.format(item))

if not os.access(cfg.dst_dir, os.W_OK):
    errors.append('cannot write to {!r}'.format(cfg.dst_dir))
if not os.access(cfg.src_dir, os.R_OK):
    errors.append('cannot read {!r}'.format(cfg.src_dir))

for msg in warn:
    log.warn(msg)
for msg in errors:
    log.error(msg)
if len(errors):
    log.error('Aborting..!')
    raise SystemExit(1)

