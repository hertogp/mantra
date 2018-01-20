'''
Utilities for Mantra.
'''

import yaml
import pathlib
import time
import json
from functools import wraps
from inspect import ismethod, isfunction


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


# -- FILE operations


def find_files(topdirs, suffixes, recurse=True):
    if isinstance(topdirs, str):
        topdirs = [topdirs]
    if isinstance(suffixes, str):
        suffixes = [suffixes]

    patterns = ['*.{}'.format(x) for x in suffixes]
    topdirs = [pathlib.Path(x).expanduser().resolve() for x in topdirs]

    for topdir in topdirs:
        globdir = topdir.rglob if recurse else topdir.glob
        for pattern in patterns:
            for fname in globdir(pattern):
                if not fname.is_file():
                    continue
                # fstat = fname.stat()
                # ctime, mtime = fstat.st_ctime, fstat.st_mtime
                subdir = fname.relative_to(topdir)
                # cat = subdir.parts
                # cat = cat[0] if len(cat) else ''
                # yield (cat, topdir, subdir, ctime, mtime, fname.name)
                yield (topdir, subdir, fname)


# -- SETTINGs

def load_config(filename):
    try:
        path = pathlib.Path(filename).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return {}
        cfg = yaml.safe_load(open(path.name, 'rt'))
    except FileNotFoundError:
        return {}
    except ValueError as e:
        print('Error in yaml config')
        print(repr(e))
        raise SystemExit(1)

    # TODO: sanitize dir- and filenames?

    return cfg


