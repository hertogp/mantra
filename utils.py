# -*- encoding: utf8 -*-
'''
Utilities for Mantra.
'''

import os
import re
import weakref
import base64
import struct
import hashlib
import time
import json
import fnmatch
from collections import namedtuple
from functools import wraps
from inspect import ismethod, isfunction
import logging

# TODO: make utils independent of cfg or Mantra in general
# - cannot import utils in tests without import the whole app
# App imports
# from config import cfg

# -- Globals
APP_NAME = 'Mantra'      # sameas cfg.app_name
MSTR_IDX = 'mantra.idx'  # in cfg.dst_dir topdir
TEST_IDX = 'mtr.idx'     # in cfg.dst_dir subdir's (per test)

log = logging.getLogger('Mantra')  # hard coded: avoid import config
log.debug('logging via %s', log.name)

DOM_ID_TYPES = [
    'controls',   # cache for controls on a page
    'vars',       # cache for variables in a page
    'display',    # page display div
]

# -- Utils constructs

MtrIdx = namedtuple('MtrIdx', [
    'flag',      # status flag for the test
    'src',       # abspath to source file
    'category',  # subdir(s) under src_root
    'test_id',   # original test_id
])

# Mantra's urls look like: http://netloc:8050/path;param?query=arg#frag
UrlNav = namedtuple('UrlNav', [
    'href',        # original url
    'query',       # decoded as dict, if any
    'frag',        # if any found end of url
    'page_id',     # page handling this url (if any)
    'test_id',     # if any found in url
    'controls',    # DOM id of page's control cache
    'vars',        # DOM id of page's var cache
])


# -- dumpers
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
        log.debug('%s.%s : %s', func.__module__, func.__name__, end - start)
        return r
    return wrapper


def trace(f):
    'trace calls to f'
    @wraps(f)
    def wrapper(*a, **kw):
        log.debug('trace: %s(%s,%s)', f.__name__, a, kw)
        rv = f(*a, **kw)
        log.debug(' %s', jsondump(rv))
        return rv
    return wrapper


class Cached(type):
    'meta class to return job by ID or create new one with ID'
    # python3 cookbook, recipe 9.13: Metaclass to control instance creation
    # worker = Worker(uniq_id, other, args) -> always same instance
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__cache = weakref.WeakValueDictionary()

    def __call__(self, *args):
        'return an instance, either cached or created new'
        if args in self.__cache:
            return self.__cache[args]
        else:
            obj = super().__call__(*args)
            self.__cache[args] = obj
            log.debug('new obj %s for %s', obj, args)
        return obj


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
        log.debug('tracing %s', repr(obj))
        for name in traced:
            log.debug(' - %s', name)

    # Delegate attribute lookup to internal obj
    def __getattr__(self, name):
        attr = getattr(self._obj, name)
        log.debug('%s = %s', name, attr)
        return attr

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


# -- Page utilities


def get_domid(kind, path):
    kind = kind.lower()
    if kind not in DOM_ID_TYPES:
        raise Exception('unknown DOM id type {}'.format(kind))
    domid = 'app-{}-{}'.format(kind,
                               path if not path.startswith('/') else path[1:])
    return domid


def set_controls(layout, controls):
    if controls is None or len(controls) < 1:
        return layout
    try:
        for id_, attr, value in controls:
            obj = layout.get(id_, None)
            if obj is None:
                continue
            setattr(obj, attr, value)
    except ValueError:
        log.debug('invalid list of (id,attr,val) pairs in %s', controls)

    return layout


# -- HASH ops


def hashfnv64(text, salt=''):
    'fnv64 hash of text'
    salt = salt or 'mantra'
    data = salt.encode('ascii') + text.encode('ascii')
    hash_n = 0xcbf29ce484222325
    for b in data:
        hash_n *= 0x100000001b3
        hash_n &= 0xffffffffffffffff
        hash_n ^= b
    hash_b = struct.pack('<Q', hash_n)
    return base64.urlsafe_b64encode(hash_b)[:-1].decode('ascii')


def get_test_id(topdir, filename):
    'fnv64 hash of basename and category of a src filename'
    basename = os.path.basename(filename)
    category = os.path.relpath(os.path.dirname(filename), topdir)
    data = category.encode('ascii') + basename.encode('ascii')
    hash_n = 0xcbf29ce484222325
    for b in data:
        hash_n *= 0x100000001b3
        hash_n &= 0xffffffffffffffff
        hash_n ^= b
    hash_b = struct.pack('<Q', hash_n)
    return base64.urlsafe_b64encode(hash_b)[:-1].decode('ascii')


def file_ctime(filename):
    'return ctime of filename or 0 if unreadable'
    try:
        return os.stat(filename).st_ctime
    except FileNotFoundError:
        return 0


