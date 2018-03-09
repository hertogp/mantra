# -*- encoding: utf8 -*-
import sys
import os
import shutil
import copy
import time
import urllib.request
import json
import pypandoc as pp
import pandocfilters as pf
from collections import namedtuple
from itertools import chain
import io
import logging
import threading

# Mantra imports
from config import cfg
from log import getlogger, ThreadFilter
import utils

# Globals
msgfmt = '%(asctime)s [%(threadName)s] %(funcName)s: %(message)s'
datefmt = '%H:%M:%S'
FORMAT = logging.Formatter(fmt=msgfmt, datefmt=datefmt)

# Thread Local storage
# - initialize only once (not per thread)
# - access by importing it where needed
TLS = threading.local()

# setup generic qparse logger
# log = getlogger(__name__)
log = logging.getLogger(cfg.app_name)
log.debug('logging via %s', log.name)
log.setLevel(logging.DEBUG)

# pylint disable: E265
# - helpers nopep8

# Thread Local Storage for this module
# - holds thread-specific logger instance (and test_id)
# - logging output ends up in thread specific log file
# - Quiz is the entry point and it's __init__ sets up the logger
# TLS = threading.local()


def as_block(key, value):
    'return (key,value)-combination as a block element'
    return {'t': key, 'c': value}


def as_ast(key, value):
    'return mini-ast for this key, value'
    # document = [{'unMeta': {}, [BLOCKs]]
    # but our PandocAst only takes the [blocks]
    return [as_block(key, value)]


def as_roman(num):
    'Convert an integer to a Roman numeral.'
    if not isinstance(num, type(1)):
        raise TypeError("expected integer, got %s" % type(num))
    if not 0 < num < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L',
            'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = []
    for i in range(len(ints)):
        count = int(num / ints[i])
        result.append(nums[i] * count)
        num -= ints[i] * count
    return ''.join(result)


def ol_num(num, style):
    'return a styled number for a numbered list'
    if num > 25:
        return num

    if style == 'Example':
        return num   # (@) style, starts at 1
    elif style == 'Decimal':
        return num   # #. style, starts at 1
    elif style == 'LowerAlpha':
        return chr(num - 1 + ord('a'))
    elif style == 'UpperAlpha':
        return chr(num - 1 + ord('A'))
    elif style == 'LowerRoman':
        return as_roman(num).lower()
    elif style == 'UpperRoman':
        return as_roman(num).upper()

    return num


# CLASSES
Token = namedtuple('Token', ['type', 'value'])


class QError(Exception):
    pass


class OpenAnything(object):
    'Context handler for reading some source'

    def __init__(self, source):
        self.source = source
        self.reader = None

    def __enter__(self):
        # simplified version from "dive into python"
        # already readable?
        if hasattr(self.source, 'read'):
            self.reader = self.source
            return self.reader

        # is it stdin?
        if self.source == '-':
            self.reader = sys.stdin
            return self.reader

        # can we treat it as a native filename
        try:
            self.reader = open(self.source)
            return self.reader
        except (IOError, OSError, TypeError):
            pass

        # can we treat it as an url?
        # NOTE: this originally came before file
        try:
            self.reader = urllib.request.urlopen(self.source)
            return self.reader
        except (IOError, OSError, TypeError):
            pass

        # finally, treat source as a string & make it readable
        self.reader = io.StringIO(str(self.source))
        return self.reader

    def __exit__(self, exc_type, exc_value, traceback):
        if self.reader is not sys.stdin:
            self.reader.close()


