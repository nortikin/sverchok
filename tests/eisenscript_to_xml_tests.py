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
Tests for the EisenScript -> XML converter (utils.modules.eisenscript.to_xml).

Standalone unittest — no Blender dependency.
"""

import unittest
import sys
import os

# Add project root to path for standalone execution
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from xml.etree import ElementTree as ET

from sverchok.utils.modules.eisenscript.to_xml import (
    ast_to_xml,
    eisenscript_to_xml,
    xml_to_string,
    _trans_to_token,
    _collect_transforms,
)
from sverchok.utils.modules.eisenscript.ast import (
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    TranslateX, TranslateY, TranslateZ,
    RotateX, RotateY, RotateZ,
    Scale,
    MatrixTransform,
    MirrorX, MirrorY, MirrorZ,
    HueShift, SaturationMul, BrightnessMul, AlphaMul,
    SetColor, BlendColor,
    Box, Grid, Sphere, Line, Point, Triangle,
)


class TransformTokenTests(unittest.TestCase):
    """Test individual transformation -> token conversion."""

    def test_translate_x(self):
        self.assertEqual(_trans_to_token(TranslateX(5)), "tx 5")

    def test_translate_y_negative(self):
        self.assertEqual(_trans_to_token(TranslateY(-2.5)), "ty -2.5")

    def test_translate_z(self):
        self.assertEqual(_trans_to_token(TranslateZ(3.14)), "tz 3.14")

    def test_rotate_x(self):
        self.assertEqual(_trans_to_token(RotateX(90)), "rx 90")

    def test_rotate_y(self):
        self.assertEqual(_trans_to_token(RotateY(45)), "ry 45")

    def test_rotate_z_negative(self):
        self.assertEqual(_trans_to_token(RotateZ(-30)), "rz -30")

    def test_scale_uniform(self):
        self.assertEqual(_trans_to_token(Scale(2)), "sa 2")

    def test_scale_per_axis(self):
        self.assertEqual(_trans_to_token(Scale(0.5, 1, 2)), "s 0.5 1 2")

    def test_matrix(self):
        m = MatrixTransform([1, 0, 0, 0, 1, 0, 0, 0, 1])
        self.assertEqual(_trans_to_token(m), "m 1 0 0 0 1 0 0 0 1")

    def test_mirror_x(self):
        self.assertEqual(_trans_to_token(MirrorX()), "fx")

    def test_mirror_y(self):
        self.assertEqual(_trans_to_token(MirrorY()), "fy")

    def test_mirror_z(self):
        self.assertEqual(_trans_to_token(MirrorZ()), "fz")

    def test_hue_short(self):
        self.assertEqual(_trans_to_token(HueShift(180)), "h 180")

    def test_saturation(self):
        self.assertEqual(_trans_to_token(SaturationMul(0.5)), "sat 0.5")

    def test_brightness(self):
        self.assertEqual(_trans_to_token(BrightnessMul(0.8)), "b 0.8")

    def test_alpha(self):
        self.assertEqual(_trans_to_token(AlphaMul(0.5)), "a 0.5")

    def test_set_color(self):
        self.assertEqual(_trans_to_token(SetColor("red")), "color red")

    def test_blend_color(self):
        self.assertEqual(_trans_to_token(BlendColor("blue", 0.5)), "blend blue 0.5")


class CollectTransformsTests(unittest.TestCase):
    """Test _collect_transforms helper."""

    def test_empty(self):
        transforms, count = _collect_transforms([])
        self.assertEqual(transforms, "")
        self.assertIsNone(count)

    def test_single_repeat(self):
        reps = [Repeat(10, [TranslateX(1), RotateY(36)])]
        transforms, count = _collect_transforms(reps)
        self.assertEqual(transforms, "tx 1 ry 36")
        self.assertEqual(count, 10)

    def test_multiple_repeats(self):
        reps = [
            Repeat(3, [TranslateX(1)]),
            Repeat(5, [RotateZ(10)]),
        ]
        transforms, count = _collect_transforms(reps)
        self.assertEqual(transforms, "tx 1 rz 10")
        self.assertEqual(count, 5)  # last count wins


class AstToXmlBasicTests(unittest.TestCase):
    """Test ast_to_xml with hand-crafted AST nodes."""

    def test_empty_program(self):
        prog = Program()
        root = ast_to_xml(prog)
        self.assertEqual(root.tag, "rules")
        self.assertEqual(root.get("max_depth"), "1000")
        self.assertEqual(len(root), 0)

    def test_program_with_maxdepth(self):
        prog = Program(settings=[SetStatement("maxdepth", 200)])
        root = ast_to_xml(prog)
        self.assertEqual(root.get("max_depth"), "200")

    def test_simple_rule_with_box(self):
        prog = Program(rules=[
            Rule(name="start", body=[
                Branch(repetitions=[], terminal=Box()),
            ]),
        ])
        root = ast_to_xml(prog)
        rules = root.findall("rule")
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].get("name"), "start")
        instances = rules[0].findall("instance")
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].get("shape"), "box")

    def test_rule_with_call(self):
        prog = Program(rules=[
            Rule(name="start", body=[
                Branch(repetitions=[], terminal=RuleRef("child")),
            ]),
        ])
        root = ast_to_xml(prog)
        rules = root.findall("rule")
        calls = rules[0].findall("call")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get("rule"), "child")

    def test_rule_with_weight(self):
        prog = Program(rules=[
            Rule(name="leaf", weight=3.0, body=[
                Branch(repetitions=[], terminal=Box()),
            ]),
        ])
        root = ast_to_xml(prog)
        rules = root.findall("rule")
        self.assertEqual(rules[0].get("weight"), "3.0")

    def test_rule_with_maxdepth(self):
        prog = Program(rules=[
            Rule(name="tree", maxdepth=20, body=[
                Branch(repetitions=[], terminal=Box()),
            ]),
        ])
        root = ast_to_xml(prog)
        rules = root.findall("rule")
        self.assertEqual(rules[0].get("max_depth"), "20")

    def test_branch_with_repetition(self):
        prog = Program(rules=[
            Rule(name="start", body=[
                Branch(
                    repetitions=[Repeat(10, [TranslateX(1)])],
                    terminal=RuleRef("child"),
                ),
            ]),
        ])
        root = ast_to_xml(prog)
        calls = root[0].findall("call")
        self.assertEqual(calls[0].get("count"), "10")
        self.assertIn("tx 1", calls[0].get("transforms"))

    def test_branch_with_transforms(self):
        prog = Program(rules=[
            Rule(name="start", body=[
                Branch(
                    repetitions=[Repeat(1, [RotateZ(90), Scale(0.5)])],
                    terminal=Box(),
                ),
            ]),
        ])
        root = ast_to_xml(prog)
        instances = root[0].findall("instance")
        transforms = instances[0].get("transforms", "")
        self.assertIn("rz 90", transforms)
        self.assertIn("sa 0.5", transforms)

    def test_rule_retirement(self):
        ref = RuleRef("leaf", retirement_depth=5, retirement_rule="fallback")
        prog = Program(rules=[
            Rule(name="start", body=[
                Branch(repetitions=[], terminal=ref),
            ]),
        ])
        root = ast_to_xml(prog)
        calls = root[0].findall("call")
        self.assertEqual(calls[0].get("max_depth"), "5")
        self.assertEqual(calls[0].get("successor"), "fallback")

    def test_all_primitives(self):
        prog = Program(rules=[
            Rule(name="start", body=[
                Branch(repetitions=[], terminal=Box()),
                Branch(repetitions=[], terminal=Grid()),
                Branch(repetitions=[], terminal=Sphere()),
                Branch(repetitions=[], terminal=Line()),
                Branch(repetitions=[], terminal=Point()),
                Branch(repetitions=[], terminal=Triangle([(0, 0, 0), (1, 0, 0), (0, 1, 0)])),
            ]),
        ])
        root = ast_to_xml(prog)
        instances = root[0].findall("instance")
        self.assertEqual(len(instances), 6)
        self.assertEqual(instances[0].get("shape"), "box")
        self.assertEqual(instances[1].get("shape"), "grid")
        self.assertEqual(instances[2].get("shape"), "sphere")
        self.assertEqual(instances[3].get("shape"), "line")
        self.assertEqual(instances[4].get("shape"), "point")
        self.assertEqual(instances[5].get("shape"), "triangle")

    def test_wrong_type_raises(self):
        with self.assertRaises(TypeError):
            ast_to_xml("not a program")


class EisenScriptToXmlTests(unittest.TestCase):
    """Test eisenscript_to_xml end-to-end (source string -> XML)."""

    def test_simple_rule(self):
        src = "rule start { box }"
        root = eisenscript_to_xml(src)
        self.assertEqual(root.tag, "rules")
        self.assertEqual(len(root.findall("rule")), 1)
        self.assertEqual(root[0].get("name"), "start")

    def test_multiple_rules(self):
        src = """
        rule start { child }
        rule child { box }
        """
        root = eisenscript_to_xml(src)
        self.assertEqual(len(root.findall("rule")), 2)

    def test_rule_with_modifiers(self):
        src = "rule tree maxdepth 20 w 3 { box }"
        root = eisenscript_to_xml(src)
        rule = root[0]
        self.assertEqual(rule.get("max_depth"), "20")
        self.assertEqual(rule.get("weight"), "3.0")

    def test_implicit_start_rule(self):
        src = "10 * { x 1 ry 36 } box"
        root = eisenscript_to_xml(src)
        rules = root.findall("rule")
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].get("name"), "start")

    def test_set_maxdepth(self):
        src = "set maxdepth 500\nrule start { box }"
        root = eisenscript_to_xml(src)
        self.assertEqual(root.get("max_depth"), "500")

    def test_transforms_in_call(self):
        src = "rule start { 5 * { x 1 rz 72 } child }"
        root = eisenscript_to_xml(src)
        calls = root[0].findall("call")
        self.assertEqual(calls[0].get("count"), "5")
        transforms = calls[0].get("transforms", "")
        self.assertIn("tx 1", transforms)
        self.assertIn("rz 72", transforms)

    def test_color_transforms(self):
        src = "rule start { { h 120 sat 0.8 b 0.9 a 0.5 } box }"
        root = eisenscript_to_xml(src)
        instances = root[0].findall("instance")
        transforms = instances[0].get("transforms", "")
        self.assertIn("h 120", transforms)
        self.assertIn("sat 0.8", transforms)
        self.assertIn("b 0.9", transforms)
        self.assertIn("a 0.5", transforms)

    def test_matrix_transform(self):
        src = "rule start { { m 1 0 0 0 1 0 0 0 1 } box }"
        root = eisenscript_to_xml(src)
        instances = root[0].findall("instance")
        transforms = instances[0].get("transforms", "")
        self.assertTrue(transforms.startswith("m "))
        # Matrix values are floats: 1.0 0.0 ...
        vals = transforms.split()[1:]
        self.assertEqual(len(vals), 9)

    def test_mirror_transforms(self):
        src = "rule start { { fx } box }"
        root = eisenscript_to_xml(src)
        instances = root[0].findall("instance")
        transforms = instances[0].get("transforms", "")
        self.assertIn("fx", transforms)


class XmlToStringTests(unittest.TestCase):
    """Test xml_to_string pretty-printing."""

    def test_produces_string(self):
        src = "rule start { box }"
        root = eisenscript_to_xml(src)
        s = xml_to_string(root)
        self.assertIsInstance(s, str)
        self.assertIn("<rules", s)
        self.assertIn("</rules>", s)

    def test_indented(self):
        src = "rule start { box }"
        root = eisenscript_to_xml(src)
        s = xml_to_string(root)
        lines = s.strip().split("\n")
        # Should have multiple lines with indentation
        self.assertGreater(len(lines), 1)


class FullProgramXmlTests(unittest.TestCase):
    """Test conversion of complete EisenScript programs."""

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
        root = eisenscript_to_xml(src)
        self.assertEqual(root.get("max_depth"), "100")
        rules = root.findall("rule")
        # start (implicit) + 3 r1 rules
        self.assertEqual(len(rules), 4)
        self.assertEqual(rules[0].get("name"), "start")

    def test_original_sample(self):
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
        root = eisenscript_to_xml(src)
        self.assertEqual(root.get("max_depth"), "100")
        rules = root.findall("rule")
        self.assertEqual(len(rules), 4)

        # Check implicit r1
        self.assertEqual(rules[0].get("name"), "r1")
        calls = rules[0].findall("call")
        self.assertEqual(calls[0].get("count"), "36")

        # Check explicit r1 with maxdepth
        self.assertEqual(rules[1].get("name"), "r1")
        self.assertEqual(rules[1].get("max_depth"), "10")

        # Check r2 with weight
        self.assertEqual(rules[3].get("name"), "r2")
        self.assertEqual(rules[3].get("weight"), "2.0")


if __name__ == "__main__":
    unittest.main()
