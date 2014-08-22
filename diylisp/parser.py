# -*- coding: utf-8 -*-

import re
import logging

from .ast import is_boolean, is_list
from .types import LispError

"""
This is the parser module, with the `parse` function which you'll implement as part 1 of
the workshop. Its job is to convert strings into data structures that the evaluator can
understand.
"""

logger = logging.getLogger(__name__)

WHITESPACE    = " \t\n\r"
TOK_PAR_OPEN  = '('
TOK_PAR_CLOSE = ')'
TOK_QUOTE     = '\''

def parse(source):
    """Parse string representation of one *single* expression
    into the corresponding Abstract Syntax Tree."""
    logger.debug("parse: source=%s", source)
    source = source.strip()
    source = remove_comments(source)


    expr, pend = do_parse(source, 0)

    logger.debug("parse: %r, %d (%d)", expr, pend, len(source))

    if pend != len(source):
        raise LispError("Expected EOF")

    return expr

def do_parse(source, pos, level=0):
    def log(msg, *args):
        logger.debug("%s do_parse: " + msg, level*"    ", *args)

    log("source[%d:]: %s", pos, source[pos:])


    pos = skip_whitespace(source, pos)

    c = source[pos]
    if c == TOK_PAR_OPEN:
        log("TOK_PAR_OPEN")
        expr, pend = parse_expr(source, pos, level + 1)

    elif c == TOK_PAR_CLOSE:
        log("TOK_PAR_CLOSE")

    elif c == TOK_QUOTE:
        log("TOK_QUOTE")
        expr, pend = parse_quote(source, pos, level + 1)

    elif c == '#':
        log("BOOL")
        expr, pend = parse_boolean(source, pos)

    elif parse_int(source, pos):
        log("INT")
        expr, pend = parse_int(source, pos)

    else:
        log("SYMBOL")
        expr, pend = parse_symbol(source, pos)

    log("=> %r, %d %d", expr, pend, len(source))
    return expr, pend

def parse_expr(source, pos, level=0):
    """parse_expr() -> ()

    >> parse_expr("()", 0)
    ([], 2)

    >>> parse_expr("foo", 0)
    Traceback (most recent call last):
    ...
    AssertionError
    """
    def log(msg, *args):
        logger.debug("%s parse_expr: " + msg, level*"    ", *args)
    assert source[pos] == TOK_PAR_OPEN


    pclose = find_matching_paren(source, pos)
    pos += 1 # skip (
    log("source[%d:%d]: %s", pos, pclose, source[pos:pclose])


    expr = []

    while pos < pclose:
        log("expr: %r pos: %d", expr, pos)
        pos = skip_whitespace(source, pos)

        sub_expr, pos = do_parse(source[:pclose], pos, level + 1)
        log("sub_expr: %r pos: %d rest: %s", sub_expr, pos, source[pos:pclose])

        expr.append(sub_expr)

        pos += 1

    pos = pclose + 1  # skip )
    log("=> %r, %d", expr, pos)
    return expr, pos

def parse_quote(source, pos, level=0):
    """parse_quote() -> ()

    >>> parse_quote("'foo", 0)
    (['quote', 'foo'], 4)

    >>> parse_quote("'()", 0)
    (['quote', []], 3)

    """
    def log(msg, *args):
        logger.debug("%s parse_quote: " + msg, level*"    ", *args)
    assert source[pos] == TOK_QUOTE

    pos = pos + 1  # skip '

    sub_expr, pos = do_parse(source, pos, level + 1)

    expr = ["quote", sub_expr]

    log("=> %r, %d", expr, pos)
    return expr, pos

def parse_int(source, pos):
    """parse_int(source, pos) -> (expr, pos)

    Parse integer::

    >>> parse_int("111", 0)
    (111, 3)

    >> parse_int("", 0)
    None
    """
    tok, pend = next_token(source, pos)
    if not tok:
        return None

    try:
        return int(tok), pend
    except ValueError, e:
        pass

    return None

def parse_boolean(source, pos):
    """parse_boolean(source, pos) -> (expr, pos)

    Parse a boolean, retunr expression / pos tuple.

    >>> parse_boolean("#f", 0)
    (False, 2)

    >>> parse_boolean("#f ", 0)
    (False, 2)
    """
    assert source[pos] == "#"

    tok, pend = next_token(source, pos)
    if tok == "#t":
        return True, pend
    elif tok == "#f":
        return False, pend

    raise LispError("Parse error: " + tok)

