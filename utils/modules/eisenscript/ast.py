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
AST nodes for the EisenScript language.

EisenScript is a procedural geometry scripting language based on L-systems.
This module defines the abstract syntax tree classes that represent
parsed EisenScript programs.

Grammar overview:
    program       -> (set_statement | rule_definition)*
    set_statement -> 'set' setting_name value*
    rule_definition -> 'rule'? rule_name rule_modifier* '{' rule_body '}'
    rule_body     -> branch*
    branch        -> repetition* (rule_ref | primitive)
    repetition    -> count '*' '{' transformation+ '}'
    rule_ref      -> rule_name | 'md' count '>' rule_name
    primitive     -> 'box' | 'grid' | 'sphere' | 'line' | 'point' | 'triangle'
    transformation -> 'x'|'y'|'z' (float | expr)
                   | 'rx'|'ry'|'rz' (float | expr)
                   | 's' (float | expr) { (float | expr) (float | expr) }
                   | 'm' (float | expr){9}
                   | 'fx'|'fy'|'fz'
                   | 'h'|'hue' (float | expr)
                   | 'sat' (float | expr)
                   | 'b'|'brightness' (float | expr)
                   | 'a'|'alpha' (float | expr)
                   | 'color' color
                   | 'blend' color (float | expr)
    expr          -> '(' python_expression ')'
"""

import ast


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------

class AstNode:
    """Base class for all EisenScript AST nodes."""

    def __repr__(self):
        name = self.__class__.__name__
        return name + "()"


class Transformation(AstNode):
    """Base class for all transformation actions inside a rule body."""


class Primitive(AstNode):
    """Base class for drawing primitives (box, sphere, etc.)."""


# Sentinel name for the implicit entry-point rule.
# Chosen so it can never collide with a user-defined rule name
# (rule names must be valid identifiers, this is not).
IMPLICIT_START_RULE = "###START###"


# ---------------------------------------------------------------------------
# Program-level nodes
# ---------------------------------------------------------------------------

class Program(AstNode):
    """
    Top-level AST node representing a complete EisenScript program.

    Attributes:
        defines: Dict mapping variable names to their numeric values (float).
        settings: List of SetStatement nodes (global settings).
        rules: List of Rule nodes (rule definitions).
    """

    def __init__(self, defines=None, settings=None, rules=None):
        self.defines = defines or {}
        self.settings = settings or []
        self.rules = rules or []

    def __repr__(self):
        return f"Program(defines={len(self.defines)}, settings={len(self.settings)}, rules={len(self.rules)})"


class SetStatement(AstNode):
    """
    Global setting statement (e.g. 'set maxdepth 100').

    Attributes:
        name: Setting name (maxdepth, maxobjects, minsize, maxsize, seed,
              background, color, colorpool).
        value: Setting value (int, float, or str for color strings).
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Set({self.name}, {self.value!r})"


