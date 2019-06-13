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
from itertools import chain
import ast
from math import *
import os

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntProperty
from mathutils.geometry import interpolate_bezier
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.socket_data import SvNoDataError
from sverchok.data_structure import fullList, updateNode, dataCorrect, match_long_repeat
from sverchok.utils.parsec import *
from sverchok.utils.logging import info, debug, warning
from sverchok.utils.sv_curve_utils import Arc
from sverchok.utils.sv_update_utils import sv_get_local_path

'''
input like:

    M|m <2v coordinate>
    L|l <2v coordinate 1> <2v coordinate 2> <2v coordinate n> [z]
    C|c <2v control1> <2v control2> <2v knot2> <int num_segments> [z]
    S|s <2v control2> <2v knot2> <int num_segments> [z]
    A|a <2v rx,ry> <float rot> <int flag1> <int flag2> <2v x,y> <int num_verts> [z]
    H|h <x1> <x2> ... ;
    V|v <y1> <y2> ... ;
    X
    #
    -----
    <>  : mandatory field
    []  : optional field
    2v  : two point vector `a,b`
            - no space between ,
            - no backticks
            - a and b can be number literals or lowercase 1-character symbols for variables
    <int .. >
        : means the value will be cast as an int even if you input float
        : flags generally are 0 or 1.
    z   : is optional for closing a line
    X   : as a final command to close the edges (cyclic) [-1, 0]
        in addition, if the first and last vertex share coordinate space
        the last vertex is dropped and the cycle is made anyway.
    #   : single line comment prefix

    Each integer or floating value may be represented as
    
    * Integer or floating literal (usual python syntax, such as 5 or 7.5)
    * Variable name, such as a or b or variable_name
    * Negation sign and a variable name, such as `-a` or `-size`.
    * Expression enclosed in curly brackets, such as {a+1} or {sin(phi)}
    
    Statements may optionally be separated by semicolons (;).
    For some commands (namely: H/h, V/v) the trailing semicolon is *required*!

'''

"""
Our DSL has relatively simple BNF:

    <Profile> ::= <Statement> *
    <Statement> ::= <MoveTo> | <LineTo> | <CurveTo> | <SmoothLineTo>
                    | <ArcTo> | <HorLineTo> | <VertLineTo> | "X"

    <MoveTo> ::= ("M" | "m") <Value> "," <Value>
    <LineTo> ::= ...
    <CurveTo> ::= ...
    <SmoothCurveTo> ::= ...
    <ArcTo> ::= ...
    <HorLineTo> ::= ("H" | "h") <Value> * ";"
    <VertLineTo> ::= ("V" | "v") <Value> * ";"

    <Value> ::= "{" <Expression> "}" | <Variable> | <NegatedVariable> | <Const>
    <Expression> ::= Standard Python expression
    <Variable> ::= Python variable identifier
    <NegatedVariable> ::= "-" <Variable>
    <Const> ::= Python integer or floating-point literal

"""

##########################################
# Expression classes
##########################################

class Expression(object):
    def __init__(self, expr, string):
        self.expr = expr
        self.string = string

    safe_names = dict(sin=sin, cos=cos, pi=pi, sqrt=sqrt)

    def __repr__(self):
        return "Expr({})".format(self.string)

    @classmethod
    def from_string(cls, string):
        try:
            string = string[1:][:-1]
            expr = ast.parse(string, mode='eval')
            return Expression(expr, string)
        except Exception as e:
            print(e)
            print(string)
            return None

    def eval_(self, variables):
        env = dict()
        env.update(self.safe_names)
        env.update(variables)
        env["__builtins__"] = {}
        return eval(compile(self.expr, "<expression>", 'eval'), env)

    def get_variables(self):
        result = {node.id for node in ast.walk(self.expr) if isinstance(node, ast.Name)}
        return result.difference(self.safe_names.keys())

class Const(Expression):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_string(cls, string):
        try:
            return Const( float(string) )
        except ValueError:
            return None

    def __repr__(self):
        return "Const({})".format(self.value)

    def eval_(self, variables):
        return self.value

    def get_variables(self):
        return set()

