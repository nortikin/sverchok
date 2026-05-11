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
Tests for the EisenScript parser (utils.modules.eisenscript.parser).

The parser does not require Blender, so these tests use plain unittest
and can be run standalone or through the Sverchok test framework.
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
    _strip_comments,
    parse_branch,
    parse_rule_definition,
    parse_set_statement,
    parse_transformation_block,
    parse_repetition,
    parse_rule_ref_with_retirement,
    parse_primitive,
    parse_identifier,
    parse_int,
)
from sverchok.utils.modules.eisenscript.ast import (
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    VariableRef,
    TranslateX, TranslateY, TranslateZ,
    RotateX, RotateY, RotateZ,
    Scale,
    MatrixTransform,
    MirrorX, MirrorY, MirrorZ,
    HueShift, SaturationMul, BrightnessMul, AlphaMul,
    SetColor, BlendColor,
    Box, Grid, Sphere, Line, Point, Triangle,
)


class CommentStripTests(unittest.TestCase):
    """Test comment removal from EisenScript source."""

    def test_no_comments(self):
        src = "rule start { box }"
        self.assertEqual(_strip_comments(src), "rule start { box }")

    def test_line_comment(self):
        src = "rule start { box } // this is a comment"
        self.assertEqual(_strip_comments(src), "rule start { box } ")

    def test_line_comment_at_start(self):
        src = "// comment\nrule start { box }"
        self.assertEqual(_strip_comments(src), "\nrule start { box }")

    def test_block_comment(self):
        src = "/* comment */ rule start { box }"
        self.assertEqual(_strip_comments(src), " rule start { box }")

    def test_multiline_block_comment(self):
        src = "/*\n  multi\n  line\n*/ rule start { box }"
        self.assertEqual(_strip_comments(src), " rule start { box }")

    def test_multiple_comments(self):
        src = "// c1\n/* c2 */ rule start { box } // c3"
        self.assertEqual(_strip_comments(src), "\n rule start { box } ")

    def test_nested_block_comments_not_supported(self):
        # Nested block comments are not supported; first */ ends the comment
        src = "/* outer /* inner */ done */"
        result = _strip_comments(src)
        self.assertEqual(result, " done */")


class SetStatementTests(unittest.TestCase):
    """Test parsing of 'set' statements."""

    def test_maxdepth(self):
        prog = parse("set maxdepth 100")
        self.assertEqual(len(prog.settings), 1)
        self.assertIsInstance(prog.settings[0], SetStatement)
        self.assertEqual(prog.settings[0].name, "maxdepth")
        self.assertEqual(prog.settings[0].value, 100)

    def test_maxobjects(self):
        prog = parse("set maxobjects 5000")
        self.assertEqual(prog.settings[0].name, "maxobjects")
        self.assertEqual(prog.settings[0].value, 5000)

    def test_minsize(self):
        prog = parse("set minsize 0.01")
        self.assertEqual(prog.settings[0].name, "minsize")
        self.assertAlmostEqual(prog.settings[0].value, 0.01)

    def test_maxsize(self):
        prog = parse("set maxsize 10.5")
        self.assertEqual(prog.settings[0].name, "maxsize")
        self.assertAlmostEqual(prog.settings[0].value, 10.5)

    def test_seed_integer(self):
        prog = parse("set seed 42")
        self.assertEqual(prog.settings[0].name, "seed")
        self.assertEqual(prog.settings[0].value, 42)

    def test_seed_initial(self):
        prog = parse("set seed initial")
        self.assertEqual(prog.settings[0].name, "seed")
        self.assertEqual(prog.settings[0].value, "initial")

    def test_background_hex(self):
        prog = parse("set background #FFFFFF")
        self.assertEqual(prog.settings[0].name, "background")
        self.assertEqual(prog.settings[0].value, "#FFFFFF")

    def test_background_keyword(self):
        prog = parse("set background white")
        self.assertEqual(prog.settings[0].name, "background")
        self.assertEqual(prog.settings[0].value, "white")

    def test_color_random(self):
        prog = parse("set color random")
        self.assertEqual(prog.settings[0].name, "color")
        self.assertEqual(prog.settings[0].value, "random")

    def test_colorpool_scheme(self):
        prog = parse("set colorpool randomhue")
        self.assertEqual(prog.settings[0].name, "colorpool")
        self.assertEqual(prog.settings[0].value, "randomhue")

    def test_multiple_settings(self):
        src = "set maxdepth 100\nset maxobjects 5000\nset seed 42"
        prog = parse(src)
        self.assertEqual(len(prog.settings), 3)
        self.assertEqual(prog.settings[0].name, "maxdepth")
        self.assertEqual(prog.settings[1].name, "maxobjects")
        self.assertEqual(prog.settings[2].name, "seed")