class VariableRef(AstNode):
    """
    Reference to a #define variable.

    Attributes:
        name: Variable name (string).
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Var({self.name!r})"


class Expr(AstNode):
    """
    A Python expression enclosed in parentheses, e.g. ``(x * 2 + sin(t))``.

    The expression string is validated at parse time via ``ast.parse(mode='eval')``.
    At interpretation time it is evaluated with ``eval()`` using a safe namespace
    (math functions, constants, and #define variables).

    Attributes:
        source: The raw expression string (without surrounding parens).
        ast_node: The parsed ``ast.Expression`` from ``ast.parse(source, mode='eval')``.
    """

    def __init__(self, source: str, ast_node):
        self.source = source
        self.ast_node = ast_node

    def __repr__(self):
        return f"Expr({self.source!r})"

    def __eq__(self, other):
        return isinstance(other, Expr) and self.source == other.source

    def get_variables(self):
        """Return the set of variable names referenced in this expression."""
        return {
            node.id
            for node in ast.walk(self.ast_node)
            if isinstance(node, ast.Name)
        }


# ---------------------------------------------------------------------------
# Rule nodes
# ---------------------------------------------------------------------------

class Rule(AstNode):
    """
    Rule definition.

    Attributes:
        name: Rule identifier (string).
        maxdepth: Optional maximum recursion depth for this rule (int or None).
        retirement_rule: Optional rule to substitute when maxdepth is reached
            (string or None).  Written as 'maxdepth N > retirement_rule'.
        weight: Ambiguity weight for random rule selection (float or None,
                default 1.0).
        body: List of Branch nodes forming the rule body.
    """

    def __init__(self, name, maxdepth=None, retirement_rule=None,
                 weight=None, body=None):
        self.name = name
        self.maxdepth = maxdepth
        self.retirement_rule = retirement_rule
        self.weight = weight if weight is not None else 1.0
        self.body = body or []

    def __repr__(self):
        return f"Rule({self.name!r}, md={self.maxdepth}, w={self.weight})"


class Branch(AstNode):
    """
    A single branch inside a rule body.

    A branch consists of zero or more repetition blocks followed by a
    terminal: either a rule reference or a primitive.

    Attributes:
        repetitions: List of Repeat nodes.
        terminal: RuleRef or Primitive node.
    """

    def __init__(self, repetitions=None, terminal=None):
        self.repetitions = repetitions or []
        self.terminal = terminal

    def __repr__(self):
        return f"Branch(reps={len(self.repetitions)}, term={self.terminal!r})"


class Repeat(AstNode):
    """
    Repetition construct: 'N * { transformations... }'.

    Attributes:
        count: Number of repetitions (int).
        transformations: List of Transformation nodes applied each iteration.
    """

    def __init__(self, count, transformations=None):
        self.count = count
        self.transformations = transformations or []

    def __repr__(self):
        return f"Repeat({self.count}, {len(self.transformations)} transforms)"


# ---------------------------------------------------------------------------
# Rule reference
# ---------------------------------------------------------------------------

class RuleRef(AstNode):
    """
    Reference to another rule (terminal of a branch).

    Attributes:
        name: Referenced rule name (string).
        retirement_depth: Optional maxdepth for rule retirement (int or None).
        retirement_rule: Optional rule to substitute when retirement_depth
                         is reached (string or None).
    """

    def __init__(self, name, retirement_depth=None, retirement_rule=None):
        self.name = name
        self.retirement_depth = retirement_depth
        self.retirement_rule = retirement_rule

    def __repr__(self):
        if self.retirement_depth is not None:
            ret = f"md={self.retirement_depth}"
            if self.retirement_rule:
                ret += f">{self.retirement_rule}"
            return f"RuleRef({self.name!r}, {ret})"
        return f"RuleRef({self.name!r})"


# ---------------------------------------------------------------------------
# Geometrical transformations
# ---------------------------------------------------------------------------

# Axis constants
AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2
AXIS_NAMES = {0: 'x', 1: 'y', 2: 'z'}


class Translate(Transformation):
    """
    Translation along a single axis: 'x'|'y'|'z' <float>.

    Attributes:
        axis: 0=X, 1=Y, 2=Z.
        value: Translation distance (float).
    """

    def __init__(self, axis, value):
        self.axis = axis
        self.value = value

    def __repr__(self):
        return f"Translate({AXIS_NAMES[self.axis]}, {self.value})"


class Rotate(Transformation):
    """
    Rotation about a single axis in degrees: 'rx'|'ry'|'rz' <float>.

    Attributes:
        axis: 0=X, 1=Y, 2=Z.
        angle: Rotation angle in degrees (float).
    """

    def __init__(self, axis, angle):
        self.axis = axis
        self.angle = angle

    def __repr__(self):
        return f"Rotate({AXIS_NAMES[self.axis]}, {self.angle})"


class Mirror(Transformation):
    """
    Mirror about a single axis: 'fx'|'fy'|'fz'.

    Attributes:
        axis: 0=X, 1=Y, 2=Z.
    """

    def __init__(self, axis):
        self.axis = axis

    def __repr__(self):
        return f"Mirror({AXIS_NAMES[self.axis]})"


class Scale(Transformation):
    """
    Scale transformation.

    Can be uniform 's <float>' or per-axis 's <f1> <f2> <f3>'.

    Attributes:
        x: Scale factor for X axis (float).
        y: Scale factor for Y axis (float, None if uniform).
        z: Scale factor for Z axis (float, None if uniform).
    """

    def __init__(self, x, y=None, z=None):
        self.x = x
        self.y = y
        self.z = z

    @property
    def is_uniform(self):
        return self.y is None and self.z is None

    def __repr__(self):
        if self.is_uniform:
            return f"Scale({self.x})"
        return f"Scale({self.x}, {self.y}, {self.z})"


class MatrixTransform(Transformation):
    """
    3x3 matrix transformation: 'm <f1> ... <f9>'.

    Attributes:
        matrix: List of 9 floats (row-major order).
    """

    def __init__(self, matrix):
        self.matrix = matrix  # 9 floats, row-major

    def __repr__(self):
        return f"Matrix({self.matrix})"


# ---------------------------------------------------------------------------
# Color transformations
# ---------------------------------------------------------------------------

class HueShift(Transformation):
    """Hue shift: 'h' or 'hue' <float> (adds to current hue, wraps 0-360)."""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Hue({self.value})"


class SaturationMul(Transformation):
    """Saturation multiplier: 'sat' <float> (clamped to [0, 1])."""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Sat({self.value})"


class BrightnessMul(Transformation):
    """Brightness multiplier: 'b' or 'brightness' <float> (clamped to [0, 1])."""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Brightness({self.value})"


class AlphaMul(Transformation):
    """Alpha multiplier: 'a' or 'alpha' <float> (clamped to [0, 1])."""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Alpha({self.value})"


class SetColor(Transformation):
    """
    Absolute color set: 'color <color>'.

    Attributes:
        color: Color string (HTML hex like '#FF0000' or SVG keyword like 'red').
    """

    def __init__(self, color):
        self.color = color

    def __repr__(self):
        return f"SetColor({self.color!r})"


class BlendColor(Transformation):
    """
    Color blend: 'blend <color> <strength>'.

    Blends current color with specified color in HSV space.
    Strength 1.0 weights both colors evenly.

    Attributes:
        color: Color string to blend with.
        strength: Blend strength (float).
    """

    def __init__(self, color, strength):
        self.color = color
        self.strength = strength

    def __repr__(self):
        return f"Blend({self.color!r}, {self.strength})"


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

class Box(Primitive):
    """Solid box primitive: 'box'."""

    def __repr__(self):
        return "Box()"


class Grid(Primitive):
    """Wireframe box primitive: 'grid'."""

    def __repr__(self):
        return "Grid()"


class Sphere(Primitive):
    """Sphere primitive: 'sphere'."""

    def __repr__(self):
        return "Sphere()"


class Line(Primitive):
    """
    Line primitive along X axis, centered in YZ plane: 'line'.
    """

    def __repr__(self):
        return "Line()"


class Point(Primitive):
    """Point primitive centered in coordinate system: 'point'."""

    def __repr__(self):
        return "Point()"


class Triangle(Primitive):
    """
    Custom triangle/polygon primitive.

    Syntax: Triangle[x1,y1,z1;x2,y2,z2;x3,y3,z3]

    Attributes:
        vertices: List of (x, y, z) tuples.
    """

    def __init__(self, vertices):
        self.vertices = vertices

    def __repr__(self):
        return f"Triangle({self.vertices})"
