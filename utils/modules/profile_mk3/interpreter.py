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

import ast
from math import *

from mathutils.geometry import interpolate_bezier
from mathutils import Vector, Matrix

from sverchok.utils.logging import info, debug, warning
from sverchok.utils.geom import interpolate_quadratic_bezier
from sverchok.utils.sv_curve_utils import Arc
from sverchok.utils.curve import SvCircle, SvLine, SvBezierCurve, SvCubicBezierCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve

def make_functions_dict(*functions):
    return dict([(function.__name__, function) for function in functions])

# Functions
safe_names = make_functions_dict(
        # From math module
        acos, acosh, asin, asinh, atan, atan2,
        atanh, ceil, copysign, cos, cosh, degrees,
        erf, erfc, exp, expm1, fabs, factorial, floor,
        fmod, frexp, fsum, gamma, hypot, isfinite, isinf,
        isnan, ldexp, lgamma, log, log10, log1p, log2, modf,
        pow, radians, sin, sinh, sqrt, tan, tanh, trunc,
        # Additional functions
        abs,
        # From mathutlis module
        Vector, Matrix,
        # Python type conversions
        tuple, list, str
    )
# Constants
safe_names['e'] = e
safe_names['pi'] = pi

##########################################
# Expression classes
##########################################

class Expression(object):
    def __init__(self, expr, string):
        self.expr = expr
        self.string = string

    def __repr__(self):
        return "Expr({})".format(self.string)

    def __eq__(self, other):
        # Proper comparasion of ast.Expression would be too complex to implement
        # (it is not implemented in the ast module).
        return isinstance(other, Expression) and self.string == other.string

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
        env.update(safe_names)
        env.update(variables)
        env["__builtins__"] = {}
        return eval(compile(self.expr, "<expression>", 'eval'), env)

    def get_variables(self):
        result = {node.id for node in ast.walk(self.expr) if isinstance(node, ast.Name)}
        return result.difference(safe_names.keys())

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

    def __eq__(self, other):
        return isinstance(other,Const) and self.value == other.value

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

    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name

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

    def __eq__(self, other):
        return isinstance(other, NegatedVariable) and self.name == other.name

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
    
    def get_variables(self):
        return set()

    def get_hidden_inputs(self):
        return set()

    def get_optional_inputs(self):
        return set()

    def _interpolate(self, v0, v1, num_segments):
        if num_segments is None or num_segments <= 1:
            return [v0, v1]
        dx_total, dy_total = v1[0] - v0[0], v1[1] - v0[1]
        dx, dy = dx_total / float(num_segments), dy_total / float(num_segments)
        x, y = v0
        dt = 1.0 / float(num_segments)
        result = []
        t = 0
        for i in range(round(num_segments)):
            result.append((x,y))
            x = x + dx
            y = y + dy
        result.append(v1)
        return result