class DefineStatementTests(unittest.TestCase):
    """Test parsing of #define statements."""

    def test_simple_define(self):
        prog = parse("#define n 10")
        self.assertEqual(prog.defines, {"n": 10.0})

    def test_multiple_defines(self):
        prog = parse("#define steps 20\n#define angle 18")
        self.assertEqual(prog.defines, {"steps": 20.0, "angle": 18.0})

    def test_define_with_fraction(self):
        prog = parse("#define ratio 1/3")
        self.assertAlmostEqual(prog.defines["ratio"], 1/3, places=10)

    def test_define_with_float(self):
        prog = parse("#define scale 0.75")
        self.assertEqual(prog.defines["scale"], 0.75)

    def test_define_in_program(self):
        prog = parse("#define n 10\nrule start { n * { x 1 } box }")
        self.assertEqual(prog.defines, {"n": 10.0})
        self.assertEqual(len(prog.rules), 1)

    def test_variable_as_count(self):
        prog = parse("#define n 10\nrule start { n * { x 1 } box }")
        rep = prog.rules[0].body[0].repetitions[0]
        self.assertIsInstance(rep.count, VariableRef)
        self.assertEqual(rep.count.name, "n")

    def test_variable_as_transform_value(self):
        prog = parse("#define angle 36\nrule start { 10 * { ry angle } box }")
        trans = prog.rules[0].body[0].repetitions[0].transformations[0]
        self.assertIsInstance(trans, RotateY)
        self.assertIsInstance(trans.angle, VariableRef)
        self.assertEqual(trans.angle.name, "angle")


class PrimitiveTests(unittest.TestCase):
    """Test parsing of drawing primitives."""

    def _parse_primitive(self, code):
        """Helper: wrap primitive in a rule and parse."""
        prog = parse(f"rule test {{ {code} }}")
        rule = prog.rules[0]
        branch = rule.body[0]
        return branch.terminal

    def test_box(self):
        term = self._parse_primitive("box")
        self.assertIsInstance(term, Box)

    def test_grid(self):
        term = self._parse_primitive("grid")
        self.assertIsInstance(term, Grid)

    def test_sphere(self):
        term = self._parse_primitive("sphere")
        self.assertIsInstance(term, Sphere)

    def test_line(self):
        term = self._parse_primitive("line")
        self.assertIsInstance(term, Line)

    def test_point(self):
        term = self._parse_primitive("point")
        self.assertIsInstance(term, Point)

    def test_triangle_two_coords(self):
        term = self._parse_primitive("Triangle[0,0;1,0;0.5,0.5]")
        self.assertIsInstance(term, Triangle)
        self.assertEqual(len(term.vertices), 3)
        self.assertAlmostEqual(term.vertices[0][0], 0.0)
        self.assertAlmostEqual(term.vertices[0][1], 0.0)
        self.assertAlmostEqual(term.vertices[0][2], 0.0)

    def test_triangle_three_coords(self):
        term = self._parse_primitive("Triangle[0,0,0;1,0,0;0,1,0]")
        self.assertIsInstance(term, Triangle)
        self.assertEqual(len(term.vertices), 3)
        self.assertAlmostEqual(term.vertices[2][1], 1.0)
        self.assertAlmostEqual(term.vertices[2][2], 0.0)


