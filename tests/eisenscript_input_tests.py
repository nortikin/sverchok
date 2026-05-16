# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) your version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program;  if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Tests for the #input directive in EisenScript.

Covers:
    - Parsing #input with/without type and default value
    - Name conflict between #input and #define
    - Runtime value resolution (input_values dict)
    - Fallback to default value
    - Error when no default and no runtime value
    - Input variables in expressions and #define
    - Parameter shadowing of input variables
    - Serialization round-trip
    - XML conversion rejection
"""

import unittest
import sys
import os

# Ensure project root is on path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sverchok.utils.modules.eisenscript.parser import parse
from sverchok.utils.modules.eisenscript.interpreter import Interpreter
from sverchok.utils.modules.eisenscript.serializer import ast_to_string
from sverchok.utils.modules.eisenscript.to_xml import ast_to_xml, ExpressionInXmlError
from sverchok.utils.modules.eisenscript.ast import InputDef, IMPLICIT_START_RULE


# ---------------------------------------------------------------------------
# Parsing tests
# ---------------------------------------------------------------------------

class TestInputParsing(unittest.TestCase):
    """Test parsing of #input directives."""

    def test_input_no_default(self):
        """#input name — no type, no default."""
        src = "#input width"
        prog = parse(src)
        self.assertIn("width", prog.inputs)
        self.assertIsNone(prog.inputs["width"].default_value)

    def test_input_with_default(self):
        """#input name value — no type, with default."""
        src = "#input height 17"
        prog = parse(src)
        self.assertIn("height", prog.inputs)
        self.assertAlmostEqual(prog.inputs["height"].default_value, 17.0)

    def test_input_with_type_and_default(self):
        """#input name number value — explicit type and default."""
        src = "#input depth number 5"
        prog = parse(src)
        self.assertIn("depth", prog.inputs)
        self.assertAlmostEqual(prog.inputs["depth"].default_value, 5.0)

    def test_input_with_type_no_default(self):
        """#input name number — explicit type, no default."""
        src = "#input radius number"
        prog = parse(src)
        self.assertIn("radius", prog.inputs)
        self.assertIsNone(prog.inputs["radius"].default_value)

    def test_input_float_default(self):
        """#input with float default value."""
        src = "#input scale 0.75"
        prog = parse(src)
        self.assertAlmostEqual(prog.inputs["scale"].default_value, 0.75)

    def test_input_negative_default(self):
        """#input with negative default value."""
        src = "#input offset -3.5"
        prog = parse(src)
        self.assertAlmostEqual(prog.inputs["offset"].default_value, -3.5)

    def test_input_fraction_default(self):
        """#input with fraction default value."""
        src = "#input ratio 1/3"
        prog = parse(src)
        self.assertAlmostEqual(prog.inputs["ratio"].default_value, 1 / 3, places=6)

    def test_input_multiple(self):
        """Multiple #input directives."""
        src = "#input w 10\n#input h 20\n#input d 30"
        prog = parse(src)
        self.assertEqual(len(prog.inputs), 3)
        self.assertAlmostEqual(prog.inputs["w"].default_value, 10.0)
        self.assertAlmostEqual(prog.inputs["h"].default_value, 20.0)
        self.assertAlmostEqual(prog.inputs["d"].default_value, 30.0)

    def test_input_with_define(self):
        """#input and #define coexist without conflict."""
        src = "#input w 10\n#define double_w (w * 2)"
        prog = parse(src)
        self.assertIn("w", prog.inputs)
        self.assertIn("double_w", prog.defines)

    def test_input_conflict_with_define(self):
        """#input and #define with same name raises SyntaxError."""
        src = "#input w 10\n#define w 20"
        with self.assertRaises(SyntaxError) as ctx:
            parse(src)
        self.assertIn("Name conflict", str(ctx.exception))
        self.assertIn("w", str(ctx.exception))

    def test_input_conflict_with_define_reverse(self):
        """#define before #input with same name raises SyntaxError."""
        src = "#define w 20\n#input w 10"
        with self.assertRaises(SyntaxError) as ctx:
            parse(src)
        self.assertIn("Name conflict", str(ctx.exception))

    def test_input_not_expression(self):
        """#input default must be a number, not an expression.

        An expression left after #input name is a parse error because
        the parser cannot consume it.
        """
        src = "#input w (a + b)"
        with self.assertRaises(SyntaxError):
            parse(src)

    def test_input_not_variable(self):
        """#input default must be a number, not a variable reference."""
        src = "#input w other_var"
        prog = parse(src)
        # other_var is not a valid numeric value, so it's not consumed
        self.assertIn("w", prog.inputs)
        self.assertIsNone(prog.inputs["w"].default_value)


