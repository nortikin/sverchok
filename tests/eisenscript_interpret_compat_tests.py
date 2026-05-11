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
Compatibility tests between the new EisenScript interpreter and the
legacy XML interpreter (LSystem) from nodes/script/generative_art.py.

Each test:
    1. Parses an EisenScript program
    2. Runs it through the new Interpreter
    3. Converts the AST to XML and runs it through LSystem.evaluate()
    4. Compares the results

Discrepancies are flagged.  If the legacy interpreter contradicts the
EisenScript specification, a NOTE is added in the test docstring.
"""

import unittest
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import importlib.util

# ------------------------------------------------------------------
# Direct module loading (avoids bpy import in sverchok/__init__.py)
# ------------------------------------------------------------------

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

ast_mod = _load_module(
    "sverchok.utils.modules.eisenscript.ast",
    os.path.join(project_root, "utils/modules/eisenscript/ast.py"))
parser_mod = _load_module(
    "sverchok.utils.modules.eisenscript.parser",
    os.path.join(project_root, "utils/modules/eisenscript/parser.py"))
to_xml_mod = _load_module(
    "sverchok.utils.modules.eisenscript.to_xml",
    os.path.join(project_root, "utils/modules/eisenscript/to_xml.py"))
interp_mod = _load_module(
    "sverchok.utils.modules.eisenscript.interpreter",
    os.path.join(project_root, "utils/modules/eisenscript/interpreter.py"))

parse = parser_mod.parse
Interpreter = interp_mod.Interpreter
ast_to_xml = to_xml_mod.ast_to_xml
eisenscript_to_xml = to_xml_mod.eisenscript_to_xml

# ------------------------------------------------------------------
# Legacy LSystem helpers (re-implemented without bpy dependency)
# ------------------------------------------------------------------

import math
import random
from xml.etree.ElementTree import fromstring

import mathutils as mu


def _radians_legacy(d):
    """Legacy LSystem uses 3.141 instead of math.pi."""
    return float(d * 3.141 / 180.0)


_xform_cache = {}


def _parse_xform(xform_string):
    """Parse XML transforms string into a 4x4 matrix (legacy behavior)."""
    if xform_string in _xform_cache:
        return _xform_cache[xform_string]

    matrix = mu.Matrix.Identity(4)
    tokens = xform_string.split()
    t = 0
    while t < len(tokens) - 1:
        command, t = tokens[t], t + 1

        if command == 'tx':
            x, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Translation(mu.Vector((x, 0, 0)))
        elif command == 'ty':
            y, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Translation(mu.Vector((0, y, 0)))
        elif command == 'tz':
            z, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Translation(mu.Vector((0, 0, z)))
        elif command == 't':
            x, t = float(tokens[t]), t + 1
            y, t = float(tokens[t]), t + 1
            z, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Translation(mu.Vector((x, y, z)))

        elif command == 'rx':
            theta, t = _radians_legacy(float(tokens[t])), t + 1
            matrix @= mu.Matrix.Rotation(theta, 4, 'X')
        elif command == 'ry':
            theta, t = _radians_legacy(float(tokens[t])), t + 1
            matrix @= mu.Matrix.Rotation(theta, 4, 'Y')
        elif command == 'rz':
            theta, t = _radians_legacy(float(tokens[t])), t + 1
            matrix @= mu.Matrix.Rotation(theta, 4, 'Z')

        elif command == 'sx':
            x, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Scale(x, 4, mu.Vector((1.0, 0.0, 0.0)))
        elif command == 'sy':
            y, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Scale(y, 4, mu.Vector((0.0, 1.0, 0.0)))
        elif command == 'sz':
            z, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Scale(z, 4, mu.Vector((0.0, 0.0, 1.0)))
        elif command == 'sa':
            v, t = float(tokens[t]), t + 1
            matrix @= mu.Matrix.Scale(v, 4)
        elif command == 's':
            x, t = float(tokens[t]), t + 1
            y, t = float(tokens[t]), t + 1
            z, t = float(tokens[t]), t + 1
            mx = mu.Matrix.Scale(x, 4, mu.Vector((1.0, 0.0, 0.0)))
            my = mu.Matrix.Scale(y, 4, mu.Vector((0.0, 1.0, 0.0)))
            mz = mu.Matrix.Scale(z, 4, mu.Vector((0.0, 0.0, 1.0)))
            matrix @= mx @ my @ mz

        else:
            raise ValueError(f"unrecognized transform: '{command}'")

    _xform_cache[xform_string] = matrix
    return matrix


def _pick_rule_xml(tree, name):
    """Pick a rule element from XML tree by name (weighted random)."""
    rules = tree.findall("rule")
    elements = [r for r in rules if r.get("name") == name]
    if not elements:
        raise ValueError(f"No rule found with name '{name}'")

    if len(elements) == 1:
        return elements[0]

    total = sum(int(r.get("weight", 1)) for r in elements)
    n = random.randint(0, total - 1)
    for elem in elements:
        w = int(elem.get("weight", 1))
        if n < w:
            return elem
        n -= w
    return elements[-1]


def _evaluate_xml(xml_string, max_objects=10000, seed=0):
    """
    Evaluate an XML string using the legacy LSystem algorithm.

    Returns a dict mapping shape name -> list of Matrix.
    """
    random.seed(seed)
    tree = fromstring(xml_string)
    global_max_depth = int(tree.get("max_depth", 1000))

    rule = _pick_rule_xml(tree, "entry")
    stack = [(rule, 0, mu.Matrix.Identity(4))]
    result = {}
    nobjects = 0

    while stack:
        if nobjects > max_objects:
            break

        rule, depth, matrix = stack.pop()

        local_max_depth = global_max_depth
        if "max_depth" in rule.attrib:
            local_max_depth = int(rule.get("max_depth"))

        if len(stack) > global_max_depth:
            continue

        if depth > local_max_depth:
            if "successor" in rule.attrib:
                successor = rule.get("successor")
                succ_rule = _pick_rule_xml(tree, successor)
                stack.append((succ_rule, 0, matrix))
            continue

        base_matrix = matrix.copy()
        for statement in rule:
            tstr = statement.get("transforms", "")
            if not tstr:
                tstr = ''
                for t in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz',
                          'sa', 'sx', 'sy', 'sz']:
                    tvalue = statement.get(t)
                    if tvalue:
                        n = float(tvalue)
                        tstr += f"{t} {n:f} "
            xform = _parse_xform(tstr) if tstr else mu.Matrix.Identity(4)
            count = int(statement.get("count", 1))
            count_xform = mu.Matrix.Identity(4)

            for _ in range(count):
                count_xform @= xform
                mat = base_matrix @ count_xform

                if statement.tag == "call":
                    target = _pick_rule_xml(tree, statement.get("rule"))
                    stack.append((target, depth + 1, mat.copy()))
                elif statement.tag == "instance":
                    name = statement.get("shape")
                    if name and name != "None":
                        result.setdefault(name, []).append(mat)
                        nobjects += 1

    return result


# ------------------------------------------------------------------
# Comparison helpers
# ------------------------------------------------------------------

def _mat_key(m, tol=1e-4):
    """Create a hashable key from a matrix (rounded for tolerance)."""
    return tuple(round(m[r][c], -int(__import__('math').log10(tol)))
                 for r in range(4) for c in range(4))


def _compare_matrices(mats_a, mats_b, tol=1e-4):
    """
    Compare two lists of 4x4 matrices (order-independent).

    The EisenScript spec does not define an evaluation order, so the
    legacy LSystem (stack-based, LIFO) and the new interpreter may
    produce the same placements in different order.  We compare as
    sets.

    Returns (ok, message) tuple.
    """
    set_a = set(_mat_key(m, tol) for m in mats_a)
    set_b = set(_mat_key(m, tol) for m in mats_b)

    if len(set_a) != len(set_b):
        return False, f"Count mismatch: {len(set_a)} vs {len(set_b)}"

    missing_in_b = set_a - set_b
    if missing_in_b:
        return False, f"{len(missing_in_b)} matrix(es) in new interpreter but not in legacy"

    missing_in_a = set_b - set_a
    if missing_in_a:
        return False, f"{len(missing_in_a)} matrix(es) in legacy but not in new interpreter"

    return True, "OK"


def _compare_results(new_result, xml_result, tol=1e-4):
    """
    Compare InterpreterResult with legacy XML result dict.

    Returns (ok, message) tuple.
    """
    shapes_new = set(new_result.matrices.keys())
    shapes_xml = set(xml_result.keys())

    if shapes_new != shapes_xml:
        return False, f"Shape mismatch: {shapes_new} vs {shapes_xml}"

    for shape in shapes_new:
        ok, msg = _compare_matrices(
            new_result.matrices[shape], xml_result[shape], tol)
        if not ok:
            return False, f"Shape '{shape}': {msg}"

    return True, "All shapes match"


# ------------------------------------------------------------------
# Test cases
# ------------------------------------------------------------------

class CompatTestBase(unittest.TestCase):
    """Base class providing run_compat helper."""

    def run_compat(self, src, seed=0, tol=1e-4):
        """
        Run EisenScript through both interpreters and compare.

        Args:
            src: EisenScript source code.
            seed: Random seed for weighted rule selection.
            tol: Floating-point tolerance for matrix comparison.

        Returns:
            (new_result, xml_result) for further inspection.
        """
        prog = parse(src)
        new_result = Interpreter(seed=seed).interpret(prog)

        xml_elem = ast_to_xml(prog)
        from xml.etree.ElementTree import tostring
        xml_str = tostring(xml_elem, encoding="unicode")
        xml_result = _evaluate_xml(xml_str, seed=seed)

        ok, msg = _compare_results(new_result, xml_result, tol)
        self.assertTrue(ok, f"Compatibility check failed: {msg}")
        return new_result, xml_result


class TestSimplePrimitive(CompatTestBase):
    """Single primitive, no transforms."""

    def test_single_box(self):
        self.run_compat("1 * {} box")

    def test_single_sphere(self):
        self.run_compat("1 * {} sphere")


class TestTranslation(CompatTestBase):
    """Translation transforms (x, y, z)."""

    def test_translate_x(self):
        self.run_compat("1 * { x 5 } box")

    def test_translate_y(self):
        self.run_compat("1 * { y 3 } box")

    def test_translate_z(self):
        self.run_compat("1 * { z 7 } box")

    def test_combined_translation(self):
        self.run_compat("1 * { x 1 y 2 z 3 } box")


class TestRotation(CompatTestBase):
    """Rotation transforms (rx, ry, rz).

    NOTE: Legacy LSystem uses 3.141 instead of math.pi for radians
    conversion, so rotation results will differ slightly.  We use
    a relaxed tolerance (1e-2) for rotation tests.
    """

    def test_rotate_z_90(self):
        self.run_compat("1 * { rz 90 x 1 } box", tol=1e-2)

    def test_rotate_y_90(self):
        self.run_compat("1 * { ry 90 x 1 } box", tol=1e-2)

    def test_rotate_x_90(self):
        self.run_compat("1 * { rx 90 z 1 } box", tol=1e-2)

    def test_small_rotation(self):
        self.run_compat("1 * { rz 5 x 1 } box", tol=1e-2)


class TestScale(CompatTestBase):
    """Scale transforms (uniform and per-axis)."""

    def test_uniform_scale(self):
        self.run_compat("1 * { s 2 x 1 } box")

    def test_per_axis_scale(self):
        self.run_compat("1 * { s 2 3 4 x 1 y 1 z 1 } box")

    def test_scale_with_translation(self):
        self.run_compat("1 * { s 0.5 x 2 } box")


class TestMirror(CompatTestBase):
    """Mirror transforms (fx, fy, fz).

    NOTE: The legacy LSystem (generative_art.py) does NOT support
    mirror transforms (fx, fy, fz).  These are EisenScript-specific
    features.  The compatibility tests here are skipped because the
    legacy XML interpreter cannot process them.
    """

    @unittest.skip("Legacy LSystem does not support fx/fy/fz")
    def test_mirror_x(self):
        self.run_compat("1 * { fx x 1 } box")

    @unittest.skip("Legacy LSystem does not support fx/fy/fz")
    def test_mirror_y(self):
        self.run_compat("1 * { fy y 1 } box")

    @unittest.skip("Legacy LSystem does not support fx/fy/fz")
    def test_mirror_z(self):
        self.run_compat("1 * { fz z 1 } box")


class TestRepetition(CompatTestBase):
    """Repetition (loop) semantics."""

    def test_simple_repetition(self):
        self.run_compat("5 * { x 1 } box")

    def test_repetition_with_rotation(self):
        self.run_compat("4 * { rz 90 x 1 } box", tol=1e-2)

    def test_nested_repetitions(self):
        self.run_compat("2 * { x 1 } 3 * { z 0.5 } box")

    def test_triple_nested_repetitions(self):
        self.run_compat("2 * { x 1 } 3 * { y 1 } 4 * { z 1 } box")

    def test_repetition_with_scale(self):
        self.run_compat("3 * { s 0.9 x 1 } box")


class TestRuleCalls(CompatTestBase):
    """Rule call semantics."""

    def test_simple_call(self):
        self.run_compat("""
            child
            rule child { 1 * {} box }
        """)

    def test_call_with_transform(self):
        self.run_compat("""
            1 * { x 5 } child
            rule child { 1 * {} box }
        """)

    def test_multiple_calls(self):
        self.run_compat("""
            1 * { x 1 } child
            1 * { y 1 } child
            rule child { 1 * {} box }
        """)

    def test_call_with_repetition(self):
        self.run_compat("""
            3 * { x 1 } child
            rule child { 1 * {} box }
        """)


class TestRecursiveRules(CompatTestBase):
    """Recursive rules with max_depth."""

    def test_simple_recursion(self):
        """Linear recursion with retirement to box."""
        self.run_compat("""
            1 * { x 1 } start
            rule start maxdepth 5 { 1 * { x 1 } start }
            rule start maxdepth 5 { 1 * {} box }
        """)


class TestRetirement(CompatTestBase):
    """Rule retirement (successor) semantics."""

    def test_retirement_with_successor(self):
        """Rule retires to a successor rule."""
        self.run_compat("""
            1 * { x 1 } start
            rule start maxdepth 2 > leaf { 1 * { x 1 } start }
            rule leaf { 1 * {} box }
        """)


class TestVariables(CompatTestBase):
    """#define variable substitution."""

    def test_variable_count(self):
        self.run_compat("#define n 5\nn * { x 1 } box")

    def test_variable_transform(self):
        self.run_compat("#define d 10\n1 * { x d } box")

    def test_variable_rotation(self):
        self.run_compat("#define angle 72\n5 * { rz angle x 1 } box", tol=1e-2)

    def test_variable_maxdepth(self):
        self.run_compat("""
            #define depth 5
            1 * { x 1 } start
            rule start maxdepth depth { 1 * { x 1 } start }
            rule start maxdepth depth { 1 * {} box }
        """)