class GeometricTransformationTests(unittest.TestCase):
    """Test parsing of geometrical transformations inside blocks."""

    def _parse_transforms(self, code):
        """Helper: parse transformations from a block '{ code }'."""
        for transforms, _ in parse_transformation_block(f"{{{code}}}"):
            return transforms
        self.fail("No transformations parsed")

    def test_translate_x(self):
        transforms = self._parse_transforms("x 5")
        self.assertEqual(len(transforms), 1)
        self.assertIsInstance(transforms[0], TranslateX)
        self.assertAlmostEqual(transforms[0].value, 5.0)

    def test_translate_y_negative(self):
        transforms = self._parse_transforms("y -2.5")
        self.assertIsInstance(transforms[0], TranslateY)
        self.assertAlmostEqual(transforms[0].value, -2.5)

    def test_translate_z(self):
        transforms = self._parse_transforms("z 3.14")
        self.assertIsInstance(transforms[0], TranslateZ)
        self.assertAlmostEqual(transforms[0].value, 3.14)

    def test_rotate_x(self):
        transforms = self._parse_transforms("rx 90")
        self.assertIsInstance(transforms[0], RotateX)
        self.assertAlmostEqual(transforms[0].angle, 90.0)

    def test_rotate_y(self):
        transforms = self._parse_transforms("ry 45")
        self.assertIsInstance(transforms[0], RotateY)
        self.assertAlmostEqual(transforms[0].angle, 45.0)

    def test_rotate_z_negative(self):
        transforms = self._parse_transforms("rz -30")
        self.assertIsInstance(transforms[0], RotateZ)
        self.assertAlmostEqual(transforms[0].angle, -30.0)

    def test_scale_uniform(self):
        transforms = self._parse_transforms("s 2")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].x, 2.0)
        self.assertTrue(transforms[0].is_uniform)

    def test_scale_per_axis(self):
        transforms = self._parse_transforms("s 0.5 1 2")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].x, 0.5)
        self.assertAlmostEqual(transforms[0].y, 1.0)
        self.assertAlmostEqual(transforms[0].z, 2.0)
        self.assertFalse(transforms[0].is_uniform)

    def test_mirror_x(self):
        transforms = self._parse_transforms("fx")
        self.assertIsInstance(transforms[0], MirrorX)

    def test_mirror_y(self):
        transforms = self._parse_transforms("fy")
        self.assertIsInstance(transforms[0], MirrorY)

    def test_mirror_z(self):
        transforms = self._parse_transforms("fz")
        self.assertIsInstance(transforms[0], MirrorZ)

    def test_matrix_identity(self):
        transforms = self._parse_transforms("m 1 0 0 0 1 0 0 0 1")
        self.assertIsInstance(transforms[0], MatrixTransform)
        self.assertEqual(len(transforms[0].matrix), 9)
        self.assertAlmostEqual(transforms[0].matrix[0], 1.0)
        self.assertAlmostEqual(transforms[0].matrix[4], 1.0)
        self.assertAlmostEqual(transforms[0].matrix[8], 1.0)

    def test_multiple_transformations(self):
        transforms = self._parse_transforms("x 1 y 2 rz 90")
        self.assertEqual(len(transforms), 3)
        self.assertIsInstance(transforms[0], TranslateX)
        self.assertIsInstance(transforms[1], TranslateY)
        self.assertIsInstance(transforms[2], RotateZ)