class MoveTo(Statement):
    def __init__(self, is_abs, x, y):
        self.is_abs = is_abs
        self.x = x
        self.y = y

    def __repr__(self):
        letter = "M" if self.is_abs else "m"
        return "{} {} {}".format(letter, self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, MoveTo) and \
                self.is_abs == other.is_abs and \
                self.x == other.x and \
                self.y == other.y

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
    def __init__(self, is_abs, pairs, num_segments, close):
        self.is_abs = is_abs
        self.pairs = pairs
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        for x, y in self.pairs:
            variables.update(x.get_variables())
            variables.update(y.get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "L" if self.is_abs else "l"
        return "{} {} n={} {}".format(letter, self.pairs, self.num_segments, self.close)
    
    def __eq__(self, other):
        return isinstance(other, LineTo) and \
                self.is_abs == other.is_abs and \
                self.pairs == other.pairs and \
                self.num_segments == other.num_segments and \
                self.close == other.close

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        v0 = interpreter.position
        if interpreter.has_last_vertex:
            prev_index = interpreter.get_last_vertex()
        else:
            prev_index = interpreter.new_vertex(*v0)

        if self.num_segments is not None:
            num_segments = interpreter.eval_(self.num_segments, variables)
        else:
            num_segments = None

        for i, (x_expr, y_expr) in enumerate(self.pairs):
            v1 = interpreter.calc_vertex(self.is_abs, x_expr, y_expr, variables)
            interpreter.position = v1
            for vertex in self._interpolate(v0, v1, num_segments)[1:]:
                v_index = interpreter.new_vertex(*vertex)
                interpreter.new_edge(prev_index, v_index)
                prev_index = v_index
            interpreter.new_line_segment(v0, v1)
            v0 = v1
            interpreter.new_knot("L#.{}".format(i), *v1)

        if self.close:
            interpreter.close_segment(v_index)

        interpreter.has_last_vertex = True

class HorizontalLineTo(Statement):
    def __init__(self, is_abs, xs, num_segments):
        self.is_abs = is_abs
        self.xs = xs
        self.num_segments = num_segments

    def get_variables(self):
        variables = set()
        for x in self.xs:
            variables.update(x.get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "H" if self.is_abs else "h"
        return "{} {} n={};".format(letter, self.xs, self.num_segments)

    def __eq__(self, other):
        return isinstance(other, HorizontalLineTo) and \
                self.is_abs == other.is_abs and \
                self.num_segments == other.num_segments and \
                self.xs == other.xs

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        v0 = interpreter.position
        if interpreter.has_last_vertex:
            prev_index = interpreter.get_last_vertex()
        else:
            prev_index = interpreter.new_vertex(*v0)

        if self.num_segments is not None:
            num_segments = interpreter.eval_(self.num_segments, variables)
        else:
            num_segments = None

        for i, x_expr in enumerate(self.xs):
            x0,y0 = interpreter.position
            x = interpreter.eval_(x_expr, variables)
            if not self.is_abs:
                x = x0 + x
            v1 = (x, y0)
            interpreter.position = v1
            verts = self._interpolate(v0, v1, num_segments)
            #debug("V0 %s, v1 %s, N %s => %s", v0, v1, num_segments, verts)
            for vertex in verts[1:]:
                v_index = interpreter.new_vertex(*vertex)
                interpreter.new_edge(prev_index, v_index)
                prev_index = v_index
            interpreter.new_line_segment(v0, v1)
            v0 = v1
            interpreter.new_knot("H#.{}".format(i), *v1)

        interpreter.has_last_vertex = True

class VerticalLineTo(Statement):
    def __init__(self, is_abs, ys, num_segments):
        self.is_abs = is_abs
        self.ys = ys
        self.num_segments = num_segments

    def get_variables(self):
        variables = set()
        for y in self.ys:
            variables.update(y.get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "V" if self.is_abs else "v"
        return "{} {} n={};".format(letter, self.ys, self.num_segments)

    def __eq__(self, other):
        return isinstance(other, VerticalLineTo) and \
                self.is_abs == other.is_abs and \
                self.num_segments == other.num_segments and \
                self.ys == other.ys

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        interpreter.start_new_segment()
        v0 = interpreter.position
        if interpreter.has_last_vertex:
            prev_index = interpreter.get_last_vertex()
        else:
            prev_index = interpreter.new_vertex(*v0)

        if self.num_segments is not None:
            num_segments = interpreter.eval_(self.num_segments, variables)
        else:
            num_segments = None

        for i, y_expr in enumerate(self.ys):
            x0,y0 = interpreter.position
            y = interpreter.eval_(y_expr, variables)
            if not self.is_abs:
                y = y0 + y
            v1 = (x0, y)
            interpreter.position = v1
            for vertex in self._interpolate(v0, v1, num_segments)[1:]:
                v_index = interpreter.new_vertex(*vertex)
                interpreter.new_edge(prev_index, v_index)
                prev_index = v_index
            interpreter.new_line_segment(v0, v1)
            v0 = v1
            interpreter.new_knot("V#.{}".format(i), *v1)

        interpreter.has_last_vertex = True

class CurveTo(Statement):
    class Segment(object):
        def __init__(self, control1, control2, knot2):
            self.control1 = control1
            self.control2 = control2
            self.knot2 = knot2

        def __repr__(self):
            return "{} {} {}".format(self.control1, self.control2, self.knot2)

        def __eq__(self, other):
            return self.control1 == other.control1 and \
                    self.control2 == other.control2 and \
                    self.knot2 == other.knot2

    def __init__(self, is_abs, segments, num_segments, close):
        self.is_abs = is_abs
        self.segments = segments
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        for segment in self.segments:
            variables.update(segment.control1[0].get_variables())
            variables.update(segment.control1[1].get_variables())
            variables.update(segment.control2[0].get_variables())
            variables.update(segment.control2[1].get_variables())
            variables.update(segment.knot2[0].get_variables())
            variables.update(segment.knot2[1].get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "C" if self.is_abs else "c"
        segments = " ".join(str(segment) for segment in self.segments)
        return "{} {} n={} {}".format(letter, segments, self.num_segments, self.close)

    def __eq__(self, other):
        return isinstance(other, CurveTo) and \
                self.is_abs == other.is_abs and \
                self.segments == other.segments and \
                self.num_segments == other.num_segments and \
                self.close == other.close

    def interpret(self, interpreter, variables):
        vec = lambda v: Vector((v[0], v[1], 0))

        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        knot1 = None
        for i, segment in enumerate(self.segments):
            # For first segment, knot1 is initial pen position;
            # for the following, knot1 is knot2 of previous segment.
            if knot1 is None:
                knot1 = interpreter.position
            else:
                knot1 = knot2

            handle1 = interpreter.calc_vertex(self.is_abs, segment.control1[0], segment.control1[1], variables)

            # In Profile mk2, for "c" handle2 was calculated relative to handle1,
            # and knot2 was calculated relative to handle2.
            # But in SVG specification, 
            # >> ...  *At the end of the command*, the new current point becomes
            # >> the final (x,y) coordinate pair used in the polybézier.
            # This is also behaivour of browsers.

            #interpreter.position = handle1
            handle2 = interpreter.calc_vertex(self.is_abs, segment.control2[0], segment.control2[1], variables)
            #interpreter.position = handle2
            knot2 = interpreter.calc_vertex(self.is_abs, segment.knot2[0], segment.knot2[1], variables)
            # Judging by the behaivour of Inkscape and Firefox, by "end of command"
            # SVG spec means "end of segment".
            interpreter.position = knot2

            if self.num_segments is not None:
                r = interpreter.eval_(self.num_segments, variables)
            else:
                r = interpreter.dflt_num_verts

            curve = SvCubicBezierCurve(vec(knot1), vec(handle1), vec(handle2), vec(knot2))
            interpreter.new_curve(curve, self)

            points = interpolate_bezier(vec(knot1), vec(handle1), vec(handle2), vec(knot2), r)

            interpreter.new_knot("C#.{}.h1".format(i), *handle1)
            interpreter.new_knot("C#.{}.h2".format(i), *handle2)
            interpreter.new_knot("C#.{}.k".format(i), *knot2)

            interpreter.prev_bezier_knot = handle2

            for point in points[1:]:
                v1_index = interpreter.new_vertex(point.x, point.y)
                interpreter.new_edge(v0_index, v1_index)
                v0_index = v1_index

        if self.close:
            interpreter.close_segment(v1_index)

        interpreter.has_last_vertex = True

class SmoothCurveTo(Statement):
    class Segment(object):
        def __init__(self, control2, knot2):
            self.control2 = control2
            self.knot2 = knot2

        def __repr__(self):
            return "{} {}".format(self.control2, self.knot2)

        def __eq__(self, other):
            return self.control2 == other.control2 and \
                    self.knot2 == other.knot2

    def __init__(self, is_abs, segments, num_segments, close):
        self.is_abs = is_abs
        self.segments = segments
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        for segment in self.segments:
            variables.update(segment.control2[0].get_variables())
            variables.update(segment.control2[1].get_variables())
            variables.update(segment.knot2[0].get_variables())
            variables.update(segment.knot2[1].get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "S" if self.is_abs else "s"
        segments = " ".join(str(segment) for segment in self.segments)
        return "{} {} n={} {}".format(letter, segments, self.num_segments, self.close)

    def __eq__(self, other):
        return isinstance(other, SmoothCurveTo) and \
                self.is_abs == other.is_abs and \
                self.segments == other.segments and \
                self.num_segments == other.num_segments and \
                self.close == other.close

    def interpret(self, interpreter, variables):
        vec = lambda v: Vector((v[0], v[1], 0))

        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        knot1 = None
        for i, segment in enumerate(self.segments):
            # For first segment, knot1 is initial pen position;
            # for the following, knot1 is knot2 of previous segment.
            if knot1 is None:
                knot1 = interpreter.position
            else:
                knot1 = knot2

            if interpreter.prev_bezier_knot is None:
                # If there is no previous command or if the previous command was
                # not an C, c, S or s, assume the first control point is coincident
                # with the current point.
                handle1 = knot1
            else:
                # The first control point is assumed to be the reflection of the
                # second control point on the previous command relative to the
                # current point. 
                prev_knot_x, prev_knot_y = interpreter.prev_bezier_knot
                x0, y0 = knot1
                dx, dy = x0 - prev_knot_x, y0 - prev_knot_y
                handle1 = x0 + dx, y0 + dy

            # I assume that handle2 should be relative to knot1, not to handle1.
            # interpreter.position = handle1
            handle2 = interpreter.calc_vertex(self.is_abs, segment.control2[0], segment.control2[1], variables)
            # interpreter.position = handle2
            knot2 = interpreter.calc_vertex(self.is_abs, segment.knot2[0], segment.knot2[1], variables)
            interpreter.position = knot2

            if self.num_segments is not None:
                r = interpreter.eval_(self.num_segments, variables)
            else:
                r = interpreter.dflt_num_verts

            curve = SvCubicBezierCurve(vec(knot1), vec(handle1), vec(handle2), vec(knot2))
            interpreter.new_curve(curve, self)

            points = interpolate_bezier(vec(knot1), vec(handle1), vec(handle2), vec(knot2), r)

            interpreter.new_knot("S#.{}.h1".format(i), *handle1)
            interpreter.new_knot("S#.{}.h2".format(i), *handle2)
            interpreter.new_knot("S#.{}.k".format(i), *knot2)

            interpreter.prev_bezier_knot = handle2

            for point in points[1:]:
                v1_index = interpreter.new_vertex(point.x, point.y)
                interpreter.new_edge(v0_index, v1_index)
                v0_index = v1_index

        if self.close:
            interpreter.close_segment(v1_index)

        interpreter.has_last_vertex = True

class QuadraticCurveTo(Statement):
    class Segment(object):
        def __init__(self, control, knot2):
            self.control = control
            self.knot2 = knot2

        def __repr__(self):
            return "{} {}".format(self.control, self.knot2)

        def __eq__(self, other):
            return self.control == other.control and \
                    self.knot2 == other.knot2

    def __init__(self, is_abs, segments, num_segments, close):
        self.is_abs = is_abs
        self.segments = segments
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        for segment in self.segments:
            variables.update(segment.control[0].get_variables())
            variables.update(segment.control[1].get_variables())
            variables.update(segment.knot2[0].get_variables())
            variables.update(segment.knot2[1].get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "Q" if self.is_abs else "q"
        segments = " ".join(str(segment) for segment in self.segments)
        return "{} {} n={} {}".format(letter, segments, self.num_segments, self.close)

    def __eq__(self, other):
        return isinstance(other, QuadraticCurveTo) and \
                self.is_abs == other.is_abs and \
                self.segments == other.segments and \
                self.num_segments == other.num_segments and \
                self.close == other.close

    def interpret(self, interpreter, variables):
        vec = lambda v: Vector((v[0], v[1], 0))

        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        knot1 = None
        for i, segment in enumerate(self.segments):
            # For first segment, knot1 is initial pen position;
            # for the following, knot1 is knot2 of previous segment.
            if knot1 is None:
                knot1 = interpreter.position
            else:
                knot1 = knot2

            handle = interpreter.calc_vertex(self.is_abs, segment.control[0], segment.control[1], variables)
            knot2 = interpreter.calc_vertex(self.is_abs, segment.knot2[0], segment.knot2[1], variables)
            interpreter.position = knot2

            if self.num_segments is not None:
                r = interpreter.eval_(self.num_segments, variables)
            else:
                r = interpreter.dflt_num_verts

            curve = SvBezierCurve([vec(knot1), vec(handle), vec(knot2)])
            interpreter.new_curve(curve, self)

            points = interpolate_quadratic_bezier(vec(knot1), vec(handle), vec(knot2), r)

            interpreter.new_knot("Q#.{}.h".format(i), *handle)
            interpreter.new_knot("Q#.{}.k".format(i), *knot2)

            interpreter.prev_quad_bezier_knot = handle

            for point in points[1:]:
                v1_index = interpreter.new_vertex(point.x, point.y)
                interpreter.new_edge(v0_index, v1_index)
                v0_index = v1_index

        if self.close:
            interpreter.close_segment(v1_index)

        interpreter.has_last_vertex = True

class SmoothQuadraticCurveTo(Statement):
    class Segment(object):
        def __init__(self, knot2):
            self.knot2 = knot2

        def __repr__(self):
            return str(self.knot2)

        def __eq__(self, other):
            return self.knot2 == other.knot2

    def __init__(self, is_abs, segments, num_segments, close):
        self.is_abs = is_abs
        self.segments = segments
        self.num_segments = num_segments
        self.close = close

    def get_variables(self):
        variables = set()
        for segment in self.segments:
            variables.update(segment.knot2[0].get_variables())
            variables.update(segment.knot2[1].get_variables())
        if self.num_segments:
            variables.update(self.num_segments.get_variables())
        return variables

    def __repr__(self):
        letter = "T" if self.is_abs else "t"
        segments = " ".join(str(segment) for segment in self.segments)
        return "{} {} n={} {}".format(letter, segments, self.num_segments, self.close)

    def __eq__(self, other):
        return isinstance(other, SmoothQuadraticCurveTo) and \
                self.is_abs == other.is_abs and \
                self.segments == other.segments and \
                self.num_segments == other.num_segments and \
                self.close == other.close

    def interpret(self, interpreter, variables):
        vec = lambda v: Vector((v[0], v[1], 0))

        interpreter.assert_not_closed()
        interpreter.start_new_segment()

        v0 = interpreter.position
        if interpreter.has_last_vertex:
            v0_index = interpreter.get_last_vertex()
        else:
            v0_index = interpreter.new_vertex(*v0)

        knot1 = None
        for i, segment in enumerate(self.segments):
            # For first segment, knot1 is initial pen position;
            # for the following, knot1 is knot2 of previous segment.
            if knot1 is None:
                knot1 = interpreter.position
            else:
                knot1 = knot2

            if interpreter.prev_quad_bezier_knot is None:
                # If there is no previous command or if the previous command was
                # not a Q, q, T or t, assume the control point is coincident with
                # the current point.
                handle = knot1
            else:
                # The first control point is assumed to be the reflection of the
                # second control point on the previous command relative to the
                # current point. 
                prev_knot_x, prev_knot_y = interpreter.prev_quad_bezier_knot
                x0, y0 = knot1
                dx, dy = x0 - prev_knot_x, y0 - prev_knot_y
                handle = x0 + dx, y0 + dy

            knot2 = interpreter.calc_vertex(self.is_abs, segment.knot2[0], segment.knot2[1], variables)
            interpreter.position = knot2

            if self.num_segments is not None:
                r = interpreter.eval_(self.num_segments, variables)
            else:
                r = interpreter.dflt_num_verts

            curve = SvBezierCurve([vec(knot1), vec(handle), vec(knot2)])
            interpreter.new_curve(curve, self)

            points = interpolate_quadratic_bezier(vec(knot1), vec(handle), vec(knot2), r)

            interpreter.new_knot("T#.{}.h".format(i), *handle)
            interpreter.new_knot("T#.{}.k".format(i), *knot2)

            interpreter.prev_quad_bezier_knot = handle

            for point in points[1:]:
                v1_index = interpreter.new_vertex(point.x, point.y)
                interpreter.new_edge(v0_index, v1_index)
                v0_index = v1_index

        if self.close:
            interpreter.close_segment(v1_index)

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
        return "{} {} {} {} {} {} n={} {}".format(letter, self.radii, self.rot, self.flag1, self.flag2, self.end, self.num_verts, self.close)

    def __eq__(self, other):
        return isinstance(other, ArcTo) and \
                self.is_abs == other.is_abs and \
                self.radii == other.radii and \
                self.rot == other.rot and \
                self.flag1 == other.flag1 and \
                self.flag2 == other.flag2 and \
                self.end == other.end and \
                self.num_verts == other.num_verts and \
                self.close == other.close

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
        rad_x = interpreter.eval_(rad_x_expr, variables)
        rad_y = interpreter.eval_(rad_y_expr, variables)
        radius = complex(rad_x, rad_y)
        xaxis_rot = interpreter.eval_(self.rot, variables)
        flag1 = interpreter.eval_(self.flag1, variables)
        flag2 = interpreter.eval_(self.flag2, variables)

        # numverts, requires -1 else it means segments (21 verts is 20 segments).
        if self.num_verts is not None:
            num_verts = interpreter.eval_(self.num_verts, variables)
        else:
            num_verts = interpreter.dflt_num_verts
        num_verts -= 1

        end = interpreter.calc_vertex(self.is_abs, self.end[0], self.end[1], variables)
        end = complex(*end)

        arc = Arc(start, radius, xaxis_rot, flag1, flag2, end)

        theta = 1/num_verts
        for i in range(1, num_verts+1):
            v1 = x, y = arc.point(theta * i)
            v1_index = interpreter.new_vertex(x, y)
            interpreter.new_edge(v0_index, v1_index)
            v0_index = v1_index

        curve = SvCircle.from_arc(arc, z_axis=interpreter.z_axis)
        interpreter.new_curve(curve, self)

        interpreter.position = v1
        interpreter.new_knot("A.#", *v1)
        if self.close:
            interpreter.close_segment(v1_index)

        interpreter.has_last_vertex = True

class CloseAll(Statement):
    def __init__(self):
        pass

    def __repr__(self):
        return "X"

    def __eq__(self, other):
        return isinstance(other, CloseAll)

    def get_variables(self):
        return set()

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        if not interpreter.has_last_vertex:
            info("X statement: no current point, do nothing")
            return

        v0 = interpreter.vertices[0]
        v1 = interpreter.vertices[-1]

        distance = (Vector(v0) - Vector(v1)).length

        if distance < interpreter.close_threshold:
            interpreter.pop_last_vertex()

        v1_index = interpreter.get_last_vertex()
        interpreter.new_edge(v1_index, 0)

        interpreter.new_line_segment(v1, v0)

        interpreter.closed = True

class ClosePath(Statement):
    def __init__(self):
        pass

    def __repr__(self):
        return "x"

    def __eq__(self, other):
        return isinstance(other, ClosePath)

    def get_variables(self):
        return set()

    def interpret(self, interpreter, variables):
        interpreter.assert_not_closed()
        if not interpreter.has_last_vertex:
            info("X statement: no current point, do nothing")
            return

        v0 = interpreter.vertices[interpreter.close_first_index]
        v1 = interpreter.vertices[-1]

        distance = (Vector(v0) - Vector(v1)).length

        if distance < interpreter.close_threshold:
            interpreter.pop_last_vertex()

        v1_index = interpreter.get_last_vertex()
        interpreter.new_edge(v1_index, interpreter.close_first_index)
        interpreter.new_line_segment(v1_index, interpreter.close_first_index)
        interpreter.close_first_index = interpreter.next_vertex_index

class Default(Statement):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return "default {} = {}".format(self.name, self.value)

    def __eq__(self, other):
        return isinstance(other, Default) and \
                self.name == other.name and \
                self.value == other.value

    def get_variables(self):
        return self.value.get_variables()

    def get_optional_inputs(self):
        return set([self.name])

    def interpret(self, interpreter, variables):
        if self.name in interpreter.defaults:
            raise Exception("Value for the `{}' variable has been already assigned!".format(self.name))
        if self.name not in interpreter.input_names:
            value = interpreter.eval_(self.value, variables)
            interpreter.defaults[self.name] = value

class Assign(Default):
    def __repr__(self):
        return "let {} = {}".format(self.name, self.value)

    def __eq__(self, other):
        return isinstance(other, Assign) and \
                self.name == other.name and \
                self.value == other.value

    def get_hidden_inputs(self):
        return set([self.name])

#################################
# DSL Interpreter
#################################

# This class does the following:
#
# * Stores the "drawing" state, such as "current pen position"
# * Provides API for Statement classes to add vertices, edges to the current
#   drawing
# * Contains the interpret() method, which runs the whole interpretation process.

class Interpreter(object):

    NURBS = 'NURBS'
    BEZIER = 'BEZIER'

    def __init__(self, node, input_names, curves_form = None, force_curves_form = False, z_axis='Z'):
        self.position = (0, 0)
        self.next_vertex_index = 0
        self.segment_start_index = 0
        self.segment_continues_line = False
        self.segment_number = 0
        self.has_last_vertex = False
        self.closed = False
        self.close_first_index = 0
        self.prev_bezier_knot = None
        self.prev_quad_bezier_knot = None
        self.curves = []
        self.vertices = []
        self.edges = []
        self.knots = []
        self.knotnames = []
        self.dflt_num_verts = node.curve_points_count
        self.close_threshold = node.close_threshold
        self.defaults = dict()
        self.input_names = input_names
        self.curves_form = curves_form
        self.force_curves_form = force_curves_form
        self.z_axis = z_axis

    def to3d(self, vertex):
        if self.z_axis == 'X':
            return Vector((0, vertex[0], vertex[1]))
        elif self.z_axis == 'Y':
            return Vector((vertex[0], 0, vertex[1]))
        else: # self.z_axis == 'Z':
            return Vector((vertex[0], vertex[1], 0))

    def assert_not_closed(self):
        if self.closed:
            raise Exception("Path was already closed, will not process any further directives!")

    def relative(self, x, y):
        x0, y0 = self.position
        return x0+x, y0+y

    def calc_vertex(self, is_abs, x_expr, y_expr, variables):
        x = self.eval_(x_expr, variables)
        y = self.eval_(y_expr, variables)
        if is_abs:
            return x,y
        else:
            return self.relative(x,y)

    def new_vertex(self, x, y):
        index = self.next_vertex_index
        vertex = (x, y)
        self.vertices.append(vertex)
        self.next_vertex_index += 1
        return index

    def new_edge(self, v1, v2):
        self.edges.append((v1, v2))

    def new_knot(self, name, x, y):
        self.knots.append((x, y))
        name = name.replace("#", str(self.segment_number))
        self.knotnames.append(name)

    def new_curve(self, curve, statement):
        if self.curves_form == Interpreter.NURBS:
            if hasattr(curve, 'to_nurbs'):
                curve = curve.to_nurbs()
            else:
                if self.force_curves_form:
                    raise Exception(f"Cannot convert curve to NURBS: {statement}")
        elif self.curves_form == Interpreter.BEZIER:
            if not isinstance(curve, (SvBezierCurve, SvCubicBezierCurve)):
                if hasattr(curve, 'to_bezier'):
                    curve = curve.to_bezier()
                else:
                    if self.force_curves_form:
                        raise Exception("Cannot convert curve to Bezier: {statement}")
        self.curves.append(curve)

    def new_line_segment(self, v1, v2):
        if isinstance(v1, int):
            v1, v2 = self.vertices[v1], self.vertices[v2]
        v1, v2 = self.to3d(v1), self.to3d(v2)
        if (v1 - v2).length < self.close_threshold:
            return
        curve = SvLine.from_two_points(v1, v2)
        self.new_curve(curve, None)

    def start_new_segment(self):
        self.segment_start_index = self.next_vertex_index
        self.segment_continues_line = self.has_last_vertex
        self.segment_number += 1

    def close_segment(self, v_index):
        if self.segment_continues_line:
            start_index = self.segment_start_index-1
        else:
            start_index = self.segment_start_index
        self.new_edge(v_index, start_index)

    def get_last_vertex(self):
        return self.next_vertex_index - 1

    def pop_last_vertex(self):
        self.vertices.pop()
        self.next_vertex_index -= 1
        is_not_last = lambda e: e[0] != self.next_vertex_index and e[1] != self.next_vertex_index
        self.edges = list(filter(is_not_last, self.edges))

    def eval_(self, expr, variables):
        variables_ = self.defaults.copy()
        for name in variables:
            value = variables[name]
            if value is not None:
                variables_[name] = value
        return expr.eval_(variables_)

    def interpret(self, profile, variables):
        if not profile:
            return
        for statement in profile:
            debug("Interpret: %s", statement)
            statement.interpret(self, variables)

