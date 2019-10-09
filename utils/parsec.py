# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
This module contains a very simplistic framework for parsing DSLs.
Such DSL is used, for example, in the Profile (mk3) node.

This framework implements the approach known as "combinatorial parsing",
see https://en.wikipedia.org/wiki/Parser_combinator for starters.

A parser is a function, that takes a string to be parsed, and
yields a pair: a parsed object and the rest of the string. It can
yield several pairs if the string can be parsed in several ways.

We say that parser *succeeds* or *applies** if it yields at least one
pair.

We say that parser *fails* if it does not yield anything.

If a call of parser("var = value") yields, for example, a pair
(Variable("var"), "= value"), we say that the parser *returned* a
Variable("var") object; it *consumed* the "var " string and *retained*
"= value" string to be parsed by subsequential parsers.

The common pattern

    parser = ...
    for value, rest in parser(src):
        if ...
            yield ..., rest

means: apply parser, then analyze returned value, then yield something
and the rest of the string.

A parser combinator is a function that takes one or several parsers,
and returns another parser. The returned parser is somehow combined
from the parsers provided. Parser combinator may, for example, apply
several parsers sequentionally, or try one parser and then try another,
or something like that.

This module provides minimalistic set of standard parsers and parser combinators.

It still has poor error detection/recovery. Maybe some day...

"""

import re
from itertools import chain

number_regex = re.compile(r"(-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(.*)", re.DOTALL)
string_regex = re.compile(r"('(?:[^\\']|\\['\\/bfnrt]|\\u[0-9a-fA-F]{4})*?')\s*(.*)", re.DOTALL)
whitespace_regex = re.compile(r"[ \n\r\t]*")

def return_(src):
    """
    Trivial parser, that parses an empty tuple and retains
    the input string untouched.
    """
    yield (), src

def sequence(*funcs):
    """
    Parser combinator, that applies several parsers in sequence.
    For example, if parser_a parses "A" and parser_b parses "B",
    then sequence(parser_a, parser_b) parses "AB".
    This corresponds to
        <ParserA> <ParserB>
    in BNF notation.
    """
    if len(funcs) == 0:
        return return_

    def parser(src):
        for arg1, src in funcs[0](src):
            for others, src in sequence(*funcs[1:])(src):
                yield (arg1,) + others, src

    return parser

def one_of(*funcs):
    """
    Parser combinator, that tries to apply one of several parsers.
    For example, if parser_foo parses "foo" and parser_bar parses "bar",
    then one_of(parser_foo, parser_bar) will parse either "foo" or "bar".
    This corresponds to
        <ParserA> | <ParserB>
    in BNF notation.
    """
    def parser(src):
        generators = [func(src) for func in funcs]
        for match in chain(*generators):
            yield match
            return
    return parser

def many(func, backtracking=False):
    """
    Parser combinator, that applies one parser as many times as it
    could be applied. For example, if parser_a parses "A", then
    many(parser_a) parses "A", "AA", "AAA" and so on.
    This corresponds to
        <Parser> *
    in BNF notation.
    If backtracking is set to False, then the parser will iterate
    as far as it can, even if consequential parsers will fail then.
    With backtracking set to True, the parser will be able to go back
    if it sees that some of consequencing parsers will fail.
    """
    def parser(src):
        for (value, values), rest in sequence(func, parser)(src):
            yield [value] + values, rest
            # Stop on first possible parsing variant?
            if not backtracking:
                return
        
        for value, rest in func(src):
            yield [value], rest
    return parser

def optional(func):
    """
    Parser combinator, that tries to apply specified parser, and
    returns None if it can not.
    This corresponds to
        <Parser> | ""
    in BNF notation.
    """
    def parser(src):
        met = False
        for value, rest in func(src):
            yield value, rest
            met = True
        if not met:
            yield None, src
    return parser

def parse_number(src):
    """
    Parse an integer or floating-point number.
    """
    match = number_regex.match(src)
    if match is not None:
        number, rest = match.groups()
        yield eval(number), rest

def parse_word(word, value=None):
    """
    Parse the specified word and return specified value.
    It skips any whitespace that follows the word.

    For example, parse_word("word")("word 123") parses
    "word" and retains "123" as the rest of string.
    """
    l = len(word)
    if value is None:
        value = word

    def result(src):
        if src.startswith(word):
            yield value, src[l:].lstrip()

    result.__name__ = "parse_%s" % word
    return result

def parse_regexp(regexp):
    if isinstance(regexp, str):
        regexp = re.compile(regexp)

    def parser(src):
        match = regexp.match(src)
        if match is not None:
            try:
                result = match.group(1)
            except IndexError:
                result = match.group(0)
            n = match.end()
            rest = src[n:]
            yield result, rest

    return parser

parse_whitespace = parse_regexp(whitespace_regex)

def parse_string(src):
    """
    Parse string literal in single quotes.
    """
    match = string_regex.match(src)
    if match is not None:
        string, rest = match.groups()
        yield string, rest

def parse(func, s):
    """
    Interface function: apply the parser to the string
    and return parser's return value.
    If the parser can not parse the string, or can parse
    it in more than one way - this function will raise an
    exception.
    Also it will raise an exception if something remained
    in the input string after applying the parser.
    """
    s = s.strip()
    match = list(func(s))
    if len(match) != 1:
        raise ValueError("invalid syntax: " + str(match))
    result, rest = match[0]
    if rest.strip():
        raise ValueError("parsed: {}\nleftover: {}".format(result, rest))
    return result