class FractionParsingTests(unittest.TestCase):
    """Test parsing of fractional numeric values."""

    @staticmethod
    def _parse_transforms(code):
        """Helper: parse transformations from a block '{ code }'."""
        for transforms, _ in parse_transformation_block(f"{{{code}}}"):
            return transforms
        raise AssertionError("No transformations parsed")

    def test_simple_fraction_in_scale(self):
        transforms = self._parse_transforms("s 1/3 1 1.3")
        self.assertEqual(len(transforms), 1)
        scale = transforms[0]
        self.assertAlmostEqual(scale.x, 1/3, places=10)
        self.assertAlmostEqual(scale.y, 1.0)
        self.assertAlmostEqual(scale.z, 1.3)

    def test_fraction_in_translate(self):
        transforms = self._parse_transforms("x 1/4 y 2/3")
        self.assertAlmostEqual(transforms[0].value, 0.25, places=10)
        self.assertAlmostEqual(transforms[1].value, 2/3, places=10)

    def test_negative_fraction(self):
        transforms = self._parse_transforms("x -1/3")
        self.assertAlmostEqual(transforms[0].value, -1/3, places=10)

    def test_fraction_in_rotation(self):
        transforms = self._parse_transforms("rz 1/6")
        self.assertAlmostEqual(transforms[0].angle, 1/6, places=10)

    def test_fraction_in_rule_body(self):
        prog = parse("rule start { { s 1/2 1/3 1/4 } box }")
        branch = prog.rules[0].body[0]
        scale = branch.repetitions[0].transformations[0]
        self.assertAlmostEqual(scale.x, 0.5)
        self.assertAlmostEqual(scale.y, 1/3, places=10)
        self.assertAlmostEqual(scale.z, 0.25)


class ColorTransformationTests(unittest.TestCase):
    """Test parsing of color transformations inside blocks."""

    def _parse_transforms(self, code):
        for transforms, _ in parse_transformation_block(f"{{{code}}}"):
            return transforms
        self.fail("No transformations parsed")

    def test_hue_short(self):
        transforms = self._parse_transforms("h 180")
        self.assertIsInstance(transforms[0], HueShift)
        self.assertAlmostEqual(transforms[0].value, 180.0)

    def test_hue_long(self):
        transforms = self._parse_transforms("hue 45")
        self.assertIsInstance(transforms[0], HueShift)
        self.assertAlmostEqual(transforms[0].value, 45.0)

    def test_saturation(self):
        transforms = self._parse_transforms("sat 0.5")
        self.assertIsInstance(transforms[0], SaturationMul)
        self.assertAlmostEqual(transforms[0].value, 0.5)

    def test_brightness_short(self):
        transforms = self._parse_transforms("b 0.8")
        self.assertIsInstance(transforms[0], BrightnessMul)
        self.assertAlmostEqual(transforms[0].value, 0.8)

    def test_brightness_long(self):
        transforms = self._parse_transforms("brightness 0.9")
        self.assertIsInstance(transforms[0], BrightnessMul)
        self.assertAlmostEqual(transforms[0].value, 0.9)

    def test_alpha_short(self):
        transforms = self._parse_transforms("a 0.5")
        self.assertIsInstance(transforms[0], AlphaMul)
        self.assertAlmostEqual(transforms[0].value, 0.5)

    def test_alpha_long(self):
        transforms = self._parse_transforms("alpha 0.75")
        self.assertIsInstance(transforms[0], AlphaMul)
        self.assertAlmostEqual(transforms[0].value, 0.75)

    def test_set_color_keyword(self):
        transforms = self._parse_transforms("color red")
        self.assertIsInstance(transforms[0], SetColor)
        self.assertEqual(transforms[0].color, "red")

    def test_set_color_hex(self):
        transforms = self._parse_transforms("color #FF0000")
        self.assertIsInstance(transforms[0], SetColor)
        self.assertEqual(transforms[0].color, "#FF0000")

    def test_blend_color(self):
        transforms = self._parse_transforms("blend blue 0.5")
        self.assertIsInstance(transforms[0], BlendColor)
        self.assertEqual(transforms[0].color, "blue")
        self.assertAlmostEqual(transforms[0].strength, 0.5)