class IterPeek(object):
    'Iterator with lookback and lookahead'

    def __init__(self, source, distance=1):
        self.source = iter(source)
        self.delta = int(abs(distance))
        self.buflen = 1 + 2*self.delta
        self.buftok = [None] * self.buflen
        self.bufpos = 0    # points to the current token

        for p in range(self.delta):
            try:
                tok = self.source.next()
            except StopIteration:
                tok = None
            self.buftok[self._relpos(p+1)] = tok

    def _relpos(self, pos):
        return (self.bufpos+self.buflen+pos) % self.buflen

    def peek(self, pos=1):
        'return token (might be None) at pos, 0 is current token'
        if abs(pos) > self.delta:
            raise IndexError('peek range exceeded')
        return self.buftok[self._relpos(pos)]

    def __iter__(self):
        return self

    def next(self):
        try:
            tok = self.source.next()                 # buffer a new token
        except StopIteration:
            tok = None                               # buffer StopIter. as well
        self.bufpos = self._relpos(1)                # advance tok pointer
        self.buftok[self._relpos(self.delta)] = tok  # store new tok at edge

        if self.buftok[self.bufpos] is None:         # None -> StopIteration
            raise StopIteration

        return self.buftok[self.bufpos]              # yield a new token

    def filterfalse(self, predicate):
        'remove tokens until predicate(self) is true, return removed tokens'
        buftok = []                                 # save current history
        for pos in range(self.delta, -1, -1):
            buftok.append(self.peek(-pos))

        rv = []                                     # filter future tokens
        while not predicate(self):
            try:
                rv.append(self.next())
            except StopIteration:
                break

        for pos in range(1, self.delta+1):          # copy new future
            buftok.append(self.peek(pos))

        self.buftok = buftok                        # rewrite reality
        self.bufpos = self.delta
        return rv                                   # return filtered tokens

    def collectfalse(self, predicate):
        'advance until predicate(self) is true, return collected tokens'
        rv = []                                     # filter future tokens
        while not predicate(self):
            try:
                rv.append(self.next())
            except StopIteration:
                break
        return rv


class PandocAst(object):
    '''
    Convert pandoc markdown to an AST or load an existing AST;
    - provides iterators for headers & tokens.

    Usage:

    ast = PandocAst.from_file('file.md')      # convert markdown to AST
    for token in ast:                         # iterate AST's tokens
        print(token)

    for level, header in ast.headers:    # iterate across doc's headers
        for tok in PandocAst(header):    # iterate across tokens in header-AST
            print(tok)
    '''
    MD_XTRA = ['--atx-header', '--standalone']  # for convert to another fmt
    MD_OPTS = [  # 'hard_line_breaks',          # for reading an input file
        'yaml_metadata_block',
        'fenced_code_attributes',
        'inline_code_attributes',
        'fancy_lists',
        'lists_without_preceding_blankline',
        ]
    FMT = 'markdown'

    def __init__(self, ast, meta=None):
        'pandoc json AST iterator/converter'
        self.meta = meta or {u'unMeta': {}}
        self.ast = ast

    # Alternate constructor
    @classmethod
    def from_file(cls, filename, fmt=None, opts=None):
        fmt = '+'.join([fmt or cls.FMT] + (opts or cls.MD_OPTS))
        try:
            txt = pp.convert_file(filename, 'json', format=fmt)
            meta, ast = json.loads(txt)
        except Exception as e:
            log.debug('cannot convert file %r\n  ->  (%s)', filename, repr(e))
            raise QError('err converting file {!r}'.format(filename)) from e
        return cls(ast, meta)

    def __iter__(self):
        'turn instance into an ast token iterator as well'
        return self.tokens

    @property
    def tokens(self):
        'iterate over tokens in the AST'
        for _tok in pf.walk(self.ast, lambda k, v, f, m: Token(k, v), '', {}):
            yield _tok

    @property
    def headers(self):
        'return (level, AST) per header, level=0 is pre-header AST'
        level, ast = 0, []
        for _tok in self:
            if _tok.type == u'Header':
                # words = pf.stringify(subast).replace(',', ' ').lower()
                log.debug('lvl[%s] %r', level, pf.stringify(_tok.value))
                yield level, ast                 # yield last header's ast
                level, ast = _tok.value[0], []   # start this header's new ast
            ast.append(as_block(*_tok))
        yield level, ast

    def convert(self, out_fmt=None, xtra=None):
        'turn pandoc json AST into output format'
        out_fmt = out_fmt or self.FMT
        xtra = xtra or self.MD_XTRA
        json_str = json.dumps([self.meta, self.ast])
        return pp.convert_text(json_str, out_fmt, 'json', extra_args=xtra)


