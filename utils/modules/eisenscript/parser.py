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
    program           -> (input_stmt | define_stmt | set_statement
                         | rule_definition | implicit_start)*
    input_stmt        -> '#input' identifier ['number'] [number]
    define_stmt       -> '#define' identifier (number | expr)
    set_statement     -> 'set' setting_name value*
    rule_definition   -> 'rule' identifier param_list? modifier* '{' rule_body '}'
    param_list        -> '(' identifier {',' identifier} ')'
    implicit_start    -> branch  // bare branch → rule 'start' { branch }
    rule_modifier     -> ('maxdepth' | 'md') value ['>' identifier]
                      | ('weight' | 'w') value
    rule_body         -> branch*
    branch            -> (repetition | transform_block)* (rule_ref | primitive)
    repetition        -> count '*' '{' transformation+ '}'
    transform_block   -> '{' transformation+ '}'
    count             -> int | identifier | expr
    rule_ref          -> identifier arg_list? | 'md' value ['>' identifier] identifier
    arg_list          -> '(' value {',' value} ')'
    primitive         -> 'box' | 'grid' | 'sphere' | 'line' | 'point'
                      | 'Triangle' '[' coord {';' coord} ']'
    coord             -> float {',' float}
    transformation    -> ('x' | 'y' | 'z') value
                      | ('rx' | 'ry' | 'rz') value
                      | 's' (value | value value value)
                      | 'm' value{9}
                      | 'fx' | 'fy' | 'fz'
                      | ('h' | 'hue') value
                      | 'sat' value
                      | ('b' | 'brightness') value
                      | ('a' | 'alpha') value
                      | 'color' color_string
                      | 'blend' color_string value
    value             -> float | identifier | expr
    expr              -> '(' python_expression ')'
