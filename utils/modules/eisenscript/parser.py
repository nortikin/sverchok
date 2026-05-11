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
Parser for the EisenScript language using the combinator parser framework
from sverchok.utils.parsec.

Grammar (EBNF):
    program           -> (set_statement | rule_definition | implicit_start)*
    set_statement     -> 'set' setting_name value*
    rule_definition   -> 'rule'? identifier rule_modifier* '{' rule_body '}'
    implicit_start    -> branch  // bare branch → rule 'start' { branch }
    rule_modifier     -> ('maxdepth' | 'md') int ['>' identifier]
                      | ('weight' | 'w') float
    rule_body         -> branch*
    branch            -> (repetition | transform_block)* (rule_ref | primitive)
    repetition        -> count '*' '{' transformation+ '}'
    transform_block   -> '{' transformation+ '}'
    count             -> int | identifier
    rule_ref          -> identifier | 'md' int ['>' identifier] identifier
    primitive         -> 'box' | 'grid' | 'sphere' | 'line' | 'point'
                      | 'Triangle' '[' coord {';' coord} ']'
    coord             -> float {',' float}
    transformation    -> ('x' | 'y' | 'z') float
                      | ('rx' | 'ry' | 'rz') float
                      | 's' (float | float float float)
                      | 'm' float{9}
                      | 'fx' | 'fy' | 'fz'
                      | ('h' | 'hue') float
                      | 'sat' float
                      | ('b' | 'brightness') float
                      | ('a' | 'alpha') float
                      | 'color' color_string
                      | 'blend' color_string float
