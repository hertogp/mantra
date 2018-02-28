# -*- encoding: utf8 -*-
import sys
import os
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
from log import getlogger, MethodFilter

# Globals
msgfmt = '%(asctime)s [%(name)s] %(funcName)s: %(message)s'
datefmt = '%H:%M:%S'
FORMAT = logging.Formatter(fmt=msgfmt, datefmt=datefmt)

# Thread Local storage
# - initialize only once (not per thread)
# - access by importing it where needed
TLS = threading.local()

# pylint disable: E265
# - helpers nopep8

# Thread Local Storage for this module
# - holds thread-specific logger instance (and test_id)
# - all functions/methods use TLS.log.debug/info/warn etc ...
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


class Closure(object):
    'simple container object'
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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

    ast = PandocAst.convert_file('file.md')   # convert markdown to AST
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
    def convert_file(cls, filename, fmt=None, opts=None):
        fmt = '+'.join([fmt or cls.FMT] + (opts or cls.MD_OPTS))
        try:
            txt = pp.convert_file(filename, 'json', format=fmt)
            meta, ast = json.loads(txt)
        except Exception as e:
            TLS.log.debug('cannot convert file %r\n  ->  (%s)', filename, repr(e))
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
                TLS.log.debug('lvl[%s] %r', level, pf.stringify(_tok.value))
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


