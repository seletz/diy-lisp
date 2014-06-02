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
logger.setLevel(logging.DEBUG)

TOK_PAR_OPEN  = '('
TOK_PAR_CLOSE = ')'

def parse(source):
    """Parse string representation of one *single* expression
    into the corresponding Abstract Syntax Tree."""
    logger.debug("parse: source=%s", source)

    source = source.strip()
    source = remove_comments(source)

    ast = None
    stack = []

    for tok in token_gen(source):
        logger.debug("parse: tok=%s, ast=%r, stack=%r", tok, ast, stack)
        value = None
        if tok == TOK_PAR_OPEN:
            logger.debug("parse: TOK_PAR_OPEN")
            if ast:
                # new open paren -- push current ast to the stack, make new ast.
                stack.append(ast)

            ast = []

        elif tok == TOK_PAR_CLOSE:
            logger.debug("parse: TOK_PAR_CLOSE")
            if stack:
                # closing paren -- restore previous ast
                prev = stack.pop()
                prev.append(ast)
                ast = prev

        elif parse_boolean(tok) is not None:
            value = parse_boolean(tok)
            logger.debug("parse: BOOLEAN: %r", value)

        elif parse_int(tok) is not None:
            value = parse_int(tok)
            logger.debug("parse: INTEGER: %r", value)

        else:
            logger.debug("parse: SYMBOL")
            value = tok

        if value is not None:
            if ast is not None:
                ast.append(value)
            else:
                return value

    return ast

def parse_int(tok):
    try:
        return int(tok)
    except ValueError, e:
        pass

    return None

def parse_boolean(tok):
    if tok == "#t":
        return True
    elif tok == "#f":
        return False
    return None

def parse_symbol(tok):
    return strip(tok)


def token_gen(e, level=0):
    logger.debug("%02d token_gen: e=%s" % (level, e))
    tok = ""
    pos = 0
    while pos < len(e):
        c = e[pos]
        logging.debug(" %d %c: '%s'" % (pos, c, tok))
        if c == TOK_PAR_OPEN:
            logging.debug("TOK_PAR_OPEN")
            p = find_matching_paren(e, pos)
            yield TOK_PAR_OPEN

            logging.debug("recur {")
            for tok1 in token_gen(e[pos+1:p], level=level+1):
                yield tok1

            logging.debug("} recur")

            yield TOK_PAR_CLOSE

            pos = p + 1

            tok = ""
        elif c == TOK_PAR_CLOSE:
            raise LispError("Unmatched closing paren.")
        elif c  in " \n\r":
            logging.debug("WHITESPACE")
            if len(tok):
                yield tok
            tok = ""
        else:
            logging.debug("TOKEN")
            tok = tok + c

        pos = pos + 1

    if len(tok):
        yield tok


##
## Below are a few useful utility functions. These should come in handy when
## implementing `parse`. We don't want to spend the day implementing parenthesis
## counting, after all.
##

def next_token(e, pos):
    tok = ""
    if len(e) == 0:
        return (None, 0, "")

    for c in e[pos:]:
        if c in " \n\r":
            return (tok, pos, e[pos:])
        tok = tok + c
        pos = pos + 1

    return (None, pos, e)


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
