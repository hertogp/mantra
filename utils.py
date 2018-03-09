# -*- encoding: utf8 -*-
'''
Utilities for Mantra.
'''

import os
import re
import base64
import struct
import hashlib
import pathlib
import time
import json
import yaml
from collections import namedtuple
from functools import wraps
from inspect import ismethod, isfunction
import logging

from config import cfg


# -- Globals
log = logging.getLogger(cfg.app_name)
log.debug('logging via %s', log.name)

DOM_ID_TYPES = [
    'controls',   # cache for controls on a page
    'vars',       # cache for variables in a page
    'display',    # page display div
]

MSTR_IDX = 'mantra.idx'  # in cfg.dst_dir topdir
TEST_IDX = 'mtr.idx'     # in cfg.dst_dir subdir's (per test)
# status/compilation flags
F_PLAYABLE = 1  # src updated since last compilation
F_OUTDATED = 2  # dst is older than src
F_DSTERROR = 4  # dst files not ok (eg subdir != mtr.idx.test_id)
F_SRCERROR = 8  # src files not ok (eg src deleted or missing files)

MtrIdx = namedtuple('MtrIdx', [
    'src_file',      # abspath to source file
    'src_hash',      # to see if it has changed
    'dst_dir',      # where compiled version ends up
    'category',      # subdir(s) under src_root
    'test_id',       # original test_id
    'grade',         # the hash of (filename, category)
    'score',         # last score
    'numq',          # number of questions in the directory
    'cflags',        # flags to signal status
])

# -- Utils constructs
# Mantra's urls look like:
#   http://netloc:8050/path;param?query=arg#frag
# nav = UrlNav(...), then if needed: nav = nav._replace(key=val)
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


def get_test_id(filename):
    'fnv64 hash of basename and category of a src filename'
    basename = os.path.basename(filename)
    category = os.path.relpath(os.path.dirname(filename), cfg.src_dir)
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


def find_files(topdirs, patterns, recurse=True):
    topdirs = [topdirs] if isinstance(topdirs, str) else topdirs
    patterns = [patterns] if isinstance(patterns, str) else patterns
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


def yield_files(topdir, patterns, recurse=True):
    'yield filenames matching a pattern or patterns'
    patterns = [patterns] if isinstance(patterns, str) else patterns
    cpatterns = [re.compile(p) for p in patterns]
    for path, dirs, files in os.walk(topdir):
        for fname in files:
            for cp in cpatterns:
                if cp.search(fname):
                    yield os.path.join(path, fname)
                    break
        if not recurse:
            break

# src_root/<cat:path>/src<x>.md
#                    /img/img<y>.png
# compiling gives ->
# dst_root/<test_id>/mtr.his        - required: history of tests taken + results
#                   /mtr.idx        - required: index details (src, name, num q's, ..)
#                   /mtr.log        - optional: compiler log/lock file
#                   /q001.json      - required: first question
#                   /..             - .. more questions
#                   /quiz.yml       - required: test info (like passing score etc..)
#                   /img/img<y>.png - optional: images of questions
# create_index gives ->
# dst_root/mtr.idx                  - master index across srcs/dsts


def idx_by_dst():
    'collect index entries by dst_dir/<test_id>/mtr.idx-files'
    # XXX: update so orpahned subdirs without mtr.idx are added as well
    index = {}  # [test_id] -> cfg.dst_dir's mtr.idx index entry
    for idx_file in yield_files(cfg.dst_dir, TEST_IDX):
        with open(idx_file, 'rt') as fh:
            # dta = json.loads(fh.read())
            idx = MtrIdx(*json.loads(fh.read())) # dta)
        dst_dir = os.path.dirname(idx_file)
        test_id = os.path.relpath(dst_dir, cfg.dst_dir)
        if test_id == '.':
            continue  # skip files in dst_dir topdir
        if test_id != idx.test_id:
            # somebody changed test_id-dir name?
            log.debug('test_ids donot match %s vs %s', test_id, idx.test_id)
            idx = idx._replace(cflags=idx.cflags | F_DSTERROR)
        index[test_id] = idx
        log.debug('add %s', test_id)
    return index