def parse_symbol(source, pos):
    """parse_symbol(source, pos) -> (expr, pos)

    Parse a symbol, retunr expression / pos tuple.

    >>> parse_symbol("foo bar baz", 0)
    ('foo', 3)

    >>> parse_symbol("foo bar baz", 4)
    ('bar', 7)

    >>> parse_symbol("foo bar baz", 8)
    ('baz', 11)
    """
    tok, pend = next_token(source, pos)
    expr = source[pos:pend]
    return expr, pend

def next_token(source, pos):
    """next_token(source, start) -> (token, pos)

    Get next token from start::

    >>> next_token("foo", 0)
    ('foo', 3)

    >>> next_token("foo bar baz", 0)
    ('foo', 3)

    >>> next_token("foo bar baz", 4)
    ('bar', 7)

    >>> next_token("foo()", 0)
    ('foo', 3)

    >>> next_token("foo bar baz", 8)
    ('baz', 11)

    """
    pend = skip_symbol(source, pos)
    if pend <= len(source):
        tok = source[pos:pend]
        return tok, pend

    return None, pend

def skip_whitespace(source, start):
    """
    Skip whitespace in source form start::

    >>> skip_whitespace("   foo", 0)
    3

    >>> skip_whitespace("   foo", 2)
    3

    >>> skip_whitespace("foo", 0)
    0

    >>> skip_whitespace("   ", 0)
    3
    """
    return skip_until(source, start, WHITESPACE)

def skip_symbol(source, start):
    """skip_symbol(source, start) -> int

    Skip symbol starting at start::

    >>> skip_symbol("foo", 0)
    3

    >>> skip_symbol("foo(", 0)
    3
    """
    return find_chars(source, start, WHITESPACE + TOK_PAR_OPEN + TOK_PAR_CLOSE + TOK_QUOTE)

def find_whitespace(source, start):
    return find_chars(source, start, WHITESPACE)

def skip_until(source, start, chars):
    for n, c in enumerate(source[start:]):
        if c not in chars:
            return start + n
    else:
        return len(source)

def find_chars(source, start, chars):
    for n, c in enumerate(source[start:]):
        if c in chars:
            return start + n
    else:
        return len(source)

##
## Below are a few useful utility functions. These should come in handy when
## implementing `parse`. We don't want to spend the day implementing parenthesis
## counting, after all.
##


def remove_comments(source):
    """Remove from a string anything in between a ; and a linebreak"""
    return re.sub(r";.*\n", "\n", source)


def find_matching_paren(source, start=0):
    """Given a string and the index of an opening parenthesis, determines
    the index of the matching closing paren."""

    assert source[start] == '('
    pos = start
    open_brackets = 1
    while open_brackets > 0:
        pos += 1
        if len(source) == pos:
            raise LispError("Incomplete expression: %s" % source[start:])
        if source[pos] == '(':
            open_brackets += 1
        if source[pos] == ')':
            open_brackets -= 1
    return pos


def split_exps(source):
    """Splits a source string into subexpressions
    that can be parsed individually.

    Example:

        > split_exps("foo bar (baz 123)")
        ["foo", "bar", "(baz 123)"]
    """

    rest = source.strip()
    exps = []
    while rest:
        exp, rest = first_expression(rest)
        exps.append(exp)
    return exps


def first_expression(source):
    """Split string into (exp, rest) where exp is the
    first expression in the string and rest is the
    rest of the string after this expression."""

    source = source.strip()
    if source[0] == "'":
        exp, rest = first_expression(source[1:])
        return source[0] + exp, rest
    elif source[0] == "(":
        last = find_matching_paren(source)
        return source[:last + 1], source[last + 1:]
    else:
        match = re.match(r"^[^\s)']+", source)
        end = match.end()
        atom = source[:end]
        return atom, source[end:]

##
## The functions below, `parse_multiple` and `unparse` are implemented in order for
## the REPL to work. Don't worry about them when implementing the language.
##


def parse_multiple(source):
    """Creates a list of ASTs from program source constituting multiple expressions.

    Example:

        >>> parse_multiple("(foo bar) (baz 1 2 3)")
        [['foo', 'bar'], ['baz', 1, 2, 3]]

    """

    source = remove_comments(source)
    return [parse(exp) for exp in split_exps(source)]


def unparse(ast):
    """Turns an AST back into lisp program source"""

    if is_boolean(ast):
        return "#t" if ast else "#f"
    elif is_list(ast):
        if len(ast) > 0 and ast[0] == "quote":
            return "'%s" % unparse(ast[1])
        else:
            return "(%s)" % " ".join([unparse(x) for x in ast])
    else:
        # integers or symbols (or lambdas)
        return str(ast)