class Question(object):
    'models a question'
    TYPE_NRS = {
        0: 'empty',     # initial, default value (for Question())
        1: 'intro',     # front matter stuff after yaml & before 1st header
        2: 'mchoice',   # multiple choice
        3: 'mcorrect',  # multiple correct
        9: 'unknown',   # not really a question
    }
    # map names to numbers as well
    TYPES = dict((v, k) for k, v in TYPE_NRS.items())

    _ATTR_DEFAULTS = {      # attrs for jsonfication
        'level': 0,         # header level of this question
        'type': 0,          # q's type_nr question
        'tags': [],         # q's tags, incl. lowel level tags
        'section': '',      # section keyword, if any
        'title': '',        # q's title (in markdown), if any
        'text': '',         # q's actual question in markdown
        'choices': [],      # q's possible answers as [(val, label), ..] list
        'answer': [],       # q's correct answer(s) as [val1, val2, ..]
        'explain': '',      # Explanation of answer(s), in markdown
        'markdown': ''      # Original markdown, incl. header starting the q
    }

    def __init__(self, **kwargs):
        'Init new Question with supplied kw-args or defaults'
        # use shallow copy.copy(default) since some attrs are lists.
        # - if not, all q's would share the same _ATTR_DEFAULTS-lists
        # - if using lists of lists -> deepcopy would be required!
        for attr, default in self._ATTR_DEFAULTS.items():
            setattr(self, attr, kwargs.get(attr, copy.copy(default)))

    # alternate constructor
    @classmethod
    def load_json(cls, json_str):
        'Create new Question from json_str, ignores unknown attrs'
        try:
            return cls(**json.loads(json_str))
        except Exception as err:
            log.error('cannot load json string\n%s', json_str)
            raise QError('Error creating Question from a json string') from err

    # alternate constructor
    @classmethod
    def read(cls, filename):
        'Create new Question from file in json format, ignores unknown attrs'
        with open(filename, 'rt') as fh:
            return cls.load_json(fh.read())

    def to_json(self):
        'dump to json string'
        _DEF = self._ATTR_DEFAULTS
        attrs = dict((attr, getattr(self, attr, _DEF[attr])) for attr in _DEF)
        json_str = json.dumps(attrs, indent=3)
        return json_str

    def save(self, filename):
        with open(filename, 'wt') as fh:
            fh.write(self.to_json())