def idx_by_src():
    'create index entries by valid test.md files in cfg.src_dir'
    index = {}
    pats = ['.{}'.format(x) for x in cfg.tst_ext]
    for src_file in yield_files(cfg.src_dir, pats):
        src_dir = os.path.dirname(src_file)
        category = os.path.relpath(src_dir, cfg.src_dir)
        if category == '.':
            continue  # skip files in cfg.src_dir itself
        test_id = get_test_id(src_file)
        dst_dir = os.path.join(cfg.dst_dir, test_id)
        log.debug('add %s', test_id)
        index[test_id] = MtrIdx(src_file, file_checksum(src_file), dst_dir,
                                category, get_test_id(src_file), 0, 0, 0, 0)
    return index


def idx_flags(idx):
    'run checks on idx and return error-flags as cflags'
    cflags = 0
    try:
        if not os.access(idx.src_file, os.R_OK):
            cflags |= F_SRCERROR  # src not available/readable
        elif idx.src_hash != file_checksum(idx.src_file):
            cflags |= F_OUTDATED  # src differs from what was compiled

        # a missing cfg.dst_dir/test_id means not playable, needs compiling
        dst_dir = os.path.join(cfg.dst_dir, idx.test_id)
        if not os.access(dst_dir, os.R_OK):
            return cflags | F_OUTDATED

        # required files in cfg.dst_dir/test_id/
        for fname in ['mtr.his', 'mtr.idx', 'quiz.yml']:
            if not os.access(os.path.join(dst_dir, fname), os.R_OK):
                log.debug('missing dst file %s/%s', idx.test_id, fname)
                cflags |= F_DSTERROR + F_OUTDATED

        try:
            numq = int(idx.numq)
        except (TypeError, ValueError):
            log.debug('invalid numq %s', idx.numq)
            return cflags | F_DSTERROR

        # required cfg.dst_dir/test_id/q<ddd>.json files
        for qnr in range(numq):
            qfile = os.path.join(cfg.dst_dir,
                                 idx.test_id,
                                 'q{:03d}.json'.format(qnr))
            if not os.access(qfile, os.R_OK):
                log.debug('missing (some) q<ddd>-files')
                cflags |= F_DSTERROR + F_OUTDATED
                break
        else:
            if numq > 0:
                cflags |= F_PLAYABLE  # no break, all q's are there

    except AttributeError as e:
        log.debug('corrupt %s: %s', idx, repr(e))
        return F_DSTERROR

    return cflags


def mtr_idx_create():
    'create a fresh dst_dir/mtr.idx of playable/compilable tests'
    master = idx_by_dst()
    for test_id, idx in idx_by_src().items():
        if test_id not in master:
            master[test_id] = idx  # a fresh, non-compiled source
        elif idx.src_file != master[test_id].src_file:
            # adopt src's src_file and flag output dir as erronuous
            ix = master[test_id]
            master[test_id] = ix._replace(cflags=ix.cflags | F_DSTERROR,
                                          src_file=idx.src_file)

    # run some checks and raise any flags if necessary
    for test_id, idx in master.items():
        master[test_id] = idx._replace(cflags=idx_flags(idx))

    # log results
    for test_id, idx in master.items():
        log.debug('%s -> %s', test_id, idx.src_file)

    # write to disk
    with open(os.path.join(cfg.dst_dir, MSTR_IDX), 'wt') as f:
        json.dump(master, f)

    return master


# XXX: use a decorator to cache reads based on ctime: only
# read the file if its ctime is more recent than what's in memory
def mtr_idx_read():
    'read master index from disk'
    with open(os.path.join(cfg.dst_dir, MSTR_IDX), 'rt') as fp:
        dct = json.load(fp)
    return dict((k, MtrIdx(*idx)) for k, idx in dct.items())


def idx_getstats(idx):
    pass