class RepetitionTests(unittest.TestCase):
    """Test parsing of repetition constructs."""

    def test_integer_count(self):
        for rep, rest in parse_repetition("36 * { x 1 } box"):
            self.assertIsInstance(rep, Repeat)
            self.assertEqual(rep.count, 36)
            self.assertEqual(len(rep.transformations), 1)
            self.assertIsInstance(rep.transformations[0], TranslateX)
            self.assertEqual(rest.strip(), "box")
            break
        else:
            self.fail("No repetition parsed")

    def test_negative_count_rejected(self):
        """Negative repetition counts raise SyntaxError (P4)."""
        with self.assertRaises(SyntaxError) as ctx:
            list(parse_repetition("-5 * { ry 10 } sphere"))
        self.assertIn("-5", str(ctx.exception))

    def test_multiple_transformations_in_repeat(self):
        for rep, _ in parse_repetition("10 * { x 1 ry 36 } box"):
            self.assertEqual(len(rep.transformations), 2)
            self.assertIsInstance(rep.transformations[0], TranslateX)
            self.assertIsInstance(rep.transformations[1], RotateY)
            break
        else:
            self.fail("No repetition parsed")

    def test_variable_count(self):
        for rep, rest in parse_repetition("n * { x 1 } box"):
            self.assertIsInstance(rep, Repeat)
            self.assertIsInstance(rep.count, VariableRef)
            self.assertEqual(rep.count.name, "n")
            break
        else:
            self.fail("No repetition parsed")


class RuleReferenceTests(unittest.TestCase):
    """Test parsing of rule references and retirement."""

    def test_simple_ref(self):
        for ref, rest in parse_rule_ref_with_retirement("child"):
            self.assertIsInstance(ref, RuleRef)
            self.assertEqual(ref.name, "child")
            self.assertIsNone(ref.retirement_depth)
            self.assertIsNone(ref.retirement_rule)
            break
        else:
            self.fail("No rule ref parsed")

    def test_retirement_depth_only(self):
        for ref, rest in parse_rule_ref_with_retirement("md 5 leaf"):
            self.assertEqual(ref.name, "leaf")
            self.assertEqual(ref.retirement_depth, 5)
            self.assertIsNone(ref.retirement_rule)
            break
        else:
            self.fail("No rule ref parsed")

    def test_retirement_with_substitution(self):
        for ref, rest in parse_rule_ref_with_retirement("md 10 > fallback box"):
            self.assertEqual(ref.name, "box")
            self.assertEqual(ref.retirement_depth, 10)
            self.assertEqual(ref.retirement_rule, "fallback")
            break
        else:
            self.fail("No rule ref parsed")

    def test_keywords_not_matched_as_refs(self):
        # Keywords like 'rule', 'set', 'md' should not be matched as rule refs
        results = list(parse_rule_ref_with_retirement("rule"))
        self.assertEqual(len(results), 0)

        results = list(parse_rule_ref_with_retirement("set"))
        self.assertEqual(len(results), 0)


