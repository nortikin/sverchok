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
Serialize EisenScript AST back to EisenScript source text.

Reverse of ``parser.parse``: takes a
:class:`~sverchok.utils.modules.eisenscript.ast.Program` and produces
a human-readable EisenScript string that the parser can round-trip.

Mapping overview (AST → text):
    Program            → #define / set / rule blocks
    SetStatement       → ``set <name> <value>``
    Rule               → ``rule <name> <modifiers> { ... }``
    Branch             → ``<repetitions> <terminal>``
    Repeat             → ``<count> * { <transformations> }``
    RuleRef            → ``<name>`` or ``md <depth> [<succ>] <name>``
    VariableRef        → ``<name>``
    Translate          → ``x|y|z <value>``
    Rotate             → ``rx|ry|rz <angle>``
    Mirror             → ``fx|fy|fz``
    Scale              → ``s <x>`` or ``s <x> <y> <z>``
    MatrixTransform    → ``m <f1> ... <f9>``
    HueShift           → ``hue <value>``
    SaturationMul      → ``sat <value>``
    BrightnessMul      → ``brightness <value>``
    AlphaMul           → ``alpha <value>``
    SetColor           → ``color <color>``
    BlendColor         → ``blend <color> <strength>``
    Box/Grid/Sphere/Line/Point → keyword
    Triangle           → ``Triangle[x,y,z;x,y;z;x,y,z]``
