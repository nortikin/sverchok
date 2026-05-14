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
Tests for the XML → EisenScript AST converter (utils.modules.eisenscript.from_xml).

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

from sverchok.utils.modules.eisenscript.from_xml import (
    xml_to_ast,
    _parse_transforms_string,
    _safe_eval,
)
from sverchok.utils.modules.eisenscript.ast import (
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    AXIS_X, AXIS_Y, AXIS_Z,
    Translate,
    Rotate,
    Scale,
    MatrixTransform,
    Mirror,
    HueShift,
    SaturationMul,
    BrightnessMul,
    AlphaMul,
    SetColor,
    BlendColor,
    Box,
    Grid,
    Sphere,
    Line,
    Point,
    Triangle,
    IMPLICIT_START_RULE,
)


class SafeEvalTests(unittest.TestCase):
    """Test the safe expression evaluator for constants."""

    def test_simple_number(self):
        self.assertAlmostEqual(_safe_eval("3.14", {}), 3.14)

    def test_arithmetic(self):
        self.assertAlmostEqual(_safe_eval("1+2*3", {}), 7.0)

    def test_power(self):
        self.assertAlmostEqual(_safe_eval("5**0.5", {}), 5 ** 0.5)

    def test_phi_expression(self):
        phi = _safe_eval("((1+5**0.5)/2)", {})
        self.assertAlmostEqual(phi, 1.618033988749895)

    def test_reference_substitution(self):
        defines = {"phi": 1.618}
        self.assertAlmostEqual(_safe_eval("{phi}+1", defines), 2.618)

    def test_nested_reference(self):
        defines = {"phi": 1.618}
        val = _safe_eval("({phi}+0.75)**0.5", defines)
        self.assertAlmostEqual(val, (1.618 + 0.75) ** 0.5)

    def test_unsafe_expression_raises(self):
        with self.assertRaises(ValueError):
            _safe_eval("__import__('os')", {})


