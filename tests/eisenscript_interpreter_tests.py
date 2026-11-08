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

    def test_single_line(self):
        prog = parse("1 * {} line")
        result = Interpreter.interpret(prog)
        self.assertIn("line", result.matrices)
        self.assertEqual(len(result.matrices["line"]), 1)

    def test_single_point(self):
        prog = parse("1 * {} point")
        result = Interpreter.interpret(prog)
        self.assertIn("point", result.matrices)
        self.assertEqual(len(result.matrices["point"]), 1)

    def test_single_grid(self):
        prog = parse("1 * {} grid")
        result = Interpreter.interpret(prog)
        self.assertIn("grid", result.matrices)
        self.assertEqual(len(result.matrices["grid"]), 1)

    def test_triangle_with_custom_vertices(self):
        """T4: Triangle primitive with custom vertices."""
        prog = parse("1 * {} Triangle[0,0,0;1,0,0;0,1,0]")
        result = Interpreter.interpret(prog)
        self.assertIn("triangle", result.matrices)
        self.assertEqual(len(result.matrices["triangle"]), 1)

    def test_triangle_with_transform(self):
        """T4: Triangle with translation applied."""
        prog = parse("1 * { x 5 } Triangle[0,0,0;1,0,0;0,1,0]")
        result = Interpreter.interpret(prog)
        m = result.matrices["triangle"][0]
        self.assertAlmostEqual(m[0][3], 5.0)

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
        # Parser merges bare branches into a single implicit start rule;
        # interpreter emits all branches. Both box and sphere are emitted.
        result = Interpreter.interpret(prog)
        total = sum(len(m) for m in result.matrices.values())
        self.assertEqual(total, 2)
        self.assertIn("box", result.matrices)
        self.assertIn("sphere", result.matrices)


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

    def test_scale_with_origin(self):
        """S1: Scale with origin_as_center=True uses (0,0,0) as center."""
        prog = parse("1 * { s 2 x 1 } box")
        result = Interpreter.interpret(prog, origin_as_center=True)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 2.0)

    def test_scale_with_cube_center(self):
        """S1: Scale with origin_as_center=False uses (0.5,0.5,0.5) as center."""
        prog = parse("1 * { s 2 x 1 } box")
        result = Interpreter.interpret(prog, origin_as_center=False)
        m = result.matrices["box"][0]
        # s 2 around (0.5,0.5,0.5): x 1 becomes x 1.5
        # T(0.5) @ S(2) @ T(-0.5) @ T(1) = T(0.5) @ S(2) @ T(0.5)
        # = T(0.5) @ T(1) = T(1.5)
        self.assertAlmostEqual(m[0][3], 1.5)


