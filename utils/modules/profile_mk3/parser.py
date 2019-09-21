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

import re

from sverchok.utils.parsec import *
from sverchok.utils.logging import info, debug, warning
from sverchok.utils.modules.profile_mk3.interpreter import *

#########################################
# DSL parsing
#########################################

# Compare these definitions with BNF definition at the top of profile_mk3.py.

expr_regex = re.compile(r"({[^}]+})\s*", re.DOTALL)

def parse_expr(src):
    for string, rest in parse_regexp(expr_regex)(src):
        expr = Expression.from_string(string)
        if expr is not None:
            yield expr, rest

identifier_regexp = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

parse_semicolon = parse_word(";")

def parse_identifier(src):
    for (name, _), rest in sequence(parse_regexp(identifier_regexp), parse_whitespace)(src):
        yield name, rest

def parse_negated_variable(src):
    for (_, name, _), rest in sequence(parse_word("-"), parse_regexp(identifier_regexp), parse_whitespace)(src):
        yield NegatedVariable(name), rest

def parse_value(src):
    for smth, rest in one_of(parse_number, parse_identifier, parse_negated_variable, parse_expr)(src):
        if isinstance(smth, (int, float)):
            yield Const(smth), rest
        elif isinstance(smth, str):
            yield Variable(smth), rest
        else:
            yield smth, rest

def parse_pair(src):
    parser = sequence(parse_value, parse_word(","), parse_value)
    for (x, _, y), rest in parser(src):
        yield (x,y), rest

def parse_letter(absolute, relative):
    def parser(src):
        for smth, rest in one_of(parse_word(absolute), parse_word(relative))(src):
            is_abs = smth == absolute
            yield is_abs, rest
    return parser

def parse_MoveTo(src):
    parser = sequence(parse_letter("M", "m"), parse_pair, optional(parse_semicolon))
    for (is_abs, (x, y), _), rest in parser(src):
        yield MoveTo(is_abs, x, y), rest

def parse_LineTo(src):
    parser = sequence(
                parse_letter("L", "l"),
                many(parse_pair),
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon))
    for (is_abs, pairs, num_segments, z, _), rest in parser(src):
        yield LineTo(is_abs, pairs, num_segments, z is not None), rest

def parse_parameter(name):
    def parser(src):
        for (_, _, value), rest in sequence(parse_word(name), parse_word("="), parse_value)(src):
            yield value, rest
    return parser

def parse_CurveTo(src):

    def parse_segment(src):
        parser = sequence(parse_pair, parse_pair, parse_pair)
        for (control1, control2, knot2), rest in parser(src):
            yield CurveTo.Segment(control1, control2, knot2), rest

    parser = sequence(
                parse_letter("C", "c"),
                many(parse_segment),
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, segments, num_segments, z, _), rest in parser(src):
        yield CurveTo(is_abs, segments, num_segments, z is not None), rest

def parse_SmoothCurveTo(src):

    def parse_segment(src):
        parser = sequence(parse_pair, parse_pair)
        for (control2, knot2), rest in parser(src):
            yield SmoothCurveTo.Segment(control2, knot2), rest

    parser = sequence(
                parse_letter("S", "s"),
                many(parse_segment),
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, segments, num_segments, z, _), rest in parser(src):
        yield SmoothCurveTo(is_abs, segments, num_segments, z is not None), rest

def parse_QuadCurveTo(src):

    def parse_segment(src):
        parser = sequence(parse_pair, parse_pair)
        for (control, knot2), rest in parser(src):
            yield QuadraticCurveTo.Segment(control, knot2), rest

    parser = sequence(
                parse_letter("Q", "q"),
                many(parse_segment),
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, segments, num_segments, z, _), rest in parser(src):
        yield QuadraticCurveTo(is_abs, segments, num_segments, z is not None), rest

def parse_SmoothQuadCurveTo(src):

    def parse_segment(src):
        for knot2, rest in parse_pair(src):
            yield SmoothQuadraticCurveTo.Segment(knot2), rest

    parser = sequence(
                parse_letter("T", "t"),
                many(parse_segment),
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, knot2, num_segments, z, _), rest in parser(src):
        yield SmoothQuadraticCurveTo(is_abs, knot2, num_segments, z is not None), rest

def parse_ArcTo(src):
    parser = sequence(
                parse_letter("A", "a"),
                parse_pair,
                parse_value,
                parse_value,
                parse_value,
                parse_pair,
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, radii, rot, flag1, flag2, end, num_verts, z, _), rest in parser(src):
        yield ArcTo(is_abs, radii, rot, flag1, flag2, end, num_verts, z is not None), rest

def parse_HorLineTo(src):
    # NB: H/h command MUST end with semicolon, otherwise we will not be able to
    # understand where it ends, i.e. does the following letter begin a new statement
    # or is it just next X value denoted by variable.
    parser = sequence(parse_letter("H", "h"),
                many(parse_value, backtracking=True),
                optional(parse_parameter("n")),
                parse_semicolon)
    for (is_abs, xs, num_segments, _), rest in parser(src):
        yield HorizontalLineTo(is_abs, xs, num_segments), rest

def parse_VertLineTo(src):
    # NB: V/v command MUST end with semicolon, otherwise we will not be able to
    # understand where it ends, i.e. does the following letter begin a new statement
    # or is it just next X value denoted by variable.
    parser = sequence(parse_letter("V", "v"),
                many(parse_value, backtracking=True),
                optional(parse_parameter("n")),
                parse_semicolon)
    for (is_abs, ys, num_segments, _), rest in parser(src):
        yield VerticalLineTo(is_abs, ys, num_segments), rest

parse_CloseAll = parse_word("X", CloseAll())
parse_ClosePath = parse_word("x", ClosePath())

def parse_Default(src):
    parser = sequence(
                parse_word("default"),
                parse_identifier,
                parse_word("="),
                parse_value,
                optional(parse_semicolon)
            )
    for (_, name, _, value, _), rest in parser(src):
        yield Default(name, value), rest

def parse_Assign(src):
    parser = sequence(
                parse_word("let"),
                parse_identifier,
                parse_word("="),
                parse_value,
                optional(parse_semicolon)
            )
    for (_, name, _, value, _), rest in parser(src):
        yield Assign(name, value), rest

parse_statement = one_of(
                    parse_Default,
                    parse_Assign,
                    parse_MoveTo,
                    parse_LineTo,
                    parse_HorLineTo,
                    parse_VertLineTo,
                    parse_CurveTo,
                    parse_SmoothCurveTo,
                    parse_QuadCurveTo,
                    parse_SmoothQuadCurveTo,
                    parse_ArcTo,
                    parse_ClosePath,
                    parse_CloseAll
                )

parse_definition = many(parse_statement)

def parse_profile(src):
    # Strip comments
    # (hope noone uses # in expressions)
    cleaned = ""
    for line in src.split("\n"):
        comment_idx = line.find('#')
        if comment_idx != -1:
            line = line[:comment_idx]
        cleaned = cleaned + " " + line
    
    profile = parse(parse_definition, cleaned)
    debug(profile)
    return profile