class Parser(object):
    'Parse a PandocAst into a list of 0 or more Questions'
    # an Attribute Para starts with one of these:
    ATTR_KEYWORDS = ['tags:', 'answer:', 'explanation:', 'section:']

    def __init__(self, idx):
        self.idx = idx    # src to be compiled
        self.meta = {}    # doc's yaml meta data
        self.tags = []    # document tags (from meta)
        self.qstn = []    # list of individual Question's or front matter
        self.imgs = []    # [(src_img, dst_img), ..] to be copied
        self.intro = ''   # q-zero's text, if any, is intro story
        self.flags = []   # [sS][iI][dD]

    def parse(self):
        doc_ast = PandocAst.from_file(self.idx.src_file)
        self._docmeta(doc_ast.meta)            # process meta data

        for level, header in doc_ast.headers:
            self._ast = []                     # ast for question being parsed
            self.qstn.append(Question())       # new empty Question
            ptr = self.qstn[-1]                # shorthand to new Question
            hdr = PandocAst(header)            # setup for iteration of tokens
            ptr.markdown = hdr.convert()       # org markdown question text

            # extract parts of header sub-ast
            for key, val in hdr.tokens:
                if key == u'Header':
                    self._header(key, val)
                elif key == u'Para':
                    self._para(key, val)
                elif key == u'OrderedList':
                    self._orderedlist(key, val)
                else:
                    self._ast.append(as_block(key, val))

            # save remaining parts of sub-ast as actual question text
            ptr.text = PandocAst(self._ast).convert('markdown')

        self._inherit_tags()  # higher levels inherit lower level tags
        self._prune()         # remove non-questions
        return self

    def _docmeta(self, meta):
        'update meta data and adopt any document level tags'
        unmeta = meta.get(u'unMeta', {})
        for key, val in unmeta.items():
            # bare numbers in yaml header -> {'t': 'MetaString', 'c': 'digits'}
            # not as 'MetaInlines'-blocks, pf.stringify makes 'em disappear?
            if val.get('t', None) != 'MetaInlines':
                val = {'t': 'MetaInlines', 'c': [val]}
            unmeta[key] = pf.stringify(val)
            if key.lower() != 'tags':
                continue
            tags = unmeta[key].lower().replace(',', ' ').split()
            self.tags = sorted(set(tags))
        self.meta.update(unmeta)

    def _header(self, key, val):
        'header starts a new question'
        # Header -> [level, [slug, [(key,val),..]], [header-blocks]]
        q = self.qstn[-1]
        q.level = val[0]
        q.title = PandocAst(as_ast(key, val)).convert('markdown')
        q.title = q.title.strip()
        log.debug('[level %d] %s', q.level, q.title)

    def _para(self, key, val):
        # Para -> [Block], might be an <attribute:>-para
        if len(val) < 1:
            return  # nothing todo

        q = self.qstn[-1]
        attrs = self._para_attr(val)
        if len(attrs):
            # it was an attr-para, retrieve only known attributes
            # skip the rest of the paragraph.
            q.answer = attrs.get('answer:', [])
            q.tags = attrs.get('tags:', [])
            q.section = attrs.get('section:', '')
            q.explain = attrs.get('explanation:', '')
        else:
            # modify para's img urls & collect [(src,dst)'s] for copying later
            for k, v in PandocAst(val):
                # Image -> [attrs, Inlines, target]
                # - attrs = [ident, [classes], [(key,val)-pairs]]
                # - Inlines = [Inline-elements]  (of the alt-text)
                # - target = [url, title]
                if k == 'Image':
                    src_path = v[-1][0]  # is url or relative to src_dir
                    if src_path.startswith('http'):
                        continue
                    # it should be a file on disk ...
                    dst_path = '{}/{}'.format(self.idx.dst_dir, src_path)
                    v[-1][0] = dst_path  # is relative to dst_dir
                    src_dir = os.path.dirname(self.idx.src_file)
                    self.imgs.append(
                         (os.path.join(src_dir, src_path),
                          os.path.join(self.idx.dst_dir, dst_path))
                    )

            self._ast.append(as_block(key, val))  # append as normal paragraph

    def _orderedlist(self, key, val):
        'An OrderedList is a multiple-choice (or multiple-correct) element'
        # OrderedList -> ListAttributes [[Block]]
        # - ListAttributes = (Int, ListNumberStyle, ListNumberDelim)
        # - only the first OrderedList is the choices-list for the question
        q = self.qstn[-1]
        if len(q.choices) > 0:
            log.debug('ignore ordered list (already have one)')
            self._ast.append(as_block(key, val))
        else:
            (num, style, delim), items = val
            style = style.get('t')
            delim = delim.get('t')
            for n, item in enumerate(items):
                txt = PandocAst(item).convert('markdown').strip()
                q.choices.append((ol_num(n+1, style), txt))
            log.debug('choices q[%d] is %r', len(self.qstn), q.choices)

    def _para_attr(self, para):
        'extract and return attributes from para (if any)'
        # An attribute Para starts with a known attribute: keyword
        # - parameter para is the 'c'-val from {'t': 'Para', 'c': [...]}
        # - list of words may span multiple lines
        # - explanation: is the only attr whose value is markdown text.

        attrs = {}  # attrs{attr} -> sub-ast
        # check if para starts with an attribute keyword, if not return {}
        try:
            if para[0]['t'] != 'Str':
                return attrs
            attr = para[0]['c'].lower()
            if attr not in self.ATTR_KEYWORDS:
                return attrs
        except Exception as e:
            log.debug('cannot retrieve attributes from para: %s', repr(e))
            return attrs

        # collect subast per attribute in ATTR_KEYWORDS
        ptr = attrs.setdefault(attr, [])
        for key, val in PandocAst(para).tokens:
            if key != 'Str':
                ptr.append(as_block(key, val))    # append non-Str to ptr
                continue
            attr = val.lower()
            if attr in self.ATTR_KEYWORDS:
                ptr = attrs.setdefault(attr, [])  # keyword: starts new ptr
                continue
            ptr.append(as_block(key, val))        # otherwise, append to ptr

        # process known attributes
        for attr, subast in attrs.items():
            if attr not in self.ATTR_KEYWORDS:
                continue
            if attr == 'explanation:':
                xpl = PandocAst(as_ast('Para', subast)).convert('markdown')
                attrs[attr] = xpl.strip()

            elif attr == 'tags:':
                # list of words, possibly separated by spaces and/or comma's
                words = pf.stringify(subast).replace(',', ' ').lower()
                attrs[attr] = sorted(set(words.split()))

            elif attr == 'answer:':
                # list of letters or numbers, possibly separated by non-alnum's
                answers = pf.stringify(subast).lower()
                attrs[attr] = sorted(set(x for x in answers if x.isalnum()))

            elif attr == 'section:':
                # section: keyword for this question
                words = pf.stringify(subast).replace(',', ' ').lower()
                attrs[attr] = words.split()[0]  # keep only 1st word

        # log any attributes found
        log.debug('found %d attributes: %s', len(attrs), attrs.keys())
        return attrs

    def _codeblock(self, key, val):
        # [[id, [classes,..], [(key,val),..]], string]
        # TODO: add support for reordering & dragndrop questions back in
        (qid, qclass, att), code = val
        if qid.lower() in ['reorder', 'dragndrop']:
            log.debug('SPECIAL CODE BLOCK %s', repr(val))
        self._ast.append(as_block(key, val))
        log.debug('qid %s, qclass %s, attr %s', qid, qclass, att)

    def _inherit_tags(self):
        'questions inherit last section keyword & tags of lower levels'
        level_tags = {}  # [tags] indexed by level nrs <= q.level
        section = ''
        for q in self.qstn:
            section = q.section or section
            level_tags[q.level] = q.tags
            for high in [l for l in level_tags if l > q.level]:
                level_tags.pop(high, None)
            q.tags = sorted(set(chain(*level_tags.values())))
            q.section = section
        log.debug('%d questions tagged', len(self.qstn))
        return self

    def _prune(self):
        'remove question-less headers'
        # these only serve to group questions into logical units in the doc
        idxs = []
        for nr, q in enumerate(self.qstn):
            if len(q.choices) == 0 or len(q.answer) == 0:
                idxs.append(nr)
        log.debug('total %d, pruned %d -> %d remaining',
                  len(self.qstn), len(idxs), len(self.qstn) - len(idxs))
        for idx in reversed(idxs):
            del self.qstn[idx]
        return self


