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
Convert EisenScript AST to Generative Art XML (eisenxml).

Produces XML compatible with the Sverchok Generative Art node.
See generative-art-examples/*.xml for reference format.

Mapping overview:
    Program            -> <rules> (root element)
    SetStatement       -> attributes on <rules> (max_depth, etc.)
    Rule               -> <rule> with name, weight, max_depth, successor
    Branch             -> <call> (RuleRef) or <instance> (Primitive)
    Repeat             -> count + transforms on <call>/<instance>
    Transformation     -> space-separated tokens in 'transforms' attribute

Transformation token mapping:
    x <v>       -> tx <v>
    y <v>       -> ty <v>
    z <v>       -> tz <v>
    rx <v>      -> rx <v>
    ry <v>      -> ry <v>
    rz <v>      -> rz <v>
    s <v>       -> sa <v>          (uniform)
    s <x> <y> <z> -> s <x> <y> <z>  (per-axis)
    m <9 floats> -> m <9 floats>
    fx          -> fx
    fy          -> fy
    fz          -> fz
    h/hue <v>   -> h <v>
    sat <v>     -> sat <v>
    b/brightness <v> -> b <v>
    a/alpha <v> -> a <v>
    color <c>   -> color <c>
    blend <c> <s> -> blend <c> <s>
"""

from xml.etree import ElementTree as ET
from collections import Counter

from sverchok.utils import sv_logging
from sverchok.utils.modules.eisenscript.parser import parse as parse_eisenscript
from sverchok.utils.modules.eisenscript.ast import (
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    VariableRef,
    Expr,
    IMPLICIT_START_RULE,
    # Axis constants
    AXIS_X, AXIS_Y, AXIS_Z,
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
# Custom exception
# ---------------------------------------------------------------------------

class ExpressionInXmlError(ValueError):
    """
    Raised when an EisenScript AST containing :class:`Expr` nodes is
    converted to XML.

    XML format (Generative Art) does not support Python expressions —
    all values must be concrete numbers or resolvable :class:`VariableRef`
    (via ``#define``).

    Example:
        ::

            1 * { x (a + 1) } box

        ``a + 1`` is an expression and cannot be represented in XML.
        Pre-compute the value and use a ``#define`` instead:
        ::

            #define offset 2
            1 * { x offset } box
    """
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def coalesce(value, dflt):
    if value is None:
        return dflt
    return value


def _resolve_var(value, defines):
    """
    Resolve a value that may be a VariableRef to its numeric value.

    Args:
        value: A float or VariableRef.
        defines: Dict of variable names to their values.

    Returns:
        The resolved float value.

    Raises:
        ExpressionInXmlError: If the value is an :class:`Expr` node.
        ValueError: If the variable is not defined.
    """
    if isinstance(value, Expr):
        raise ExpressionInXmlError(
            f"Expression ({value.source!r}) cannot be converted to XML. "
            f"XML format does not support Python expressions. "
            f"Pre-compute the value and use a #define instead."
        )
    if isinstance(value, VariableRef):
        if value.name not in defines:
            raise ValueError(f"Undefined variable: {value.name}")
        return defines[value.name]
    return value


def _fmt(value, defines, as_int=False):
    """
    Format a value (float or VariableRef) for XML output.

    Args:
        value: A float or VariableRef.
        defines: Dict of variable names to their values.
        as_int: If True, round to integer.

    Returns:
        Formatted string.
    """
    resolved = _resolve_var(value, defines)
    if as_int:
        return str(round(resolved))
    return str(resolved)


# ---------------------------------------------------------------------------
# Transformation -> XML token
# ---------------------------------------------------------------------------

def _trans_to_token(trans, support_colors=False, defines=None):
    """Convert a single Transformation AST node to an XML token string.

    Args:
        trans: A Transformation AST node.
        support_colors: If False, color transformations are skipped.
        defines: Dict of variable names to their values.
    """
    if defines is None:
        defines = {}

    if isinstance(trans, Translate):
        axis_char = "xyz"[trans.axis]
        return f"t{axis_char} {_fmt(trans.value, defines)}"

    if isinstance(trans, Rotate):
        axis_char = "xyz"[trans.axis]
        return f"r{axis_char} {_fmt(trans.angle, defines)}"

    if isinstance(trans, Scale):
        if trans.is_uniform:
            return f"sa {_fmt(trans.x, defines)}"
        return f"s {_fmt(trans.x, defines)} {_fmt(coalesce(trans.y, 1), defines)} {_fmt(coalesce(trans.z, 1), defines)}"

    if isinstance(trans, MatrixTransform):
        return "m " + " ".join(_fmt(v, defines) for v in trans.matrix)

    if isinstance(trans, Mirror):
        axis_char = "xyz"[trans.axis]
        return f"f{axis_char}"

    # Color transformations — only when supported
    if support_colors:
        if isinstance(trans, HueShift):
            return f"h {_fmt(trans.value, defines)}"
        if isinstance(trans, SaturationMul):
            return f"sat {_fmt(trans.value, defines)}"
        if isinstance(trans, BrightnessMul):
            return f"b {_fmt(trans.value, defines)}"
        if isinstance(trans, AlphaMul):
            return f"a {_fmt(trans.value, defines)}"

        if isinstance(trans, SetColor):
            return f"color {trans.color}"
        if isinstance(trans, BlendColor):
            return f"blend {trans.color} {_fmt(trans.strength, defines)}"

    # Unknown transformation — skip with warning
    _logger.warning(
        "Unknown transformation type %s — skipped in XML output",
        type(trans).__name__,
    )
    return ""


def _rep_transforms_str(rep, support_colors=False, defines=None):
    """Get the transforms string for a single Repeat node."""
    if defines is None:
        defines = {}
    tokens = []
    for trans in rep.transformations:
        token = _trans_to_token(trans, support_colors=support_colors, defines=defines)
        if token:
            tokens.append(token)
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Branch -> <call> / <instance> + optional intermediate rules
# ---------------------------------------------------------------------------

def _make_terminal_elem(parent, terminal, transforms_str=None, count=None, defines=None):
    """
    Create a <call> or <instance> element under *parent* for the given
    terminal (RuleRef or Primitive).

    Returns the created element.
    """
    if defines is None:
        defines = {}

    if isinstance(terminal, RuleRef):
        elem = ET.SubElement(parent, "call")
        elem.set("rule", terminal.name)
        if terminal.retirement_depth is not None:
            if isinstance(terminal.retirement_depth, Expr):
                raise ExpressionInXmlError(
                    f"Expression ({terminal.retirement_depth.source!r}) in "
                    f"rule reference retirement depth cannot be converted to XML. "
                    f"XML format does not support Python expressions. "
                    f"Pre-compute the value and use a #define instead."
                )
            elem.set("max_depth", str(terminal.retirement_depth))
        if terminal.retirement_rule is not None:
            elem.set("successor", terminal.retirement_rule)
    elif isinstance(terminal, Box):
        elem = ET.SubElement(parent, "instance")
        elem.set("shape", "box")
    elif isinstance(terminal, Grid):
        elem = ET.SubElement(parent, "instance")
        elem.set("shape", "grid")
    elif isinstance(terminal, Sphere):
        elem = ET.SubElement(parent, "instance")
        elem.set("shape", "sphere")
    elif isinstance(terminal, Line):
        elem = ET.SubElement(parent, "instance")
        elem.set("shape", "line")
    elif isinstance(terminal, Point):
        elem = ET.SubElement(parent, "instance")
        elem.set("shape", "point")
    elif isinstance(terminal, Triangle):
        elem = ET.SubElement(parent, "instance")
        elem.set("shape", "triangle")
        coords = []
        for v in terminal.vertices:
            coords.append(",".join(str(c) for c in v))
        elem.set("vertices", ";".join(coords))
    else:
        return None

    if transforms_str:
        elem.set("transforms", transforms_str)
    if count is not None:
        # count can be a VariableRef — resolve it
        resolved_count = _resolve_var(count, defines)
        elem.set("count", str(round(resolved_count)))
    return elem


def _branch_to_xml(rules_elem, parent_rule_elem, branch, support_colors=False,
                   name_counter=None, defines=None):
    """
    Convert a Branch into XML, creating intermediate rules for nested
    repetitions when needed.

    Each repetition in a branch represents a nested loop:
        10 * { A } 30 * { B } r1
    becomes:
        <call count="10" transforms="A" rule="__intermediate_0"/>
        <rule name="__intermediate_0">
            <call count="30" transforms="B" rule="r1"/>
        </rule>

    Args:
        rules_elem: The root <rules> element (for appending intermediate rules).
        parent_rule_elem: The parent <rule> element (for the first <call>).
        branch: Branch AST node.
        support_colors: If False, color transformations are skipped.
        name_counter: Counter for generating unique intermediate rule names.
        defines: Dict of variable names to their values.

    Returns:
        None
    """
    if name_counter is None:
        name_counter = Counter()
    if defines is None:
        defines = {}

    repetitions = branch.repetitions
    terminal = branch.terminal

    if len(repetitions) == 0:
        # No repetitions — direct terminal
        _make_terminal_elem(parent_rule_elem, terminal, defines=defines)
        return

    if len(repetitions) == 1:
        # Single repetition — straightforward
        rep = repetitions[0]
        tstr = _rep_transforms_str(rep, support_colors=support_colors, defines=defines)
        _make_terminal_elem(parent_rule_elem, terminal,
                            transforms_str=tstr or None,
                            count=rep.count, defines=defines)
        return

    # Multiple repetitions — create a chain of intermediate rules.
    # Walk from outermost to innermost, linking each to the next.
    current_parent = parent_rule_elem

    for i, rep in enumerate(repetitions):
        tstr = _rep_transforms_str(rep, support_colors=support_colors, defines=defines)
        is_last = (i == len(repetitions) - 1)

        if is_last:
            # Last repetition calls the terminal directly
            _make_terminal_elem(current_parent, terminal,
                                transforms_str=tstr or None,
                                count=rep.count, defines=defines)
        else:
            # Create an intermediate rule for the next level
            idx = name_counter["intermediate"]
            name_counter["intermediate"] += 1
            inter_name = f"__intermediate_{idx}"

            # Call from current parent to the intermediate rule
            call_elem = ET.SubElement(current_parent, "call")
            call_elem.set("rule", inter_name)
            if tstr:
                call_elem.set("transforms", tstr)
            resolved_count = _resolve_var(rep.count, defines)
            call_elem.set("count", str(round(resolved_count)))

            # Create the intermediate rule at the <rules> level
            inter_rule = ET.SubElement(rules_elem, "rule")
            inter_rule.set("name", inter_name)
            current_parent = inter_rule


# ---------------------------------------------------------------------------
# Rule -> <rule>
# ---------------------------------------------------------------------------

def _rule_to_xml(rules_elem, rule, support_colors=False, name_counter=None,
                 defines=None):
    """Append a <rule> child to the <rules> element.

    Args:
        rules_elem: The <rules> root element.
        rule: Rule AST node.
        support_colors: If False, color transformations are skipped.
        name_counter: Shared counter for unique intermediate rule names.
        defines: Dict of variable names to their values.
    """
    if name_counter is None:
        name_counter = Counter()
    if defines is None:
        defines = {}

    rule_elem = ET.SubElement(rules_elem, "rule")
    # In XML format, the start rule is always called 'entry'
    xml_name = "entry" if rule.name == IMPLICIT_START_RULE else rule.name
    rule_elem.set("name", xml_name)

    if rule.maxdepth is not None:
        resolved_md = _resolve_var(rule.maxdepth, defines)
        rule_elem.set("max_depth", str(round(resolved_md)))
    if rule.retirement_rule is not None:
        rule_elem.set("successor", rule.retirement_rule)
    if rule.weight is not None and rule.weight != 1.0:
        resolved_w = _resolve_var(rule.weight, defines)
        rule_elem.set("weight", str(round(resolved_w)))

    for branch in rule.body:
        _branch_to_xml(rules_elem, rule_elem, branch,
                       support_colors=support_colors,
                       name_counter=name_counter, defines=defines)


# ---------------------------------------------------------------------------
# Program -> <rules> (root)
# ---------------------------------------------------------------------------

def ast_to_xml(program, support_colors=False):
    """
    Convert an EisenScript AST :class:`Program` to an XML ElementTree element.

    Args:
        program: A :class:`sverchok.utils.modules.eisenscript.ast.Program` instance.
        support_colors: If False (default), color transformations (hue,
            saturation, brightness, alpha, color, blend) are omitted
            from the XML output.

    Returns:
        xml.etree.ElementTree.Element -- the root ``<rules>`` element.
    """
    if not isinstance(program, Program):
        raise TypeError(f"Expected Program, got {type(program).__name__}")

    # Check for expression values in #define
    for name, val in program.defines.items():
        if isinstance(val, Expr):
            raise ExpressionInXmlError(
                f"#define {name} has expression ({val.source!r}) which cannot "
                f"be converted to XML. XML format does not support Python "
                f"expressions in #define. Pre-compute the value."
            )

    rules_elem = ET.Element("rules")

    # Global max_depth from settings
    global_maxdepth = None
    for setting in program.settings:
        if setting.name == "maxdepth":
            global_maxdepth = setting.value

    if global_maxdepth is not None:
        rules_elem.set("max_depth", str(global_maxdepth))
    else:
        # Default max_depth used by Generative Art node
        rules_elem.set("max_depth", "1000")

    # Convert rules
    name_counter = Counter()
    for rule in program.rules:
        _rule_to_xml(rules_elem, rule, support_colors=support_colors,
                     name_counter=name_counter, defines=program.defines)

    return rules_elem


# ---------------------------------------------------------------------------
# Convenience: source string -> XML
# ---------------------------------------------------------------------------

def eisenscript_to_xml(source, support_colors=False):
    """
    Parse EisenScript source and convert to XML in one step.

    Args:
        source: EisenScript source code (string).
        support_colors: If False (default), color transformations (hue,
            saturation, brightness, alpha, color, blend) are omitted
            from the XML output.

    Returns:
        xml.etree.ElementTree.Element -- the root ``<rules>`` element.

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    program = parse_eisenscript(source)
    return ast_to_xml(program, support_colors=support_colors)


# ---------------------------------------------------------------------------
# Pretty-printing helper
# ---------------------------------------------------------------------------

def xml_to_string(root, indent="    "):
    """
    Pretty-print an XML element tree to a string.

    Uses xml.dom.minidom for formatting (same approach as the original
    eisenscript_to_xml.py converter).

    Args:
        root: xml.etree.ElementTree.Element
        indent: Indent string (default 4 spaces).

    Returns:
        str -- pretty-printed XML.
    """
    from xml.dom import minidom

    rough = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(rough)
    return dom.toprettyxml(indent=indent)