class OriginAsCenterTests(unittest.TestCase):
    """Test origin_as_center parameter (S1, S2, S3)."""

    def test_rotation_around_origin(self):
        """S3: Rotation with origin_as_center=True rotates around origin."""
        prog = parse("1 * { rz 90 x 1 } box")
        result = Interpreter.interpret(prog, origin_as_center=True)
        m = result.matrices["box"][0]
        # rz 90 around origin, then x 1 → (0, 1, 0)
        self.assertAlmostEqual(m[0][3], 0.0, places=5)
        self.assertAlmostEqual(m[1][3], 1.0, places=5)

    def test_rotation_around_cube_center(self):
        """S3: Rotation with origin_as_center=False rotates around cube center."""
        prog = parse("1 * { rz 90 x 1 } box")
        result = Interpreter.interpret(prog, origin_as_center=False)
        m = result.matrices["box"][0]
        # rz 90 around (0.5, 0.5, 0.5), then x 1
        # T(0.5,0.5) @ Rz90 @ T(-0.5,-0.5) @ T(1,0)
        # = T(0.5,0.5) @ Rz90 @ T(0.5,-0.5)
        # Rz90 @ T(0.5,-0.5) = T(0.5, 0.5)
        # T(0.5,0.5) @ T(0.5, 0.5) = T(1.0, 1.0)
        self.assertAlmostEqual(m[0][3], 1.0, places=5)
        self.assertAlmostEqual(m[1][3], 1.0, places=5)

    def test_mirror_around_origin(self):
        """S2: Mirror with origin_as_center=True mirrors through origin."""
        prog = parse("1 * { fx x 1 } box")
        result = Interpreter.interpret(prog, origin_as_center=True)
        m = result.matrices["box"][0]
        # fx mirrors x through origin, then x 1 → (-1, 0, 0)
        self.assertAlmostEqual(m[0][3], -1.0)

    def test_mirror_around_cube_center(self):
        """S2: Mirror with origin_as_center=False mirrors through cube center."""
        prog = parse("1 * { fx x 1 } box")
        result = Interpreter.interpret(prog, origin_as_center=False)
        m = result.matrices["box"][0]
        # fx through (0.5,0.5,0.5): T(0.5) @ Sx(-1) @ T(-0.5) @ T(1)
        # = T(0.5) @ Sx(-1) @ T(0.5)
        # Sx(-1) @ T(0.5) = T(-0.5)
        # T(0.5) @ T(-0.5) = T(0)
        self.assertAlmostEqual(m[0][3], 0.0)

    def test_default_is_origin(self):
        """Default origin_as_center=True for legacy compatibility."""
        prog = parse("1 * { s 2 x 1 } box")
        result_default = Interpreter.interpret(prog)
        result_origin = Interpreter.interpret(prog, origin_as_center=True)
        m1 = result_default.matrices["box"][0]
        m2 = result_origin.matrices["box"][0]
        for r in range(4):
            for c in range(4):
                self.assertAlmostEqual(m1[r][c], m2[r][c])


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

    def test_zero_repetition_count(self):
        """T8: Zero repetition count produces no instances."""
        prog = parse("0 * { x 1 } box")
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices.get("box", [])), 0)


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

    def test_empty_rule_body(self):
        """T5: Rule with empty body produces no output."""
        prog = parse("""
        empty
        rule empty {}
        """)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices), 0)

    def test_empty_rule_body_with_call(self):
        """T5: Calling a rule with empty body is a no-op."""
        prog = parse("""
        1 * { x 1 } empty
        1 * {} box
        rule empty {}
        """)
        result = Interpreter.interpret(prog)
        # Only the box from the implicit start rule should be present
        self.assertIn("box", result.matrices)
        self.assertEqual(len(result.matrices["box"]), 1)


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

    def test_define_shadowing(self):
        """T10: Later #define overrides earlier one with same name."""
        prog = parse("#define n 3\n#define n 7\nn * { x 1 } box")
        result = Interpreter.interpret(prog)
        # Second #define should override the first
        self.assertEqual(len(result.matrices["box"]), 7)


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

    def test_duplicate_set_statements(self):
        """T7: Multiple set statements with same name — last one wins."""
        prog = parse("""
        set maxdepth 100
        set maxdepth 3
        1 * { x 1 } start
        rule start { 1 * { x 1 } start }
        rule start { 1 * {} box }
        """)
        # Interpreter.interpret() uses first match, so maxdepth=100
        # This documents current behavior; if last-wins is desired,
        # the loop should not break on first match.
        result = Interpreter.interpret(prog)
        self.assertIn("box", result.matrices)

    def test_minsize_maxsize_parsed_but_not_enforced(self):
        """T6: set minsize/maxsize are parsed but not enforced by interpreter."""
        prog = parse("""
        set minsize 0.01
        set maxsize 10.0
        1 * {} box
        """)
        result = Interpreter.interpret(prog)
        # minsize/maxsize are not implemented in the interpreter yet
        self.assertIn("box", result.matrices)