"""

import ast
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
# Expression parser
# ---------------------------------------------------------------------------

def _find_matching_paren(src, start):
    """
    Find the index of the closing ')' that matches '(' at position *start*.

    Handles nested parentheses correctly.  Returns the index of the
    matching ')' or ``-1`` if no match is found.
    """
    if start >= len(src) or src[start] != '(':
        return -1
    depth = 1
    i = start + 1
    while i < len(src) and depth > 0:
        if src[i] == '(':
            depth += 1
        elif src[i] == ')':
            depth -= 1
        i += 1
    if depth == 0:
        return i - 1
    return -1


def parse_expression(src):
    """
    Parse a parenthesized Python expression: ``( <python_expr> )``.

    Yields ``(Expr, rest)`` on success.  Raises ``SyntaxError`` if the
    inner content is not valid Python.
    """
    stripped = src.lstrip()
    if not stripped.startswith('('):
        return

    close = _find_matching_paren(stripped, 0)
    if close == -1:
        return  # unbalanced parens — not an expression

    inner = stripped[1:close]
    rest = stripped[close + 1:]

    # Validate the inner content as a Python expression
    try:
        ast_node = ast.parse(inner, mode='eval')
    except SyntaxError as e:
        raise SyntaxError(f"Invalid expression: {inner!r}") from e

    yield Expr(inner, ast_node), rest.lstrip()


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
_float_tok = _num + r"(?:\.\d+)?(?:[eE][+-]?\d+)?(?:\s*/\s*" + _num + r"(?:\.\d+)?)?"
# Extended token: number or identifier (for variable references)
# Exclude known transformation keywords to avoid matching 'rz' as a variable in 's 0.9 rz 5'
_transform_kw = r"(?:x|y|z|rx|ry|rz|s|m|fx|fy|fz|hue|h|sat|brightness|b|alpha|a|color|blend)"
_num_or_id = r"(?:" + _float_tok + r"|(?!" + _transform_kw + r"\b)[a-zA-Z_][a-zA-Z0-9_]*)"

# Translation: x/y/z <float>
_translate_x_re = re.compile(r"x\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)
_translate_y_re = re.compile(r"y\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)
_translate_z_re = re.compile(r"z\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)

# Rotation: rx/ry/rz <float>
_rotate_x_re = re.compile(r"rx\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)
_rotate_y_re = re.compile(r"ry\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)
_rotate_z_re = re.compile(r"rz\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)

# Scale: s <f> or s <f1> <f2> <f3>
_scale_re = re.compile(
    r"s\s+(" + _num_or_id + r")\s*"
    r"(" + _num_or_id + r")?\s*"
    r"(" + _num_or_id + r")?\s*(.*)",
    re.DOTALL,
)

# Matrix: m <f1> ... <f9>
_matrix_re = re.compile(
    r"m\s+(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s+"
    r"(" + _num_or_id + r")\s*(.*)",
    re.DOTALL,
)

# Mirror: fx/fy/fz
_mirror_x_re = re.compile(r"fx\s*(.*)", re.DOTALL)
_mirror_y_re = re.compile(r"fy\s*(.*)", re.DOTALL)
_mirror_z_re = re.compile(r"fz\s*(.*)", re.DOTALL)

# Hue: h|hue <float>
_hue_re = re.compile(r"(?:hue|h)\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)

# Saturation: sat <float>
_sat_re = re.compile(r"sat\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)

# Brightness: b|brightness <float>
_bright_re = re.compile(r"(?:brightness|b)\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)

# Alpha: a|alpha <float>
_alpha_re = re.compile(r"(?:alpha|a)\s+(" + _num_or_id + r")\s*(.*)", re.DOTALL)

# Color: color <color_string>
_setcolor_re = re.compile(
    r"color\s+((?:#[0-9a-fA-F]{3,8})|(?:'[^']*')|(?:[a-zA-Z][a-zA-Z0-9]*))\s*(.*)",
    re.DOTALL,
)

# Blend: blend <color> <float>
_blend_re = re.compile(
    r"blend\s+((?:#[0-9a-fA-F]{3,8})|(?:'[^']*')|(?:[a-zA-Z][a-zA-Z0-9]*))\s+"
    r"(" + _num_or_id + r")\s*(.*)",
    re.DOTALL,
)


def _to_float(s):
    """Convert a numeric string to float, supporting fractions like '1/3'."""
    if "/" in s:
        parts = s.split("/")
        return float(parts[0].strip()) / float(parts[1].strip())
    return float(s)


def _to_num_or_var(s):
    """
    Convert a string to either a float or a VariableRef.

    If the string is a valid number (int, float, fraction), returns the float.
    If the string is an identifier, returns a VariableRef.
    """
    try:
        return _to_float(s)
    except (ValueError, ZeroDivisionError):
        pass
    return VariableRef(s)


# ---------------------------------------------------------------------------
# Unified value parser: tries expression first, then number/variable
# ---------------------------------------------------------------------------

def _parse_value(src):
    """
    Parse a value token from *src*: expression, number, or variable.

    Returns ``(value, rest)`` where *value* is one of:
    - ``Expr``       — parenthesized Python expression
    - ``float``      — numeric literal (int, float, fraction)
    - ``VariableRef`` — identifier (variable reference)

    Raises ``SyntaxError`` on invalid expression syntax.

    Note: identifiers that match transformation keywords (x, y, z, rx, ry,
    rz, s, m, fx, fy, fz, hue, h, sat, brightness, b, alpha, a, color,
    blend) are NOT accepted as variable references — they are reserved
    for transformation keywords.  Use an expression ``(a)`` instead if
    you need a variable with such a name.
    """
    stripped = src.lstrip()

    # 1. Try parenthesized expression
    if stripped.startswith('('):
        for expr, rest in parse_expression(stripped):
            return expr, rest

    # 2. Try number or identifier (exclude transformation keywords)
    match = re.match(r"(" + _num_or_id + r")\s*(.*)", stripped, re.DOTALL)
    if match:
        token, rest = match.groups()
        return _to_num_or_var(token), rest.lstrip()

    return None, src  # no match


def _parse_value_any(src):
    """
    Parse a value token from *src* accepting ANY identifier (including
    transformation keywords like 'a', 'b', 'x').

    Used AFTER a transformation keyword has been consumed, where the
    next token is unambiguously a value (e.g. after 'x' in 'x a').

    Returns ``(value, rest)`` or ``(None, src)``.
    """
    stripped = src.lstrip()

    # 1. Try parenthesized expression
    if stripped.startswith('('):
        for expr, rest in parse_expression(stripped):
            return expr, rest

    # 2. Try number or plain identifier (no keyword exclusion)
    match = re.match(
        r"(" + _float_tok + r"|[a-zA-Z_][a-zA-Z0-9_]*)\s*(.*)",
        stripped,
        re.DOTALL,
    )
    if match:
        token, rest = match.groups()
        return _to_num_or_var(token), rest.lstrip()

    return None, src  # no match


# ---------------------------------------------------------------------------
# Keyword-matching helpers
# ---------------------------------------------------------------------------

def _starts_with_kw(src, *keywords):
    """Check if *src* (stripped) starts with one of the given keywords.

    Returns ``(keyword, remainder)`` or ``(None, stripped_src)``.
    """
    s = src.lstrip()
    for kw in keywords:
        if s.startswith(kw):
            after = s[len(kw):]
            if not after or after[0].isspace() or after[0] == '(':
                return kw, after
    return None, s


# ---------------------------------------------------------------------------
# Transformation parsers (keyword-first, value via _parse_value)
# ---------------------------------------------------------------------------


def parse_TranslateX(src):
    kw, after = _starts_with_kw(src, 'x')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield Translate(AXIS_X, val), rest


def parse_TranslateY(src):
    kw, after = _starts_with_kw(src, 'y')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield Translate(AXIS_Y, val), rest


def parse_TranslateZ(src):
    kw, after = _starts_with_kw(src, 'z')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield Translate(AXIS_Z, val), rest


def parse_RotateX(src):
    kw, after = _starts_with_kw(src, 'rx')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield Rotate(AXIS_X, val), rest


def parse_RotateY(src):
    kw, after = _starts_with_kw(src, 'ry')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield Rotate(AXIS_Y, val), rest


def parse_RotateZ(src):
    kw, after = _starts_with_kw(src, 'rz')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield Rotate(AXIS_Z, val), rest


def parse_Scale(src):
    """Parse 's <v>' or 's <v1> <v2> <v3>'.

    Uses _parse_value which excludes transformation keywords (x, y, z, rx, ry,
    rz, s, h, b, a, etc.) to avoid ambiguity.  If you need a variable whose
    name matches a keyword as a scale value, wrap it in an expression:
    ``s (x) (y) 1`` instead of ``s x y 1``.
    """
    s = src.lstrip()
    if not s.startswith('s'):
        return
    after = s[1:]
    # Make sure 's' is a standalone keyword (not 'sat', 'scale', etc.)
    if after and not (after[0].isspace() or after[0] == '('):
        return
    val1, rest = _parse_value(after)
    if val1 is None:
        return
    # Try to parse second value
    val2, rest2 = _parse_value(rest)
    if val2 is not None:
        # Try to parse third value
        val3, rest3 = _parse_value(rest2)
        if val3 is not None:
            yield Scale(val1, val2, val3), rest3.lstrip()
            return
        yield Scale(val1, val2), rest2.lstrip()
        return
    yield Scale(val1), rest.lstrip()


def parse_MatrixTransform(src):
    s = src.lstrip()
    if not s.startswith('m'):
        return
    after = s[1:]
    # Make sure 'm' is standalone (not 'md', 'maxdepth', etc.)
    if after and not (after[0].isspace() or after[0] == '('):
        return
    values = []
    current = after
    for _ in range(9):
        val, current = _parse_value(current)
        if val is None:
            return
        values.append(val)
    yield MatrixTransform(values), current.lstrip()


def parse_MirrorX(src):
    s = src.lstrip()
    if s.startswith('fx'):
        after = s[2:]
        if not after or after[0].isspace():
            yield Mirror(AXIS_X), after.lstrip()


def parse_MirrorY(src):
    s = src.lstrip()
    if s.startswith('fy'):
        after = s[2:]
        if not after or after[0].isspace():
            yield Mirror(AXIS_Y), after.lstrip()


def parse_MirrorZ(src):
    s = src.lstrip()
    if s.startswith('fz'):
        after = s[2:]
        if not after or after[0].isspace():
            yield Mirror(AXIS_Z), after.lstrip()


def parse_HueShift(src):
    kw, after = _starts_with_kw(src, 'hue', 'h')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield HueShift(val), rest


def parse_SaturationMul(src):
    kw, after = _starts_with_kw(src, 'sat')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield SaturationMul(val), rest


def parse_BrightnessMul(src):
    kw, after = _starts_with_kw(src, 'brightness', 'b')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield BrightnessMul(val), rest


def parse_AlphaMul(src):
    kw, after = _starts_with_kw(src, 'alpha', 'a')
    if kw is None:
        return
    val, rest = _parse_value_any(after)
    if val is None:
        return
    yield AlphaMul(val), rest


def parse_SetColor(src):
    s = src.lstrip()
    if not s.startswith('color'):
        return
    after = s[5:].lstrip()
    for color, rest in parse_color_string(after):
        yield SetColor(color), rest


def parse_BlendColor(src):
    s = src.lstrip()
    if not s.startswith('blend'):
        return
    after = s[5:].lstrip()
    for color, rest in parse_color_string(after):
        val, rest2 = _parse_value_any(rest)
        if val is None:
            return
        yield BlendColor(color, val), rest2


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

def _parse_arg_list(src):
    """
    Parse a parenthesized, comma-separated argument list: ``(arg1, arg2, ...)``.

    Each argument is a value: expression, number, or variable.
    Handles nested parentheses inside expressions correctly.

    Returns a list of argument values (Expr, float, or VariableRef),
    or None if the source doesn't start with '('.
    """
    s = src.lstrip()
    if not s.startswith('('):
        return None

    close = _find_matching_paren(s, 0)
    if close == -1:
        return None

    inner = s[1:close].strip()
    rest = s[close + 1:].lstrip()

    # Empty parens () — no arguments
    if not inner:
        return []

    # Split by commas (respecting nested parens)
    args = []
    depth = 0
    current = []
    for ch in inner:
        if ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            token = ''.join(current).strip()
            if token:
                val, _ = _parse_value_any(token)
                if val is not None:
                    args.append(val)
            current = []
        else:
            current.append(ch)
    # Last token
    token = ''.join(current).strip()
    if token:
        val, _ = _parse_value_any(token)
        if val is not None:
            args.append(val)

    return args


def _parse_param_list(src):
    """
    Parse a parenthesized, comma-separated parameter list:
    ``(p1, p2, ...)`` where each element is an identifier.

    Returns a list of parameter name strings, or None if not a param list.
    """
    s = src.lstrip()
    if not s.startswith('('):
        return None

    close = _find_matching_paren(s, 0)
    if close == -1:
        return None

    inner = s[1:close].strip()
    rest = s[close + 1:].lstrip()

    # Empty parens () — no parameters
    if not inner:
        return []

    params = []
    for token_str in inner.split(','):
        token_str = token_str.strip()
        if not token_str:
            continue
        for name, _ in parse_identifier(token_str):
            params.append(name)
            break
        else:
            return None  # Not a valid identifier

    return params


def parse_rule_ref_with_retirement(src):
    """
    Parse rule reference that may include 'md <value> ['> <id>']' prefix
    and optional argument list '(arg1, arg2, ...)'.
    Returns (RuleRef, rest).
    """
    src_stripped = src.lstrip()

    # Try 'md <value> ['> <id>'] <rulename>'
    if src_stripped.startswith('md'):
        after = src_stripped[2:]
        val, rest = _parse_value(after)
        if val is not None:
            retirement_rule = None
            rest_stripped = rest.lstrip()
            if rest_stripped.startswith('>'):
                rest_stripped = rest_stripped[1:].lstrip()
                for name2, rest2 in parse_identifier(rest_stripped):
                    retirement_rule = name2
                    rest_stripped = rest2
            # Now parse the rule name
            for name, rest3 in parse_identifier(rest_stripped):
                retirement_depth = None
                if isinstance(val, float) and val == int(val):
                    retirement_depth = int(val)
                else:
                    retirement_depth = val
                yield RuleRef(name, retirement_depth=retirement_depth,
                              retirement_rule=retirement_rule), rest3.lstrip()
                return
        return

    # Plain identifier as rule reference, optionally followed by (args)
    for name, rest in parse_identifier(src_stripped):
        if name in ("rule", "set", "md", "maxdepth", "weight", "w"):
            continue

        rest_stripped = rest.lstrip()
        args = []

        # Check for argument list (args) after the identifier
        if rest_stripped.startswith('('):
            parsed_args = _parse_arg_list(rest_stripped)
            if parsed_args is not None:
                args = parsed_args
                # Find the rest after the closing paren
                close = _find_matching_paren(rest_stripped, 0)
                if close != -1:
                    rest = rest_stripped[close + 1:]
                else:
                    rest = rest_stripped

        yield RuleRef(name, args=args), rest.lstrip()


# ---------------------------------------------------------------------------
# Repetition parser
# ---------------------------------------------------------------------------

def _parse_transformations_from_string(inner_content):
    """
    Parse a list of transformations from a string.

    Uses the shared ``parse_transformation`` combinator so that the
    parser list is defined in exactly one place (see P1 fix).

    Raises SyntaxError if any unrecognized token is encountered.
    """
    transforms = []
    current = inner_content.strip()
    while current:
        result = list(parse_transformation(current))
        if not result:
            # Extract the offending token for a clear error message
            token = current.split()[0] if current.split() else current.strip()
            raise SyntaxError(f"Unknown transformation: '{token}'")
        tf, remainder = result[0]
        transforms.append(tf)
        current = remainder.lstrip() if remainder else ""
    return transforms


def _extract_brace_block(src):
    """
    Extract content between '{' and '}' from *src*.

    Returns ``(inner_content, rest_after_brace)`` or ``(None, None)``.
    Uses [^}]* (non-nested) since repetition blocks are always shallow.
    """
    s = src.lstrip()
    if not s.startswith('{'):
        return None, None
    close = s.find('}')
    if close == -1:
        return None, None
    return s[1:close], s[close + 1:]


def parse_repetition(src):
    """
    Parse '<count> * { transformations... }'.

    The content between { and } is matched with [^}]* (non-nested).
    This is intentional: EisenScript repetitions never contain nested
    braces — the inner block holds only a flat sequence of
    transformations.  Rule bodies use _find_matching_brace for proper
    nesting, but repetition blocks are always shallow (P3).
    """
    s = src.lstrip()

    # Try: expression * { ... }
    if s.startswith('('):
        for count, after_expr in parse_expression(s):
            after_star = after_expr.lstrip()
            if after_star.startswith('*'):
                after_star = after_star[1:].lstrip()
                inner, rest = _extract_brace_block(after_star)
                if inner is not None:
                    transforms = _parse_transformations_from_string(inner)
                    yield Repeat(count, transforms), rest.lstrip()
                    return
        return

    # Try: integer * { ... }
    rep_int_re = re.compile(
        r"(-?(?:0|[1-9]\d*))\s*\*\s*\{([^}]*)\}\s*(.*)",
        re.DOTALL,
    )
    match = rep_int_re.match(s)
    if match:
        count_str, inner, rest = match.groups()
        count = int(count_str)
        if count < 0:
            raise SyntaxError(f"Negative repetition count: {count}")
        transforms = _parse_transformations_from_string(inner)
        yield Repeat(count, transforms), rest.lstrip()
        return

    # Try: identifier * { ... } (variable reference as count)
    rep_id_re = re.compile(
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\s*\{([^}]*)\}\s*(.*)",
        re.DOTALL,
    )
    match = rep_id_re.match(s)
    if match:
        name, inner, rest = match.groups()
        transforms = _parse_transformations_from_string(inner)
        yield Repeat(VariableRef(name), transforms), rest.lstrip()


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
        maxdepth <value> ['>' <id>]
        md <value> ['>' <id>]
        weight <value>
        w <value>

    <value> can be a number, variable, or parenthesized expression.

    Returns a dict of {name: value} or {name: (value, sub_rule)}.
    """
    src_stripped = src.lstrip()

    # maxdepth / md <value> ['>' <id>]
    kw, after = _starts_with_kw(src_stripped, 'maxdepth', 'md')
    if kw is not None:
        val, rest = _parse_value(after)
        if val is None:
            return
        # Check for optional '> <id>'
        retirement_rule = None
        rest_stripped = rest.lstrip()
        if rest_stripped.startswith('>'):
            rest_stripped = rest_stripped[1:].lstrip()
            for name, rest2 in parse_identifier(rest_stripped):
                retirement_rule = name
                rest = rest2
        modifier = {"maxdepth": val}
        if retirement_rule:
            modifier["retirement_rule"] = retirement_rule
        yield modifier, rest.lstrip()
        return

    # weight / w <value>
    kw, after = _starts_with_kw(src_stripped, 'weight', 'w')
    if kw is not None:
        val, rest = _parse_value(after)
        if val is None:
            return
        yield {"weight": val}, rest.lstrip()
        return