"""

import re

from sverchok.utils.parsec import (
    parse_number,
    parse_whitespace,
    parse_word,
    one_of,
)
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
# Low-level parsers
# ---------------------------------------------------------------------------

# Identifier: starts with letter or underscore, followed by alphanumerics/underscores
_identifier_re = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*)", re.DOTALL)

# Integer
_int_re = re.compile(r"(-?(?:0|[1-9]\d*))\s*(.*)", re.DOTALL)

# Color string: hex (#xxx or #xxxxxx) or SVG keyword / quoted string
_color_re = re.compile(
    r"((?:#[0-9a-fA-F]{3,8})|(?:'[^']*')|(?:[a-zA-Z][a-zA-Z0-9]*))\s*(.*)",
    re.DOTALL,
)

def parse_int(src):
    """Parse an integer literal."""
    match = _int_re.match(src)
    if match:
        value, rest = match.groups()
        yield int(value), rest


def parse_identifier(src):
    """Parse an identifier."""
    match = _identifier_re.match(src)
    if match:
        name, rest = match.groups()
        yield name, rest


def parse_color_string(src):
    """Parse a color string (hex, SVG keyword, or quoted)."""
    match = _color_re.match(src)
    if match:
        color, rest = match.groups()
        # Strip quotes if present
        if color.startswith("'") and color.endswith("'"):
            color = color[1:-1]
        yield color, rest


# ---------------------------------------------------------------------------
# Transformation parsers
# ---------------------------------------------------------------------------
#
# Each transformation parser uses a regex to match the keyword + arguments,
# then yields the appropriate AST node and the remaining source string.
#
# Pattern: keyword followed by optional float arguments.
# We use regex for reliability since the parsec sequence combinator
# returns (tuple_of_results, rest) and we need the rest value.

# Regex for a numeric value: integer, decimal, scientific, or fraction (e.g. 1/3)
_num = r"-?(?:0|[1-9]\d*)"
_float_tok = r"" + _num + r"(?:\.\d+)?(?:[eE][+-]?\d+)?(?:\s*/\s*" + _num + r"(?:\.\d+)?)?"

# Translation: x/y/z <float>
_translate_x_re = re.compile(r"x\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)
_translate_y_re = re.compile(r"y\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)
_translate_z_re = re.compile(r"z\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)

# Rotation: rx/ry/rz <float>
_rotate_x_re = re.compile(r"rx\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)
_rotate_y_re = re.compile(r"ry\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)
_rotate_z_re = re.compile(r"rz\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)

# Scale: s <f> or s <f1> <f2> <f3>
_scale_re = re.compile(
    r"s\s+(" + _float_tok + r")\s*"
    r"(" + _float_tok + r")?\s*"
    r"(" + _float_tok + r")?\s*(.*)",
    re.DOTALL,
)

# Matrix: m <f1> ... <f9>
_matrix_re = re.compile(
    r"m\s+(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s+"
    r"(" + _float_tok + r")\s*(.*)",
    re.DOTALL,
)

# Mirror: fx/fy/fz
_mirror_x_re = re.compile(r"fx\s*(.*)", re.DOTALL)
_mirror_y_re = re.compile(r"fy\s*(.*)", re.DOTALL)
_mirror_z_re = re.compile(r"fz\s*(.*)", re.DOTALL)

# Hue: h|hue <float>
_hue_re = re.compile(r"(?:hue|h)\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)

# Saturation: sat <float>
_sat_re = re.compile(r"sat\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)

# Brightness: b|brightness <float>
_bright_re = re.compile(r"(?:brightness|b)\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)

# Alpha: a|alpha <float>
_alpha_re = re.compile(r"(?:alpha|a)\s+(" + _float_tok + r")\s*(.*)", re.DOTALL)

# Color: color <color_string>
_setcolor_re = re.compile(
    r"color\s+((?:#[0-9a-fA-F]{3,8})|(?:'[^']*')|(?:[a-zA-Z][a-zA-Z0-9]*))\s*(.*)",
    re.DOTALL,
)

# Blend: blend <color> <float>
_blend_re = re.compile(
    r"blend\s+((?:#[0-9a-fA-F]{3,8})|(?:'[^']*')|(?:[a-zA-Z][a-zA-Z0-9]*))\s+"
    r"(" + _float_tok + r")\s*(.*)",
    re.DOTALL,
)


def _to_float(s):
    """Convert a numeric string to float, supporting fractions like '1/3'."""
    if "/" in s:
        parts = s.split("/")
        return float(parts[0].strip()) / float(parts[1].strip())
    return float(s)


def _try_regex_parse(regex, src, factory):
    """Helper: try to match regex on src, yield factory(result), rest."""
    match = regex.match(src.lstrip())
    if match:
        groups = match.groups()
        yield factory(groups), groups[-1]  # last group is always rest


def parse_TranslateX(src):
    def make(g):
        return TranslateX(_to_float(g[0]))
    yield from _try_regex_parse(_translate_x_re, src, make)


def parse_TranslateY(src):
    def make(g):
        return TranslateY(_to_float(g[0]))
    yield from _try_regex_parse(_translate_y_re, src, make)


def parse_TranslateZ(src):
    def make(g):
        return TranslateZ(_to_float(g[0]))
    yield from _try_regex_parse(_translate_z_re, src, make)


def parse_RotateX(src):
    def make(g):
        return RotateX(_to_float(g[0]))
    yield from _try_regex_parse(_rotate_x_re, src, make)


def parse_RotateY(src):
    def make(g):
        return RotateY(_to_float(g[0]))
    yield from _try_regex_parse(_rotate_y_re, src, make)


def parse_RotateZ(src):
    def make(g):
        return RotateZ(_to_float(g[0]))
    yield from _try_regex_parse(_rotate_z_re, src, make)


def parse_Scale(src):
    def make(g):
        x = _to_float(g[0])
        y = _to_float(g[1]) if g[1] else None
        z = _to_float(g[2]) if g[2] else None
        return Scale(x, y, z)
    yield from _try_regex_parse(_scale_re, src, make)


def parse_MatrixTransform(src):
    def make(g):
        return MatrixTransform([_to_float(g[i]) for i in range(9)])
    yield from _try_regex_parse(_matrix_re, src, make)


def parse_MirrorX(src):
    def make(g):
        return MirrorX()
    yield from _try_regex_parse(_mirror_x_re, src, make)


def parse_MirrorY(src):
    def make(g):
        return MirrorY()
    yield from _try_regex_parse(_mirror_y_re, src, make)


def parse_MirrorZ(src):
    def make(g):
        return MirrorZ()
    yield from _try_regex_parse(_mirror_z_re, src, make)


def parse_HueShift(src):
    def make(g):
        return HueShift(_to_float(g[0]))
    yield from _try_regex_parse(_hue_re, src, make)


def parse_SaturationMul(src):
    def make(g):
        return SaturationMul(_to_float(g[0]))
    yield from _try_regex_parse(_sat_re, src, make)


def parse_BrightnessMul(src):
    def make(g):
        return BrightnessMul(_to_float(g[0]))
    yield from _try_regex_parse(_bright_re, src, make)


def parse_AlphaMul(src):
    def make(g):
        return AlphaMul(_to_float(g[0]))
    yield from _try_regex_parse(_alpha_re, src, make)


def parse_SetColor(src):
    def make(g):
        color = g[0]
        if color.startswith("'") and color.endswith("'"):
            color = color[1:-1]
        return SetColor(color)
    yield from _try_regex_parse(_setcolor_re, src, make)


def parse_BlendColor(src):
    def make(g):
        color = g[0]
        if color.startswith("'") and color.endswith("'"):
            color = color[1:-1]
        return BlendColor(color, _to_float(g[1]))
    yield from _try_regex_parse(_blend_re, src, make)


# ---------------------------------------------------------------------------
# Combined transformation parser
# ---------------------------------------------------------------------------

parse_transformation = one_of(
    parse_RotateX,
    parse_RotateY,
    parse_RotateZ,
    parse_Scale,
    parse_MatrixTransform,
    parse_HueShift,
    parse_SaturationMul,
    parse_BrightnessMul,
    parse_AlphaMul,
    parse_SetColor,
    parse_BlendColor,
    parse_TranslateX,
    parse_TranslateY,
    parse_TranslateZ,
    parse_MirrorX,
    parse_MirrorY,
    parse_MirrorZ,
)

# ---------------------------------------------------------------------------
# Primitive parsers
# ---------------------------------------------------------------------------

parse_Box = parse_word("box", Box())
parse_Grid = parse_word("grid", Grid())
parse_Sphere = parse_word("sphere", Sphere())
parse_Line = parse_word("line", Line())
parse_Point = parse_word("point", Point())


def parse_Triangle(src):
    """Parse 'Triangle[x1,y1,z1;x2,y2,z2;x3,y3,z3]'."""
    if not src.lstrip().startswith("Triangle["):
        return
    start = src.lstrip()
    offset = len(src) - len(start)
    inner_start = offset + len("Triangle[")
    bracket_end = start.find("]")
    if bracket_end == -1:
        return
    coords_str = start[len("Triangle["):bracket_end]
    rest = src[inner_start + bracket_end + 1:]

    vertices = []
    for vertex_str in coords_str.split(";"):
        vertex_str = vertex_str.strip()
        if not vertex_str:
            continue
        parts = vertex_str.split(",")
        x = float(parts[0].strip())
        y = float(parts[1].strip()) if len(parts) > 1 else 0.0
        z = float(parts[2].strip()) if len(parts) > 2 else 0.0
        vertices.append((x, y, z))

    if vertices:
        yield Triangle(vertices), rest.lstrip()


parse_primitive = one_of(
    parse_Triangle,
    parse_Box,
    parse_Grid,
    parse_Sphere,
    parse_Line,
    parse_Point,
)

# ---------------------------------------------------------------------------
# Rule reference parser
# ---------------------------------------------------------------------------

def parse_rule_ref_with_retirement(src):
    """
    Parse rule reference that may include 'md <int> ['> <id>']' prefix.
    Returns (RuleRef, rest).
    """
    src_stripped = src.lstrip()

    # Try 'md <int> ['> <id>'] <rulename>'
    md_re = re.compile(
        r"md\s+(-?\d+)\s*(?:>\s*([a-zA-Z_][a-zA-Z0-9_]*))?\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*)",
        re.DOTALL,
    )
    match = md_re.match(src_stripped)
    if match:
        depth, retirement_rule, name, rest = match.groups()
        yield RuleRef(name, int(depth), retirement_rule), rest.lstrip()
        return

    # Plain identifier as rule reference
    for name, rest in parse_identifier(src_stripped):
        if name not in ("rule", "set", "md", "maxdepth", "weight", "w"):
            yield RuleRef(name), rest.lstrip()


# ---------------------------------------------------------------------------
# Repetition parser
# ---------------------------------------------------------------------------

def _parse_transformations_from_string(inner_content):
    """Parse a list of transformations from a string."""
    _TRANSFORM_PARSERS = [
        parse_RotateX, parse_RotateY, parse_RotateZ,
        parse_Scale, parse_MatrixTransform,
        parse_HueShift, parse_SaturationMul,
        parse_BrightnessMul, parse_AlphaMul,
        parse_SetColor, parse_BlendColor,
        parse_TranslateX, parse_TranslateY, parse_TranslateZ,
        parse_MirrorX, parse_MirrorY, parse_MirrorZ,
    ]
    transforms = []
    current = inner_content.strip()
    while current:
        found = False
        for tf_parser in _TRANSFORM_PARSERS:
            for tf, remainder in tf_parser(current):
                transforms.append(tf)
                current = remainder.lstrip() if remainder else ""
                found = True
                break
            if found:
                break
        if not found:
            break
    return transforms


def parse_repetition(src):
    """Parse '<count> * { transformations... }'."""
    # Use regex to match: <int_or_id> * { <content> }
    # Use [^}]* to match content between { and } (non-nested)
    rep_int_re = re.compile(
        r"(-?(?:0|[1-9]\d*))\s*\*\s*\{([^}]*)\}\s*(.*)",
        re.DOTALL,
    )
    match = rep_int_re.match(src.lstrip())
    if match:
        count_str, inner, rest = match.groups()
        count = int(count_str)
        if count < 0:
            return
        transforms = _parse_transformations_from_string(inner)
        if transforms:
            yield Repeat(count, transforms), rest.lstrip()
            return

    # Try: identifier * { ... }
    rep_id_re = re.compile(
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\s*\{([^}]*)\}\s*(.*)",
        re.DOTALL,
    )
    match = rep_id_re.match(src.lstrip())
    if match:
        name, inner, rest = match.groups()
        transforms = _parse_transformations_from_string(inner)
        if transforms:
            yield Repeat(name, transforms), rest.lstrip()


# ---------------------------------------------------------------------------
# Transformation block parser (without repetition count)
# ---------------------------------------------------------------------------

def parse_transformation_block(src):
    """
    Parse a standalone transformation block: '{ transformations... }'
    This is used for branches like '{ y 1 h 12 a 0.9 rx 36 } r1'.
    """
    src_stripped = src.lstrip()
    if not src_stripped.startswith("{"):
        return

    # Find matching } (non-nested, use [^}]* pattern)
    block_re = re.compile(r"\{([^}]*)\}\s*(.*)", re.DOTALL)
    match = block_re.match(src_stripped)
    if match:
        inner, rest = match.groups()
        transforms = _parse_transformations_from_string(inner)
        if transforms:
            yield transforms, rest.lstrip()


# ---------------------------------------------------------------------------
# Branch parser
# ---------------------------------------------------------------------------

def parse_branch(src):
    """
    Parse a branch: (repetition | transform_block)* (rule_ref | primitive)

    A branch can contain:
    - Repetitions: 'N * { transforms }'
    - Transformation blocks: '{ transforms }' (without count)
    - Terminal: rule_ref or primitive
    """
    src_stripped = src.lstrip()

    # Collect repetitions and transformation blocks
    repetitions = []
    current = src_stripped
    while current:
        # Try repetition first (N * { ... })
        found = False
        for rep, remainder in parse_repetition(current):
            repetitions.append(rep)
            current = remainder.lstrip() if remainder else ""
            found = True
            break

        # Try transformation block ({ ... } without count)
        if not found:
            for transforms, remainder in parse_transformation_block(current):
                # Convert to a Repeat with count=1 for consistency
                repetitions.append(Repeat(1, transforms))
                current = remainder.lstrip() if remainder else ""
                found = True

        if not found:
            break

    if not current.strip():
        return

    # Parse terminal: rule_ref or primitive
    # Try primitives first (they are keywords)
    for prim, remainder in parse_primitive(current):
        yield Branch(repetitions, prim), remainder.lstrip() if remainder else ""
        return

    # Try rule reference
    for ref, remainder in parse_rule_ref_with_retirement(current):
        yield Branch(repetitions, ref), remainder.lstrip() if remainder else ""
        return


# ---------------------------------------------------------------------------
# Rule body parser
# ---------------------------------------------------------------------------

def _find_matching_brace(src, start_pos):
    """
    Find the position of the matching '}' for '{' at start_pos.
    Handles nested braces by tracking depth.
    Returns the position of the matching '}' or -1 if not found.
    """
    if start_pos >= len(src) or src[start_pos] != "{":
        return -1
    depth = 1
    i = start_pos + 1
    while i < len(src) and depth > 0:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
        i += 1
    if depth == 0:
        return i - 1  # Position of the matching '}'
    return -1


def parse_rule_body(src):
    """Parse the content inside '{' ... '}' of a rule definition."""
    src_stripped = src.lstrip()
    if not src_stripped.startswith("{"):
        return
    offset = len(src) - len(src_stripped)

    # Find matching closing brace with proper nesting
    close_pos = _find_matching_brace(src_stripped, 0)
    if close_pos == -1:
        return

    inner_content = src_stripped[1:close_pos]
    rest = src[offset + close_pos + 1:]

    # Parse branches from inner content
    branches = []
    current = inner_content.strip()
    while current:
        for branch, remainder in parse_branch(current):
            branches.append(branch)
            current = remainder.lstrip() if remainder else ""
            break
        else:
            # No more branches can be parsed
            break

    yield branches, rest.lstrip()


# ---------------------------------------------------------------------------
# Rule modifier parser
# ---------------------------------------------------------------------------

def parse_rule_modifier(src):
    """
    Parse rule modifiers:
        maxdepth <int> ['>' <id>]
        md <int> ['>' <id>]
        weight <float>
        w <float>
    Returns a dict of {name: value} or {name: (value, sub_rule)}.
    """
    src_stripped = src.lstrip()

    # maxdepth / md <int> ['>' <id>]
    md_re = re.compile(
        r"(?:maxdepth|md)\s+(-?\d+)\s*(?:>\s*([a-zA-Z_][a-zA-Z0-9_]*))?\s*(.*)",
        re.DOTALL,
    )
    match = md_re.match(src_stripped)
    if match:
        depth, retirement_rule, rest = match.groups()
        modifier = {"maxdepth": int(depth)}
        if retirement_rule:
            modifier["retirement_rule"] = retirement_rule
        yield modifier, rest.lstrip()
        return

    # weight / w <float>
    w_re = re.compile(
        r"(?:weight|w)\s+([-+]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(.*)",
        re.DOTALL,
    )
    match = w_re.match(src_stripped)
    if match:
        weight, rest = match.groups()
        yield {"weight": float(weight)}, rest.lstrip()
        return


# ---------------------------------------------------------------------------
# Rule definition parser
# ---------------------------------------------------------------------------

def parse_rule_definition(src):
    """
    Parse a rule definition:
        'rule'? identifier modifier* '{' rule_body '}'
    """
    src_stripped = src.lstrip()

    # Optional 'rule' keyword
    has_rule_kw = src_stripped.startswith("rule")
    if has_rule_kw:
        src_stripped = src_stripped[4:].lstrip()
    original_offset = len(src) - len(src.lstrip())

    # Rule name
    for name, after_name in parse_identifier(src_stripped):
        src_after = after_name.lstrip()

        # Parse modifiers
        maxdepth = None
        weight = None
        retirement_rule = None
        current = src_after
        while current:
            for mod, remainder in parse_rule_modifier(current):
                if "maxdepth" in mod:
                    maxdepth = mod["maxdepth"]
                if "retirement_rule" in mod:
                    retirement_rule = mod["retirement_rule"]
                if "weight" in mod:
                    weight = mod["weight"]
                current = remainder.lstrip()
                break
            else:
                break

        # Parse rule body
        for branches, rest in parse_rule_body(current):
            rule = Rule(
                name=name,
                maxdepth=maxdepth,
                retirement_rule=retirement_rule,
                weight=weight,
                body=branches,
            )
            yield rule, rest.lstrip()
            return


# ---------------------------------------------------------------------------
# Set statement parser
# ---------------------------------------------------------------------------

def parse_set_statement(src):
    """
    Parse 'set <name> <value>' statements.
    """
    src_stripped = src.lstrip()
    if not src_stripped.startswith("set"):
        return

    after_set = src_stripped[3:].lstrip()

    # Parse setting name
    for name, after_name in parse_identifier(after_set):
        after_name = after_name.lstrip()

        # Special multi-word settings
        if name == "seed" and after_name.startswith("initial"):
            yield SetStatement("seed", "initial"), after_name[len("initial"):]
            return

        if name == "background":
            for color, rest in parse_color_string(after_name):
                yield SetStatement("background", color), rest.lstrip()
                return

        if name == "color":
            # 'set color random'
            if after_name.startswith("random"):
                yield SetStatement("color", "random"), after_name[len("random"):]
                return
            # 'set color <color_value>' — absolute color as global setting
            for color, rest in parse_color_string(after_name):
                yield SetStatement("color", color), rest.lstrip()
                return

        if name == "colorpool":
            # Parse colorpool scheme (may contain colons, commas)
            match = re.match(
                r"([a-zA-Z][a-zA-Z0-9_:.,/=\[\]]*(?:\s*,\s*[a-zA-Z][a-zA-Z0-9_:.,/=\[\]]*)*)\s*(.*)",
                after_name,
                re.DOTALL,
            )
            if match:
                scheme, rest = match.groups()
                yield SetStatement("colorpool", scheme), rest.lstrip()
                return

        # Numeric settings
        for value, rest in parse_number(after_name):
            yield SetStatement(name, value), rest.lstrip()
            return

        # String settings
        for value, rest in parse_color_string(after_name):
            yield SetStatement(name, value), rest.lstrip()
            return


# ---------------------------------------------------------------------------
# Top-level statement parser
# ---------------------------------------------------------------------------

def parse_implicit_rule(src):
    """
    Parse an implicit rule definition:
        identifier
        branch

    This is shorthand for 'rule identifier { branch }'.
    The identifier and branch may be separated by newlines.
    """
    src_stripped = src.lstrip()

    # Get identifier
    for name, after_name in parse_identifier(src_stripped):
        after_name = after_name.lstrip()

        # Skip any blank lines between identifier and branch
        branch_src = after_name.lstrip()

        # Try to parse a branch
        for branch, rest in parse_branch(branch_src):
            rule = Rule(name=name, body=[branch])
            yield rule, rest.lstrip() if rest else ""
            return


def parse_top_statement(src):
    """Parse a top-level statement (set or rule definition)."""
    # Try set statement first
    for stmt, rest in parse_set_statement(src):
        yield stmt, rest
        return

    # Try explicit rule definition (with 'rule' keyword or modifiers)
    for rule, rest in parse_rule_definition(src):
        yield rule, rest
        return

    # Try implicit rule definition: identifier followed by branch
    for rule, rest in parse_implicit_rule(src):
        yield rule, rest
        return

    # Try implicit start rule: a bare branch without a rule name.
    # This is shorthand for 'rule start { branch }'.
    for branch, rest in parse_branch(src):
        rule = Rule(name="start", body=[branch])
        yield rule, rest.lstrip() if rest else ""
        return


# ---------------------------------------------------------------------------
# Program parser
# ---------------------------------------------------------------------------

def _strip_comments(source):
    """
    Remove comments from EisenScript source.
    Handles '//' line comments and '/* ... */' block comments.
    """
    result = []
    i = 0
    in_block_comment = False

    while i < len(source):
        if in_block_comment:
            if source[i:i + 2] == "*/":
                in_block_comment = False
                i += 2
            else:
                i += 1
        else:
            if source[i:i + 2] == "//":
                # Skip to end of line
                while i < len(source) and source[i] != "\n":
                    i += 1
            elif source[i:i + 2] == "/*":
                in_block_comment = True
                i += 2
            else:
                result.append(source[i])
                i += 1

    return "".join(result)


def parse(source, check_full=True):
    """
    Parse an EisenScript source string into a Program AST.

    Args:
        source: EisenScript source code string.
        check_full: If True, raise an error if not all input is consumed.

    Returns:
        Program AST node.

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    # Strip comments
    cleaned = _strip_comments(source)

    # Parse all top-level statements
    statements = []
    current = cleaned.strip()

    while current:
        for stmt, rest in parse_top_statement(current):
            statements.append(stmt)
            current = rest.strip() if rest else ""
            break
        else:
            if current.strip():
                raise SyntaxError(f"Cannot parse: {current[:50]!r}")
            break

    # Separate settings and rules
    settings = []
    rules = []
    for stmt in statements:
        if isinstance(stmt, SetStatement):
            settings.append(stmt)
        elif isinstance(stmt, Rule):
            rules.append(stmt)
        else:
            settings.append(stmt)

    return Program(settings=settings, rules=rules)