class Variable(Expression):
    def __init__(self, name):
        self.name = name

    @classmethod
    def from_string(cls, string):
        return Variable(string)

    def __repr__(self):
        return "Variable({})".format(self.name)

    def eval_(self, variables):
        value = variables.get(self.name, None)
        if value is not None:
            return value
        else:
            raise SyntaxError("Unknown variable: " + self.name)

    def get_variables(self):
        return set([self.name])

# In general, this does not have very much sense:
# instead of -a one can write {-a}, then it will
# be parsed as Expression and will work fine.
# This is mostly implemented for compatibility
# with older Profile node syntax.
class NegatedVariable(Variable):
    @classmethod
    def from_string(cls, string):
        return NegatedVariable(string)

    def eval_(self, variables):
        value = variables.get(self.name, None)
        if value is not None:
            return -value
        else:
            raise SyntaxError("Unknown variable: " + self.name)

    def __repr__(self):
        return "NegatedVariable({})".format(self.name)

############################################
# Statement classes
# Classes for AST of our DSL
############################################

# These classes are responsible for interpretation of specific DSL statements.
# Each of these classes does the following:
# 
#  * Stores statement parameters (for example, MoveTo stores x and y).
#  * defines get_variables() method, which should return a set of all
#    variables used by all expressions in the statement.
#  * defines interpret() method, which should calculate all vertices and
#    edges according to statement parameters, and pass them to the interpreter.

class Statement(object):
    pass

class MoveTo(Statement):
    def __init__(self, is_abs, x, y):
        self.is_abs = is_abs
        self.x = x
        self.y = y

    def __repr__(self):
        letter = "M" if self.is_abs else "m"
        return "{} {} {}".format(letter, self.x, self.y)

    def get_variables(self):
        variables = set()
        variables.update(self.x.get_variables())
        variables.update(self.y.get_variables())
        return variables

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        pos = interpreter.calc_vertex(self.is_abs, self.x, self.y, variables)
        interpreter.position = pos
        interpreter.new_knot("M.#", *pos)
        interpreter.has_last_vertex = False

class LineTo(Statement):
    def __init__(self, is_abs, pairs, close):
        self.is_abs = is_abs
        self.pairs = pairs
        self.close = close

    def get_variables(self):
        variables = set()
        for x, y in self.pairs:
            variables.update(x.get_variables())
            variables.update(y.get_variables())
        return variables

    def __repr__(self):
        letter = "L" if self.is_abs else "l"
        return "{} {} {}".format(letter, self.pairs, self.close)
    
    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        for i, (x_expr, y_expr) in enumerate(self.pairs):
            v1 = interpreter.calc_vertex(self.is_abs, x_expr, y_expr, variables)
            interpreter.position = v1
            v1_index = interpreter.new_vertex(*v1)
            interpreter.new_edge(v0_index, v1_index)
            interpreter.new_knot("L#.{}".format(i), *v1)
            v0_index = v1_index

        if self.close:
            interpreter.new_edge(v1_index, interpreter.segment_start_index)

        interpreter.has_last_vertex = True

class HorizontalLineTo(Statement):
    def __init__(self, is_abs, xs):
        self.is_abs = is_abs
        self.xs = xs

    def get_variables(self):
        variables = set()
        for x in self.xs:
            variables.update(x.get_variables())
        return variables

    def __repr__(self):
        letter = "H" if self.is_abs else "h"
        return "{} {}".format(letter, self.xs)

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        for i, x_expr in enumerate(self.xs):
            x0,y0 = interpreter.position
            x = x_expr.eval_(variables)
            if not self.is_abs:
                x = x0 + x
            v1 = (x, y0)
            interpreter.position = v1
            v1_index = interpreter.new_vertex(*v1)
            interpreter.new_edge(v0_index, v1_index)
            interpreter.new_knot("H#.{}".format(i), *v1)
            v0_index = v1_index

        interpreter.has_last_vertex = True