class BranchTests(unittest.TestCase):
    """Test parsing of branches (repetitions + terminals)."""

    def test_simple_rule_ref_branch(self):
        for branch, rest in parse_branch("child"):
            self.assertEqual(len(branch.repetitions), 0)
            self.assertIsInstance(branch.terminal, RuleRef)
            self.assertEqual(branch.terminal.name, "child")
            break
        else:
            self.fail("No branch parsed")

    def test_simple_primitive_branch(self):
        for branch, rest in parse_branch("box"):
            self.assertEqual(len(branch.repetitions), 0)
            self.assertIsInstance(branch.terminal, Box)
            break
        else:
            self.fail("No branch parsed")

    def test_branch_with_repetition(self):
        for branch, rest in parse_branch("10 * { x 1 } child"):
            self.assertEqual(len(branch.repetitions), 1)
            self.assertEqual(branch.repetitions[0].count, 10)
            self.assertIsInstance(branch.terminal, RuleRef)
            self.assertEqual(branch.terminal.name, "child")
            break
        else:
            self.fail("No branch parsed")

    def test_branch_with_transform_block(self):
        for branch, rest in parse_branch("{ y 1 h 12 } child"):
            self.assertEqual(len(branch.repetitions), 1)
            # Transform blocks become Repeat(1, transforms)
            self.assertEqual(branch.repetitions[0].count, 1)
            self.assertEqual(len(branch.repetitions[0].transformations), 2)
            break
        else:
            self.fail("No branch parsed")

    def test_branch_with_multiple_blocks(self):
        for branch, rest in parse_branch("{ x 1 } 3 * { ry 10 } child"):
            self.assertEqual(len(branch.repetitions), 2)
            self.assertEqual(branch.repetitions[0].count, 1)
            self.assertEqual(branch.repetitions[1].count, 3)
            break
        else:
            self.fail("No branch parsed")

    def test_branch_with_retirement_ref(self):
        for branch, rest in parse_branch("md 5 > fallback child"):
            self.assertIsInstance(branch.terminal, RuleRef)
            self.assertEqual(branch.terminal.name, "child")
            self.assertEqual(branch.terminal.retirement_depth, 5)
            self.assertEqual(branch.terminal.retirement_rule, "fallback")
            break
        else:
            self.fail("No branch parsed")


class RuleDefinitionTests(unittest.TestCase):
    """Test parsing of rule definitions."""

    def test_simple_rule(self):
        prog = parse("rule start { box }")
        self.assertEqual(len(prog.rules), 1)
        rule = prog.rules[0]
        self.assertEqual(rule.name, "start")
        self.assertIsNone(rule.maxdepth)
        self.assertEqual(rule.weight, 1.0)
        self.assertEqual(len(rule.body), 1)

    def test_rule_with_maxdepth(self):
        prog = parse("rule tree maxdepth 20 { box }")
        rule = prog.rules[0]
        self.assertEqual(rule.name, "tree")
        self.assertEqual(rule.maxdepth, 20)

    def test_rule_with_md_short(self):
        prog = parse("rule tree md 20 { box }")
        rule = prog.rules[0]
        self.assertEqual(rule.maxdepth, 20)

    def test_rule_with_weight(self):
        prog = parse("rule leaf w 3 { box }")
        rule = prog.rules[0]
        self.assertEqual(rule.weight, 3.0)

    def test_rule_with_weight_long(self):
        prog = parse("rule leaf weight 2.5 { box }")
        rule = prog.rules[0]
        self.assertEqual(rule.weight, 2.5)

    def test_rule_with_multiple_modifiers(self):
        prog = parse("rule tree maxdepth 10 w 2 { box }")
        rule = prog.rules[0]
        self.assertEqual(rule.maxdepth, 10)
        self.assertEqual(rule.weight, 2.0)

    def test_rule_with_multiple_branches(self):
        src = "rule tree { { x 1 } left { x -1 } right }"
        prog = parse(src)
        rule = prog.rules[0]
        self.assertEqual(len(rule.body), 2)
        self.assertEqual(rule.body[0].terminal.name, "left")
        self.assertEqual(rule.body[1].terminal.name, "right")

    def test_implicit_rule(self):
        src = "start\nbox"
        prog = parse(src)
        self.assertEqual(len(prog.rules), 1)
        self.assertEqual(prog.rules[0].name, "start")

    def test_implicit_rule_with_branch(self):
        src = "start\n10 * { x 1 } box"
        prog = parse(src)
        rule = prog.rules[0]
        self.assertEqual(rule.name, "start")
        self.assertEqual(len(rule.body), 1)
        self.assertEqual(rule.body[0].repetitions[0].count, 10)

    def test_ambiguous_rules(self):
        src = "rule leaf w 3 { sphere }\nrule leaf w 1 { box }"
        prog = parse(src)
        self.assertEqual(len(prog.rules), 2)
        self.assertEqual(prog.rules[0].weight, 3.0)
        self.assertEqual(prog.rules[1].weight, 1.0)