class TestWeightedRules(CompatTestBase):
    """Weighted rule selection (deterministic with seed)."""

    def test_weighted_selection_seed_zero(self):
        """With seed=0, weighted selection is deterministic."""
        self.run_compat("""
            child
            rule child w 10 { 1 * {} box }
            rule child w 1 { 1 * {} sphere }
        """, seed=0)


class TestMixedTransforms(CompatTestBase):
    """Combinations of different transform types."""

    def test_translate_rotate_scale(self):
        self.run_compat("1 * { x 1 rz 45 s 0.5 } box", tol=1e-2)

    def test_multiple_rotations(self):
        self.run_compat("1 * { rx 30 ry 45 rz 60 x 1 } box", tol=1e-2)

    def test_repetition_mixed_transforms(self):
        self.run_compat("3 * { x 1 rz 120 s 0.9 } box", tol=1e-2)


class TestGlobalMaxDepth(CompatTestBase):
    """Global max_depth setting."""

    def test_global_maxdepth(self):
        self.run_compat("""
            set maxdepth 10
            1 * { x 1 } start
            rule start { 1 * { x 1 } start }
            rule start { 1 * {} box }
        """)


class TestComplexProgram(CompatTestBase):
    """More complex programs combining multiple features."""

    def test_branching_tree(self):
        """Simple branching tree structure."""
        self.run_compat("""
            1 * { ry 90 } trunk
            rule trunk maxdepth 5 {
                1 * {} box
                1 * { tz 1 rx 30 } trunk
                1 * { tz 1 rz 120 rx 30 } trunk
            }
        """, tol=1e-2)

    def test_spiral(self):
        """Spiral pattern with rotation and translation."""
        self.run_compat("""
            10 * { rz 36 tz 0.5 s 0.95 } box
        """, tol=1e-2)


if __name__ == "__main__":
    unittest.main()