class TransformTokenTests(unittest.TestCase):
    """Test individual transformation token parsing."""

    def test_translate_x(self):
        transforms = _parse_transforms_string("tx 5")
        self.assertEqual(len(transforms), 1)
        self.assertIsInstance(transforms[0], Translate)
        self.assertEqual(transforms[0].axis, AXIS_X)
        self.assertAlmostEqual(transforms[0].value, 5.0)

    def test_translate_y(self):
        transforms = _parse_transforms_string("ty -2.5")
        self.assertIsInstance(transforms[0], Translate)
        self.assertEqual(transforms[0].axis, AXIS_Y)
        self.assertAlmostEqual(transforms[0].value, -2.5)

    def test_translate_z(self):
        transforms = _parse_transforms_string("tz 3.14")
        self.assertIsInstance(transforms[0], Translate)
        self.assertEqual(transforms[0].axis, AXIS_Z)
        self.assertAlmostEqual(transforms[0].value, 3.14)

    def test_rotate_x(self):
        transforms = _parse_transforms_string("rx 90")
        self.assertIsInstance(transforms[0], Rotate)
        self.assertEqual(transforms[0].axis, AXIS_X)
        self.assertAlmostEqual(transforms[0].angle, 90.0)

    def test_rotate_y(self):
        transforms = _parse_transforms_string("ry 45")
        self.assertIsInstance(transforms[0], Rotate)
        self.assertEqual(transforms[0].axis, AXIS_Y)
        self.assertAlmostEqual(transforms[0].angle, 45.0)

    def test_rotate_z_negative(self):
        transforms = _parse_transforms_string("rz -30")
        self.assertIsInstance(transforms[0], Rotate)
        self.assertEqual(transforms[0].axis, AXIS_Z)
        self.assertAlmostEqual(transforms[0].angle, -30.0)

    def test_scale_uniform(self):
        transforms = _parse_transforms_string("sa 2")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].x, 2.0)
        self.assertTrue(transforms[0].is_uniform)

    def test_scale_per_axis(self):
        transforms = _parse_transforms_string("s 0.5 1 2")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].x, 0.5)
        self.assertAlmostEqual(transforms[0].y, 1.0)
        self.assertAlmostEqual(transforms[0].z, 2.0)
        self.assertFalse(transforms[0].is_uniform)

    def test_scale_x_only(self):
        transforms = _parse_transforms_string("sx 3")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].x, 3.0)
        self.assertIsNone(transforms[0].y)
        self.assertIsNone(transforms[0].z)

    def test_scale_y_only(self):
        transforms = _parse_transforms_string("sy 2")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].y, 2.0)

    def test_scale_z_only(self):
        transforms = _parse_transforms_string("sz 1.5")
        self.assertIsInstance(transforms[0], Scale)
        self.assertAlmostEqual(transforms[0].z, 1.5)

    def test_matrix_transform(self):
        transforms = _parse_transforms_string("m 1 0 0 0 1 0 0 0 1")
        self.assertIsInstance(transforms[0], MatrixTransform)
        self.assertEqual(len(transforms[0].matrix), 9)

    def test_mirror_x(self):
        transforms = _parse_transforms_string("fx")
        self.assertIsInstance(transforms[0], Mirror)
        self.assertEqual(transforms[0].axis, AXIS_X)

    def test_mirror_y(self):
        transforms = _parse_transforms_string("fy")
        self.assertIsInstance(transforms[0], Mirror)
        self.assertEqual(transforms[0].axis, AXIS_Y)

    def test_mirror_z(self):
        transforms = _parse_transforms_string("fz")
        self.assertIsInstance(transforms[0], Mirror)
        self.assertEqual(transforms[0].axis, AXIS_Z)

    def test_hue_short(self):
        transforms = _parse_transforms_string("h 180")
        self.assertIsInstance(transforms[0], HueShift)
        self.assertAlmostEqual(transforms[0].value, 180.0)

    def test_hue_long(self):
        transforms = _parse_transforms_string("hue 60")
        self.assertIsInstance(transforms[0], HueShift)
        self.assertAlmostEqual(transforms[0].value, 60.0)

    def test_saturation(self):
        transforms = _parse_transforms_string("sat 0.5")
        self.assertIsInstance(transforms[0], SaturationMul)
        self.assertAlmostEqual(transforms[0].value, 0.5)

    def test_brightness_short(self):
        transforms = _parse_transforms_string("b 0.8")
        self.assertIsInstance(transforms[0], BrightnessMul)
        self.assertAlmostEqual(transforms[0].value, 0.8)

    def test_brightness_long(self):
        transforms = _parse_transforms_string("brightness 0.9")
        self.assertIsInstance(transforms[0], BrightnessMul)
        self.assertAlmostEqual(transforms[0].value, 0.9)

    def test_alpha_short(self):
        transforms = _parse_transforms_string("a 0.5")
        self.assertIsInstance(transforms[0], AlphaMul)
        self.assertAlmostEqual(transforms[0].value, 0.5)

    def test_alpha_long(self):
        transforms = _parse_transforms_string("alpha 0.75")
        self.assertIsInstance(transforms[0], AlphaMul)
        self.assertAlmostEqual(transforms[0].value, 0.75)

    def test_set_color(self):
        transforms = _parse_transforms_string("color red")
        self.assertIsInstance(transforms[0], SetColor)
        self.assertEqual(transforms[0].color, "red")

    def test_blend_color(self):
        transforms = _parse_transforms_string("blend blue 0.5")
        self.assertIsInstance(transforms[0], BlendColor)
        self.assertEqual(transforms[0].color, "blue")
        self.assertAlmostEqual(transforms[0].strength, 0.5)

    def test_multiple_transforms(self):
        transforms = _parse_transforms_string("tx 1 rz 90 sa 0.5")
        self.assertEqual(len(transforms), 3)
        self.assertIsInstance(transforms[0], Translate)
        self.assertIsInstance(transforms[1], Rotate)
        self.assertIsInstance(transforms[2], Scale)

    def test_empty_string(self):
        transforms = _parse_transforms_string("")
        self.assertEqual(transforms, [])

    def test_whitespace_only(self):
        transforms = _parse_transforms_string("   ")
        self.assertEqual(transforms, [])