# ---------------------------------------------------------------------------
# Rule definition parser
# ---------------------------------------------------------------------------

def parse_rule_definition(src):
    """
    Parse a rule definition:
        'rule' identifier ['(' param {',' param} ')'] modifier* '{' rule_body '}'

    Requires the 'rule' keyword to distinguish from implicit rule definitions
    (identifier(params)\nbranch) and bare branches (identifier(args)).
    """
    src_stripped = src.lstrip()

    # Require 'rule' keyword
    if not src_stripped.startswith("rule"):
        return
    src_stripped = src_stripped[4:].lstrip()

    # Rule name
    for name, after_name in parse_identifier(src_stripped):
        src_after = after_name.lstrip()

        # Optional parameter list (p1, p2, ...)
        params = []
        if src_after.startswith('('):
            parsed_params = _parse_param_list(src_after)
            if parsed_params is None:
                return  # Invalid param list — not a rule definition
            params = parsed_params
            close = _find_matching_paren(src_after, 0)
            if close != -1:
                src_after = src_after[close + 1:].lstrip()

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
                params=params,
                maxdepth=maxdepth,
                retirement_rule=retirement_rule,
                weight=weight,
                body=branches,
            )
            yield rule, rest.lstrip()
            return


# ---------------------------------------------------------------------------
# Define statement parser
# ---------------------------------------------------------------------------