# ---------------------------------------------------------------------------
# Interpreter tests
# ---------------------------------------------------------------------------

class TestInputInterpretation(unittest.TestCase):
    """Test #input variable resolution at interpretation time."""

    def test_input_used_in_rule(self):
        """Input variable used as scale factor."""
        src = "#input w 5\n{s w 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 5.0)

    def test_input_override_at_runtime(self):
        """Runtime value overrides default."""
        src = "#input w 5\n{s w 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"w": 10})
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 10.0)

    def test_input_no_default_no_value_error(self):
        """Missing input with no default raises ValueError."""
        src = "#input w\n{s w 1 1} box"
        prog = parse(src)
        with self.assertRaises(ValueError) as ctx:
            Interpreter.interpret(prog)
        self.assertIn("w", str(ctx.exception))
        self.assertIn("no default", str(ctx.exception).lower())

    def test_input_no_default_with_value_ok(self):
        """Missing input with no default is OK if provided at runtime."""
        src = "#input w\n{s w 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"w": 7})
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 7.0)

    def test_input_in_expression(self):
        """Input variable used inside a Python expression."""
        src = "#input r 3\n{s (r * 2) 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 6.0)

    def test_input_in_define(self):
        """Input variable used in a #define expression."""
        src = "#input base 4\n#define doubled (base * 2)\n{s doubled 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 8.0)

    def test_input_in_define_override(self):
        """Runtime input value propagates through #define."""
        src = "#input base 4\n#define doubled (base * 2)\n{s doubled 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"base": 10})
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 20.0)

    def test_input_shadowed_by_param(self):
        """Rule parameter shadows #input with same name."""
        src = "#input scale 2\nrule r(scale) { {s scale 1 1} box }\nr(5)"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # Parameter value (5) shadows input value (2)
        self.assertAlmostEqual(m[0][0], 5.0)

    def test_input_in_repetition_count(self):
        """Input variable used as repetition count."""
        src = "#input n 3\nn * {x 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 3)

    def test_input_in_repetition_override(self):
        """Runtime input value affects repetition count."""
        src = "#input n 3\nn * {x 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"n": 5})
        self.assertEqual(len(result.matrices["box"]), 5)

    def test_multiple_inputs(self):
        """Multiple input variables used together."""
        # Use non-keyword names (h is a hue keyword)
        src = "#input sx 2\n#input sy 3\n{s sx sy 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 2.0)
        self.assertAlmostEqual(m[1][1], 3.0)

    def test_multiple_inputs_partial_override(self):
        """Only some inputs overridden at runtime."""
        src = "#input sx 2\n#input sy 3\n{s sx sy 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"sx": 10})
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 10.0)  # overridden
        self.assertAlmostEqual(m[1][1], 3.0)    # default

    def test_input_priority_over_define(self):
        """#input has priority over #define when resolving variables."""
        # Note: this tests that inputs are checked before defines.
        # Since they share a namespace, this is a design choice.
        src = "#input val 10\n#define doubled (val + 1)\n{s doubled 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 11.0)

    def test_input_in_nested_expression(self):
        """Input used in a complex expression."""
        src = "#import math\n#define angle (360 / n)\n#input n 12\nn * {rz angle x 2} box"
        # Actually, #import is not a thing. Let me simplify:
        src = "#input n 4\n#define angle (360 / n)\nn * {rz angle x 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 4)

    def test_extra_input_values_ignored(self):
        """Extra keys in input_values that don't match any #input are ignored."""
        src = "#input w 5\n{s w 1 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"w": 10, "extra": 99})
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 10.0)


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------