class XmlToAstBasicTests(unittest.TestCase):
    """Test basic XML → AST conversion."""

    def _parse(self, xml_str):
        """Helper: parse XML string to Program."""
        root = ET.fromstring(xml_str)
        return xml_to_ast(root)

    def test_empty_program(self):
        prog = self._parse('<rules/>')
        self.assertIsInstance(prog, Program)
        self.assertEqual(len(prog.rules), 0)
        self.assertEqual(len(prog.settings), 0)

    def test_global_maxdepth(self):
        prog = self._parse('<rules max_depth="100"/>')
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].name, "maxdepth")
        self.assertEqual(prog.settings[0].value, 100)

    def test_simple_rule_with_call(self):
        xml = '''
        <rules>
            <rule name="entry">
                <call rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertEqual(len(prog.rules), 2)
        self.assertEqual(prog.rules[0].name, IMPLICIT_START_RULE)
        self.assertEqual(prog.rules[1].name, "child")

    def test_rule_with_weight(self):
        xml = '''
        <rules>
            <rule name="r1" weight="10">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertAlmostEqual(prog.rules[0].weight, 10.0)

    def test_rule_with_maxdepth(self):
        xml = '''
        <rules>
            <rule name="r1" max_depth="5">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertEqual(prog.rules[0].maxdepth, 5)

    def test_rule_with_successor(self):
        xml = '''
        <rules>
            <rule name="r1" max_depth="5" successor="leaf">
                <call rule="r1"/>
            </rule>
            <rule name="leaf">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertEqual(prog.rules[0].retirement_rule, "leaf")

    def test_call_with_count(self):
        xml = '''
        <rules>
            <rule name="entry">
                <call count="10" rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        self.assertEqual(len(branch.repetitions), 1)
        self.assertEqual(branch.repetitions[0].count, 10)

    def test_call_with_transforms(self):
        xml = '''
        <rules>
            <rule name="entry">
                <call transforms="tx 1 rz 90" rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        self.assertEqual(len(branch.repetitions), 1)
        self.assertEqual(branch.repetitions[0].count, 1)
        self.assertEqual(len(branch.repetitions[0].transformations), 2)

    def test_call_with_count_and_transforms(self):
        xml = '''
        <rules>
            <rule name="entry">
                <call count="5" transforms="rz 72" rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        rep = branch.repetitions[0]
        self.assertEqual(rep.count, 5)
        self.assertEqual(len(rep.transformations), 1)
        self.assertIsInstance(rep.transformations[0], Rotate)

    def test_instance_all_primitives(self):
        xml = '''
        <rules>
            <rule name="entry">
                <instance shape="box"/>
                <instance shape="grid"/>
                <instance shape="sphere"/>
                <instance shape="line"/>
                <instance shape="point"/>
                <instance shape="triangle"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        primitives = [type(b.terminal) for b in prog.rules[0].body]
        self.assertIn(Box, primitives)
        self.assertIn(Grid, primitives)
        self.assertIn(Sphere, primitives)
        self.assertIn(Line, primitives)
        self.assertIn(Point, primitives)
        self.assertIn(Triangle, primitives)

    def test_instance_with_transforms(self):
        xml = '''
        <rules>
            <rule name="entry">
                <instance transforms="sa 3 ry 90" shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        self.assertEqual(len(branch.repetitions), 1)
        self.assertEqual(len(branch.repetitions[0].transformations), 2)

    def test_instance_with_count(self):
        xml = '''
        <rules>
            <rule name="entry">
                <instance count="3" shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        self.assertEqual(len(branch.repetitions), 1)
        self.assertEqual(branch.repetitions[0].count, 3)

    def test_constants(self):
        xml = '''
        <rules>
            <constants phi="((1+5**0.5)/2)"/>
            <rule name="entry">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertIn("phi", prog.defines)
        self.assertAlmostEqual(prog.defines["phi"], 1.618033988749895)

    def test_constants_with_reference(self):
        xml = '''
        <rules>
            <constants phi="((1+5**0.5)/2)"/>
            <constants s1="1/{phi}"/>
            <rule name="entry">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertIn("phi", prog.defines)
        self.assertIn("s1", prog.defines)
        self.assertAlmostEqual(prog.defines["s1"], 1.0 / prog.defines["phi"])

    def test_multiple_branches_in_rule(self):
        xml = '''
        <rules>
            <rule name="entry">
                <instance shape="box"/>
                <call rule="child"/>
                <call transforms="rz 180" rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="sphere"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertEqual(len(prog.rules[0].body), 3)

    def test_entry_rule_maps_to_implicit_start(self):
        """XML rule named 'entry' is the implicit start rule."""
        xml = '''
        <rules>
            <rule name="entry">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertEqual(prog.rules[0].name, IMPLICIT_START_RULE)

    def test_non_entry_rule_preserved(self):
        """Rule names other than 'entry' are preserved as-is."""
        xml = '''
        <rules>
            <rule name="start">
                <instance shape="box"/>
            </rule>
            <rule name="child">
                <instance shape="sphere"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        self.assertEqual(prog.rules[0].name, "start")
        self.assertEqual(prog.rules[1].name, "child")

    def test_ambiguous_rules(self):
        xml = '''
        <rules>
            <rule name="r1" weight="10">
                <instance shape="box"/>
            </rule>
            <rule name="r1" weight="20">
                <instance shape="sphere"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        r1_rules = [r for r in prog.rules if r.name == "r1"]
        self.assertEqual(len(r1_rules), 2)
        self.assertAlmostEqual(r1_rules[0].weight, 10.0)
        self.assertAlmostEqual(r1_rules[1].weight, 20.0)

    def test_individual_transform_attributes(self):
        """XML can use individual attributes like rz="72" instead of transforms="rz 72"."""
        xml = '''
        <rules>
            <rule name="entry">
                <call count="5" rz="72" rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        rep = branch.repetitions[0]
        self.assertEqual(rep.count, 5)
        self.assertEqual(len(rep.transformations), 1)
        self.assertIsInstance(rep.transformations[0], Rotate)
        self.assertEqual(rep.transformations[0].axis, AXIS_Z)
        self.assertAlmostEqual(rep.transformations[0].angle, 72.0)

    def test_combined_and_individual_transforms(self):
        """Both transforms="..." and individual attributes are supported."""
        xml = '''
        <rules>
            <rule name="entry">
                <call transforms="tx 1" rz="90" rule="child"/>
            </rule>
            <rule name="child">
                <instance shape="box"/>
            </rule>
        </rules>
        '''
        prog = self._parse(xml)
        branch = prog.rules[0].body[0]
        rep = branch.repetitions[0]
        self.assertEqual(len(rep.transformations), 2)
        self.assertIsInstance(rep.transformations[0], Translate)
        self.assertIsInstance(rep.transformations[1], Rotate)


class FullProgramXmlTests(unittest.TestCase):
    """Test conversion of complete XML programs from examples."""

    def _parse_file(self, path):
        """Helper: parse XML file to Program."""
        tree = ET.parse(path)
        return xml_to_ast(tree.getroot())

    def test_tree_example(self):
        prog = self._parse_file("generative-art-examples/tree.xml")
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].value, 200)
        # entry rule + 4 spiral rules
        self.assertEqual(len(prog.rules), 5)

    def test_fern_example(self):
        prog = self._parse_file("generative-art-examples/fern.xml")
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].value, 2000)
        self.assertEqual(len(prog.rules), 4)  # entry, curl1, curl2, curlsmall

    def test_spirals_6_example(self):
        prog = self._parse_file("generative-art-examples/spirals_6.xml")
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].value, 150)

    def test_pentaflake_example(self):
        prog = self._parse_file("generative-art-examples/pentaflake.xml")
        self.assertEqual(len(prog.rules), 3)  # entry, R1, pentagon
        r1 = [r for r in prog.rules if r.name == "R1"][0]
        self.assertEqual(r1.retirement_rule, "pentagon")

    def test_pipes_example(self):
        prog = self._parse_file("generative-art-examples/pipes.xml")
        r1_rules = [r for r in prog.rules if r.name == "R1"]
        self.assertEqual(len(r1_rules), 7)  # 7 ambiguous R1 rules

    def test_ball_example(self):
        prog = self._parse_file("generative-art-examples/ball.xml")
        r1_rules = [r for r in prog.rules if r.name == "R1"]
        self.assertEqual(len(r1_rules), 2)

    def test_nouveau_example(self):
        prog = self._parse_file("generative-art-examples/nouveau.xml")
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].value, 2000)

    def test_octopus_example(self):
        prog = self._parse_file("octopus.xml")
        self.assertEqual(len(prog.settings), 1)
        self.assertEqual(prog.settings[0].value, 100)


class RoundTripTests(unittest.TestCase):
    """Test that EisenScript → XML → AST round-trip preserves structure."""

    def test_simple_round_trip(self):
        from sverchok.utils.modules.eisenscript.parser import parse
        from sverchok.utils.modules.eisenscript.to_xml import ast_to_xml

        source = "10 * { rz 36 z 0.5 s 0.95 } box"
        original = parse(source)
        xml = ast_to_xml(original)
        restored = xml_to_ast(xml)

        # Both should have same structure
        self.assertEqual(len(original.rules), len(restored.rules))
        self.assertEqual(len(original.rules[0].body), len(restored.rules[0].body))

    def test_complex_round_trip(self):
        from sverchok.utils.modules.eisenscript.parser import parse
        from sverchok.utils.modules.eisenscript.to_xml import ast_to_xml

        source = """
        set maxdepth 100
        rule r1 {
            10 * { rz 36 z 0.5 s 0.95 } box
        }
        """
        original = parse(source)
        xml = ast_to_xml(original)
        restored = xml_to_ast(xml)

        self.assertEqual(len(original.settings), len(restored.settings))
        self.assertEqual(original.settings[0].name, restored.settings[0].name)
        self.assertEqual(original.settings[0].value, restored.settings[0].value)


if __name__ == "__main__":
    unittest.main()
