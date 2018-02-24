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

from log import getlogger
msgfmt = '%(asctime)s [%(name)s] %(funcName)s %(message)s'
datefmt = '%H:%M:%S'
FORMAT = logging.Formatter(fmt=msgfmt, datefmt=datefmt)

# pylint disable: E265
# - helpers nopep8


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


#--CLASSES
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
    provides iterators for headers & tokens.

    ast = PandocAst('file.md')           # convert markdown to AST
    for token in ast:                    # - iterate AST's tokens
        print(token)

    hdr = PandocAst()                    # new instance
    for level, header in ast.headers:    # - header is a sub-AST
        for tok in hdr.load(ast=header): # - load sub-AT and
            print(tok)                   #   iterate its tokens
    '''
    MD_XTRA = ['--atx-header', '--standalone']
    MD_OPTS = [  # 'hard_line_breaks',
        'yaml_metadata_block',
        'fenced_code_attributes',
        'inline_code_attributes',
        'fancy_lists',
        'lists_without_preceding_blankline',
        ]
    FMT = 'markdown'

    def __init__(self, log=None, source=None, ast=None, fmt=None, opts=None,
                 xtra=None):
        'create META,AST from source or use ast if source is None'
        self.log = log if log else getlogger(__name__)
        self.xtra = xtra or self.MD_XTRA
        self.opts = opts or self.MD_OPTS
        self.fmt = '+'.join(chain([fmt or self.FMT], opts or self.MD_OPTS))
        self.meta = {u'unMeta': {}}

        self.source = source    # if given, will override any ast provided
        self.ast = ast          # supply this to iterate across subset ast
        self.log.debug(source)
        if source is not None:  # source overrides any given ast
            with OpenAnything(source) as f:
                try:
                    src = f.read()
                    txt = pp.convert_text(src, 'json', format=self.fmt)
                    self.meta, self.ast = json.loads(txt)
                except Exception as e:
                    raise QError("Can't convert {}: {}".format(self.source, e))

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
                yield level, ast                 # yield last header's ast
                level, ast = _tok.value[0], []   # start this header's new ast
            ast.append(as_block(*_tok))

        yield level, ast

    def convert(self, out_fmt=None, xtra=[]):
        'turn AST into output format'
        in_fmt = 'json'
        out_fmt = out_fmt or self.FMT
        xtra = xtra or self.MD_XTRA
        json_str = json.dumps([self.meta, self.ast])
        return pp.convert_text(json_str, out_fmt, in_fmt, extra_args=xtra)


class Parser(object):
    'Parse a PandocAst into a list of 0 or more questions'
    # an Attribute Para starts with one of these:
    ATTR_KEYWORDS = ['tags:', 'answer:', 'explanation:', 'section:']

    def __init__(self, log=None, in_fmt=None, opts=None):
        self.log = log if log else getlogger(__name__)
        self.fmt = in_fmt
        self.opts = opts
        self.meta = {u'unMeta': {}}
        self.tags = [[]]  # list of tag-list per header level (=idx)
        self.qstn = []    # the list of Question instances
        self.log.debug('in_fmt  %s:', in_fmt)
        self.log.debug('options %s:', opts)

    def parse(self, ast):
        'parse ast and return a quiz object w/ 0 or more questions'
        self.meta.update(ast.meta)                 # keep existing meta data

        # adopt any level-0 tags: defined in the YAML part (self.tags[0])
        unmeta = self.meta.get(u'unMeta', {})
        for key, val in unmeta.items():
            if key.lower() != 'tags':
                continue
            tags = pf.stringify(val).lower().replace(',', ' ').split()
            self.tags[0] = sorted(set(self.tags[0] + tags))

        # process front matter and subsequent headers as questions
        for level, hdr in ast.headers:
            if level == 0:
                self._front_matter(hdr)
            else:
                self.qstn.append(self.question(ast=hdr))
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
                       ast=[],        # qstn's ast with attributes removed
                       markdown='')   # qstn's orginal markdown

        ast = PandocAst(ast=ast)
        qstn.markdown = ast.convert()
        for key, val in ast.tokens:
            if key == u'Header':
                self._header(key, val, qstn)
            elif key == u'Para':
                self._para(key, val, qstn)
            elif key == u'OrderedList':
                self._orderedlist(key, val, qstn)
            else:
                qstn.ast.append(as_block(key, val))

        qstn.text = PandocAst(ast=qstn.ast).convert('markdown')
        return qstn

    def _para_attr(self, para):
        'extract any attributes from para and return the rest'
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
        except Exception:
            return attrs

        # collect subast per attribute in ATTR_KEYWORDS
        ptr = attrs.setdefault(attr, [])
        for key, val in PandocAst(ast=para).tokens:
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
                xpl = PandocAst(ast=as_ast('Para', subast)).convert('markdown')
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

        for attr, val in attrs.items():
            print(attr, val)
        return attrs

    def _front_matter(self, ast):
        'parse stuff before the first header'
        # only pick up any additional tags, ignore the rest
        for _token in PandocAst(ast=ast).tokens:
            if _token.type != u'Para':
                continue
            if _token.value[0]['t'] != u'Str':
                continue
            if _token.value[0]['c'].lower() != 'tags:':
                continue
            tagstr = pf.stringify(_token.value[1:]).replace(',', ' ').lower()
            self.tags[0] = sorted(set().union(self.tags[0], tagstr.split()))

    def _header(self, key, val, qstn):
        'header starts a new question'
        # Header -> [level, [slug, [(key,val),..]], [header-blocks]]
        qstn.level = val[0]
        qstn.title = PandocAst(ast=as_ast(key, val)).convert('markdown')
        qstn.title = qstn.title.strip()

    def _para(self, key, val, qstn):
        # Para -> [Block], might be an <attribute:>-para
        if len(val) < 1:
            return  # nothing todo

        attrs = self._para_attr(val)
        if len(attrs):
            qstn.answer = attrs.get('answer:', [])
            qstn.tags = attrs.get('tags:', [])
            qstn.section = attrs.get('section:', '')
            qstn.explain = attrs.get('explanation:', '')
        else:
            qstn.ast.append(as_block(key, val))  # append as normal paragraph

    def _orderedlist(self, key, val, qstn):
        'An OrderedList is a multiple-choice (or multiple-correct) element'
        # OrderedList -> ListAttributes [[Block]]
        # - ListAttributes = (Int, ListNumberStyle, ListNumberDelim)
        # - only the first OrderedList is the choices-list for the question
        if len(qstn.choices) > 0:
            qstn.ast.append(as_block(key, val))
        else:
            (num, style, delim), items = val
            style = style.get('t')
            delim = delim.get('t')

            for n, item in enumerate(items):
                txt = PandocAst(ast=item).convert('markdown').strip()
                qstn.choices.append((ol_num(n+1, style), txt))

    def _codeblock(self, key, val, qstn):
        # [[id, [classes,..], [(key,val),..]], string]
        (qid, qclass, att), code = val
        if qid.lower() in ['reorder', 'dragndrop']:
            print('-'*80, 'SPECIAL CODE BLOCK', val)
            pass
        qstn.ast.append(as_block(key, val))
        print(qid, qclass, att)


class Quiz(object):
    '''
    Compile a srfile (fullpath) to a quiz with 1 or more questions.
    Log messages to logfile (relative to dstdir)
    '''
    # this class ties PandocAst and Parser together
    def __init__(self, srcfile, dst_dir):
        try:
            kwargs = {'funcName': 'quiz.init'}
            self.dst_dir = dst_dir
            self.srcfile = srcfile
            self.test_id = os.path.basename(dst_dir)
            self.logfile = os.path.join(dst_dir, 'mtr.log')

            # setup handler to log to specific file
            self.log = getlogger(self.test_id)
            self.log.propagate = False               # qparse logs stop here
            self.log.setLevel(logging.DEBUG)
            self._handler = logging.FileHandler(self.logfile)
            self._handler.setFormatter(FORMAT)
            self.log.addHandler(self._handler)

            p = Parser(self.log)
            ast = PandocAst(self.log, source=srcfile)
            p.parse(ast)
            self.meta = p.meta
            self.tags = p.tags
            self.questions = p.qstn
            self.log.debug('Found %s questions', len(p.qstn), kwargs=kwargs)

        except Exception as e:
            self.log.debug('Error parsing markdown file: %s', srcfile)
            raise QError('Error parsing markdown file: {}'.format(e))

    def __del__(self):
        'instance bucketlist'
        import shutil
        import time
        time.sleep(1)  # give logfile a chance to appear
        shutil.copyfile(self.logfile, self.logfile + '.delme')
        os.remove(self.logfile)

    def __iter__(self):
        'iterate across available questions in a Quiz instance'
        return iter(self.questions)