def file_checksum(filename, block_size=65536):
    'checksum to determine is a file has been changed'
    try:
        sha256 = hashlib.sha256()
        with open(filename, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()
    except FileNotFoundError:
        return None


# -- FILE operations

def rgx_files(topdir, include=None, exclude=None):
    'yield rgx included & not rgx excluded filepaths relative to topdir'
    include = [re.compile('.*')] if include is None else include
    exclude = [] if exclude is None else exclude

    for dirname, _, fnames in os.walk(topdir):
        reldir = os.path.relpath(dirname, topdir)
        for fname in fnames:
            relpath = os.path.join(reldir, fname)
            if not any(rgx.match(relpath) for rgx in include):
                continue
            if any(rgx.match(relpath) for rgx in exclude):
                continue
            yield relpath


def glob_files(topdir, includes=None, excludes=None):
    'list glob included & then not excluded filepaths relative to topdir'
    includes = ['*'] if includes is None else includes
    excludes = [] if excludes is None else excludes

    accept = [re.compile(fnmatch.translate(p)) for p in includes]
    ignore = [re.compile(fnmatch.translate(p)) for p in excludes]

    for dirname, subdirs, files in os.walk(topdir):
        reldir = os.path.relpath(dirname, topdir)
        for fname in files:
            # no normpath just yet to allow globs like '[!.]*/mtr.idx'
            relpath = os.path.join(reldir, fname)
            if not any(r.match(relpath) for r in accept):
                continue
            if any(r.match(relpath) for r in ignore):
                continue
            # loose any ./ or //'s .. etc
            yield os.path.normpath(relpath)


class MantraIdx:
    'the index of tests based on src.md and its mtr.idx, img.idx files'
    # no need for dst include/exclude since those names are fixed
    # donot include any files in src_dir (topdir)
    INCLUDE = ['[!.]**/*.md', '[!.]**/*.markdown', '[!.]**/*.pd']
    EXCLUDE = ['**/notes.*', '**/index.*']

    def __init__(self, src_dir, dst_dir, sync=True):
        'if sync is False, manual <instance>.sync() required'
        if not os.path.isdir(src_dir):
            raise Exception('src_dir %s is missing' % src_dir)
        if not os.path.isdir(dst_dir):
            raise Exception('dst_dir %s is missing' % dst_dir)

        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.set_filter()
        self.idx = {}
        if sync:
            self.sync()

    def __iter__(self):
        for k in self.idx:
            yield self.idx[k]

    def test_id(self, test_id):
        return self.idx.get(test_id, None)

    def sync(self):
        'sync index to files present on disk'
        self.idx.clear()
        return self._add_srcs()._add_dsts()

    def save(self, outname='mantra.idx'):
        'save index to dst_dir/mantra.idx'
        fname = os.path.join(self.dst_dir, outname)
        try:
            with open(fname, 'wt') as fh:
                fh.write(json.dumps(self.idx))
        except OSError:
            log.error('could not save mantra.idx')

        return self

    def read(self, inpname='mantra.idx'):
        'read index from dst_dir/mantra.idx'
        fname = os.path.join(self.dst_dir, inpname)
        try:
            with open(fname, 'rt') as fh:
                self.idx = json.loads(fh.read())
        except OSError:
            log.error('could not read %s' % fname)

        return self

    def set_filter(self, include=None, exclude=None):
        'set include/exclude globs for src files (None means use default)'
        include = self.INCLUDE if include is None else include
        exclude = self.EXCLUDE if exclude is None else exclude
        self.include = [re.compile(fnmatch.translate(p)) for p in include]
        self.exclude = [re.compile(fnmatch.translate(p)) for p in exclude]
        self.dst_mtr = [re.compile(fnmatch.translate('[!.]**/mtr.idx'))]
        return self

    def _read_img_idx(self, fname):
        'return list of [(src.img, dst.img)] or []'
        try:
            with open(fname) as fh:
                imgs = json.loads(fh.read())
        except OSError:
            return []  # simply might not be there
        except Exception:
            log.error('reading json encoded img index %s' % fname)
            return []
        return imgs

    def _read_mtr_idx(self, fname):
        'return python obj from mtr.idx file or None in case of errors'
        try:
            with open(fname) as fh:
                return MtrIdx(*json.loads(fh.read()))
        except OSError:
            log.error('read error %r' % fname)
        except Exception:
            log.error('json decode error %r' % fname)
        return None

    def _add_srcs(self):
        'add idx entries based on sources'
        for frel in rgx_files(self.src_dir, self.include, self.exclude):
            src = os.path.join(self.src_dir, frel)
            cat = os.path.dirname(frel)
            test_id = hashfnv64(os.path.basename(frel), cat)
            dst = os.path.join(self.dst_dir, test_id, 'mtr.idx')
            dst_mtime = os.path.getmtime(dst) if os.path.isfile(dst) else 0
            src_mtime = os.path.getmtime(src)  # should exist.
            # flags: C(reate) dst, U(pdate) dst, P(lay) dst
            flag = 'U' if src_mtime > dst_mtime else 'P'
            flag = 'C' if dst_mtime == 0 else flag  # special case 'updatable'
            self.idx[test_id] = MtrIdx(flag, src, cat, test_id)

        return self

    def _add_dsts(self):
        'add/update idx entries based on destinations'
        for frel in rgx_files(self.dst_dir, self.dst_mtr):
            if frel.count('/') != 1:
                log.error('weirdly placed mtr.idx', frel)
                continue

            test_id = os.path.dirname(frel)
            if test_id not in self.idx:
                # flag: O(rphaned) but playable (hopefully)
                log.debug('Orphan found %r (source is missing)', test_id)
                fname = os.path.join(self.dst_dir, test_id, 'mtr.idx')
                idx = self._read_mtr_idx(fname)
                if idx is not None:
                    self.idx[test_id] = idx._replace(flag='O')
                continue

            # set flag to U(pdateable) if at least 1 src.img is newer
            fname = os.path.join(self.dst_dir, test_id, 'img.idx')
            imgs = self._read_img_idx(fname)
            for src, dst in imgs:
                stime = os.path.getmtime(src) if os.path.isfile(src) else 0
                dtime = os.path.getmtime(dst) if os.path.isfile(dst) else 0
                if stime > dtime:
                    f, src, cat, _ = self.idx[test_id]
                    self.idx[test_id] = MtrIdx('U', src, cat, test_id)
                    break

        return self