def parse_input_statement(src):
    """
    Parse '#input <name> [number] [default_value]' statements.

    *name* is an identifier.
    *number* is an optional type keyword (currently the only supported type).
    *default_value* is an optional numeric literal (int, float, fraction).

    Returns an :class:`InputDef` and the remaining source.
    """
    from sverchok.utils.modules.eisenscript.ast import InputDef

    src_stripped = src.lstrip()
    if not src_stripped.startswith("#input"):
        return

    after_kw = src_stripped[len("#input"):].lstrip()

    # Parse identifier
    for name, after_name in parse_identifier(after_kw):
        after_name = after_name.lstrip()

        # Optional type keyword 'number'
        if after_name.startswith("number"):
            after_type = after_name[len("number"):]
            if not after_type or after_type[0].isspace():
                after_name = after_type.lstrip()
            else:
                return  # 'number' not a standalone keyword here

        # Optional default value (numeric only, no expressions/variables)
        default_value = None
        if after_name:
            for val, rest in _parse_numeric_value(after_name):
                default_value = val
                yield InputDef(name, default_value), rest.lstrip()
                return

        # No default value provided
        yield InputDef(name, None), after_name
        return


def parse_define_statement(src):
    """
    Parse '#define <identifier> <value>' statements.

    *value* can be a numeric literal (int, float, fraction) or a
    parenthesized Python expression.

    Returns a tuple of (name, value) and the remaining source.
    *value* is either a ``float`` or an :class:`Expr` node.
    """
    src_stripped = src.lstrip()
    if not src_stripped.startswith("#define"):
        return

    after_kw = src_stripped[len("#define"):].lstrip()

    # Parse identifier
    for name, after_name in parse_identifier(after_kw):
        after_name = after_name.lstrip()

        # Try expression first
        if after_name.startswith('('):
            for val, rest in parse_expression(after_name):
                yield (name, val), rest.lstrip()
                return

        # Fall back to numeric value
        for val, rest in _parse_numeric_value(after_name):
            yield (name, val), rest.lstrip()
            return


