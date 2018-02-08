# -*- encoding: utf8 -*-
'''
Utilities for Mantra.
'''

import base64
import struct
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

# -- HASH ops


def fnv64(data):
    hash_ = 0xcbf29ce484222325
    for b in data:
        hash_ *= 0x100000001b3
        hash_ &= 0xffffffffffffffff
        hash_ ^= b
    return hash_

def hash_dn(dn, salt):
    # Turn dn into bytes with a salt, dn is expected to be ascii data
    data = salt.encode("ascii") + dn.encode("ascii")
    # Hash data
    hash_ = fnv64(data)
    # Pack hash (int) into bytes
    bhash = struct.pack("<Q", hash_)
    # Encode in base64. There is always a padding "=" at the end, because the
    # hash is always 64bits long. We don't need it.
    return base64.urlsafe_b64encode(bhash)[:-1].decode("ascii")


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
    print('find_files %s, look at %s' % (topdirs, suffixes))
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

    return cfg