"""

from typing import List, Optional

from sverchok.utils.modules.eisenscript.ast import (
    # Axis constants
    AXIS_X, AXIS_Y, AXIS_Z,
    AXIS_NAMES,
    # Program structure
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    VariableRef,
    IMPLICIT_START_RULE,
    # Geometrical transformations
    Translate,
    Rotate,
    Mirror,
    Scale,
    MatrixTransform,
    # Color transformations
    HueShift,
    SaturationMul,
    BrightnessMul,
    AlphaMul,
    SetColor,
    BlendColor,
    # Primitives
    Box,
    Grid,
    Sphere,
    Line,
    Point,
    Triangle,
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_num(value) -> str:
    """
    Format a numeric value (float or VariableRef) for EisenScript output.

    Integers are rendered without decimal point (``3`` not ``3.0``).
    VariableRefs are rendered as their name.
    """
    if isinstance(value, VariableRef):
        return value.name
    v = float(value)
    if v == int(v) and -1e6 <= v <= 1e6:
        return str(int(v))
    # Use repr-like precision but strip trailing zeros
    return f"{v:g}"


def _indent(lines: List[str], level: int, width: int = 4) -> str:
    """Join lines with indentation."""
    pad = " " * (level * width)
    return "\n".join(f"{pad}{line}" for line in lines)


# ---------------------------------------------------------------------------
# Transformation serialization
# ---------------------------------------------------------------------------

def _trans_to_str(trans) -> str:
    """Convert a single Transformation AST node to EisenScript text."""
    if isinstance(trans, Translate):
        axis = AXIS_NAMES[trans.axis]
        return f"{axis} {_fmt_num(trans.value)}"

    if isinstance(trans, Rotate):
        axis = AXIS_NAMES[trans.axis]
        return f"r{axis} {_fmt_num(trans.angle)}"

    if isinstance(trans, Mirror):
        axis = AXIS_NAMES[trans.axis]
        return f"f{axis}"

    if isinstance(trans, Scale):
        if trans.is_uniform:
            return f"s {_fmt_num(trans.x)}"
        parts = [_fmt_num(trans.x)]
        if trans.y is not None:
            parts.append(_fmt_num(trans.y))
        else:
            parts.append("1")
        if trans.z is not None:
            parts.append(_fmt_num(trans.z))
        else:
            parts.append("1")
        return f"s {' '.join(parts)}"

    if isinstance(trans, MatrixTransform):
        vals = " ".join(_fmt_num(v) for v in trans.matrix)
        return f"m {vals}"

    if isinstance(trans, HueShift):
        return f"hue {_fmt_num(trans.value)}"

    if isinstance(trans, SaturationMul):
        return f"sat {_fmt_num(trans.value)}"

    if isinstance(trans, BrightnessMul):
        return f"brightness {_fmt_num(trans.value)}"

    if isinstance(trans, AlphaMul):
        return f"alpha {_fmt_num(trans.value)}"

    if isinstance(trans, SetColor):
        return f"color {trans.color}"

    if isinstance(trans, BlendColor):
        return f"blend {trans.color} {_fmt_num(trans.strength)}"

    return ""


# ---------------------------------------------------------------------------
# Primitive serialization
# ---------------------------------------------------------------------------

def _primitive_to_str(primitive) -> str:
    """Convert a Primitive AST node to EisenScript text."""
    if isinstance(primitive, Box):
        return "box"
    if isinstance(primitive, Grid):
        return "grid"
    if isinstance(primitive, Sphere):
        return "sphere"
    if isinstance(primitive, Line):
        return "line"
    if isinstance(primitive, Point):
        return "point"
    if isinstance(primitive, Triangle):
        if not primitive.vertices:
            return "triangle"
        coords = ";".join(
            f"{v[0]},{v[1]},{v[2]}" for v in primitive.vertices
        )
        return f"Triangle[{coords}]"
    return "box"  # fallback


# ---------------------------------------------------------------------------
# Branch serialization
# ---------------------------------------------------------------------------

def _branch_to_str(branch: Branch) -> str:
    """
    Convert a Branch to EisenScript text.

    A branch is: (repetition)* (rule_ref | primitive)
    """
    parts = []

    # Repetitions: N * { transforms... }
    for rep in branch.repetitions:
        count = _fmt_num(rep.count)
        if rep.transformations:
            trans_str = " ".join(_trans_to_str(t) for t in rep.transformations)
            parts.append(f"{count} * {{{trans_str}}}")
        else:
            parts.append(f"{count} * {{}}")

    # Terminal: rule_ref or primitive
    if isinstance(branch.terminal, RuleRef):
        ref = branch.terminal
        if ref.retirement_depth is not None:
            md = _fmt_num(ref.retirement_depth)
            if ref.retirement_rule:
                parts.append(f"md {md} > {ref.retirement_rule} {ref.name}")
            else:
                parts.append(f"md {md} {ref.name}")
        else:
            parts.append(ref.name)
    else:
        parts.append(_primitive_to_str(branch.terminal))

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Rule serialization
# ---------------------------------------------------------------------------

def _rule_to_str(rule: Rule, indent_level: int = 1) -> str:
    """Convert a Rule to EisenScript text block."""
    lines = []

    # Rule header: rule <name> [maxdepth N [> successor]] [weight W]
    header_parts = ["rule", rule.name]
    if rule.maxdepth is not None:
        header_parts.append(f"maxdepth {_fmt_num(rule.maxdepth)}")
        if rule.retirement_rule:
            header_parts[-1] += f" > {rule.retirement_rule}"
    if rule.weight is not None and rule.weight != 1.0:
        header_parts.append(f"weight {_fmt_num(rule.weight)}")

    lines.append(" ".join(header_parts))

    # Rule body
    if rule.body:
        body_lines = []
        for branch in rule.body:
            body_lines.append(_branch_to_str(branch))
        lines.append("{")
        lines.append(_indent(body_lines, indent_level + 1))
        lines.append("}")
    else:
        lines.append("{}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Set statement serialization
# ---------------------------------------------------------------------------

def _set_to_str(stmt: SetStatement) -> str:
    """Convert a SetStatement to EisenScript text."""
    name = stmt.name
    value = stmt.value

    # Special handling for known settings
    if name == "maxdepth":
        return f"set maxdepth {_fmt_num(value)}"
    if name == "maxobjects":
        return f"set maxobjects {_fmt_num(value)}"
    if name == "minsize":
        return f"set minsize {_fmt_num(value)}"
    if name == "maxsize":
        return f"set maxsize {_fmt_num(value)}"
    if name == "seed":
        if isinstance(value, str) and value.lower() == "initial":
            return "set seed initial"
        return f"set seed {_fmt_num(value)}"
    if name == "background":
        return f"set background {value}"
    if name == "color":
        return f"set color {value}"
    if name == "colorpool":
        return f"set colorpool {value}"

    # Generic fallback
    if isinstance(value, str):
        return f"set {name} {value}"
    return f"set {name} {_fmt_num(value)}"


# ---------------------------------------------------------------------------
# Main serialization function
# ---------------------------------------------------------------------------

def ast_to_string(program: Program) -> str:
    """
    Convert an EisenScript AST to source text.

    Produces human-readable EisenScript that the parser can round-trip.
    The implicit start rule (``IMPLICIT_START_RULE``) is emitted as bare
    branches without a ``rule`` keyword.

    Args:
        program: The :class:`~sverchok.utils.modules.eisenscript.ast.Program`
            to serialize.

    Returns:
        EisenScript source code string.
    """
    blocks: List[str] = []

    # #define directives
    for name, value in program.defines.items():
        blocks.append(f"#define {name} {_fmt_num(value)}")

    # set statements
    for stmt in program.settings:
        blocks.append(_set_to_str(stmt))

    # rule definitions
    for rule in program.rules:
        if rule.name == IMPLICIT_START_RULE:
            # Implicit start rule: emit bare branches
            for branch in rule.body:
                blocks.append(_branch_to_str(branch))
        else:
            blocks.append(_rule_to_str(rule))

    # Join blocks with blank lines between logical sections
    result_parts = []
    current_section: List[str] = []

    def flush():
        if current_section:
            result_parts.append("\n".join(current_section))
            current_section.clear()

    for block in blocks:
        if block.startswith("#define") or block.startswith("set "):
            current_section.append(block)
        else:
            flush()
            current_section.append(block)
    flush()

    return "\n\n".join(result_parts) + "\n" if result_parts else ""