def _parse_numeric_value(src):
    """Parse a numeric value: integer, float, or fraction."""
    num = r"-?(?:0|[1-9]\d*)"
    frac = num + r"(?:\.\d+)?(?:[eE][+-]?\d+)?(?:\s*/\s*" + num + r"(?:\.\d+)?)?"
    match = re.match(rf"({frac})\s*(.*)", src.lstrip(), re.DOTALL)
    if match:
        yield _to_float(match.group(1)), match.group(2)
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
        identifier ['(' param {',' param} ')']
        branch

    This is shorthand for 'rule identifier(params) { branch }'.
    The identifier and branch may be separated by newlines.

    If the identifier is followed by '(' that doesn't contain valid
    parameter names (identifiers), the '(' is NOT consumed — the
    branch parser will handle 'identifier(args)' as a rule call.

    IMPORTANT: if the branch starts with the same identifier (e.g.
    'foo' followed by 'foo(1)'), this is NOT an implicit rule —
    it's a bare branch.  The implicit rule 'foo' would be recursive
    (foo → foo), which is almost certainly not intended.
    """
    src_stripped = src.lstrip()

    # Get identifier
    for name, after_name in parse_identifier(src_stripped):
        src_after = after_name.lstrip()

        # Optional parameter list (p1, p2, ...)
        # Only consume if it's actually a valid param list (all identifiers)
        params = []
        if src_after.startswith('('):
            parsed_params = _parse_param_list(src_after)
            if parsed_params is not None:
                params = parsed_params
                close = _find_matching_paren(src_after, 0)
                if close != -1:
                    src_after = src_after[close + 1:].lstrip()
            # else: not a param list — leave src_after as-is
            # The branch parser will handle 'name(args)' as a rule call

        # Skip any blank lines between identifier and branch
        branch_src = src_after.lstrip()

        # Guard: if the branch starts with the same identifier, this is
        # NOT an implicit rule definition (would be recursive: foo → foo).
        # Let the caller handle it as a bare branch instead.
        if branch_src.startswith(name):
            after_name_check = branch_src[len(name):]
            if not after_name_check or after_name_check[0] in (' ', '\t', '\n', '\r', '(', '*'):
                return  # Not an implicit rule — looks like 'name name(...)' or 'name\nname'

        # Try to parse a branch
        for branch, rest in parse_branch(branch_src):
            rule = Rule(name=name, params=params, body=[branch])
            yield rule, rest.lstrip() if rest else ""
            return


def parse_top_statement(src):
    """Parse a top-level statement (input, define, set or rule definition)."""
    # Try #input first
    for result, rest in parse_input_statement(src):
        yield result, rest
        return

    # Try #define
    for result, rest in parse_define_statement(src):
        yield result, rest
        return

    # Try set statement
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
        rule = Rule(name=IMPLICIT_START_RULE, body=[branch])
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

    # Separate inputs, defines, settings and rules
    from sverchok.utils.modules.eisenscript.ast import InputDef

    inputs = {}
    defines = {}
    settings = []
    rules = []
    for stmt in statements:
        if isinstance(stmt, InputDef):
            inputs[stmt.name] = stmt
        elif isinstance(stmt, tuple) and len(stmt) == 2:
            # Define statement: (name, value)
            defines[stmt[0]] = stmt[1]
        elif isinstance(stmt, SetStatement):
            settings.append(stmt)
        elif isinstance(stmt, Rule):
            rules.append(stmt)
        else:
            settings.append(stmt)

    # Check for name conflicts between #input and #define
    conflicts = set(inputs.keys()) & set(defines.keys())
    if conflicts:
        raise SyntaxError(
            f"Name conflict between #input and #define: {', '.join(sorted(conflicts))}. "
            f"A name can be declared in either #input or #define, but not both."
        )

    # Merge multiple IMPLICIT_START_RULE rules into one.
    # Each bare branch creates a separate Rule(IMPLICIT_START_RULE),
    # but they should all be branches of a single start rule.
    start_rule = None
    other_rules = []
    for rule in rules:
        if rule.name == IMPLICIT_START_RULE:
            if start_rule is None:
                start_rule = rule
            else:
                start_rule.body.extend(rule.body)
        else:
            other_rules.append(rule)

    if start_rule is not None:
        rules = [start_rule] + other_rules
    else:
        rules = other_rules

    return Program(inputs=inputs, defines=defines, settings=settings, rules=rules)