class TestInputSerialization(unittest.TestCase):
    """Test serialization of #input directives."""

    def test_serialize_input_no_default(self):
        """#input without default serializes correctly."""
        src = "#input width"
        prog = parse(src)
        output = ast_to_string(prog)
        self.assertIn("#input width", output)

    def test_serialize_input_with_default(self):
        """#input with default serializes correctly."""
        src = "#input height 17"
        prog = parse(src)
        output = ast_to_string(prog)
        self.assertIn("#input height 17", output)

    def test_serialize_input_with_define(self):
        """#input and #define both serialize correctly."""
        src = "#input w 10\n#define double_w (w * 2)"
        prog = parse(src)
        output = ast_to_string(prog)
        self.assertIn("#input w 10", output)
        self.assertIn("#define double_w (w * 2)", output)

    def test_round_trip(self):
        """Parse → serialize → parse produces equivalent AST."""
        src = "#input w 10\n#input h 20\n#define area (w * h)\n{s w h 1} box"
        prog1 = parse(src)
        output = ast_to_string(prog1)
        prog2 = parse(output)
        self.assertEqual(len(prog1.inputs), len(prog2.inputs))
        for name, inp_def in prog1.inputs.items():
            self.assertIn(name, prog2.inputs)
            self.assertAlmostEqual(
                inp_def.default_value, prog2.inputs[name].default_value
            )


# ---------------------------------------------------------------------------
# XML conversion tests
# ---------------------------------------------------------------------------

class TestInputXml(unittest.TestCase):
    """Test XML conversion rejection for #input."""

    def test_xml_rejects_input(self):
        """XML conversion rejects programs with #input."""
        src = "#input w 10\n{s w 1 1} box"
        prog = parse(src)
        with self.assertRaises(ExpressionInXmlError) as ctx:
            ast_to_xml(prog)
        self.assertIn("#input", str(ctx.exception))
        self.assertIn("w", str(ctx.exception))

    def test_xml_rejects_multiple_inputs(self):
        """XML conversion lists all input names in error."""
        src = "#input w 10\n#input h 20\nbox"
        prog = parse(src)
        with self.assertRaises(ExpressionInXmlError) as ctx:
            ast_to_xml(prog)
        self.assertIn("w", str(ctx.exception))
        self.assertIn("h", str(ctx.exception))

    def test_xml_ok_without_input(self):
        """XML conversion works when there are no #input directives."""
        src = "#define w 10\n{s w 1 1} box"
        prog = parse(src)
        root = ast_to_xml(prog)
        self.assertIsNotNone(root)


# ---------------------------------------------------------------------------
# Advanced tests
# ---------------------------------------------------------------------------

class TestInputAdvanced(unittest.TestCase):
    """Advanced #input scenarios."""

    def test_input_in_rule_maxdepth(self):
        """Input variable used in rule maxdepth modifier."""
        src = "#input depth 5\nrule r maxdepth depth { {x 1} r }\nr"
        prog = parse(src)
        # This should parse without error
        self.assertIn("depth", prog.inputs)

    def test_input_in_rule_weight(self):
        """Input variable used in rule weight modifier."""
        src = "#input w_val 2\nrule r w w_val { box }\nr"
        prog = parse(src)
        self.assertIn("w_val", prog.inputs)

    def test_input_in_param_rule_call(self):
        """Input variable used as argument to parameterized rule."""
        src = "#input sc 3\nrule r(sv) { {s sv 1 1} box }\nr(sc)"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 3.0)

    def test_input_in_param_rule_override(self):
        """Runtime input value propagates through parameterized rule."""
        src = "#input sc 3\nrule r(sv) { {s sv 1 1} box }\nr(sc)"
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"sc": 7})
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 7.0)

    def test_input_in_repetition_transform(self):
        """Input variable used inside repetition transformations."""
        src = "#input angle 30\n3 * {rz angle x 1} box"
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 3)

    def test_input_combined_with_define_dep(self):
        """Input feeds into a chain of #define dependencies."""
        src = (
            "#input base 2\n"
            "#define a (base * 3)\n"
            "#define b (a + 1)\n"
            "#define c (b * 2)\n"
            "{s c 1 1} box"
        )
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # base=2, a=6, b=7, c=14
        self.assertAlmostEqual(m[0][0], 14.0)

    def test_input_combined_with_define_dep_override(self):
        """Runtime input value propagates through define chain."""
        src = (
            "#input base 2\n"
            "#define a (base * 3)\n"
            "#define b (a + 1)\n"
            "#define c (b * 2)\n"
            "{s c 1 1} box"
        )
        prog = parse(src)
        result = Interpreter.interpret(prog, input_values={"base": 10})
        m = result.matrices["box"][0]
        # base=10, a=30, b=31, c=62
        self.assertAlmostEqual(m[0][0], 62.0)


if __name__ == "__main__":
    unittest.main()
