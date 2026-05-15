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
Tests for EisenScript expression support (parenthesized Python expressions).

Expressions are enclosed in parentheses and parsed as Python expressions
via ``ast.parse(mode='eval')``.  At interpretation time they are evaluated
with ``eval()`` using a safe namespace (math functions, constants, and
#define variables).

Syntax::

    1 * { x (a + 1) y (sin(t)) } box
    (n * 2) * { x 1 } box
    rule tree md (depth * 2) { box }
"""

import unittest
import sys
import os

# Add project root to path for standalone execution
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sverchok.utils.modules.eisenscript.parser import (
    parse,
    parse_expression,
    _find_matching_paren,
)
from sverchok.utils.modules.eisenscript.ast import (
    Expr,
    VariableRef,
    AXIS_X, AXIS_Y, AXIS_Z,
    Translate,
    Rotate,
    Scale,
    MatrixTransform,
    HueShift,
    SaturationMul,
    BrightnessMul,
    AlphaMul,
    BlendColor,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_transforms(code):
    """Helper: parse transformations from a block '{ code }'."""
    from sverchok.utils.modules.eisenscript.parser import parse_transformation_block
    for transforms, _ in parse_transformation_block(f"{{{code}}}"):
        return transforms
    raise AssertionError(f"No transformations parsed from: {code!r}")


# ---------------------------------------------------------------------------
# Expression AST tests
# ---------------------------------------------------------------------------

class ExpressionAstTests(unittest.TestCase):
    """Test the Expr AST node."""

    def test_expr_creation(self):
        import ast
        ast_node = ast.parse("a + b", mode='eval')
        expr = Expr("a + b", ast_node)
        self.assertEqual(expr.source, "a + b")
        self.assertEqual(repr(expr), "Expr('a + b')")

    def test_expr_equality(self):
        import ast
        a = Expr("x * 2", ast.parse("x * 2", mode='eval'))
        b = Expr("x * 2", ast.parse("x * 2", mode='eval'))
        c = Expr("x + 2", ast.parse("x + 2", mode='eval'))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_expr_get_variables(self):
        import ast
        expr = Expr("a + b * c", ast.parse("a + b * c", mode='eval'))
        vars = expr.get_variables()
        self.assertEqual(vars, {"a", "b", "c"})


# ---------------------------------------------------------------------------
# Expression parser tests
# ---------------------------------------------------------------------------

class ExpressionParserTests(unittest.TestCase):
    """Test parsing of parenthesized Python expressions."""

    def test_simple_expression(self):
        results = list(parse_expression("(a + b)"))
        self.assertEqual(len(results), 1)
        expr, rest = results[0]
        self.assertIsInstance(expr, Expr)
        self.assertEqual(expr.source, "a + b")
        self.assertEqual(rest.strip(), "")

    def test_nested_parentheses(self):
        results = list(parse_expression("((a + b) * c)"))
        self.assertEqual(len(results), 1)
        expr, _ = results[0]
        self.assertEqual(expr.source, "(a + b) * c")

    def test_expression_with_function_call(self):
        results = list(parse_expression("(sin(t))"))
        self.assertEqual(len(results), 1)
        expr, _ = results[0]
        self.assertEqual(expr.source, "sin(t)")

    def test_expression_with_nested_calls(self):
        results = list(parse_expression("(sqrt(a*a + b*b))"))
        self.assertEqual(len(results), 1)
        expr, _ = results[0]
        self.assertEqual(expr.source, "sqrt(a*a + b*b)")

    def test_invalid_expression_raises_syntax_error(self):
        with self.assertRaises(SyntaxError):
            list(parse_expression("(a + )"))

    def test_unbalanced_parens_not_matched(self):
        results = list(parse_expression("(a + b"))
        self.assertEqual(len(results), 0)

    def test_find_matching_paren(self):
        self.assertEqual(_find_matching_paren("(a)", 0), 2)
        self.assertEqual(_find_matching_paren("((a))", 0), 4)
        self.assertEqual(_find_matching_paren("(a(b))", 0), 5)
        self.assertEqual(_find_matching_paren("a(b)", 0), -1)
        self.assertEqual(_find_matching_paren("(a+b", 0), -1)

    def test_expression_with_rest(self):
        results = list(parse_expression("(a + b) rz 10"))
        self.assertEqual(len(results), 1)
        expr, rest = results[0]
        self.assertEqual(expr.source, "a + b")
        self.assertIn("rz", rest)


# ---------------------------------------------------------------------------
# Expression in transformations tests
# ---------------------------------------------------------------------------

class ExpressionInTransformsTests(unittest.TestCase):
    """Test expressions in transformation values."""

    def test_expression_in_translate_x(self):
        transforms = _parse_transforms("x (a + 1)")
        self.assertIsInstance(transforms[0], Translate)
        self.assertEqual(transforms[0].axis, AXIS_X)
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "a + 1")

    def test_expression_in_translate_y(self):
        transforms = _parse_transforms("y (sin(t))")
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "sin(t)")

    def test_expression_in_translate_z(self):
        transforms = _parse_transforms("z (sqrt(2))")
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "sqrt(2)")

    def test_expression_in_rotate(self):
        transforms = _parse_transforms("rz (360 / n)")
        self.assertIsInstance(transforms[0].angle, Expr)
        self.assertEqual(transforms[0].angle.source, "360 / n")

    def test_expression_in_scale_uniform(self):
        transforms = _parse_transforms("s (a * 2)")
        self.assertIsInstance(transforms[0].x, Expr)
        self.assertEqual(transforms[0].x.source, "a * 2")

    def test_expression_in_scale_per_axis(self):
        transforms = _parse_transforms("s (a) (b) (c)")
        self.assertIsInstance(transforms[0].x, Expr)
        self.assertIsInstance(transforms[0].y, Expr)
        self.assertIsInstance(transforms[0].z, Expr)
        self.assertEqual(transforms[0].x.source, "a")
        self.assertEqual(transforms[0].y.source, "b")
        self.assertEqual(transforms[0].z.source, "c")

    def test_expression_in_matrix(self):
        transforms = _parse_transforms("m (a) (b) (c) (d) (e) (f) (g) (h) (i)")
        self.assertIsInstance(transforms[0], MatrixTransform)
        self.assertTrue(all(isinstance(v, Expr) for v in transforms[0].matrix))

    def test_expression_in_hue(self):
        transforms = _parse_transforms("hue (360 / n)")
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "360 / n")

    def test_expression_in_saturation(self):
        transforms = _parse_transforms("sat (0.5 * n)")
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "0.5 * n")

    def test_expression_in_brightness(self):
        transforms = _parse_transforms("b (0.5 + 0.5)")
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "0.5 + 0.5")

    def test_expression_in_alpha(self):
        transforms = _parse_transforms("alpha (1 / n)")
        self.assertIsInstance(transforms[0].value, Expr)
        self.assertEqual(transforms[0].value.source, "1 / n")

    def test_expression_in_blend_color(self):
        transforms = _parse_transforms("blend red (0.5 * 2)")
        self.assertIsInstance(transforms[0], BlendColor)
        self.assertIsInstance(transforms[0].strength, Expr)
        self.assertEqual(transforms[0].strength.source, "0.5 * 2")

    def test_mixed_number_variable_expression(self):
        transforms = _parse_transforms("x 1 y angle z (sin(t))")
        self.assertIsInstance(transforms[0].value, float)
        self.assertEqual(transforms[0].value, 1.0)
        self.assertIsInstance(transforms[1].value, VariableRef)
        self.assertEqual(transforms[1].value.name, "angle")
        self.assertIsInstance(transforms[2].value, Expr)
        self.assertEqual(transforms[2].value.source, "sin(t)")

    def test_variable_named_as_keyword_after_keyword(self):
        """Variable 'a' (also alpha keyword) works as value after 'x' keyword."""
        transforms = _parse_transforms("x a")
        self.assertIsInstance(transforms[0].value, VariableRef)
        self.assertEqual(transforms[0].value.name, "a")

    def test_scale_stops_at_keyword(self):
        """Scale 's 0.9' stops at keyword 'x', leaving 'x 1' for next transform."""
        transforms = _parse_transforms("s 0.9 x 1")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].x, 0.9)
        self.assertIsInstance(transforms[1], Translate)
        self.assertEqual(transforms[1].axis, AXIS_X)
        self.assertAlmostEqual(transforms[1].value, 1.0)

    def test_hue_with_variable_named_b(self):
        """Variable 'b' (also brightness keyword) works as value after 'h' keyword."""
        transforms = _parse_transforms("h b")
        self.assertIsInstance(transforms[0].value, VariableRef)
        self.assertEqual(transforms[0].value.name, "b")


# ---------------------------------------------------------------------------
# Expression in repetition count tests
# ---------------------------------------------------------------------------

class ExpressionInRepetitionTests(unittest.TestCase):
    """Test expressions in repetition counts."""

    def test_expression_as_count(self):
        prog = parse("(n * 2) * { x 1 } box")
        rep = prog.rules[0].body[0].repetitions[0]
        self.assertIsInstance(rep.count, Expr)
        self.assertEqual(rep.count.source, "n * 2")

    def test_expression_count_with_nested_parens(self):
        prog = parse("((a + b) * c) * { x 1 } box")
        rep = prog.rules[0].body[0].repetitions[0]
        self.assertIsInstance(rep.count, Expr)
        self.assertEqual(rep.count.source, "(a + b) * c")


# ---------------------------------------------------------------------------
# Expression in rule modifiers tests
# ---------------------------------------------------------------------------

class ExpressionInRuleModifiersTests(unittest.TestCase):
    """Test expressions in rule modifiers."""

    def test_expression_in_maxdepth(self):
        prog = parse("rule tree md (depth * 2) { box }")
        rule = prog.rules[0]
        self.assertIsInstance(rule.maxdepth, Expr)
        self.assertEqual(rule.maxdepth.source, "depth * 2")

    def test_expression_in_weight(self):
        prog = parse("rule leaf w (1 + 2) { box }")
        rule = prog.rules[0]
        self.assertIsInstance(rule.weight, Expr)
        self.assertEqual(rule.weight.source, "1 + 2")

    def test_expression_in_maxdepth_with_retirement(self):
        prog = parse("rule tree md (n + 1) > leaf { box }")
        rule = prog.rules[0]
        self.assertIsInstance(rule.maxdepth, Expr)
        self.assertEqual(rule.maxdepth.source, "n + 1")
        self.assertEqual(rule.retirement_rule, "leaf")


# ---------------------------------------------------------------------------
# Expression in rule reference tests
# ---------------------------------------------------------------------------

class ExpressionInRuleRefTests(unittest.TestCase):
    """Test expressions in rule reference retirement."""

    def test_expression_in_call_retirement(self):
        prog = parse("1 * { x 1 } md (n + 1) child")
        ref = prog.rules[0].body[0].terminal
        self.assertIsInstance(ref.retirement_depth, Expr)
        self.assertEqual(ref.retirement_depth.source, "n + 1")
        self.assertEqual(ref.name, "child")


# ---------------------------------------------------------------------------
# #define does NOT accept expressions
# ---------------------------------------------------------------------------

class DefineNoExpressionTests(unittest.TestCase):
    """Test that #define values are numbers only."""

    def test_define_with_number(self):
        prog = parse("#define n 10")
        self.assertEqual(prog.defines, {"n": 10.0})

    def test_define_with_fraction(self):
        prog = parse("#define ratio 1/3")
        self.assertAlmostEqual(prog.defines["ratio"], 1 / 3, places=10)

    def test_define_with_float(self):
        prog = parse("#define scale 0.75")
        self.assertEqual(prog.defines["scale"], 0.75)


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------

class BackwardCompatibilityTests(unittest.TestCase):
    """Test that existing syntax still works."""

    def test_plain_numbers_still_work(self):
        prog = parse("1 * { x 5 y -2.5 z 3.14 } box")
        trans = prog.rules[0].body[0].repetitions[0].transformations
        self.assertAlmostEqual(trans[0].value, 5.0)
        self.assertAlmostEqual(trans[1].value, -2.5)
        self.assertAlmostEqual(trans[2].value, 3.14)

    def test_variables_still_work(self):
        prog = parse("#define angle 36\n1 * { ry angle } box")
        trans = prog.rules[0].body[0].repetitions[0].transformations[0]
        self.assertIsInstance(trans.angle, VariableRef)
        self.assertEqual(trans.angle.name, "angle")

    def test_integer_repetition_still_works(self):
        prog = parse("36 * { x -2 ry 10 } r1")
        rep = prog.rules[0].body[0].repetitions[0]
        self.assertEqual(rep.count, 36)

    def test_variable_repetition_still_works(self):
        prog = parse("#define n 10\nn * { x 1 } box")
        rep = prog.rules[0].body[0].repetitions[0]
        self.assertIsInstance(rep.count, VariableRef)
        self.assertEqual(rep.count.name, "n")

    def test_original_sample_still_parses(self):
        src = """
        set maxdepth 100
        r1
        36 * { x -2 ry 10 } r1

        rule r1 maxdepth 10 {
           2 * { y -1 } 3 * { rz 15 x 1 b 0.9 h -20 } r2
           { y 1 h 12 a 0.9 rx 36 } r1
        }

        rule r2 {
           { s 0.9 0.1 1.1 hue 10 } box
        }

        rule r2 w 2 {
           { hue 113 sat 19 a 23 s 0.1 0.9 1.1 } box
        }
        """
        prog = parse(src)
        self.assertEqual(len(prog.rules), 4)


# ---------------------------------------------------------------------------
# Serializer round-trip tests
# ---------------------------------------------------------------------------

class SerializerRoundTripTests(unittest.TestCase):
    """Test that expressions survive serialization and re-parsing."""

    def test_expression_round_trip(self):
        from sverchok.utils.modules.eisenscript.serializer import ast_to_string

        src = "#define a 5\n1 * { x (a+1) y (sin(t)) } box"
        prog = parse(src)
        output = ast_to_string(prog)
        prog2 = parse(output)

        trans = prog2.rules[0].body[0].repetitions[0].transformations[0]
        self.assertIsInstance(trans.value, Expr)
        self.assertEqual(trans.value.source, "a+1")

        trans2 = prog2.rules[0].body[0].repetitions[0].transformations[1]
        self.assertIsInstance(trans2.value, Expr)
        self.assertEqual(trans2.value.source, "sin(t)")

    def test_expression_in_repetition_count_round_trip(self):
        from sverchok.utils.modules.eisenscript.serializer import ast_to_string

        src = "(n*2) * { x 1 } box"
        prog = parse(src)
        output = ast_to_string(prog)
        prog2 = parse(output)

        rep = prog2.rules[0].body[0].repetitions[0]
        self.assertIsInstance(rep.count, Expr)
        self.assertEqual(rep.count.source, "n*2")


# ---------------------------------------------------------------------------
# XML conversion tests — expressions must raise clear errors
# ---------------------------------------------------------------------------

class ExpressionToXmlTests(unittest.TestCase):
    """Test that expressions cannot be converted to XML (clear error)."""

    def setUp(self):
        from sverchok.utils.modules.eisenscript.to_xml import (
            ast_to_xml,
            ExpressionInXmlError,
        )
        self.ast_to_xml = ast_to_xml
        self.ExpressionInXmlError = ExpressionInXmlError

    def test_expression_in_translate_raises(self):
        prog = parse("1 * { x (a + 1) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("a + 1", str(ctx.exception))

    def test_expression_in_scale_raises(self):
        prog = parse("1 * { s (a * 2) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("a * 2", str(ctx.exception))

    def test_expression_in_rotation_raises(self):
        prog = parse("1 * { rz (360/n) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("360/n", str(ctx.exception))

    def test_expression_in_repetition_count_raises(self):
        prog = parse("(n * 2) * { x 1 } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("n * 2", str(ctx.exception))

    def test_expression_in_maxdepth_raises(self):
        prog = parse("rule tree md (depth * 2) { box }")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("depth * 2", str(ctx.exception))

    def test_expression_in_weight_raises(self):
        prog = parse("rule leaf w (1 + 2) { box }")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("1 + 2", str(ctx.exception))

    def test_expression_in_retirement_depth_raises(self):
        prog = parse("1 * { x 1 } md (n + 1) child")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("n + 1", str(ctx.exception))

    def test_expression_in_hue_raises(self):
        prog = parse("1 * { hue (360/n) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog, support_colors=True)
        self.assertIn("360/n", str(ctx.exception))

    def test_expression_in_blend_strength_raises(self):
        prog = parse("1 * { blend red (0.5 * 2) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog, support_colors=True)
        self.assertIn("0.5 * 2", str(ctx.exception))

    def test_expression_in_matrix_raises(self):
        prog = parse("1 * { m (a) (b) (c) (d) (e) (f) (g) (h) (i) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("a", str(ctx.exception))

    def test_plain_program_without_expressions_converts(self):
        """Programs without expressions convert to XML normally."""
        prog = parse("#define a 5\n1 * { x a } box")
        xml = self.ast_to_xml(prog)
        self.assertEqual(xml.tag, "rules")

    def test_expression_error_message_is_helpful(self):
        """Error message mentions #define as workaround."""
        prog = parse("1 * { x (a + 1) } box")
        with self.assertRaises(self.ExpressionInXmlError) as ctx:
            self.ast_to_xml(prog)
        self.assertIn("#define", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
