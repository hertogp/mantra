#!/usr/bin/env python3
import sys
import urllib.request
import json
import pypandoc as pp
import pandocfilters as pf
from collections import namedtuple
from itertools import chain
from io import StringIO

# pylint disable: E265

#-- helpers nopep8


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
            self.reader = source
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
        self.reader = StringIO(str(self.source))
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

    def __init__(self, source=None, ast=None, fmt=None, opts=None, xtra=None):
        'create META,AST from source or use ast if source is None'
        self.xtra = xtra or self.MD_XTRA
        self.opts = opts or self.MD_OPTS
        self.fmt = '+'.join(chain([fmt or self.FMT], opts or self.MD_OPTS))
        self.meta = {u'unMeta': {}}

        self.source = source    # if given, will override any ast provided
        self.ast = ast          # supply this to iterate across subset ast

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
        json_str = json.dumps([self.meta, self.ast])
        return pp.convert_text(json_str, out_fmt, in_fmt, extra_args=xtra)


class Parser(object):
    'Parse a PandocAst into a Quiz with 0 or more questions'
    def __init__(self, in_fmt=None, opts=None):
        self.fmt = in_fmt
        self.opts = opts
        self.meta = {u'unMeta': {}}
        self.tags = [[]]  # quiz tags are level 0 tags
        self.qstn = []    # the list of questions

    def parse(self, ast):
        'parse ast and return a quiz object w/ 0 or more questions'
        self.meta.update(ast.meta)                 # keep existing meta data

        # adopt any YAML defined tags, add as level-0 tags (self.tags[0])
        unmeta = self.meta.get(u'unMeta', {})
        for key, val in unmeta.items():
            if key.lower() != 'tags':
                continue
            tags = pf.stringify(val).lower().replace(',', ' ').split()
            self.tags[0] = sorted(set().union(self.tags[0], tags))

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
                       section='',    # section tag to tally score per topic
                       title=[],      # q's title
                       text=[],       # q's text
                       choices=[],    # q's possible answers
                       answer=[],     # q's correct answer(s)
                       explain=[],    # explanation of the answer(s)
                       ast=[],        # qstn's ast
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
            elif key == u'CodeBlock':
                self._codeblock(key, val, qstn)
            else:
                qstn.ast.append(as_block(key, val))

        # question's dynamic child template, which extends qbase.html & fills
        # in its {% block question %} using qstn's ast
        qstn.tpl = ''.join(['{% extends "quiz/qbase.html" %}',
                            '{% block question %}',
                            PandocAst(ast=qstn.ast).convert('html'),
                            '{% endblock %}'
                            ])
        return qstn

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
        print('_header', key, val)
        qstn.level = val[0]
        qstn.title = PandocAst(ast=as_ast(key, val)).convert('commonmark')

    def _para(self, key, val, qstn):
        # TODO: allow for multiple keywords: values in single paragraph
        # Para -> [Block], might be an <attribute:>-para
        if len(val) < 1:
            return  # nothing todo

        if val[0]['t'] != u'Str' or not val[0]['c'].endswith(':'):
            para = None                        # para is not attr para
            attr = []
        else:
            para = val[0]['c'].lower()[0:-1]   # pickup 1st word as attr name
            attr = val[1:]                     # remaining text is attr value

        # handle known types of Para's
        if para == 'tags':
            # tags: tag1, tag2, ...
            tags = pf.stringify(attr).replace(',', ' ').lower().split()
            self.tags = (self.tags + [[]]*qstn.level)[0:qstn.level]
            self.tags.append(tags)
            qstn.tags = sorted(set().union(*self.tags))

        elif para == 'answer':
            # answer: A,c  (the answer to a some previous orderedlist-field)
            qstn.answer = pf.stringify(attr).replace(',', ' ').lower().split()

        elif para == 'explanation':
            # explanation: <regular markdown explaining the answer>
            expl = PandocAst(ast=as_ast(key, val)).convert('commonmark')
            qstn.explain.append(expl)  # append normal paragraph

        else:
            # not a special para, so part of question text
            # but might still contain in-line `<fieldType>`{...} constructs
            blocks = []
            for tokk, tokv in PandocAst(ast=val).tokens:
                if tokk != u'Code':
                    blocks.append(as_block(tokk, tokv))
                    continue
                (ID, CLASS, ATTR), CODE = tokv
                print('-'*80, 'para Code block', CODE)
                print(ID, CLASS, ATTR)

                # # ensure lower case code, attr.keys & stripped list elements
                # CODE = CODE.lower()
                # ATTR = dict((k.lower(), v.split(',')) for k, v in ATTR)
                # choices = [s.strip() for s in ATTR.get('choices', [])]
                # answer = [s.strip() for s in ATTR.get('answer', [])]

                # # if applicable, keep {{ form.field_<x> }} in-line -> in blocks
                # if CODE == 'fill':
                #     # an input field to type text into
                #     blocks.appnd(as_block('Str', 'code-is-fill'))
                # elif CODE == 'select':
                #     # a dropdown to select one entry from a list of choices
                #     # TODO: check len answer is 1, answer occurs in choices
                #     choices = list(enumerate(choices))  # [(idx, value), ..]
                #     assert len(answer) == 1  # TODO raise QFieldError instead
                #     answer = answer[0]       # answer should also be in choices
                #     # XXX: turn answer into its index? DDF is coerce=int'd anyway..
                #     wtf_fld = DropDownField(choices=choices, answer=answer)
                #     wtf_ast = self._add_field(qstn, wtf_fld)
                #     blocks.extend(wtf_ast[0]['c'])  # inline, so skip outer Para
                # else:
                #     blocks.append(as_block(tokk, tokv))

            qstn.ast.append(as_block(key, blocks))  # append as normal paragraph

    def _orderedlist(self, key, val, qstn):
        'An OrderedList is a multiple-choice (or multiple-correct) element'
        # OrderedList -> ListAttributes [[Block]]
        # - ListAttributes = (Int, ListNumberStyle, ListNumberDelim)
        (num, style, delim), items = val
        style = style.get('t')
        delim = delim.get('t')

        qstn.choices = list((ol_num(n+1, style),
                             PandocAst(ast=item).convert('commonmark'))
                            for n, item in enumerate(items))

        # keep block in org ast
        qstn.ast.append(as_block(key, val))

    def _codeblock(self, key, val, qstn):
        # [[id, [classes,..], [(key,val),..]], string]
        (qid, qclass, att), code = val
        if qid.lower() in ['reorder', 'dragndrop']:
            print('-'*80, 'SPECIAL CODE BLOCK', val)
            pass
        qstn.ast.append(as_block(key, val))
        print(qid, qclass, att)