def _copy_files(src_dst):
    'safely copy src to dst (if src is newer)'
    for src, dst in src_dst:
        try:
            # src available and readable
            if not os.access(src, os.R_OK):
                log.error(' - skip missing src %s', src)
                continue

            dst_dir = os.path.dirname(dst)
            os.makedirs(dst_dir, exist_ok=True)

            if not os.access(dst, os.F_OK) or\
                    os.path.getmtime(src) > os.path.getmtime(dst):
                    shutil.copy2(src, dst)
                    log.info('- add %s', dst)
            else:
                log.info('- keep %s', dst)
        except OSError:
            log.exception('copy failed %s -> %s', src, dst)


def convert(idx):
    'convert <src_dir>/path_to_srcfile to <dst_dir>/<test_id>/-files'
    # Add test_id specific handler for this logger
    TLS.logfile = os.path.join(idx.dst_dir, 'mtr.log')
    TLS._handler = logging.FileHandler(TLS.logfile)
    TLS._handler.setFormatter(FORMAT)
    TLS._handler.addFilter(ThreadFilter(threading.current_thread().name))
    log.addHandler(TLS._handler)
    log.info('Parsing source: %s', idx.src_file)

    # parse the source file -> p.meta, p.tags, p.qstn
    p = Parser(idx).parse()

    # clear output directory (carefully)
    log.info('Delete (most) files:')
    for fname in utils.yield_files(idx.dst_dir, '.*'):
        if fname != TLS.logfile and not fname.endswith('.png'):
            log.info('- del %s', fname)
            os.remove(fname)

    # save to dst_dir
    log.info('Add new files:')
    for nr, q in enumerate(p.qstn):
        qfname = os.path.join(idx.dst_dir, 'q{:03d}.json'.format(nr))
        q.save(qfname)
        log.debug('- add %s', qfname)
    log.info('Copy images (if needed):')
    _copy_files(p.imgs)  # copy any newer/missing images

    # create mtr.idx
    log.info('meta is %r', p.meta)
    idx = idx._replace(cflags=utils.F_PLAYABLE,
                       numq=len(p.qstn),
                       grade=p.meta.get('grade', 0))
    fname = os.path.join(idx.dst_dir, 'mtr.idx')
    with open(fname, 'wt') as fh:
        fh.write(json.dumps(idx))
        log.info('Created %s', fname)
        for fld in idx._fields:
            log.info('- %-8s: %s', fld, getattr(idx, fld))

    # create quiz.json
    log.debug('meta:')
    for k, v in p.meta.items():
        log.debug('%-12s: %s', k, v)

    # remove compile job specific handler
    try:
        log.debug('all work is done, bye!')
        time.sleep(2)
        log.removeHandler(TLS._handler)
        os.remove(TLS.logfile)
    except OSError:
        log.exception('Could not remove compiler logfile')
    except Exception:
        log.exception('TLS error, could not remove TLS._handler, thread died?')

    pass


