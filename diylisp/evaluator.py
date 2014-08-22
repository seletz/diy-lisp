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
    assert is_list(ast)

    if len(ast) == 0:
        return []

    first = head(ast)
    rest  = tail(ast)

    if first == 'quote':
        assert_exp_length(ast, 2)
        return ast[1]

    elif first == "if":
        return eval_if(ast, env)

    elif first == 'atom':
        assert_exp_length(ast, 2)
        return is_atom(evaluate(ast[1], env))

    elif first == 'eq':
        return eval_eq(ast, env)

    elif first == 'define':
        return eval_define(ast, env)

    elif first == 'lambda':
        return eval_lambda(ast, env)

    elif is_closure(first):
        return eval_closure(ast, env)

    elif is_list(first):
        closure = evaluate(first, env)
        if not is_closure(closure):
            raise LispError("Can't call: %s" % unparse(first))

        return eval_closure([closure] + rest, env)

    elif is_symbol(first) and first in BUILTINS:
        return eval_builtin(ast, env)

    elif is_symbol(first):
        symbol = first
        value = env.lookup(symbol)
        if is_closure(value):
            return eval_closure([value] + rest, env)

        raise LispError("Can't call: %s" % unparse(value))
    else:
        raise LispError("not a function: %s" % unparse(first))

def eval_eq(ast, env):
    assert ast[0] == "eq"
    assert_exp_length(ast, 3)

    a = evaluate(ast[1], env)
    b = evaluate(ast[2], env)

    if not is_atom(a):
        return False

    if not is_atom(b):
        return False

    logger.debug("evaluate_list: EQ %r == %r => %r", a, b, a == b)
    return a == b


def eval_if(ast, env):
    assert ast[0] == "if"
    assert_exp_length(ast, 4)

    predicate = ast[1]
    consequence = ast[2]
    alternative = ast[3]
    if evaluate(predicate, env):
        return evaluate(consequence, env)
    else:
        return evaluate(alternative, env)

def eval_define(ast, env):
    assert ast[0] == "define"

    if len(ast) != 3:
        raise LispError("define: Wrong number of arguments")

    symbol = ast[1]
    if not is_symbol(symbol):
        raise LispError("define: non-symbol: %s", symbol)

    value = evaluate(ast[2], env)
    env.set(symbol, value)
    return value

def eval_builtin(ast, env):
    assert_exp_length(ast, 3)

    name = ast[0]
    assert is_symbol(name)
    assert name in BUILTINS

    a = evaluate(ast[1], env)
    b = evaluate(ast[2], env)

    if not is_integer(a):
        raise LispError("Builtin '%s': can only use integers: %r" % (name, a))
    if not is_integer(b):
        raise LispError("Builtin '%s': can only use integers: %r" % (name, b))

    return BUILTINS[name](a, b)

def eval_lambda(ast, env):
    assert ast[0] == "lambda"
    if len(ast) != 3:
        raise LispError("lambda: Wrong number of arguments")
    params = ast[1]
    body   = ast[2]

    if not is_list(params):
        raise LispError("lambda: params must be lists: %s" % unparse(params))

    return Closure(env, params, body)

def eval_closure(ast, env):
    closure = head(ast)
    rest    = tail(ast)
    assert is_closure(closure)
    logger.debug("eval_closure: %r", closure)
    if len(rest) != len(closure.params):
        raise LispError("wrong number of arguments, expected %d got %d" % (len(closure.params), len(rest)))

    values = map(lambda e: evaluate(e, env), rest)
    logger.debug("eval_closure: param values: %r", values)

    bindings = dict(zip(closure.params, values))
    new_env = closure.env.extend(bindings)

    return evaluate(closure.body, new_env)

def eval_atom(atom, env):
    assert is_atom(atom)

    if is_boolean(atom):
        return atom
    elif is_symbol(atom):
        symbol = atom
        return env.lookup(symbol)
    elif is_integer(atom):
        return atom
    else:
        raise LispError("Cannot evaluate atom: %s", unparse(atom))

def head(l):
    return l[0]

def tail(l):
    if len(l):
        return l[1:]
    else:
        return []