class Parser(object):
    'Parse a PandocAst into a list of 0 or more questions'
    # an Attribute Para starts with one of these:
    ATTR_KEYWORDS = ['tags:', 'answer:', 'explanation:', 'section:']

    def __init__(self, in_fmt=None, opts=None):
        self.fmt = in_fmt
        self.opts = opts
        self.meta = {u'unMeta': {}}
        self.tags = [[]]  # list of tag-list per header level (=idx)
        self.qstn = []    # the list of Question instances
        self.imgs = []    # list of (src.png,dst.png)
        TLS.log.debug('fmt %s, opts %s', in_fmt, opts)

    def parse(self, ast):
        'parse a PandocAst and build a list of 0 or more questions'
        self.meta.update(ast.meta)                 # keep existing meta data

        # adopt any level-0 tags: defined in the YAML part (self.tags[0])
        unmeta = self.meta.get(u'unMeta', {})
        for key, val in unmeta.items():
            # hack: bare numbers in doc's yaml header are not wrapped in a
            # 'MetaInlines'-block, i.e. val={'t': 'MetaString', 'c': 'digits'}
            # -> which makes 'em disappear ...
            if val.get('t', None) != 'MetaInlines':
                val = {'t': 'MetaInlines', 'c': [val]}
            unmeta[key] = pf.stringify(val)
            if key.lower() != 'tags':
                continue
            tags = unmeta[key].lower().replace(',', ' ').split()
            self.tags[0] = sorted(set(self.tags[0] + tags))

        # process front matter and subsequent headers as questions
        for level, hdr in ast.headers:
            if level == 0:
                self._front_matter(hdr)
            else:
                self.qstn.append(self.question(hdr))

        # questions also inherit document tags
        for q in self.qstn:
            q.tags.extend(self.tags[0])
        return self

    def question(self, ast):
        'turn a header-ast into a single question, if possible'
        qstn = Closure(level=0,       # header level of this question
                       tags=[],       # qstn's tags (inherits self.TAGS)
                       section='',    # section keyword
                       title=[],      # q's title
                       text=[],       # q's text in markdown
                       choices=[],    # q's possible answers (ordered list)
                       answer=[],     # q's correct answer(s) (list of letters)
                       explain=[],    # explanation of the answer
                       imgs=[],       # list of (src.png, dst.png)
                       ast=[],        # qstn's original ast
                       markdown='')   # qstn's orginal markdown

        ast = PandocAst(ast)
        qstn.markdown = ast.convert()

        # process chunks in header-ast
        for key, val in ast.tokens:
            if key == u'Header':
                self._header(key, val, qstn)
            elif key == u'Para':
                self._para(key, val, qstn)
            elif key == u'OrderedList':
                self._orderedlist(key, val, qstn)
            else:
                qstn.ast.append(as_block(key, val))

        qstn.text = PandocAst(qstn.ast).convert('markdown')
        # a question inherits lower level tags
        level = qstn.level
        for q in reversed(self.qstn):
            if level < 1:
                break
            if q.level < level:
                qstn.tags.extend(q.tags)
                level -= 1
        return qstn

    def _front_matter(self, ast):
        'pickup any tags in front matter before 1st header'
        # only pick up any additional tags, ignore the rest
        TLS.log.debug('processing front matter')
        for _token in PandocAst(ast).tokens:
            if _token.type != u'Para':
                continue
            if _token.value[0]['t'] != u'Str':
                continue
            if _token.value[0]['c'].lower() != 'tags:':
                continue
            tagstr = pf.stringify(_token.value[1:]).replace(',', ' ').lower()
            self.tags[0] = sorted(set().union(self.tags[0], tagstr.split()))
            TLS.log.debug('xtra tags %r', tagstr.split())

    def _header(self, key, val, qstn):
        'header starts a new question'
        # Header -> [level, [slug, [(key,val),..]], [header-blocks]]
        qstn.level = val[0]
        qstn.title = PandocAst(as_ast(key, val)).convert('markdown')
        qstn.title = qstn.title.strip()
        TLS.log.debug('question title: %s', qstn.title)

    def _para(self, key, val, qstn):
        # Para -> [Block], might be an <attribute:>-para
        if len(val) < 1:
            return  # nothing todo

        attrs = self._para_attr(val)
        if len(attrs):
            # it was an attr-para, retrieve only known attributes
            qstn.answer = attrs.get('answer:', [])
            qstn.tags = attrs.get('tags:', [])
            qstn.section = attrs.get('section:', '')
            qstn.explain = attrs.get('explanation:', '')
        else:
            # modify para's image urls & collect [(src,dst)'s] for copying later
            for k, v in PandocAst(val):
                # Image -> [attrs, Inlines, target]
                # - attrs = [ident, [classes], [(key,val)-pairs]]
                # - Inlines = [Inline-elements]  (of the alt-text)
                # - target = [url, title]
                if k == 'Image':
                    src_relpath = v[-1][0]  # is relative to src_dir
                    dst_relpath = '{}/{}'.format(TLS.idx.dst_dir, src_relpath)
                    v[-1][0] = dst_relpath  # is relative to dst_dir
                    src_dir = os.path.dirname(TLS.idx.src_file)
                    qstn.imgs.append(
                        (os.path.join(src_dir, src_relpath),
                         os.path.join(TLS.idx.dst_dir, dst_relpath)))

            qstn.ast.append(as_block(key, val))  # append as normal paragraph

    def _orderedlist(self, key, val, qstn):
        'An OrderedList is a multiple-choice (or multiple-correct) element'
        # OrderedList -> ListAttributes [[Block]]
        # - ListAttributes = (Int, ListNumberStyle, ListNumberDelim)
        # - only the first OrderedList is the choices-list for the question
        if len(qstn.choices) > 0:
            TLS.log.debug('ignore ordered list (already have one)')
            qstn.ast.append(as_block(key, val))
        else:
            (num, style, delim), items = val
            style = style.get('t')
            delim = delim.get('t')

            for n, item in enumerate(items):
                txt = PandocAst(item).convert(
                    'markdown').strip()
                qstn.choices.append((ol_num(n+1, style), txt))

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
            TLS.log.debug('oops, exception seen %s', repr(e))
            return attrs

        # collect subast per attribute in ATTR_KEYWORDS
        ptr = attrs.setdefault(attr, [])
        for key, val in PandocAst(para).tokens:
            if key != 'Str':
                ptr.append(as_block(key, val))    # append non-Str to ptr
                continue
            attr = val.lower()
            if attr in self.ATTR_KEYWORDS:
                ptr = attrs.setdefault(attr, [])  # new collection ptr
                continue
            ptr.append(as_block(key, val))        # append to ptr

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
                # list of letters or numbers, possibly separated
                answers = pf.stringify(subast).lower()
                attrs[attr] = sorted(set(x for x in answers if x.isalnum()))

            elif attr == 'section:':
                words = pf.stringify(subast).replace(',', ' ').lower()
                attrs[attr] = words.split()[0]  # keep only 1st word

        # log any attributes found
        for attr, val in attrs.items():
            TLS.log.debug('attribute %s -> %s', attr, val)
        return attrs

    def _codeblock(self, key, val, qstn):
        # [[id, [classes,..], [(key,val),..]], string]
        (qid, qclass, att), code = val
        if qid.lower() in ['reorder', 'dragndrop']:
            TLS.log.debug('SPECIAL CODE BLOCK %s', repr(val))
        qstn.ast.append(as_block(key, val))
        TLS.log.debug('qid %s, qclass %s, attr %s', qid, qclass, att)


