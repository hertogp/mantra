# -*- encoding: utf8 -*-
'''
Utilities for Mantra.
'''

import os
import base64
import struct
import pathlib
import time
import json
from functools import wraps
from inspect import ismethod, isfunction

from config import CONFIG

# Globs
DOM_ID_TYPES = [
    'controls',   # cache for controls on a page
    'vars',       # cache for variables in a page
    'display',    # page display div
]


# - Module logger
import app
log = app.getlogger(__name__)
log.debug('logger enabled')

#-- dumpers


class Jsonify(json.JSONEncoder):
    '''
    turn any unjsonifiable elements into repr(elm..)

    usage:
        jsondump = Jsonify(indent=4).encode
        jsondump(print) -> "<built-in function print>"
    '''

    def default(self, arg):
        return repr(arg)

jsondump = Jsonify(indent=4).encode


def timethis(func):
    'time a func, for temporal, casual use only'
    # py3 book, page 588
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        r = func(*args, **kwargs)
        end = time.perf_counter()
        print('{}.{} : {}'.format(func.__module__, func.__name__, end - start))
        return r
    return wrapper


def trace(f):
    'trace calls to f'
    @wraps(f)
    def wrapper(*a, **kw):
        print('trace: {}({},{})'.format(f.__name__, a, kw))
        rv = f(*a, **kw)
        print(jsondump(rv))
        return rv
    return wrapper


class Proxy(object):
    '''
    Proxy an object (instance) to show usage & behaviour

    Example usage:
      Proxy(html.Div('this is a div', id='blah'))
    '''

    def __init__(self, obj):
        self._obj = obj
        traced = []
        for name in dir(obj):
            attr = getattr(obj, name)
            if ismethod(attr) or isfunction(attr):
                traced.append(name)
                setattr(obj, name, trace(attr))
        print('-'*45, 'Proxy:', repr(obj), 'tracing:')
        for t in traced:
            print(' -', t)

    # Delegate attribute lookup to internal obj
    def __getattr__(self, name):
        attr = getattr(self._obj, name)
        print('-'*45, 'Proxy')
        print('getattr:', name)
        print(attr)
        print('---')

        return attr
        # return getattr(self._obj, name)

    # Delegate attribute assignment
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            print('setattr:', name, value)
            setattr(self._obj, name, value)

    # Delegate attribute deletion
    def __delattr__(self, name):
        if name.startswith('_'):
            super().__delattr__(name)
        else:
            print('delattr:', name)
            delattr(self._obj, name)

    # trace method calls
    def __call__(self, *a, **kw):
        print('cll', a, kw)
        return self._obj.__call__(*a, **kw)

# Page utilities


def get_domid(kind, path):
    kind = kind.lower()
    if kind not in DOM_ID_TYPES:
        raise Exception('unknown DOM id type {}'.format(kind))
    domid = 'app-{}-{}'.format(kind,
                               path if not path.startswith('/') else path[1:])
    log.debug('get_domid(%s,%s) -> %s', kind, path, domid)
    return domid


def set_layout_controls(layout, controls):
    if controls is None or len(controls) < 1:
        return layout

    for id_, attr, value in controls:
        obj = layout.get(id_, None)
        if obj:
            setattr(layout, attr, value)

    return layout



# -- HASH ops


# def fnv64(data):
#     hash_ = 0xcbf29ce484222325
#     for b in data:
#         hash_ *= 0x100000001b3
#         hash_ &= 0xffffffffffffffff
#         hash_ ^= b
#     return hash_

# def hash_dn(dn, salt):
#     # Turn dn into bytes with a salt, dn is expected to be ascii data
#     data = salt.encode("ascii") + dn.encode("ascii")
#     # Hash data
#     hash_ = fnv64(data)
#     # Pack hash (int) into bytes
#     bhash = struct.pack("<Q", hash_)
#     # Encode in base64. There is always a padding "=" at the end, because the
#     # hash is always 64bits long. We don't need it.
#     return base64.urlsafe_b64encode(bhash)[:-1].decode("ascii")


def hashfnv64(text, salt=''):
    'fnv64 hash of text'
    salt = salt or 'mantra!'
    data = salt.encode('ascii') + text.encode('ascii')
    hash_n = 0xcbf29ce484222325
    for b in data:
        hash_n *= 0x100000001b3
        hash_n &= 0xffffffffffffffff
        hash_n ^= b
    hash_b = struct.pack('<Q', hash_n)
    return base64.urlsafe_b64encode(hash_b)[:-1].decode('ascii')


# -- FILE operations


def find_files(topdirs, suffixes, recurse=True):
    if isinstance(topdirs, str):
        topdirs = [topdirs]
    if isinstance(suffixes, str):
        suffixes = [suffixes]

    patterns = ['*.{}'.format(x) for x in suffixes]
    topdirs = [pathlib.Path(x).expanduser().resolve() for x in topdirs]
    for topdir in topdirs:
        if not topdir.is_dir():
            continue
        globdir = topdir.rglob if recurse else topdir.glob
        for pattern in patterns:
            for fname in globdir(pattern):
                if not fname.is_file():
                    continue
                yield str(fname)


def create_test_index(topdirs, suffixes, recurse=True):
    'return dict {test_id} -> test for tests in src_dir'
    # skip files in rootdir, like index.md, which are generated by mkdocs
    # only subdirs can be categories
    src_root = CONFIG['src_dir']   # tests.md's
    dst_root = CONFIG['dst_dir']   # compiled
    rv = []
    for fpath in find_files(src_root, CONFIG['test_types']):
        ctime = os.path.getctime(fpath)
        filename = os.path.basename(fpath)
        dirname = os.path.dirname(fpath)
        category = os.path.relpath(dirname, src_root)

        # skip file in src_root itself
        if category == '.':
            continue

        # hash filename with category as salt -> unique dirname as test_id
        # - use category, so if everything is moved to diff rootdir, test_id's
        #   remain the same.
        test_id = hashfnv64(filename, category)
        test_dir = os.path.join(dst_root, test_id)
        statsfile = os.path.join(test_dir, 'stats.csv')
        available = os.path.isfile(statsfile)

        # See if src_file was compiled to questions in the past
        score, numq, action = 0, 0, 'compile'
        if os.path.isdir(test_dir):
            log.debug('searching test_dir %s', test_dir)
            for qstn in find_files(test_dir, ['json']):
                log.debug('found question %s', qstn)
                numq += 1  # maybe check filesize or timestamp

            # read the stats.csv = timestamp,mode,num_questions,score
            # test.md may have been compiled, but never taken, so no stats
            if available:
                with open(statsfile) as fh:
                    fh_csv = csv.reader(fh)
                    head = next(fh_csv)
                    Stats = namedtuple('Stats', head)
                    score, count = 0, 0
                    for r in fh_csv:
                        row = Stats(*r)
                        score += int(row.score)  # 0 - 100
                        count += 1
                score = int(score / count) if count else 0
                if os.path.getctime(statsfile) < ctime:
                    action = 'compile'
                elif numq > 0:
                    action = 'run'

        log.debug('found src file %s in category %s', filename, category)
        rv.append({'category': category,
                   'filename': filename,
                   'filepath': fpath,
                   'test_id': test_id,
                   'test_dir': test_dir,
                   'created': ctime,
                   'available': available,
                   'numq': numq,
                   'score': score,
                   'action': action,
                   })

    return rv
    pass