class FullProgramTests(unittest.TestCase):
    """Test parsing of complete EisenScript programs."""

    def test_original_sample(self):
        """Parse the original EisenScript sample from the documentation."""
        src = """
        /*
           Sample Torus.
        */

        set maxdepth 100
        r1
        36 * { x -2 ry 10 } r1

        rule r1 maxdepth 10 {
           2 * { y -1 } 3 * { rz 15 x 1 b 0.9 h -20 } r2
           { y 1 h 12 a 0.9 rx 36 } r1
        }

        rule r2 {
           { s 0.9 0.1 1.1 hue 10 } box // a comment
        }

        rule r2 w 2 {
           { hue 113 sat 19 a 23 s 0.1 0.9 1.1 } box
        }
        """
        prog = parse(src)

        # Check settings
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].name, "maxdepth")
        self.assertEqual(prog.settings[0].value, 100)

        # Check rules
        self.assertEqual(len(prog.rules), 4)

        # Implicit rule r1
        r1_implicit = prog.rules[0]
        self.assertEqual(r1_implicit.name, "r1")
        self.assertIsNone(r1_implicit.maxdepth)
        self.assertEqual(len(r1_implicit.body), 1)
        self.assertEqual(r1_implicit.body[0].repetitions[0].count, 36)
        self.assertEqual(r1_implicit.body[0].terminal.name, "r1")

        # Explicit rule r1 with maxdepth
        r1_explicit = prog.rules[1]
        self.assertEqual(r1_explicit.name, "r1")
        self.assertEqual(r1_explicit.maxdepth, 10)
        self.assertEqual(len(r1_explicit.body), 2)

        # First branch of explicit r1
        branch1 = r1_explicit.body[0]
        self.assertEqual(len(branch1.repetitions), 2)
        self.assertEqual(branch1.repetitions[0].count, 2)
        self.assertEqual(branch1.repetitions[1].count, 3)
        self.assertEqual(branch1.terminal.name, "r2")

        # Second branch of explicit r1
        branch2 = r1_explicit.body[1]
        self.assertEqual(len(branch2.repetitions), 1)
        self.assertEqual(branch2.terminal.name, "r1")

        # Rule r2 (default weight)
        r2_default = prog.rules[2]
        self.assertEqual(r2_default.name, "r2")
        self.assertEqual(r2_default.weight, 1.0)
        self.assertIsInstance(r2_default.body[0].terminal, Box)

        # Rule r2 (weighted)
        r2_weighted = prog.rules[3]
        self.assertEqual(r2_weighted.name, "r2")
        self.assertEqual(r2_weighted.weight, 2.0)

    def test_empty_program(self):
        prog = parse("")
        self.assertIsInstance(prog, Program)
        self.assertEqual(len(prog.settings), 0)
        self.assertEqual(len(prog.rules), 0)

    def test_comments_only(self):
        prog = parse("// just a comment\n/* another */")
        self.assertEqual(len(prog.settings), 0)
        self.assertEqual(len(prog.rules), 0)

    def test_whitespace_only(self):
        prog = parse("   \n\t  \n  ")
        self.assertEqual(len(prog.settings), 0)
        self.assertEqual(len(prog.rules), 0)

    def test_complex_program(self):
        """Parse a complex program with all features."""
        src = """
        set maxdepth 100
        set maxobjects 10000
        set minsize 0.01
        set maxsize 10
        set seed 42
        set background #FFFFFF

        rule start {
            10 * { x 1 ry 36 } box
        }

        rule tree maxdepth 20 {
            { y 1 } { s 0.8 hue 10 } tree
            { fx y -1 } { s 0.8 hue -10 } tree
        }

        rule leaf w 3 {
            { hue 120 sat 0.8 } sphere
        }

        rule leaf w 1 {
            { hue 60 sat 0.5 } box
        }
        """
        prog = parse(src)

        self.assertEqual(len(prog.settings), 6)
        self.assertEqual(len(prog.rules), 4)

        # Check start rule
        start = prog.rules[0]
        self.assertEqual(start.name, "start")
        self.assertEqual(start.body[0].repetitions[0].count, 10)
        self.assertIsInstance(start.body[0].terminal, Box)

        # Check tree rule
        tree = prog.rules[1]
        self.assertEqual(tree.name, "tree")
        self.assertEqual(tree.maxdepth, 20)
        self.assertEqual(len(tree.body), 2)

        # Check leaf rules (ambiguous)
        leaf1 = prog.rules[2]
        leaf2 = prog.rules[3]
        self.assertEqual(leaf1.weight, 3.0)
        self.assertEqual(leaf2.weight, 1.0)
        self.assertIsInstance(leaf1.body[0].terminal, Sphere)
        self.assertIsInstance(leaf2.body[0].terminal, Box)

    def test_octopus_sample(self):
        src = """
        set maxdepth 100

        10 * { ry 36 sat 0.9 } 30 * { ry 10 } 1 * { h 30 b 0.8 sat 0.8 a 0.3 } r1

        rule r1 w 20 {
        { s 0.9 rz 5 h 5 rx 5 x 1 } r1
        { s 1 0.2 0.5 } box
        }

        rule r1 w 20 {
        { s 0.99 rz -5 h 5 rx -5 x 1 } r1
        { s 1 0.2 0.5 } box
        }

        rule r1 {}
        """
        prog = parse(src)
        print(prog)