class Quiz(object):
    '''
    Compile a srcfile (fullpath) to a quiz with 1 or more questions.
    Log messages to logfile (relative to dstdir)
    '''
    # this class ties PandocAst and Parser together
    def __init__(self, idx, cfg):
        try:
            # setup TLS for this compile run
            TLS.idx = idx
            TLS.cfg = cfg
            self.setlogger()

            TLS.log.debug('src_file %s', idx.src_file)
            TLS.log.debug('dst_dir  %s', idx.dst_dir)

            ast = PandocAst.convert_file(TLS.idx.src_file)
            TLS.log.debug('ast.meta %s', repr(ast.meta))
            p = Parser().parse(ast)
            self.meta = p.meta
            self.tags = p.tags
            self.questions = p.qstn
            # log results
            unmeta = self.meta.get('unMeta', {})
            if len(unmeta):
                TLS.log.debug('qz %s', repr(unmeta.items()))
                # for k, v in unmeta.items():
                #     TLS.log.debug(' - %-12s: %r', k, v)
            else:
                TLS.log.debug('no meta information found')
            TLS.log.debug('Found %s questions', len(p.qstn))

            for nr, q in enumerate(p.qstn):
                TLS.log.debug('qn[%d][%d]: %d choices, %d answers, tags %s',
                              nr, q.level, len(q.choices), len(q.answer),
                              repr(q.tags))

        except Exception as e:
            TLS.log.debug('Error parsing markdown file: %s', TLS.idx.src_file)
            raise QError('Error parsing markdown file: {}'.format(e))

    def __del__(self):
        'instance bucketlist'
        # if any exceptions are raised, TLS might be gone
        import shutil
        import time
        time.sleep(2)  # so mantra reads/displays last status as well
        try:
            # TODO: if an exception was raised, TLS is cleared??
            # XXX: delme, for debug/review purposes only
            shutil.copyfile(TLS.logfile, TLS.logfile + '.delme')
            os.remove(TLS.logfile)
            TLS.log.debug('all work is done, bye!')
            TLS.log.removeHandler(TLS._handler)
            del TLS.log
        except Exception:
            log = getlogger()
            log.exception('TLS error, could not delete TLS.log, thread died?')

    def __iter__(self):
        'iterate across available questions in a Quiz instance'
        return iter(self.questions)

    def setlogger(self):
        'create and set an thread specific logger'
        TLS.log = getlogger(TLS.idx.test_id)
        TLS.log.propagate = False               # qparse logs stop here
        TLS.log.setLevel(logging.DEBUG)
        TLS.log.addFilter(MethodFilter())
        TLS.logfile = os.path.join(TLS.idx.dst_dir, 'mtr.log')
        TLS._handler = logging.FileHandler(TLS.logfile)
        TLS._handler.setFormatter(FORMAT)
        TLS.log.addHandler(TLS._handler)
        return TLS.log

    def valid(qstn):
        'say wether or not this is a valid question'
        return False

    def save(self, qstn, qid):
        'save qstn to disk'
        pass

