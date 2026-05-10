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

from sverchok.utils.modules.eisenscript.parser import parse as parse_eisenscript
from sverchok.utils.modules.eisenscript.ast import (
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    # Geometrical transformations
    TranslateX,
    TranslateY,
    TranslateZ,
    RotateX,
    RotateY,
    RotateZ,
    Scale,
    MatrixTransform,
    MirrorX,
    MirrorY,
    MirrorZ,
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
# Transformation -> XML token
# ---------------------------------------------------------------------------

def _trans_to_token(trans, support_colors=False):
    """Convert a single Transformation AST node to an XML token string.

    Args:
        trans: A Transformation AST node.
        support_colors: If False, color transformations are skipped.
    """
    if isinstance(trans, TranslateX):
        return f"tx {trans.value}"
    if isinstance(trans, TranslateY):
        return f"ty {trans.value}"
    if isinstance(trans, TranslateZ):
        return f"tz {trans.value}"

    if isinstance(trans, RotateX):
        return f"rx {trans.angle}"
    if isinstance(trans, RotateY):
        return f"ry {trans.angle}"
    if isinstance(trans, RotateZ):
        return f"rz {trans.angle}"

    if isinstance(trans, Scale):
        if trans.is_uniform:
            return f"sa {trans.x}"
        return f"s {trans.x} {trans.y} {trans.z}"

    if isinstance(trans, MatrixTransform):
        return "m " + " ".join(str(v) for v in trans.matrix)

    if isinstance(trans, MirrorX):
        return "fx"
    if isinstance(trans, MirrorY):
        return "fy"
    if isinstance(trans, MirrorZ):
        return "fz"

    # Color transformations — only when supported
    if support_colors:
        if isinstance(trans, HueShift):
            return f"h {trans.value}"
        if isinstance(trans, SaturationMul):
            return f"sat {trans.value}"
        if isinstance(trans, BrightnessMul):
            return f"b {trans.value}"
        if isinstance(trans, AlphaMul):
            return f"a {trans.value}"

        if isinstance(trans, SetColor):
            return f"color {trans.color}"
        if isinstance(trans, BlendColor):
            return f"blend {trans.color} {trans.strength}"

    # Unknown transformation — skip silently
    return ""


def _collect_transforms(repetitions, support_colors=False):
    """
    Collect all transformations from a list of Repeat nodes into a single
    transforms string.

    Each Repeat contributes its transformations. The count of the *last*
    Repeat (if any) becomes the 'count' attribute of the XML element.

    Args:
        repetitions: List of Repeat nodes.
        support_colors: If False, color transformations are skipped.
    """
    tokens = []
    count = None
    for rep in repetitions:
        for trans in rep.transformations:
            token = _trans_to_token(trans, support_colors=support_colors)
            if token:
                tokens.append(token)
        count = rep.count
    return " ".join(tokens), count


# ---------------------------------------------------------------------------
# Branch -> <call> or <instance>
# ---------------------------------------------------------------------------

def _branch_to_xml(parent, branch, support_colors=False):
    """
    Append a <call> or <instance> child to *parent* for the given Branch.

    - RuleRef terminal  -> <call rule="...">
    - Primitive terminal -> <instance shape="...">

    Args:
        parent: Parent XML element.
        branch: Branch AST node.
        support_colors: If False, color transformations are skipped.
    """
    repetitions = branch.repetitions
    terminal = branch.terminal

    transforms_str, count = _collect_transforms(repetitions, support_colors=support_colors)

    if isinstance(terminal, RuleRef):
        elem = ET.SubElement(parent, "call")
        elem.set("rule", terminal.name)

        # Rule retirement: md N > fallback -> max_depth + successor
        if terminal.retirement_depth is not None:
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
        # Store vertices as a semicolon-separated attribute
        coords = []
        for v in terminal.vertices:
            coords.append(",".join(str(c) for c in v))
        elem.set("vertices", ";".join(coords))
    else:
        # Unknown terminal — skip
        return

    if transforms_str:
        elem.set("transforms", transforms_str)
    if count is not None:
        elem.set("count", str(count))


# ---------------------------------------------------------------------------
# Rule -> <rule>
# ---------------------------------------------------------------------------

def _rule_to_xml(rules_elem, rule, support_colors=False):
    """Append a <rule> child to the <rules> element.

    Args:
        rules_elem: The <rules> root element.
        rule: Rule AST node.
        support_colors: If False, color transformations are skipped.
    """
    rule_elem = ET.SubElement(rules_elem, "rule")
    # In XML format, the start rule is always called 'entry'
    xml_name = "entry" if rule.name == "start" else rule.name
    rule_elem.set("name", xml_name)

    if rule.maxdepth is not None:
        rule_elem.set("max_depth", str(rule.maxdepth))
    if rule.weight is not None and rule.weight != 1.0:
        rule_elem.set("weight", str(rule.weight))

    for branch in rule.body:
        _branch_to_xml(rule_elem, branch, support_colors=support_colors)


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
    for rule in program.rules:
        _rule_to_xml(rules_elem, rule, support_colors=support_colors)

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