class Question(object):
    'Represent a single question'
    TYPES = {0: 'only-ok',           # only ok button
             1: 'multiple-choice',   # radio buttons
             2: 'multiple-correct',  # check boxes
             3: 'yes-no',            # Yes/No buttons
             4: 'flip-over',         # flip button
             5: 're-order',          # re-order across 2 lists
             6: 'fill-in',           # text-input
             7: 'drop-down',         # select 1 answer
             8: 'mixed'}             # select 1 answer

    def __init__(self):
        self.qtype = 0
        self.title = ''    # markdown text
        self.text = ''     # markdown text
        self.choices = []  # list of possible answers (markdown)
        self.correct = []  # list of idx's of correct answers
        self.explain = ''  # markdown text
        self.section = ''  # string
        self.tags = []     # list of stings
        self.ast = None    # pandoc ast of question


class Quiz(object):
    'Represent a quiz with 0 or more questions'
    def __init__(self, filename):
        p = Parser().parse(source=filename)
        self.filename = filename
        self.meta = p.meta
        self.tags = p.tags
        self.questions = p.qstn

    def __call__(self, qid):
        'return a question form and string template'
        try:
            qstn = self.questions[qid]
        except IndexError:
            raise QError('Quiz: question index out of range')

        return qstn  # the question

if __name__ == '__main__':
    print('qparse is alive, once again!')
    ast = PandocAst(sys.argv[1])
    # import pprint
    # for token in ast:
    #     print(token.type)
    #     pprint.pprint(token.value, indent=4)

    p = Parser().parse(ast=ast)
    print('Parser.meta', p.meta)
    print('Parser.tags', json.dumps(p.tags, indent=3))
    print()
    for q in p.qstn:
        print('-'*80)
        print('Question', q.title)
        print('\n- tags\n', q.tags)
        print('\n- title\n', q.title)
        print('\n- text\n', q.text)
        print('\n- choices\n', q.choices)
        print('\n- answer\n', q.answer)
        print('\n- explain\n', q.explain)
        print('\n- markdown\n', q.markdown)
        print('\n- ast\n', q.ast)