class VerticalLineTo(Statement):
    def __init__(self, is_abs, ys):
        self.is_abs = is_abs
        self.ys = ys

    def get_variables(self):
        variables = set()
        for y in self.ys:
            variables.update(y.get_variables())
        return variables

    def __repr__(self):
        letter = "V" if self.is_abs else "v"
        return "{} {}".format(letter, self.ys)

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        for i, y_expr in enumerate(self.ys):
            x0,y0 = interpreter.position
            y = y_expr.eval_(variables)
            if not self.is_abs:
                y = y0 + y
            v1 = (x0, y)
            interpreter.position = v1
            v1_index = interpreter.new_vertex(*v1)
            interpreter.new_edge(v0_index, v1_index)
            interpreter.new_knot("V#.{}".format(i), *v1)
            v0_index = v1_index

        interpreter.has_last_vertex = True

class CurveTo(Statement):
    def __init__(self, is_abs, control1, control2, knot2, num_segments, close):
        self.is_abs = is_abs
        self.control1 = control1
        self.control2 = control2
        self.knot2 = knot2
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        variables.update(self.control1[0].get_variables())
        variables.update(self.control1[1].get_variables())
        variables.update(self.control2[0].get_variables())
        variables.update(self.control2[1].get_variables())
        variables.update(self.knot2[0].get_variables())
        variables.update(self.knot2[1].get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "C" if self.is_abs else "c"
        return "{} {} {} {} {} {}".format(letter, self.control1, self.control2, self.knot2, self.num_segments, self.close)

    def interpret(self, interpreter, variables):
        vec = lambda v: Vector((v[0], v[1], 0))

        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        knot1 = interpreter.position
        handle1 = interpreter.calc_vertex(self.is_abs, self.control1[0], self.control1[1], variables)

        # In Profile mk2, for "c" handle2 was calculated relative to handle1,
        # and knot2 was calculated relative to handle2.
        # But in SVG specification, 
        # >> ...  *At the end of the command*, the new current point becomes
        # >> the final (x,y) coordinate pair used in the polybézier.
        # This is also behaivour of browsers.

        #interpreter.position = handle1
        handle2 = interpreter.calc_vertex(self.is_abs, self.control2[0], self.control2[1], variables)
        #interpreter.position = handle2
        knot2 = interpreter.calc_vertex(self.is_abs, self.knot2[0], self.knot2[1], variables)
        interpreter.position = knot2

        if self.num_segments is not None:
            r = self.num_segments.eval_(variables)
        else:
            r = interpreter.dflt_num_verts

        points = interpolate_bezier(vec(knot1), vec(handle1), vec(handle2), vec(knot2), r)

        interpreter.new_knot("C#.h1", *handle1)
        interpreter.new_knot("C#.h2", *handle2)
        interpreter.new_knot("C#.k", *knot2)

        interpreter.prev_curve_knot = handle2

        for point in points[1:]:
            v1_index = interpreter.new_vertex(point.x, point.y)
            interpreter.new_edge(v0_index, v1_index)
            v0_index = v1_index

        if self.close:
            interpreter.new_edge(v1_index, interpreter.segment_start_index)

        interpreter.has_last_vertex = True

class ArcTo(Statement):
    def __init__(self, is_abs, radii, rot, flag1, flag2, end, num_verts, close):
        self.is_abs = is_abs
        self.radii = radii
        self.rot = rot
        self.flag1 = flag1
        self.flag2 = flag2
        self.end = end
        self.num_verts = num_verts
        self.close = close

    def get_variables(self):
        variables = set()
        variables.update(self.radii[0].get_variables())
        variables.update(self.radii[1].get_variables())
        variables.update(self.rot.get_variables())
        variables.update(self.flag1.get_variables())
        variables.update(self.flag2.get_variables())
        variables.update(self.end[0].get_variables())
        variables.update(self.end[1].get_variables())
        if self.num_verts:
            variables.update(self.num_verts.get_variables())
        return variables

    def __repr__(self):
        letter = "A" if self.is_abs else "a"
        return "{} {} {} {} {} {} {} {}".format(letter, self.radii, self.rot, self.flag1, self.flag2, self.end, self.num_verts, self.close)

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        start = complex(*v0)
        rad_x_expr, rad_y_expr = self.radii
        rad_x = rad_x_expr.eval_(variables)
        rad_y = rad_y_expr.eval_(variables)
        radius = complex(rad_x, rad_y)
        xaxis_rot = self.rot.eval_(variables)
        flag1 = self.flag1.eval_(variables)
        flag2 = self.flag2.eval_(variables)

        # numverts, requires -1 else it means segments (21 verts is 20 segments).
        if self.num_verts is not None:
            num_verts = self.num_verts.eval_(variables)
        else:
            num_verts = interpreter.dflt_num_verts
        num_verts -= 1

        end = interpreter.calc_vertex(self.is_abs, self.end[0], self.end[1], variables)
        end = complex(*end)

        arc = Arc(start, radius, xaxis_rot, flag1, flag2, end)

        theta = 1/num_verts
        for i in range(num_verts+1):
            v1 = x, y = arc.point(theta * i)
            v1_index = interpreter.new_vertex(x, y)
            interpreter.new_edge(v0_index, v1_index)
            v0_index = v1_index

        interpreter.position = v1
        interpreter.new_knot("A.#", *v1)
        if self.close:
            interpreter.new_edge(v1_index, interpreter.segment_start_index)

        interpreter.has_last_vertex = True

class SmoothCurveTo(Statement):
    def __init__(self, is_abs, control2, knot2, num_segments, close):
        self.is_abs = is_abs
        self.control2 = control2
        self.knot2 = knot2
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        variables.update(self.control2[0].get_variables())
        variables.update(self.control2[1].get_variables())
        variables.update(self.knot2[0].get_variables())
        variables.update(self.knot2[1].get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "S" if self.is_abs else "s"
        return "{} {} {} {} {}".format(letter, self.control2, self.knot2, self.num_segments, self.close)

    def interpret(self, interpreter, variables):
        vec = lambda v: Vector((v[0], v[1], 0))

        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        knot1 = interpreter.position

        if interpreter.prev_curve_knot is None:
            # If there is no previous command or if the previous command was
            # not an C, c, S or s, assume the first control point is coincident
            # with the current point.
            handle1 = knot1
        else:
            # The first control point is assumed to be the reflection of the
            # second control point on the previous command relative to the
            # current point. 
            prev_knot_x, prev_knot_y = interpreter.prev_curve_knot
            x0, y0 = knot1
            dx, dy = x0 - prev_knot_x, y0 - prev_knot_y
            handle1 = x0 + dx, y0 + dy

        # I assume that handle2 should be relative to knot1, not to handle1.
        # interpreter.position = handle1
        handle2 = interpreter.calc_vertex(self.is_abs, self.control2[0], self.control2[1], variables)
        # interpreter.position = handle2
        knot2 = interpreter.calc_vertex(self.is_abs, self.knot2[0], self.knot2[1], variables)
        interpreter.position = knot2

        if self.num_segments is not None:
            r = self.num_segments.eval_(variables)
        else:
            r = interpreter.dflt_num_verts

        points = interpolate_bezier(vec(knot1), vec(handle1), vec(handle2), vec(knot2), r)

        interpreter.new_knot("S#.h1", *handle1)
        interpreter.new_knot("S#.h2", *handle2)
        interpreter.new_knot("S#.k", *knot2)

        interpreter.prev_curve_knot = handle2

        for point in points[1:]:
            v1_index = interpreter.new_vertex(point.x, point.y)
            interpreter.new_edge(v0_index, v1_index)
            v0_index = v1_index

        if self.close:
            interpreter.new_edge(v1_index, interpreter.segment_start_index)

        interpreter.has_last_vertex = True

class Close(Statement):
    def __init__(self):
        pass

    def __repr__(self):
        return "X"

    def get_variables(self):
        return set()

    def interpret(self, interpreter, variables):
        if not interpreter.has_last_vertex:
            info("X statement: no current point, do nothing")
            return
        v1_index = interpreter.get_last_vertex()
        interpreter.new_edge(v1_index, 0)
        interpreter.closed = True

#########################################
# DSL parsing
#########################################

# Compare these definitions with BNF definition at the top

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
                optional(parse_word("z")),
                optional(parse_semicolon))
    for (is_abs, pairs, z, _), rest in parser(src):
        yield LineTo(is_abs, pairs, z is not None), rest

def parse_parameter(name):
    def parser(src):
        for (_, _, value), rest in sequence(parse_word(name), parse_word("="), parse_value)(src):
            yield value, rest
    return parser

def parse_CurveTo(src):
    parser = sequence(
                parse_letter("C", "c"),
                parse_pair,
                parse_pair,
                parse_pair,
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, control1, control2, knot2, num_segments, z, _), rest in parser(src):
        yield CurveTo(is_abs, control1, control2, knot2, num_segments, z is not None), rest

def parse_SmoothCurveTo(src):
    parser = sequence(
                parse_letter("S", "s"),
                parse_pair,
                parse_pair,
                optional(parse_parameter("n")),
                optional(parse_word("z")),
                optional(parse_semicolon)
            )
    for (is_abs, control2, knot2, num_segments, z, _), rest in parser(src):
        yield SmoothCurveTo(is_abs, control2, knot2, num_segments, z is not None), rest

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
    parser = sequence(parse_letter("H", "h"), many(parse_value), parse_semicolon)
    for (is_abs, xs, _), rest in parser(src):
        yield HorizontalLineTo(is_abs, xs), rest

def parse_VertLineTo(src):
    # NB: V/v command MUST end with semicolon, otherwise we will not be able to
    # understand where it ends, i.e. does the following letter begin a new statement
    # or is it just next X value denoted by variable.
    parser = sequence(parse_letter("V", "v"), many(parse_value), parse_semicolon)
    for (is_abs, ys, _), rest in parser(src):
        yield VerticalLineTo(is_abs, ys), rest

parse_Close = parse_word("X", Close())

parse_statement = one_of(
                    parse_MoveTo,
                    parse_LineTo,
                    parse_HorLineTo,
                    parse_VertLineTo,
                    parse_CurveTo,
                    parse_SmoothCurveTo,
                    parse_ArcTo,
                    parse_Close)

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
    info(profile)
    return profile

#################################
# DSL Interpreter
#################################

class Interpreter(object):
    def __init__(self, node):
        self.position = (0, 0)
        self.next_vertex_index = 0
        self.segment_start_index = 0
        self.segment_number = 0
        self.has_last_vertex = False
        self.closed = False
        self.prev_curve_knot = None
        self.vertices = []
        self.edges = []
        self.knots = []
        self.knotnames = []
        self.dflt_num_verts = node.curve_points_count

    def assert_not_closed(self):
        if self.closed:
            raise Exception("Path was already closed, will not process any further directives!")

    def relative(self, x, y):
        x0, y0 = self.position
        return x0+x, y0+y

    def calc_vertex(self, is_abs, x_expr, y_expr, variables):
        x = x_expr.eval_(variables)
        y = y_expr.eval_(variables)
        if is_abs:
            return x,y
        else:
            return self.relative(x,y)

    def new_vertex(self, x, y):
        index = self.next_vertex_index
        self.vertices.append((x, y))
        self.next_vertex_index += 1
        return index

    def new_edge(self, v1, v2):
        self.edges.append((v1, v2))

    def new_knot(self, name, x, y):
        self.knots.append((x, y))
        name = name.replace("#", str(self.segment_number))
        self.knotnames.append(name)

    def start_new_segment(self):
        self.segment_start_index = self.next_vertex_index
        self.segment_number += 1

    def get_last_vertex(self):
        return self.next_vertex_index - 1

    def interpret(self, profile, variables):
        if not profile:
            return [], []
        for statement in profile:
            statement.interpret(self, variables)

#################################
# "From Selection" Operator
#################################

# Basically copy-pasted from mk2
# To understand how it works will take weeks :/

class SvPrifilizerMk3(bpy.types.Operator):
    """SvPrifilizer"""
    bl_idname = "node.sverchok_profilizer_mk3"
    bl_label = "SvPrifilizer"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename = StringProperty(name='nodename')
    treename = StringProperty(name='treename')
    knotselected = BoolProperty(description='if selected knots than use extended parsing in PN', default=False)
    x = BoolProperty(default=True)
    y = BoolProperty(default=True)


    def stringadd(self, x,selected=False):
        precision = bpy.data.node_groups[self.treename].nodes[self.nodename].precision
        if selected:
            if self.x: letterx = '+a'
            else: letterx = ''
            if self.y: lettery = '+a'
            else: lettery = ''
            a = '{'+str(round(x[0], precision))+letterx+'}' + ',' + '{'+str(round(x[1], precision))+lettery+'}' + ' '
            self.knotselected = True
        else:
            a = str(round(x[0], precision)) + ',' + str(round(x[1], precision)) + ' '
        return a
    
    def curve_points_count(self):
        count = bpy.data.node_groups[self.treename].nodes[self.nodename].curve_points_count
        return str(count)

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        precision = node.precision
        subdivisions = node.curve_points_count
        if not bpy.context.selected_objects:
            warning('Pofiler: Select curve!')
            self.report({'INFO'}, 'Select CURVE first')
            return {'CANCELLED'}
        if not bpy.context.selected_objects[0].type == 'CURVE':
            warning('Pofiler: NOT a curve selected')
            self.report({'INFO'}, 'It is not a curve selected for profiler')
            return {'CANCELLED'}

        objs = bpy.context.selected_objects
        names = str([o.name for o in objs])[1:-2]

        # test for POLY or NURBS curve types, these are not yet supported
        spline_type = objs[0].data.splines[0].type
        if spline_type in {'POLY', 'NURBS'}:
            msg = 'Pofiler: does not support {0} curve type yet'.format(spline_type)
            warning(msg)
            self.report({'INFO'}, msg)
            return {'CANCELLED'}

        # collect paths
        op = []
        clos = []
        for obj in objs:
            for spl in obj.data.splines:
                op.append(spl.bezier_points)
                clos.append(spl.use_cyclic_u)

        # define path to text
        values = '# Here is autogenerated values, \n# Please, rename text to avoid data loose.\n'
        values += '# Objects are: \n# %a' % (names)+'.\n'
        values += '# Object origin should be at 0,0,0. \n'
        values += '# Property panel has precision %a \n# and curve subdivision %s.\n\n' % (precision,subdivisions)
        # also future output for viewer indices
        out_points = []
        out_names = []
        ss = 0
        for ob_points, clo in zip(op,clos):
            values += '# Spline %a\n' % (ss)
            ss += 1
            # handles preperation
            curves_left  = [i.handle_left_type for i in ob_points]
            curves_right = ['v']+[i.handle_right_type for i in ob_points][:-1]
            # first collect C,L values to compile them later per point
            types = ['FREE','ALIGNED','AUTO']
            curves = ['C ' if x in types or c in types else 'L ' for x,c in zip(curves_left,curves_right)]
            # line for if curve was before line or not
            line = False
            curve = False

            for i,c in zip(range(len(ob_points)),curves):
                co = ob_points[i].co
                if not i:
                    # initial value
                    values += '\n'
                    values += 'M '
                    co = ob_points[0].co[:]
                    values += self.stringadd(co,ob_points[0].select_control_point)
                    values += '\n'
                    out_points.append(co)
                    out_names.append(['M.0'])
                    # pass if first 'M' that was used already upper
                    continue

                elif c == 'C ':
                    values += '\n'
                    values += '#C.'+str(i)+'\n'
                    values += c
                    hr = ob_points[i-1].handle_right[:]
                    hl = ob_points[i].handle_left[:]
                    # hr[0]hr[1]hl[0]hl[1]co[0]co[1] 20 0
                    values += self.stringadd(hr,ob_points[i-1].select_right_handle)
                    values += self.stringadd(hl,ob_points[i].select_left_handle)
                    values += self.stringadd(co,ob_points[i].select_control_point)
                    values += self.curve_points_count()
                    if curve:
                        values += '\n'
                    out_points.append(hr[:])
                    out_points.append(hl[:])
                    out_points.append(co[:])
                    #namecur = ['C.'+str(i)]
                    out_names.extend([['C.'+str(i)+'h1'],['C.'+str(i)+'h2'],['C.'+str(i)+'k']])
                    line = False
                    curve = True

                elif c == 'L ' and not line:
                    if curve:
                        values += '\n'
                    values += '#L.'+str(i)+'...'+'\n'
                    values += c
                    values += self.stringadd(co,ob_points[i].select_control_point)
                    out_points.append(co[:])
                    out_names.append(['L.'+str(i)])
                    line = True
                    curve = False

                elif c == 'L ' and line:
                    values += self.stringadd(co,ob_points[i].select_control_point)
                    out_points.append(co[:])
                    out_names.append(['L.'+str(i)])

            if clo:
                if ob_points[0].handle_left_type in types or ob_points[-1].handle_right_type in types:
                    line = False
                    values += '\n'
                    values += '#C.'+str(i+1)+'\n'
                    values += 'C '
                    hr = ob_points[-1].handle_right[:]
                    hl = ob_points[0].handle_left[:]
                    # hr[0]hr[1]hl[0]hl[1]co[0]co[1] 20 0
                    values += self.stringadd(hr,ob_points[-1].select_right_handle)
                    values += self.stringadd(hl,ob_points[0].select_left_handle)
                    values += self.stringadd(ob_points[0].co,ob_points[0].select_control_point)
                    values += self.curve_points_count()
                    values += ' 0 '
                    values += '\n'
                    out_points.append(hr[:])
                    out_points.append(hl[:])
                    out_names.extend([['C.'+str(i+1)+'h1'],['C.'+str(i+1)+'h2']])
                    # preserving overlapping
                    #out_points.append(ob_points[0].co[:])
                    #out_names.append(['C'])
                if not line:
                    # hacky way till be fixed x for curves not only for lines
                    values += '# hacky way till be fixed x\n# for curves not only for lines'
                    values += '\nL ' + self.stringadd(ob_points[0].co,ob_points[0].select_control_point)
                    values += '\nx \n\n'
                else:
                    values += '\nx \n\n'

        if self.knotselected:
            values += '# expression (#+a) added because \n# you selected knots in curve'
        self.write_values(self.nodename, values)
        #print(values)
        node.filename = self.nodename
        #print([out_points], [out_names])
        # sharing data to node:
        return{'FINISHED'}

    def write_values(self,text,values):
        texts = bpy.data.texts.items()
        exists = False
        for t in texts:
            if bpy.data.texts[t[0]].name == text:
                exists = True
                break

        if not exists:
            bpy.data.texts.new(text)
        bpy.data.texts[text].clear()
        bpy.data.texts[text].write(values)


#################################
# Example Files Import
#################################

sv_path = os.path.dirname(sv_get_local_path()[0])
profile_template_path = os.path.join(sv_path, 'profile_examples')

class SvProfileImportMenu(bpy.types.Menu):
    bl_label = "Profile templates"
    bl_idname = "SvProfileImportMenu"

    def draw(self, context):
        if context.active_node:
            node = context.active_node
            self.path_menu([profile_template_path], "node.sv_profile_import_example")

class SvProfileImportOperator(bpy.types.Operator):

    bl_idname = "node.sv_profile_import_example"
    bl_label = "Profile mk3 load"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    filepath = bpy.props.StringProperty()

    def execute(self, context):
        txt = bpy.data.texts.load(self.filepath)
        context.node.filename = os.path.basename(txt.name)
        updateNode(context.node, context)
        return {'FINISHED'}

#################################
# Node class
#################################

class SvProfileNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: svg-like 2d profiles
    Tooltip: Generate multiple parameteric 2d profiles using SVG like syntax

    SvProfileNode generates one or more profiles / elevation segments using;
    assignments, variables, and a string descriptor similar to SVG.

    This node expects simple input, or vectorized input.
    - sockets with no input are automatically 0, not None
    - The longest input array will be used to extend the shorter ones, using last value repeat.
    '''

    bl_idname = 'SvProfileNodeMK3'
    bl_label = 'Profile Parametric Mk3'
    bl_icon = 'SYNTAX_ON'

    axis_options = [("X", "X", "", 0), ("Y", "Y", "", 1), ("Z", "Z", "", 2)]

    selected_axis = EnumProperty(
        items=axis_options, update=updateNode, name="Type of axis",
        description="offers basic axis output vectors X|Y|Z", default="Z")

    def on_update(self, context):
        self.adjust_sockets()
        updateNode(self, context)

    filename = StringProperty(default="", update=on_update)

    x = BoolProperty(default=True)
    y = BoolProperty(default=True)

    precision = IntProperty(
        name="Precision", min=0, max=10, default=8, update=updateNode,
        description="decimal precision of coordinates when generating profile from selection")

    curve_points_count = IntProperty(
        name="Curve points count", min=1, max=100, default=20, update=updateNode,
        description="Default number of points on curve segment")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'selected_axis', expand=True)
        layout.prop_search(self, 'filename', bpy.data, 'texts', text='', icon='TEXT')

        col = layout.column(align=True)
        row = col.row()
        do_text = row.operator('node.sverchok_profilizer_mk3', text='from selection')
        do_text.nodename = self.name
        do_text.treename = self.id_data.name
        do_text.x = self.x
        do_text.y = self.y

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

        layout.label("Profile Generator settings")
        layout.prop(self, "precision")
        layout.prop(self, "curve_points_count")
        row = layout.row(align=True)
        row.prop(self, "x",text='x-affect', expand=True)
        row.prop(self, "y",text='y-affect', expand=True)

        layout.label("Import Examples")
        layout.menu(SvProfileImportMenu.bl_idname)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "a")

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('VerticesSocket', "Knots")
        self.outputs.new('StringsSocket', "KnotNames")

    def load_profile(self):
        if not self.filename:
            return None
        internal_file = bpy.data.texts[self.filename]
        f = internal_file.as_string()
        profile = parse_profile(f)
        return profile

    def get_variables(self):
        variables = set()
        profile = self.load_profile()
        if not profile:
            return variables

        for statement in profile:
            vs = statement.get_variables()
            variables.update(vs)

        return list(sorted(list(variables)))

    def adjust_sockets(self):
        variables = self.get_variables()
        #self.debug("adjust_sockets:" + str(variables))
        #self.debug("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if key not in variables:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('StringsSocket', v)

    def update(self):
        '''
        update analyzes the state of the node and returns if the criteria to start processing
        are not met.
        '''

        # keeping the file internal for now.
        if not (self.filename in bpy.data.texts):
            return

        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        result = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                result[var] = self.inputs[var].sv_get()[0]
        return result
    
    def extend_out_verts(self, verts):
        if self.selected_axis == 'X':
            extend = lambda v: (0, v[0], v[1])
        elif self.selected_axis == 'Y':
            extend = lambda v: (v[0], 0, v[1])
        else:
            extend = lambda v: (v[0], v[1], 0)
        return list(map(extend, verts))

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        var_names = self.get_variables()
        inputs = self.get_input()

        result_vertices = []
        result_edges = []
        result_knots = []
        result_names = []

        profile = self.load_profile()

        if var_names:
            try:
                input_values = [inputs[name] for name in var_names]
            except KeyError as e:
                name = e.args[0]
                if name in self.inputs:
                    raise SvNoDataError(self.inputs[name])
                else:
                    self.adjust_sockets()
                    raise SvNoDataError(self.inputs[name])
            parameters = match_long_repeat(input_values)
        else:
            parameters = [[[]]]

        for values in zip(*parameters):
            variables = dict(zip(var_names, values))
            interpreter = Interpreter(self)
            interpreter.interpret(profile, variables)
            verts = self.extend_out_verts(interpreter.vertices)
            result_vertices.append(verts)
            result_edges.append(interpreter.edges)
            knots = self.extend_out_verts(interpreter.knots)
            result_knots.append(knots)
            result_names.append([[name] for name in interpreter.knotnames])

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Knots'].sv_set(result_knots)
        self.outputs['KnotNames'].sv_set(result_names)

classes = [
        SvProfileImportMenu,
        SvProfileImportOperator,
        SvPrifilizerMk3,
        SvProfileNodeMK3
    ]

def register():
    for name in classes:
        bpy.utils.register_class(name)

def unregister():
    for name in reversed(classes):
        bpy.utils.unregister_class(name)

