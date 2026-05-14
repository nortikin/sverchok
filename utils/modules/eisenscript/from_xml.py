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
Convert Generative Art XML (eisenxml) to EisenScript AST.

Reverse of ``to_xml``: takes an ``xml.etree.ElementTree`` element
representing a ``<rules>`` document and produces a
:class:`~sverchok.utils.modules.eisenscript.ast.Program`.

Mapping overview (XML → AST):
    <rules>                 → Program
    <rules max_depth="N">   → SetStatement("maxdepth", N)
    <constants .../>        → Program.defines  (evaluated expressions)
    <rule name="X">         → Rule(name="X")
    <rule max_depth="N">    → Rule.maxdepth = N
    <rule weight="W">       → Rule.weight = W
    <rule successor="Y">    → Rule.retirement_rule = "Y"
    <call rule="X"/>        → Branch(terminal=RuleRef("X"))
    <call count="N"/>       → Branch(repetitions=[Repeat(N, [])], ...)
    <call transforms="..."> → Branch(repetitions=[Repeat(1, [trans...])], ...)
    <instance shape="S"/>   → Branch(terminal=<primitive>)
    <instance count="N"/>   → Branch(repetitions=[Repeat(N, [])], ...)
    <instance transforms="">→ Branch(repetitions=[Repeat(1, [trans...])], ...)

Transformation token mapping (XML → AST):
    tx <v>       → Translate(AXIS_X, v)
    ty <v>       → Translate(AXIS_Y, v)
    tz <v>       → Translate(AXIS_Z, v)
    rx <v>       → Rotate(AXIS_X, v)
    ry <v>       → Rotate(AXIS_Y, v)
    rz <v>       → Rotate(AXIS_Z, v)
    sa <v>       → Scale(v)               (uniform)
    s <x> <y> <z> → Scale(x, y, z)       (per-axis)
    sx <v>       → Scale(v, None, None)   (per-axis, x only)
    sy <v>       → Scale(None, v, None)   (per-axis, y only)
    sz <v>       → Scale(None, None, v)   (per-axis, z only)
    m <9 floats> → MatrixTransform([f1..f9])
    fx           → Mirror(AXIS_X)
    fy           → Mirror(AXIS_Y)
    fz           → Mirror(AXIS_Z)
    h/hue <v>    → HueShift(v)
    sat <v>      → SaturationMul(v)
    b/brightness <v> → BrightnessMul(v)
    a/alpha <v>  → AlphaMul(v)
    color <c>    → SetColor(c)
    blend <c> <s> → BlendColor(c, s)
