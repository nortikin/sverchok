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
Tests for the EisenScript interpreter (utils.modules.eisenscript.interpreter).
"""

import unittest

from sverchok.utils.modules.eisenscript.parser import parse
from sverchok.utils.modules.eisenscript.interpreter import (
    Interpreter,
    InterpreterResult,
)


class SimplePrimitiveTests(unittest.TestCase):
    """Test interpretation of simple programs with primitives."""

    def test_single_box(self):
        prog = parse("1 * {} box")
        result = Interpreter.interpret(prog)
        self.assertIn("box", result.matrices)
        self.assertEqual(len(result.matrices["box"]), 1)

    def test_single_sphere(self):
        prog = parse("1 * {} sphere")
        result = Interpreter.interpret(prog)
        self.assertIn("sphere", result.matrices)
        self.assertEqual(len(result.matrices["sphere"]), 1)

    def test_identity_matrix(self):
        prog = parse("1 * {} box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # Check identity
        self.assertAlmostEqual(m[0][0], 1.0)
        self.assertAlmostEqual(m[1][1], 1.0)
        self.assertAlmostEqual(m[2][2], 1.0)
        self.assertAlmostEqual(m[0][3], 0.0)
        self.assertAlmostEqual(m[1][3], 0.0)
        self.assertAlmostEqual(m[2][3], 0.0)

    def test_multiple_primitives(self):
        # Multiple branches in implicit start rule
        prog = parse("""
        1 * {} box
        1 * {} sphere
        """)
        # Parser creates two implicit start rules; interpreter picks one
        # Both should be valid outcomes
        result = Interpreter.interpret(prog)
        # At least one primitive should be present
        total = sum(len(m) for m in result.matrices.values())
        self.assertEqual(total, 1)


class TranslationTests(unittest.TestCase):
    """Test translation transforms."""

    def test_translate_x(self):
        prog = parse("1 * { x 5 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 5.0)

    def test_translate_y(self):
        prog = parse("1 * { y 3 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[1][3], 3.0)

    def test_translate_z(self):
        prog = parse("1 * { z 7 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[2][3], 7.0)

    def test_combined_translation(self):
        prog = parse("1 * { x 1 y 2 z 3 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 1.0)
        self.assertAlmostEqual(m[1][3], 2.0)
        self.assertAlmostEqual(m[2][3], 3.0)


class RotationTests(unittest.TestCase):
    """Test rotation transforms."""

    def test_rotate_z_90(self):
        prog = parse("1 * { rz 90 x 1 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # After rz 90, x 1: position should be (0, 1, 0)
        self.assertAlmostEqual(m[0][3], 0.0, places=5)
        self.assertAlmostEqual(m[1][3], 1.0, places=5)

    def test_rotate_x_90(self):
        prog = parse("1 * { rx 90 z 1 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # After rx 90, z 1: Z axis rotated to -Y, so position is (0, -1, 0)
        self.assertAlmostEqual(m[0][3], 0.0, places=5)
        self.assertAlmostEqual(m[1][3], -1.0, places=5)


class ScaleTests(unittest.TestCase):
    """Test scale transforms."""

    def test_uniform_scale(self):
        prog = parse("1 * { s 2 x 1 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 2.0)

    def test_per_axis_scale(self):
        prog = parse("1 * { s 2 3 4 x 1 y 1 z 1 } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 2.0)
        self.assertAlmostEqual(m[1][3], 3.0)
        self.assertAlmostEqual(m[2][3], 4.0)


class RepetitionTests(unittest.TestCase):
    """Test repetition (loop) semantics."""

    def test_simple_repetition(self):
        prog = parse("5 * { x 1 } box")
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 5)

    def test_repetition_with_translation(self):
        prog = parse("3 * { x 1 } box")
        result = Interpreter.interpret(prog)
        # Cumulative: x=1, x=2, x=3
        self.assertAlmostEqual(result.matrices["box"][0][0][3], 1.0)
        self.assertAlmostEqual(result.matrices["box"][1][0][3], 2.0)
        self.assertAlmostEqual(result.matrices["box"][2][0][3], 3.0)

    def test_nested_repetitions(self):
        prog = parse("2 * { x 1 } 3 * { z 0.5 } box")
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 6)

    def test_triple_nested_repetitions(self):
        prog = parse("2 * { x 1 } 3 * { y 1 } 4 * { z 1 } box")
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 24)


class RuleCallTests(unittest.TestCase):
    """Test rule call semantics."""

    def test_simple_call(self):
        prog = parse("""
        child
        rule child { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 1)

    def test_recursive_rule(self):
        prog = parse("""
        1 * { x 1 } start
        rule start { 1 * { x 1 } start }
        rule start maxdepth 3 { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        # With maxdepth 3, should produce some boxes
        self.assertGreater(len(result.matrices["box"]), 0)

    def test_weighted_rules(self):
        prog = parse("""
        child
        rule child w 10 { 1 * {} box }
        rule child w 1 { 1 * {} sphere }
        """)
        # With seed=0, should pick one deterministically
        result = Interpreter.interpret(prog)
        total = len(result.matrices.get("box", [])) + len(result.matrices.get("sphere", []))
        self.assertEqual(total, 1)


class VariableTests(unittest.TestCase):
    """Test #define variable substitution."""

    def test_variable_count(self):
        prog = parse("#define n 5\nn * { x 1 } box")
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 5)

    def test_variable_transform(self):
        prog = parse("#define d 10\n1 * { x d } box")
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 10.0)

    def test_variable_maxdepth(self):
        prog = parse("""
        #define depth 5
        1 * { x 1 } start
        rule start maxdepth depth { 1 * { x 1 } start }
        rule start maxdepth depth { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        self.assertGreater(len(result.matrices["box"]), 0)


class MaxDepthTests(unittest.TestCase):
    """Test maxdepth and retirement."""

    def test_global_maxdepth(self):
        prog = parse("""
        set maxdepth 10
        1 * { x 1 } start
        rule start { 1 * { x 1 } start }
        rule start { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        self.assertIn("box", result.matrices)

    def test_retirement(self):
        prog = parse("""
        1 * { x 1 } start
        rule start maxdepth 2 > leaf { 1 * { x 1 } start }
        rule leaf { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        self.assertGreater(len(result.matrices["box"]), 0)


class MaxObjectsTests(unittest.TestCase):
    """Test max_objects cap."""

    def test_max_objects_limits(self):
        prog = parse("100 * { x 1 } box")
        result = Interpreter(max_objects=10)._interpret(prog)
        self.assertLessEqual(len(result.matrices["box"]), 10)


class ResultTypeTests(unittest.TestCase):
    """Test InterpreterResult structure."""

    def test_result_is_dict_of_lists(self):
        prog = parse("1 * {} box")
        result = Interpreter.interpret(prog)
        self.assertIsInstance(result, InterpreterResult)
        self.assertIsInstance(result.matrices, dict)
        for key, val in result.matrices.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, list)


if __name__ == "__main__":
    unittest.main()