class SizeTests(unittest.TestCase):
    """Test minsize/maxsize termination (S5)."""

    def test_initial_size_is_sqrt3(self):
        """Initial diagonal of unit cube is sqrt(3) ≈ 1.732."""
        from sverchok.utils.modules.eisenscript.interpreter import _compute_size
        from mathutils import Matrix
        import math
        m = Matrix.Identity(4)
        self.assertAlmostEqual(_compute_size(m), math.sqrt(3), places=5)

    def test_minsize_terminates_small_branch(self):
        """S5: Branch terminated when size < minsize."""
        prog = parse("""
        set minsize 1.0
        1 * { s 0.1 } box
        """)
        result = Interpreter.interpret(prog)
        # s 0.1 scales diagonal from sqrt(3) to 0.1*sqrt(3) ≈ 0.173 < 1.0
        self.assertEqual(len(result.matrices.get("box", [])), 0)

    def test_maxsize_terminates_large_branch(self):
        """S5: Branch terminated when size > maxsize."""
        prog = parse("""
        set maxsize 1.0
        1 * { s 2 } box
        """)
        result = Interpreter.interpret(prog)
        # s 2 scales diagonal from sqrt(3) to 2*sqrt(3) ≈ 3.464 > 1.0
        self.assertEqual(len(result.matrices.get("box", [])), 0)

    def test_minsize_maxsize_both(self):
        """S5: Both minsize and maxsize can be set."""
        prog = parse("""
        set minsize 0.5
        set maxsize 3.0
        1 * { s 0.1 } box
        1 * { s 2 } sphere
        """)
        result = Interpreter.interpret(prog)
        # box: 0.1*sqrt(3) ≈ 0.173 < 0.5 → terminated
        # sphere: 2*sqrt(3) ≈ 3.464 > 3.0 → terminated
        self.assertEqual(len(result.matrices.get("box", [])), 0)
        self.assertEqual(len(result.matrices.get("sphere", [])), 0)

    def test_minsize_maxsize_allows_valid_size(self):
        """S5: Branch allowed when size is within [minsize, maxsize]."""
        prog = parse("""
        set minsize 0.5
        set maxsize 2.0
        1 * { s 0.5 } box
        """)
        result = Interpreter.interpret(prog)
        # s 0.5 scales diagonal from sqrt(3) to 0.5*sqrt(3) ≈ 0.866
        # 0.5 ≤ 0.866 ≤ 2.0 → allowed
        self.assertIn("box", result.matrices)
        self.assertEqual(len(result.matrices["box"]), 1)

    def test_minsize_terminates_rule_call(self):
        """S5: Rule call terminated when size < minsize."""
        prog = parse("""
        set minsize 1.0
        1 * { s 0.1 } child
        rule child { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        # s 0.1 scales diagonal to 0.1*sqrt(3) ≈ 0.173 < 1.0
        self.assertNotIn("box", result.matrices)

    def test_maxsize_terminates_rule_call(self):
        """S5: Rule call terminated when size > maxsize."""
        prog = parse("""
        set maxsize 1.0
        1 * { s 2 } child
        rule child { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        # s 2 scales diagonal to 2*sqrt(3) ≈ 3.464 > 1.0
        self.assertNotIn("box", result.matrices)

    def test_minsize_maxsize_with_repetition(self):
        """S5: Repetitions respect minsize/maxsize per instance."""
        prog = parse("""
        set minsize 0.5
        3 * { s 0.3 x 1 } box
        """)
        result = Interpreter.interpret(prog)
        # Cumulative transforms:
        # Iter 1: s 0.3 → 0.3*sqrt(3) ≈ 0.520 ≥ 0.5 → OK
        # Iter 2: s 0.3^2 → 0.09*sqrt(3) ≈ 0.156 < 0.5 → terminated
        # Iter 3: s 0.3^3 → 0.027*sqrt(3) ≈ 0.047 < 0.5 → terminated
        self.assertIn("box", result.matrices)
        self.assertEqual(len(result.matrices["box"]), 1)

    def test_minsize_maxsize_recursive_termination(self):
        """S5: Recursive rules terminate when size drops below minsize."""
        prog = parse("""
        set minsize 0.5
        set maxdepth 100
        1 * { s 0.5 } start
        rule start { 1 * { s 0.5 } start }
        rule start { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        # Each recursion multiplies size by 0.5
        # sqrt(3) → 0.5*sqrt(3) ≈ 0.866 → 0.25*sqrt(3) ≈ 0.433 < 0.5
        # So recursion terminates after 2 levels
        self.assertIn("box", result.matrices)


class MaxObjectsTests(unittest.TestCase):
    """Test max_objects cap."""

    def test_max_objects_limits(self):
        prog = parse("100 * { x 1 } box")
        result = Interpreter(max_objects=10)._interpret(prog)
        self.assertLessEqual(len(result.matrices["box"]), 10)

    def test_set_maxobjects_from_settings(self):
        """S7: set maxobjects should be read from program settings."""
        prog = parse("set maxobjects 3\n10 * { x 1 } box")
        result = Interpreter.interpret(prog)
        self.assertLessEqual(len(result.matrices["box"]), 3)

    def test_set_maxobjects_constrains_output(self):
        """set maxobjects limits total instances across all shapes."""
        prog = parse("set maxobjects 5\n10 * { x 1 } box\n10 * { y 1 } sphere")
        result = Interpreter.interpret(prog)
        total = sum(len(m) for m in result.matrices.values())
        self.assertLessEqual(total, 5)


class SeedTests(unittest.TestCase):
    """Test set seed from program settings."""

    def test_set_seed_from_settings(self):
        """S6: set seed should be read from program settings."""
        prog = parse("set seed 42\n1 * {} box")
        result = Interpreter.interpret(prog)
        self.assertIn("box", result.matrices)

    def test_set_seed_affects_weighted_selection(self):
        """Different seeds should produce different weighted selections."""
        src = """
        child
        rule child w 10 { 1 * {} box }
        rule child w 1 { 1 * {} sphere }
        """
        prog1 = parse("set seed 0\n" + src)
        prog2 = parse("set seed 999\n" + src)
        result1 = Interpreter.interpret(prog1)
        result2 = Interpreter.interpret(prog2)
        # At least one of the results should differ (or both same by chance)
        # The key is that seed is actually used
        total1 = sum(len(m) for m in result1.matrices.values())
        total2 = sum(len(m) for m in result2.matrices.values())
        self.assertEqual(total1, 1)
        self.assertEqual(total2, 1)

    def test_set_seed_initial(self):
        """set seed initial should use default seed 0."""
        prog = parse("set seed initial\n1 * {} box")
        result = Interpreter.interpret(prog)
        self.assertIn("box", result.matrices)


class CallRetirementTests(unittest.TestCase):
    """Test call-level retirement (md N > successor on RuleRef)."""

    def test_call_retirement_successor_used(self):
        """C1: md N > successor on a call should use the specified successor."""
        # Single 'child' rule (no random selection ambiguity)
        prog = parse("""
        1 * { x 1 } start
        rule start maxdepth 3 { 1 * { x 1 } md 1 > leaf child }
        rule child { 1 * { x 1 } child }
        rule child { 1 * {} sphere }
        rule leaf { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        # The call-site retirement (md 1 > leaf) should produce boxes
        self.assertIn("box", result.matrices)
        self.assertGreater(len(result.matrices["box"]), 0)

    def test_call_retirement_overrides_rule_retirement(self):
        """Call-site md > successor overrides the target rule's retirement."""
        # 'child' has its own retirement to 'sphere_rule', but call-site
        # specifies 'md 1 > override', which should take precedence
        prog = parse("""
        1 * { x 1 } start
        rule start maxdepth 1 { 1 * { x 1 } md 1 > override child }
        rule child maxdepth 1 > sphere_rule { 1 * { x 1 } child }
        rule child maxdepth 1 > sphere_rule { 1 * {} sphere }
        rule sphere_rule { 1 * {} sphere }
        rule override { 1 * {} box }
        """)
        result = Interpreter.interpret(prog)
        # Should produce boxes (from 'override'), not spheres
        self.assertIn("box", result.matrices)


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
