# -*- coding: utf-8 -*-
import logging

from .types import Environment, LispError, Closure
from .ast import is_boolean, is_atom, is_symbol, is_list, is_closure, is_integer
from .asserts import assert_exp_length, assert_valid_definition, assert_boolean
from .parser import unparse

"""
This is the Evaluator module. The `evaluate` function below is the heart
of your language, and the focus for most of parts 2 through 6.

A score of useful functions is provided for you, as per the above imports, 
making your work a bit easier. (We're supposed to get through this thing 
in a day, after all.)
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import operator

BUILTINS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.div,
    "mod": operator.mod,
    ">": operator.gt,
    "<": operator.lt
}


def evaluate(ast, env):
    """Evaluate an Abstract Syntax Tree in the specified environment."""
    logger.debug("evaluate: %r in %r", ast, env)
    if is_atom(ast):
        return eval_atom(ast, env)
    if is_list(ast):
        return eval_list(ast, env)

def eval_list(ast, env):
    logger.debug("evaluate_list: %r in %r", ast, env)
    car = head(ast)
    if car == 'quote':
        assert_exp_length(ast, 2)
        return ast[1]

    elif car == 'atom':
        assert_exp_length(ast, 2)
        return is_atom(evaluate(ast[1], env))

    elif car == 'eq':
        assert_exp_length(ast, 3)

        a = evaluate(ast[1], env)
        b = evaluate(ast[2], env)

        if not is_atom(a):
            return False

        if not is_atom(b):
            return False

        logger.debug("evaluate_list: EQ %r == %r => %r", a, b, a == b)
        return a == b

    elif car in BUILTINS:
        assert_exp_length(ast, 3)
        a = evaluate(ast[1], env)
        b = evaluate(ast[2], env)

        if not is_integer(a):
            raise LispError("Builtin '%s': can only use integers: %r", a)
        if not is_integer(b):
            raise LispError("Builtin '%s': can only use integers: %r", b)

        return BUILTINS[car](a, b)





def eval_atom(atom, env):
    assert is_atom(atom)

    if is_boolean(atom):
        return atom
    elif is_symbol(atom):
        return atom
    elif is_integer(atom):
        return atom

##

def head(l):
    return l[0]

def tail(l):
    return l[1:]
