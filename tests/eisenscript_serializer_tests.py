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
Tests for the EisenScript AST → text serializer
(utils.modules.eisenscript.serializer).

Standalone unittest — no Blender dependency.
"""

import unittest
import sys
import os

# Add project root to path for standalone execution
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sverchok.utils.modules.eisenscript.serializer import (
    ast_to_string,
    _fmt_num,
    _trans_to_str,
    _primitive_to_str,
    _branch_to_str,
    _rule_to_str,
    _set_to_str,
)
from sverchok.utils.modules.eisenscript.ast import (
    Program,
    SetStatement,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    VariableRef,
    AXIS_X, AXIS_Y, AXIS_Z,
    Translate,
    Rotate,
    Mirror,
    Scale,
    MatrixTransform,
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


class FmtNumTests(unittest.TestCase):
    """Test numeric formatting helper."""

    def test_integer(self):
        self.assertEqual(_fmt_num(3), "3")

    def test_float(self):
        self.assertEqual(_fmt_num(3.14), "3.14")

    def test_float_round(self):
        self.assertEqual(_fmt_num(3.0), "3")

    def test_negative(self):
        self.assertEqual(_fmt_num(-2), "-2")

    def test_small_float(self):
        self.assertEqual(_fmt_num(0.5), "0.5")

    def test_variable_ref(self):
        self.assertEqual(_fmt_num(VariableRef("phi")), "phi")

    def test_large_integer(self):
        self.assertEqual(_fmt_num(1000000), "1000000")


class TransformToTests(unittest.TestCase):
    """Test transformation → string conversion."""

    def test_translate_x(self):
        self.assertEqual(_trans_to_str(Translate(AXIS_X, 5)), "x 5")

    def test_translate_y(self):
        self.assertEqual(_trans_to_str(Translate(AXIS_Y, -2.5)), "y -2.5")

    def test_translate_z(self):
        self.assertEqual(_trans_to_str(Translate(AXIS_Z, 3.14)), "z 3.14")

    def test_rotate_x(self):
        self.assertEqual(_trans_to_str(Rotate(AXIS_X, 90)), "rx 90")

    def test_rotate_y(self):
        self.assertEqual(_trans_to_str(Rotate(AXIS_Y, 45)), "ry 45")

    def test_rotate_z_negative(self):
        self.assertEqual(_trans_to_str(Rotate(AXIS_Z, -30)), "rz -30")

    def test_scale_uniform(self):
        self.assertEqual(_trans_to_str(Scale(2)), "s 2")

    def test_scale_per_axis(self):
        self.assertEqual(_trans_to_str(Scale(0.5, 1, 2)), "s 0.5 1 2")

    def test_scale_partial(self):
        self.assertEqual(_trans_to_str(Scale(0.5, 1, None)), "s 0.5 1 1")

    def test_mirror_x(self):
        self.assertEqual(_trans_to_str(Mirror(AXIS_X)), "fx")

    def test_mirror_y(self):
        self.assertEqual(_trans_to_str(Mirror(AXIS_Y)), "fy")

    def test_mirror_z(self):
        self.assertEqual(_trans_to_str(Mirror(AXIS_Z)), "fz")

    def test_matrix(self):
        m = MatrixTransform([1, 0, 0, 0, 1, 0, 0, 0, 1])
        self.assertEqual(_trans_to_str(m), "m 1 0 0 0 1 0 0 0 1")

    def test_hue(self):
        self.assertEqual(_trans_to_str(HueShift(180)), "hue 180")

    def test_saturation(self):
        self.assertEqual(_trans_to_str(SaturationMul(0.5)), "sat 0.5")

    def test_brightness(self):
        self.assertEqual(_trans_to_str(BrightnessMul(0.8)), "brightness 0.8")

    def test_alpha(self):
        self.assertEqual(_trans_to_str(AlphaMul(0.5)), "alpha 0.5")

    def test_set_color(self):
        self.assertEqual(_trans_to_str(SetColor("red")), "color red")

    def test_blend_color(self):
        self.assertEqual(
            _trans_to_str(BlendColor("blue", 0.5)),
            "blend blue 0.5",
        )

    def test_variable_value(self):
        self.assertEqual(
            _trans_to_str(Translate(AXIS_X, VariableRef("offset"))),
            "x offset",
        )


class PrimitiveToTests(unittest.TestCase):
    """Test primitive → string conversion."""

    def test_box(self):
        self.assertEqual(_primitive_to_str(Box()), "box")

    def test_grid(self):
        self.assertEqual(_primitive_to_str(Grid()), "grid")

    def test_sphere(self):
        self.assertEqual(_primitive_to_str(Sphere()), "sphere")

    def test_line(self):
        self.assertEqual(_primitive_to_str(Line()), "line")

    def test_point(self):
        self.assertEqual(_primitive_to_str(Point()), "point")

    def test_triangle_empty(self):
        self.assertEqual(_primitive_to_str(Triangle([])), "triangle")

    def test_triangle_with_vertices(self):
        t = Triangle([(0, 0, 0), (1, 0, 0), (0.5, 0.5, 0)])
        self.assertEqual(
            _primitive_to_str(t),
            "Triangle[0,0,0;1,0,0;0.5,0.5,0]",
        )


class BranchToTests(unittest.TestCase):
    """Test branch → string conversion."""

    def test_simple_primitive(self):
        branch = Branch(terminal=Box())
        self.assertEqual(_branch_to_str(branch), "box")

    def test_simple_call(self):
        branch = Branch(terminal=RuleRef("child"))
        self.assertEqual(_branch_to_str(branch), "child")

    def test_call_with_repetition(self):
        branch = Branch(
            repetitions=[Repeat(10, [Translate(AXIS_X, 1)])],
            terminal=RuleRef("child"),
        )
        self.assertEqual(_branch_to_str(branch), "10 * {x 1} child")

    def test_call_with_repetition_and_transforms(self):
        branch = Branch(
            repetitions=[Repeat(5, [Rotate(AXIS_Z, 72), Translate(AXIS_Z, 0.5)])],
            terminal=Box(),
        )
        self.assertEqual(
            _branch_to_str(branch),
            "5 * {rz 72 z 0.5} box",
        )

    def test_multiple_repetitions(self):
        branch = Branch(
            repetitions=[
                Repeat(3, [Rotate(AXIS_Y, 120)]),
                Repeat(1, [Translate(AXIS_Z, 1)]),
            ],
            terminal=RuleRef("child"),
        )
        self.assertEqual(
            _branch_to_str(branch),
            "3 * {ry 120} 1 * {z 1} child",
        )

    def test_call_with_retirement(self):
        branch = Branch(
            terminal=RuleRef("r1", retirement_depth=5),
        )
        self.assertEqual(_branch_to_str(branch), "md 5 r1")

    def test_call_with_retirement_and_successor(self):
        branch = Branch(
            terminal=RuleRef("r1", retirement_depth=5, retirement_rule="leaf"),
        )
        self.assertEqual(_branch_to_str(branch), "md 5 > leaf r1")

    def test_empty_repetition(self):
        branch = Branch(
            repetitions=[Repeat(1, [])],
            terminal=Box(),
        )
        self.assertEqual(_branch_to_str(branch), "1 * {} box")


class RuleToTests(unittest.TestCase):
    """Test rule → string conversion."""

    def test_simple_rule(self):
        rule = Rule("r1", body=[Branch(terminal=Box())])
        result = _rule_to_str(rule)
        self.assertIn("rule r1", result)
        self.assertIn("box", result)

    def test_rule_with_maxdepth(self):
        rule = Rule("r1", maxdepth=10, body=[Branch(terminal=Box())])
        result = _rule_to_str(rule)
        self.assertIn("maxdepth 10", result)

    def test_rule_with_maxdepth_and_successor(self):
        rule = Rule("r1", maxdepth=10, retirement_rule="leaf",
                     body=[Branch(terminal=Box())])
        result = _rule_to_str(rule)
        self.assertIn("maxdepth 10 > leaf", result)

    def test_rule_with_weight(self):
        rule = Rule("r1", weight=5, body=[Branch(terminal=Box())])
        result = _rule_to_str(rule)
        self.assertIn("weight 5", result)

    def test_rule_with_default_weight(self):
        rule = Rule("r1", weight=1.0, body=[Branch(terminal=Box())])
        result = _rule_to_str(rule)
        self.assertNotIn("weight", result)

    def test_empty_rule(self):
        rule = Rule("r1", body=[])
        result = _rule_to_str(rule)
        self.assertIn("{}", result)

    def test_rule_with_multiple_branches(self):
        rule = Rule("r1", body=[
            Branch(terminal=Box()),
            Branch(terminal=RuleRef("child")),
        ])
        result = _rule_to_str(rule)
        self.assertIn("box", result)
        self.assertIn("child", result)


class SetToTests(unittest.TestCase):
    """Test set statement → string conversion."""

    def test_maxdepth(self):
        self.assertEqual(_set_to_str(SetStatement("maxdepth", 100)),
                         "set maxdepth 100")

    def test_maxobjects(self):
        self.assertEqual(_set_to_str(SetStatement("maxobjects", 5000)),
                         "set maxobjects 5000")

    def test_minsize(self):
        self.assertEqual(_set_to_str(SetStatement("minsize", 0.01)),
                         "set minsize 0.01")

    def test_maxsize(self):
        self.assertEqual(_set_to_str(SetStatement("maxsize", 100)),
                         "set maxsize 100")

    def test_seed_integer(self):
        self.assertEqual(_set_to_str(SetStatement("seed", 42)),
                         "set seed 42")

    def test_seed_initial(self):
        self.assertEqual(_set_to_str(SetStatement("seed", "initial")),
                         "set seed initial")

    def test_background(self):
        self.assertEqual(_set_to_str(SetStatement("background", "#FFFFFF")),
                         "set background #FFFFFF")

    def test_color(self):
        self.assertEqual(_set_to_str(SetStatement("color", "random")),
                         "set color random")

    def test_colorpool(self):
        self.assertEqual(_set_to_str(SetStatement("colorpool", "randomhue")),
                         "set colorpool randomhue")


class AstToStringTests(unittest.TestCase):
    """Test full program serialization."""

    def test_empty_program(self):
        prog = Program()
        self.assertEqual(ast_to_string(prog), "")

    def test_implicit_start_rule(self):
        prog = Program(rules=[
            Rule(name=IMPLICIT_START_RULE, body=[
                Branch(terminal=Box()),
            ]),
        ])
        result = ast_to_string(prog)
        self.assertIn("box", result)
        self.assertNotIn("rule ###START###", result)

    def test_simple_rule(self):
        prog = Program(rules=[
            Rule(name="r1", body=[
                Branch(terminal=Box()),
            ]),
        ])
        result = ast_to_string(prog)
        self.assertIn("rule r1", result)
        self.assertIn("box", result)

    def test_with_settings(self):
        prog = Program(
            settings=[SetStatement("maxdepth", 100)],
            rules=[
                Rule(name="r1", body=[Branch(terminal=Box())]),
            ],
        )
        result = ast_to_string(prog)
        self.assertIn("set maxdepth 100", result)

    def test_with_defines(self):
        prog = Program(
            defines={"phi": 1.618, "n": 10},
            rules=[
                Rule(name="r1", body=[Branch(terminal=Box())]),
            ],
        )
        result = ast_to_string(prog)
        self.assertIn("#define phi 1.618", result)
        self.assertIn("#define n 10", result)

    def test_complex_program(self):
        prog = Program(
            defines={"phi": 1.618},
            settings=[SetStatement("maxdepth", 100)],
            rules=[
                Rule(name=IMPLICIT_START_RULE, body=[
                    Branch(
                        repetitions=[Repeat(5, [Rotate(AXIS_Z, 72)])],
                        terminal=RuleRef("r1"),
                    ),
                ]),
                Rule(name="r1", maxdepth=10, retirement_rule="leaf", body=[
                    Branch(
                        repetitions=[Repeat(1, [Translate(AXIS_Z, 1), Scale(0.9)])],
                        terminal=RuleRef("r1"),
                    ),
                    Branch(terminal=Box()),
                ]),
                Rule(name="leaf", body=[
                    Branch(terminal=Sphere()),
                ]),
            ],
        )
        result = ast_to_string(prog)
        self.assertIn("#define phi 1.618", result)
        self.assertIn("set maxdepth 100", result)
        self.assertIn("5 * {rz 72} r1", result)
        self.assertIn("maxdepth 10 > leaf", result)
        self.assertIn("1 * {z 1 s 0.9} r1", result)
        self.assertIn("box", result)
        self.assertIn("sphere", result)

    def test_all_primitives(self):
        prog = Program(rules=[
            Rule(name=IMPLICIT_START_RULE, body=[
                Branch(terminal=Box()),
                Branch(terminal=Grid()),
                Branch(terminal=Sphere()),
                Branch(terminal=Line()),
                Branch(terminal=Point()),
                Branch(terminal=Triangle([])),
            ]),
        ])
        result = ast_to_string(prog)
        for prim in ("box", "grid", "sphere", "line", "point", "triangle"):
            self.assertIn(prim, result)

    def test_all_transformations(self):
        prog = Program(rules=[
            Rule(name=IMPLICIT_START_RULE, body=[
                Branch(
                    repetitions=[Repeat(1, [
                        Translate(AXIS_X, 1),
                        Translate(AXIS_Y, 2),
                        Translate(AXIS_Z, 3),
                        Rotate(AXIS_X, 30),
                        Rotate(AXIS_Y, 45),
                        Rotate(AXIS_Z, 60),
                        Scale(0.5),
                        Scale(1, 2, 3),
                        Mirror(AXIS_X),
                        HueShift(180),
                        SaturationMul(0.8),
                        BrightnessMul(0.9),
                        AlphaMul(0.5),
                        SetColor("red"),
                        BlendColor("blue", 0.3),
                    ])],
                    terminal=Box(),
                ),
            ]),
        ])
        result = ast_to_string(prog)
        self.assertIn("x 1", result)
        self.assertIn("y 2", result)
        self.assertIn("z 3", result)
        self.assertIn("rx 30", result)
        self.assertIn("ry 45", result)
        self.assertIn("rz 60", result)
        self.assertIn("s 0.5", result)
        self.assertIn("s 1 2 3", result)
        self.assertIn("fx", result)
        self.assertIn("hue 180", result)
        self.assertIn("sat 0.8", result)
        self.assertIn("brightness 0.9", result)
        self.assertIn("alpha 0.5", result)
        self.assertIn("color red", result)
        self.assertIn("blend blue 0.3", result)


class RoundTripTests(unittest.TestCase):
    """Test parse → serialize → parse round-trip."""

    def _round_trip(self, source):
        """Parse source, serialize, parse again, return both ASTs."""
        from sverchok.utils.modules.eisenscript.parser import parse
        original = parse(source)
        text = ast_to_string(original)
        restored = parse(text)
        return original, restored, text

    def test_simple_branch(self):
        source = "box"
        orig, restored, text = self._round_trip(source)
        self.assertEqual(len(orig.rules), len(restored.rules))
        self.assertEqual(len(orig.rules[0].body), len(restored.rules[0].body))

    def test_with_repetition(self):
        source = "10 * { rz 36 z 0.5 s 0.95 } box"
        orig, restored, text = self._round_trip(source)
        self.assertEqual(len(orig.rules), len(restored.rules))
        orig_rep = orig.rules[0].body[0].repetitions[0]
        rest_rep = restored.rules[0].body[0].repetitions[0]
        self.assertEqual(orig_rep.count, rest_rep.count)
        self.assertEqual(len(orig_rep.transformations),
                         len(rest_rep.transformations))

    def test_with_rule(self):
        source = """
        set maxdepth 100
        rule r1 {
            10 * { rz 36 z 0.5 s 0.95 } box
        }
        """
        orig, restored, text = self._round_trip(source)
        self.assertEqual(len(orig.settings), len(restored.settings))
        self.assertEqual(orig.settings[0].name, restored.settings[0].name)
        self.assertEqual(orig.settings[0].value, restored.settings[0].value)

    def test_with_define(self):
        source = """
        #define n 10
        #define angle 36
        {rz angle z 0.5 s 0.95} box
        """
        orig, restored, text = self._round_trip(source)
        self.assertEqual(orig.defines, restored.defines)

    def test_with_retirement(self):
        source = """
        rule r1 maxdepth 10 > leaf {
            r1
        }
        rule leaf {
            box
        }
        """
        orig, restored, text = self._round_trip(source)
        r1_orig = [r for r in orig.rules if r.name == "r1"][0]
        r1_rest = [r for r in restored.rules if r.name == "r1"][0]
        self.assertEqual(r1_orig.maxdepth, r1_rest.maxdepth)
        self.assertEqual(r1_orig.retirement_rule, r1_rest.retirement_rule)

    def test_with_weight(self):
        source = """
        rule r1 w 10 {
            box
        }
        rule r1 w 20 {
            sphere
        }
        """
        orig, restored, text = self._round_trip(source)
        r1_orig = [r for r in orig.rules if r.name == "r1"]
        r1_rest = [r for r in restored.rules if r.name == "r1"]
        self.assertEqual(len(r1_orig), len(r1_rest))
        for a, b in zip(r1_orig, r1_rest):
            self.assertAlmostEqual(a.weight, b.weight)

    def test_complex_program(self):
        source = """
        set maxdepth 100
        #define n 10
        #define angle 36

        rule r1 maxdepth 10 > leaf {
            n * { rz angle z 0.5 s 0.95 } r1
            box
        }

        rule leaf {
            sphere
        }
        """
        orig, restored, text = self._round_trip(source)
        self.assertEqual(len(orig.defines), len(restored.defines))
        self.assertEqual(len(orig.settings), len(restored.settings))
        self.assertEqual(len(orig.rules), len(restored.rules))


if __name__ == "__main__":
    unittest.main()