class ErrorTests(unittest.TestCase):
    """Test error handling in the parser."""

    def test_invalid_syntax(self):
        with self.assertRaises(SyntaxError):
            parse("this is not valid eisenscript!!!")

    def test_unclosed_brace(self):
        # Unclosed brace in rule body should cause parse failure
        with self.assertRaises(SyntaxError):
            parse("rule test { box")

    def test_unknown_keyword(self):
        # Completely unknown content should raise SyntaxError
        with self.assertRaises(SyntaxError):
            parse("@@@")


class LowLevelParserTests(unittest.TestCase):
    """Test low-level parser functions."""

    def test_parse_identifier_simple(self):
        for name, rest in parse_identifier("foo"):
            self.assertEqual(name, "foo")
            self.assertEqual(rest.strip(), "")
            break
        else:
            self.fail("No identifier parsed")

    def test_parse_identifier_with_rest(self):
        for name, rest in parse_identifier("foo bar"):
            self.assertEqual(name, "foo")
            self.assertEqual(rest.strip(), "bar")
            break
        else:
            self.fail("No identifier parsed")

    def test_parse_identifier_underscore(self):
        for name, _ in parse_identifier("_private"):
            self.assertEqual(name, "_private")
            break
        else:
            self.fail("No identifier parsed")

    def test_parse_identifier_with_digits(self):
        for name, _ in parse_identifier("rule2"):
            self.assertEqual(name, "rule2")
            break
        else:
            self.fail("No identifier parsed")

    def test_parse_int_positive(self):
        for val, rest in parse_int("42 bar"):
            self.assertEqual(val, 42)
            self.assertEqual(rest.strip(), "bar")
            break
        else:
            self.fail("No int parsed")

    def test_parse_int_negative(self):
        for val, _ in parse_int("-10"):
            self.assertEqual(val, -10)
            break
        else:
            self.fail("No int parsed")

    def test_parse_int_zero(self):
        for val, _ in parse_int("0"):
            self.assertEqual(val, 0)
            break
        else:
            self.fail("No int parsed")

    def test_parse_int_no_match(self):
        results = list(parse_int("abc"))
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