class Quiz(object):
    '''
    Compile a srcfile (fullpath) to a quiz with 1 or more questions.
    Log messages to logfile (relative to dstdir)
    '''
    # this class ties PandocAst and Parser together
    def __init__(self, idx):  # , cfg=None):
        try:
            # setup TLS for this compile run
            TLS.idx, TLS.cfg = idx, cfg
            self.setlogger()

            log.debug('Compiling %s', idx.src_file)
            log.debug('Saving to %s/', idx.dst_dir)

            p = Parser(idx).parse()
            self.meta = p.meta
            self.tags = p.tags
            self.qstn = p.qstn

            # log results
            log.debug('meta %r', self.meta)
            log.debug('tags %r', self.tags)
            for nr, q in enumerate(self.qstn):
                log.debug('Q%d\n%s', nr, q.to_json())

            # Update TLS.idx with results
            TLS.idx._replace(numq=len(self.qstn), cflags=0)

            self.save()
        except Exception as e:
            log.debug('Error parsing markdown file: %s', TLS.idx.src_file)
            raise QError('Error parsing markdown file: {}'.format(e))

    def __del__(self):
        'instance bucketlist'
        # if any exceptions are raised, TLS might be gone
        global log
        import shutil
        import time
        time.sleep(2)  # so mantra reads/displays last status as well
        try:
            # TODO: if an exception was raised, TLS is cleared??
            # XXX: delme, for debug/review purposes only
            shutil.copyfile(TLS.logfile, TLS.logfile + '.delme')
            os.remove(TLS.logfile)
            log.debug('all work is done, bye!')
            log.removeHandler(TLS._handler)
        except Exception:
            log = getlogger()
            log.exception('TLS error, could not delete TLS.log, thread died?')

    def __iter__(self):
        'iterate across available questions in a Quiz instance'
        return iter(self.qstn)

    def setlogger(self):
        'create and set an thread specific logger'
        TLS.logfile = os.path.join(TLS.idx.dst_dir, 'mtr.log')
        TLS._handler = logging.FileHandler(TLS.logfile)
        TLS._handler.setFormatter(FORMAT)
        TLS._handler.addFilter(ThreadFilter(threading.current_thread().name))
        log.addHandler(TLS._handler)
        return log

    def valid(qstn):
        'say wether or not this is a valid question'
        return False

    def save(self):
        'save questions to disk'
        # MtrIdx = namedtuple, with fields:
        # src_file, src_hash, dst_dir, category, test_id, grade, score, numq,
        # cflags
        dst_dir = TLS.idx.dst_dir
        log.debug('clearing %s/q*.json', dst_dir)
        log.debug('clearing %s/img/*.png', dst_dir)

        for nr, q in enumerate(self.qstn):
            qfile = 'q{:03d}.json'.format(nr)
            log.debug('- saving %s to dir %s', qfile, dst_dir)
            with open(os.path.join(dst_dir, qfile), 'wt') as fh:
                fh.write(q.to_json())

        with open(os.path.join(dst_dir, 'mtr.idx'), 'wt') as fh:
            fh.write(json.dumps(TLS.idx))

        for field in TLS.idx._fields:
            log.debug('idx.%s -> %s', field, getattr(TLS.idx, field))

