# -*- encoding: utf-8 -*-
from collections import namedtuple
import os
from ruamel.yaml import YAML
from logging import getLogger
# - globs
yaml = YAML(typ='safe')
log = getLogger('Mantra')     # hardcoded, so logger.py can import config

# MANTRA dirs & files
# nb <name> is a cfg.name attribute, while
#    {name} part of paths encountered, can by anything
#
# <root>                          -> topdir where mantra was started
#   |- <src_dir>/                 -> sources expected in subdirs below this one
#   |    |- {path}/                  -> path := category (a/b/c/)
#   |         |- test.md             -> source file with questions
#   |         |- {img}/                 -> images for source file (if any)
#   |
#   |- <mtr_dir>/                 -> mantra's topdir for output
#       |- mantra.log                -> log file
#       |- mantra.idx                -> index of tests (based on src & dst)
#       |- <dst_dir>/                -> mantra's subdir for compiled output
#       |       |- <test_id>/        -> <test_id>'s compile dst dir
#       |            |- mtr.log         -> temp lock & log file
#       |            |- mtr.idx         -> this test's idx
#       |            |- img.idx         -> [(src.img, dst.img), ..] fullpaths
#       |            |- lead.md         -> leading page for test (< 1st hdr)
#       |            |- quiz.json       -> src.md's meta data
#       |            |- qddd.json       -> question in json format
#       |            |- img/
#       |                |- img.png     -> images for questions in <test_id>
#       |
#       |- <static>/
#           |- css
#           |- js
#           |- img                      -> has favicon.ico for GET /favicon.ico
#           |- webfonts
#
# -----------------------------------------------------------------------------
# {path}/src.md, {imgs.png} -> <test_id>/mtr.idx,img.idx,q<d>.json,img/imgs.png
# -----------------------------------------------------------------------------
# Actions on dst:
# - create   C (cog f013) if src.md newer than test_id/mtr.idx (or its missing)
# - update   U (download f019) any src.img's newer than its dst.img (img.idx)
# - delete   D delete <test_id> (all files including directory)
# - assess   A take an exam and assess your expertise
# Note:
# - Mantra never deletes a src.md or src.img! only its own derived products
# - orphan   O (child f1ae) is a test_id whose src.md has gone missing
# - COU flags C(reatable), O(rphaned), U(pdatable)
# -----------------------------------------------------------------------------
# mantra.idx =  category, src.md, test_id, src_mtime, dst_mtime, C/U/O/I-flags
# mtr.idx    =  category, src.md, test_id, numq, score
# img.idx    =  [(src.img, dst.img), ..]
# quiz.json  =  org doc's meta data; grade, maxtime, etc ...
# lead.md   =  first page of quiz to display (stuff before 1st header)
# -----------------------------------------------------------------------------


_DEFAULTS = (
    ('root', os.getcwd()),           # root dir for all
    ('src_dir', 'docs'),             # topdir for sources under root
    ('mtr_dir', 'mantra'),           # topdir for mantra stuff under root
    ('dst_dir', 'output'),              # mantra's subdir for compiled output
    ('static', 'static'),               # mantra's subdir for site static's

    ('app_name', 'Mantra'),          # toplevel logger name
    ('log_level', 'DEBUG'),          # default log level for all
    ('log_file', 'mantra.log'),      # goes ino mtr_dir
    ('log_levels',                   # override log_level per module, as needed
     {'config': 'ERROR',
      'app_tests': 'DEBUG',
      }
     ),

    ('tst_ext', 'md pd markdown'.split()),
    ('logo', '/static/img/mantra-space-age.png'),
    ('favicon', 'img/favicon.ico'),  # no /static/.. (GET /favicon.ico)

    ('stylesheets', [
        '/static/css/chriddyp.css',
        '/static/css/fontawesome-all.css',
        '/static/css/mantra.css',
        # '/static/css/w3.css',

    ]),
    ('scripts', [])
)

Conf = namedtuple('Conf', [item[0] for item in _DEFAULTS])
cfg = Conf(*[item[1] for item in _DEFAULTS])

try:
    with open('mantra.yml', 'rt') as fh:
        usrcfg = yaml.load(fh) or {}
    # only use known, valid fields (ie Conf._fields)
    update = dict((k, v) for (k, v) in usrcfg.items() if hasattr(cfg, k))
    cfg = cfg._replace(**update)
except FileNotFoundError:
    pass  # user supplied 'mantra.yaml' is optional
except AttributeError:
    log.error('mantra.yaml does not yield a dict?')
    raise SystemExit(0)
except ValueError as e:
    log.error('Error in yaml config %r', e)
    raise SystemExit(0)

abspaths = {
    'src_dir': os.path.join(cfg.root, cfg.src_dir),
    'mtr_dir': os.path.join(cfg.root, cfg.mtr_dir),
    'dst_dir': os.path.join(cfg.root, cfg.mtr_dir, cfg.dst_dir),
    'static': os.path.join(cfg.root, cfg.mtr_dir, cfg.static),
    'log_file': os.path.join(cfg.root, cfg.mtr_dir, cfg.log_file)
}

cfg = cfg._replace(**abspaths)

# sanity check configuration settings
errors = []
warnings = []
if not os.access(cfg.static, os.R_OK):
    errors.append('dir missing or unreadable {!r}'.format(cfg.static))
else:
    # check availability of files in static subdir
    # - note: favicon requires prepending 'static/'
    for item in [cfg.logo, 'static/{}'.format(cfg.favicon), *cfg.stylesheets]:
        fname = os.path.normpath(os.sep.join([cfg.mtr_dir, item]))
        if not os.access(fname, os.R_OK):
            warnings.append('cannot access {!r}'.format(fname))

    for item in cfg.scripts:
        if not os.access(os.sep.join([cfg.root, item]), os.R_OK):
            errors.append('cannot access {!r}'.format(item))

# if not os.access(cfg.dst_dir, os.W_OK):
# # if compiled output dir is not readable, create it
# errors.append('cannot write to {!r}'.format(cfg.dst_dir))

try:
    os.makedirs(cfg.dst_dir, exist_ok=True)
except OSError as err:
    errors.append('cannot read/create {!r}: {!r}'.format(cfg.dst_dir, err))


if not os.access(cfg.src_dir, os.R_OK):
    # if source directory unreadable, then abort
    errors.append('cannot read {!r}'.format(cfg.src_dir))

for msg in warnings:
    log.warning('warning: %s', msg)
for msg in errors:
    log.error('error: %s', msg)
if len(errors):
    log.error('Aborting..!')
    raise SystemExit(1)