"""

import re
from typing import Dict, List, Optional, Tuple

from sverchok.utils import sv_logging
from sverchok.utils.modules.eisenscript.ast import (
    # Axis constants
    AXIS_X, AXIS_Y, AXIS_Z,
    # Program structure
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    # Geometrical transformations
    Translate,
    Rotate,
    Scale,
    MatrixTransform,
    Mirror,
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

_logger = sv_logging.sv_logger.getChild(__name__)


# ---------------------------------------------------------------------------
# Primitive name → AST class mapping
# ---------------------------------------------------------------------------

_PRIMITIVE_MAP: Dict[str, type] = {
    "box": Box,
    "grid": Grid,
    "sphere": Sphere,
    "line": Line,
    "point": Point,
    "triangle": Triangle,
}


# ---------------------------------------------------------------------------
# Safe expression evaluator for <constants>
# ---------------------------------------------------------------------------

def _safe_eval(expr: str, defines: dict) -> float:
    """
    Evaluate a constant expression safely.

    Supports basic arithmetic and references to previously-defined constants
    via ``{name}`` syntax.

    Args:
        expr: Expression string (e.g. ``"((1+5**0.5)/2)"`` or ``"{phi}+1"``).
        defines: Dictionary of already-defined constants.

    Returns:
        Evaluated float value.

    Raises:
        ValueError: If the expression cannot be evaluated.
    """
    # Substitute {name} references with their values
    resolved = expr
    for name, value in defines.items():
        resolved = resolved.replace(f"{{{name}}}", str(value))

    # Only allow safe characters: digits, operators, parentheses, dots, spaces
    if not re.match(r'^[\d\s\+\-\*\/\.\(\)\%\^\,]+$', resolved):
        raise ValueError(f"Unsafe constant expression: {expr!r}")

    try:
        # Replace ** with ** for power (already correct)
        return float(eval(resolved, {"__builtins__": {}}, {}))
    except Exception as e:
        raise ValueError(f"Cannot evaluate constant expression {expr!r}: {e}")


# ---------------------------------------------------------------------------
# Transformation token parser
# ---------------------------------------------------------------------------

def _parse_transform_token(
    tokens: List[str],
    idx: int,
) -> Tuple[object, int]:
    """
    Parse a single transformation token and its arguments.

    Args:
        tokens: Full list of tokens from the transforms string.
        idx: Current index in the token list (pointing to the keyword).

    Returns:
        (transformation_node, next_index) tuple.
    """
    token = tokens[idx]
    idx += 1

    def _num():
        nonlocal idx
        val = float(tokens[idx])
        idx += 1
        return val

    if token == "tx":
        return Translate(AXIS_X, _num()), idx
    if token == "ty":
        return Translate(AXIS_Y, _num()), idx
    if token == "tz":
        return Translate(AXIS_Z, _num()), idx

    if token == "rx":
        return Rotate(AXIS_X, _num()), idx
    if token == "ry":
        return Rotate(AXIS_Y, _num()), idx
    if token == "rz":
        return Rotate(AXIS_Z, _num()), idx

    if token == "sa":
        return Scale(_num()), idx

    if token == "s":
        x = _num()
        y = _num()
        z = _num()
        return Scale(x, y, z), idx

    if token == "sx":
        return Scale(_num(), None, None), idx
    if token == "sy":
        return Scale(None, _num(), None), idx
    if token == "sz":
        return Scale(None, None, _num()), idx

    if token == "m":
        matrix = [_num() for _ in range(9)]
        return MatrixTransform(matrix), idx

    if token == "fx":
        return Mirror(AXIS_X), idx
    if token == "fy":
        return Mirror(AXIS_Y), idx
    if token == "fz":
        return Mirror(AXIS_Z), idx

    if token in ("h", "hue"):
        return HueShift(_num()), idx
    if token == "sat":
        return SaturationMul(_num()), idx
    if token in ("b", "brightness"):
        return BrightnessMul(_num()), idx
    if token in ("a", "alpha"):
        return AlphaMul(_num()), idx

    if token == "color":
        color = tokens[idx]
        idx += 1
        return SetColor(color), idx

    if token == "blend":
        color = tokens[idx]
        idx += 1
        strength = float(tokens[idx])
        idx += 1
        return BlendColor(color, strength), idx

    raise ValueError(f"Unknown transformation token: {token!r}")


def _parse_transforms_string(transforms_str: str) -> List[object]:
    """
    Parse a transforms attribute string into a list of transformation nodes.

    Args:
        transforms_str: Space-separated transformation tokens
            (e.g. ``"tx 1 rz 30 sa 0.95"``).

    Returns:
        List of transformation AST nodes.
    """
    if not transforms_str or not transforms_str.strip():
        return []

    tokens = transforms_str.split()
    transforms = []
    i = 0
    while i < len(tokens):
        trans, i = _parse_transform_token(tokens, i)
        transforms.append(trans)
    return transforms


# ---------------------------------------------------------------------------
# Helper: collect transforms from element attributes
# ---------------------------------------------------------------------------

def _get_transforms_string(elem) -> str:
    """
    Build a transforms string from element attributes.

    XML can specify transforms in two ways:
    1. ``transforms="tx 1 rz 30"`` (combined string)
    2. ``tx="1" rz="30"`` (individual attributes)

    Returns the combined transforms string.
    """
    parts = []

    # Combined transforms attribute
    combined = elem.get("transforms", "")
    if combined:
        parts.append(combined)

    # Individual transform attributes
    for attr in ("tx", "ty", "tz", "rx", "ry", "rz",
                 "sa", "sx", "sy", "sz"):
        val = elem.get(attr)
        if val is not None:
            parts.append(f"{attr} {val}")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main conversion function
# ---------------------------------------------------------------------------

def xml_to_ast(xml_root) -> Program:
    """
    Convert a Generative Art XML ``<rules>`` element to an EisenScript AST.

    Args:
        xml_root: An ``xml.etree.ElementTree`` element representing
            the ``<rules>`` root element.

    Returns:
        A :class:`~sverchok.utils.modules.eisenscript.ast.Program` instance.

    Raises:
        ValueError: If the XML contains unknown or invalid content.
    """
    defines: Dict[str, float] = {}
    settings: List[SetStatement] = []
    rules: List[Rule] = []

    # Global max_depth from <rules> element
    global_max_depth = xml_root.get("max_depth")
    if global_max_depth:
        settings.append(SetStatement("maxdepth", int(global_max_depth)))

    for child in xml_root:
        tag = child.tag

        if tag == "constants":
            # <constants name="X" value="Y"/> or <constants phi="expr" />
            # Handle both attribute styles
            for attr_name, attr_val in child.attrib.items():
                try:
                    defines[attr_name] = _safe_eval(attr_val, defines)
                except ValueError as e:
                    _logger.warning(f"Skipping constant {attr_name}: {e}")

        elif tag == "rule":
            rule = _parse_rule(child, defines)
            rules.append(rule)

        else:
            _logger.warning(f"Unknown element: <{tag}>")

    return Program(defines=defines, settings=settings, rules=rules)


def _parse_rule(elem, defines: dict) -> Rule:
    """Parse a single <rule> element into a Rule AST node."""
    name = elem.get("name", "unnamed")
    weight = None
    maxdepth = None
    retirement_rule = None

    # Rule attributes
    if "weight" in elem.attrib:
        weight = float(elem.get("weight"))
    if "max_depth" in elem.attrib:
        maxdepth = int(elem.get("max_depth"))
    if "successor" in elem.attrib:
        retirement_rule = elem.get("successor")

    # Parse branches from child elements
    branches = []
    for child in elem:
        if child.tag == "call":
            branches.append(_parse_call(child, defines))
        elif child.tag == "instance":
            branches.append(_parse_instance(child, defines))
        else:
            _logger.warning(f"Unknown element in rule: <{child.tag}>")

    return Rule(
        name=name,
        body=branches,
        weight=weight,
        maxdepth=maxdepth,
        retirement_rule=retirement_rule,
    )


def _parse_call(elem, defines: dict) -> Branch:
    """Parse a <call> element into a Branch with RuleRef terminal."""
    rule_name = elem.get("rule", "")
    count_str = elem.get("count", "1")
    count = int(count_str)

    transforms_str = _get_transforms_string(elem)
    transforms = _parse_transforms_string(transforms_str)

    repetitions = []
    if count > 1 or transforms:
        repetitions.append(Repeat(count, transforms))

    return Branch(
        repetitions=repetitions,
        terminal=RuleRef(rule_name),
    )


def _parse_instance(elem, defines: dict) -> Branch:
    """Parse an <instance> element into a Branch with primitive terminal."""
    shape_name = elem.get("shape", "box").lower()
    count_str = elem.get("count", "1")
    count = int(count_str)

    transforms_str = _get_transforms_string(elem)
    transforms = _parse_transforms_string(transforms_str)

    # Create primitive node
    primitive_cls = _PRIMITIVE_MAP.get(shape_name)
    if primitive_cls is None:
        _logger.warning(f"Unknown primitive shape: {shape_name!r}, using box")
        primitive_cls = Box

    # Triangle requires vertices, others don't
    if primitive_cls is Triangle:
        terminal = Triangle([])  # empty vertices
    else:
        terminal = primitive_cls()

    repetitions = []
    if count > 1 or transforms:
        repetitions.append(Repeat(count, transforms))

    return Branch(
        repetitions=repetitions,
        terminal=terminal,
    )
