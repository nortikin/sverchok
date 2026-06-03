# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that will be useful,
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
Tests for EisenScript parameterized rules.

Parameterized rules allow defining rules with parameters that are
substituted at call time::

    rule my_box(w, ht) {
        {s w ht 1} box
    }

    my_box(2, 3)
"""

import unittest
import sys
import os

# Add project root to path for standalone execution
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sverchok.utils.modules.eisenscript.parser import parse
from sverchok.utils.modules.eisenscript.ast import (
    Program, Rule, Branch, RuleRef, VariableRef, Expr,
    Box, Sphere, IMPLICIT_START_RULE,
)
from sverchok.utils.modules.eisenscript.interpreter import Interpreter
from sverchok.utils.modules.eisenscript.serializer import ast_to_string
from sverchok.utils.modules.eisenscript.to_xml import (
    ast_to_xml, ExpressionInXmlError,
)


# =========================================================================
# Parser tests
# =========================================================================

class TestParamRuleParsing(unittest.TestCase):
    """Test parsing of parameterized rule definitions and calls."""

    def test_rule_with_params(self):
        """Parse 'rule name(p1, p2) { body }'."""
        src = "rule my_box(w, ht) { box }"
        prog = parse(src)
        self.assertEqual(len(prog.rules), 1)
        rule = prog.rules[0]
        self.assertEqual(rule.name, "my_box")
        self.assertEqual(rule.params, ["w", "ht"])

    def test_rule_with_single_param(self):
        """Parse 'rule name(p) { body }'."""
        src = "rule r(x) { box }"
        prog = parse(src)
        self.assertEqual(prog.rules[0].params, ["x"])

    def test_rule_with_empty_params(self):
        """Parse 'rule name() { body }' — same as no params."""
        src = "rule r() { box }"
        prog = parse(src)
        self.assertEqual(prog.rules[0].params, [])

    def test_rule_without_params(self):
        """Parse 'rule name { body }' — no params."""
        src = "rule r { box }"
        prog = parse(src)
        self.assertEqual(prog.rules[0].params, [])

    def test_implicit_rule_with_params(self):
        """Parse implicit rule 'name(p) branch'."""
        src = "my_rule(w, ht)\n{s w ht 1} box"
        prog = parse(src)
        self.assertEqual(len(prog.rules), 1)
        rule = prog.rules[0]
        self.assertEqual(rule.name, "my_rule")
        self.assertEqual(rule.params, ["w", "ht"])

    def test_rule_call_with_args(self):
        """Parse rule call 'name(arg1, arg2)'."""
        src = """
        rule r(w, ht) { box }
        r(2, 3)
        """
        prog = parse(src)
        # The start rule has a branch calling r(2, 3)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        branch = start_rule.body[0]
        ref = branch.terminal
        self.assertIsInstance(ref, RuleRef)
        self.assertEqual(ref.name, "r")
        self.assertEqual(len(ref.args), 2)
        self.assertEqual(ref.args[0], 2.0)
        self.assertEqual(ref.args[1], 3.0)

    def test_rule_call_with_var_args(self):
        """Parse rule call with variable arguments."""
        src = """
        rule r(w, ht) { box }
        r(p1, p2)
        """
        prog = parse(src)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        ref = start_rule.body[0].terminal
        self.assertIsInstance(ref.args[0], VariableRef)
        self.assertEqual(ref.args[0].name, "p1")
        self.assertIsInstance(ref.args[1], VariableRef)
        self.assertEqual(ref.args[1].name, "p2")

    def test_rule_call_with_expr_args(self):
        """Parse rule call with expression arguments."""
        src = """
        rule r(w, ht) { box }
        r((a + 1), (b * 2))
        """
        prog = parse(src)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        ref = start_rule.body[0].terminal
        self.assertIsInstance(ref.args[0], Expr)
        self.assertEqual(ref.args[0].source, "a + 1")
        self.assertIsInstance(ref.args[1], Expr)
        self.assertEqual(ref.args[1].source, "b * 2")

    def test_rule_call_empty_parens(self):
        """Parse 'name()' — same as 'name' (no args)."""
        src = """
        rule r { box }
        r()
        """
        prog = parse(src)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        ref = start_rule.body[0].terminal
        self.assertEqual(ref.args, [])

    def test_rule_call_no_parens(self):
        """Parse 'name' — no parens, no args."""
        src = """
        rule r { box }
        r
        """
        prog = parse(src)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        ref = start_rule.body[0].terminal
        self.assertEqual(ref.args, [])

    def test_rule_with_params_and_modifiers(self):
        """Parse 'rule name(p) md 5 { body }'."""
        src = "rule r(x) maxdepth 5 { box }"
        prog = parse(src)
        rule = prog.rules[0]
        self.assertEqual(rule.params, ["x"])
        self.assertEqual(rule.maxdepth, 5)

    def test_rule_params_with_spaces(self):
        """Parse params with various whitespace."""
        src = "rule r(  a  ,  b  ,  c  ) { box }"
        prog = parse(src)
        self.assertEqual(prog.rules[0].params, ["a", "b", "c"])

    def test_rule_single_arg_no_comma(self):
        """Parse 'name(arg)' — single arg, no comma."""
        src = """
        rule r(x) { box }
        r(5)
        """
        prog = parse(src)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        ref = start_rule.body[0].terminal
        self.assertEqual(len(ref.args), 1)
        self.assertEqual(ref.args[0], 5.0)

    def test_rule_call_in_branch_with_transform(self):
        """Parse '{x 1} name(args)' — transform before rule call."""
        src = """
        rule r(w) { box }
        {x 1} r(2)
        """
        prog = parse(src)
        start_rule = [r for r in prog.rules if r.name == IMPLICIT_START_RULE][0]
        branch = start_rule.body[0]
        self.assertEqual(len(branch.repetitions), 1)  # {x 1} is a transform block
        self.assertEqual(branch.terminal.name, "r")
        self.assertEqual(len(branch.terminal.args), 1)


# =========================================================================
# Interpreter tests
# =========================================================================

class TestParamRuleInterpretation(unittest.TestCase):
    """Test interpretation of parameterized rules."""

    def test_basic_param_substitution(self):
        """Parameters are substituted into the rule body."""
        # Use non-keyword param names to avoid ambiguity
        src = """
        rule my_box(w, ht) {
            {s w ht 1} box
        }
        my_box(2, 3)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertIn("box", result.matrices)
        self.assertEqual(len(result.matrices["box"]), 1)
        m = result.matrices["box"][0]
        # Scale: x=2, y=3, z=1
        self.assertAlmostEqual(m[0][0], 2.0, places=4)
        self.assertAlmostEqual(m[1][1], 3.0, places=4)
        self.assertAlmostEqual(m[2][2], 1.0, places=4)

    def test_param_with_expression(self):
        """Parameters can be expressions."""
        src = """
        #define p 4
        #define q 5
        rule my_box(w, ht) {
            {s w ht 1} box
        }
        my_box((p + 1), (q * 2))
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 5.0, places=4)  # p + 1 = 5
        self.assertAlmostEqual(m[1][1], 10.0, places=4)  # q * 2 = 10

    def test_param_shadows_define(self):
        """Parameter name can shadow a #define variable."""
        src = """
        #define scale_val 100
        rule r(scale_val) {
            {s scale_val 1 1} box
        }
        r(5)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # 'scale_val' refers to the parameter (5), not the define (100)
        self.assertAlmostEqual(m[0][0], 5.0, places=4)

    def test_param_used_in_expression_inside_rule(self):
        """Parameters are available in expressions inside the rule body."""
        src = """
        rule r(n) {
            (n) * { x 1 } box
        }
        r(3)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 3)

    def test_param_used_in_transform_expression(self):
        """Parameters in expressions within transformations."""
        src = """
        rule r(a) {
            {x (a * 2)} box
        }
        r(3)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][3], 6.0, places=4)  # x-translation = a * 2 = 6

    def test_rule_calling_param_rule(self):
        """A rule can call another parameterized rule."""
        src = """
        rule inner(w, ht) {
            {s w ht 1} box
        }
        rule outer(size) {
            inner(size, (size * 2))
        }
        outer(3)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 3.0, places=4)
        self.assertAlmostEqual(m[1][1], 6.0, places=4)

    def test_no_params_no_parens(self):
        """Rule without params called without parens."""
        src = """
        rule r {
            box
        }
        r
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 1)

    def test_no_params_empty_parens(self):
        """Rule without params called with empty parens."""
        src = """
        rule r {
            box
        }
        r()
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 1)

    def test_multiple_calls_different_args(self):
        """Same rule called multiple times with different args."""
        src = """
        rule my_box(w) {
            {s w 1 1} box
        }
        my_box(2)
        my_box(5)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 2)
        # Stack is LIFO, so my_box(5) appears first
        scales = [m[0][0] for m in result.matrices["box"]]
        self.assertIn(2.0, [round(s, 4) for s in scales])
        self.assertIn(5.0, [round(s, 4) for s in scales])

    def test_param_in_repetition_count(self):
        """Parameter used as repetition count."""
        src = """
        rule repeat_n(n) {
            (n) * { x 1 } box
        }
        repeat_n(5)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        self.assertEqual(len(result.matrices["box"]), 5)


# =========================================================================
# Error handling tests
# =========================================================================

class TestParamRuleErrors(unittest.TestCase):
    """Test error handling for parameterized rules."""

    def test_wrong_arg_count_too_few(self):
        """Calling a rule with too few arguments raises ValueError."""
        src = """
        rule r(a, b) { box }
        r(1)
        """
        prog = parse(src)
        with self.assertRaises(ValueError) as ctx:
            Interpreter.interpret(prog)
        self.assertIn("expects 2", str(ctx.exception))
        self.assertIn("got 1", str(ctx.exception))

    def test_wrong_arg_count_too_many(self):
        """Calling a rule with too many arguments raises ValueError."""
        src = """
        rule r(a) { box }
        r(1, 2, 3)
        """
        prog = parse(src)
        with self.assertRaises(ValueError) as ctx:
            Interpreter.interpret(prog)
        self.assertIn("expects 1", str(ctx.exception))
        self.assertIn("got 3", str(ctx.exception))

    def test_args_to_non_param_rule(self):
        """Calling a non-parameterized rule with args raises ValueError."""
        src = """
        rule r { box }
        r(1)
        """
        prog = parse(src)
        with self.assertRaises(ValueError) as ctx:
            Interpreter.interpret(prog)
        self.assertIn("no parameters", str(ctx.exception))

    def test_inconsistent_param_count(self):
        """Multiple definitions with different param counts raise ValueError."""
        src = """
        rule r(a) { box }
        rule r(a, b) { sphere }
        r(1)
        """
        prog = parse(src)
        with self.assertRaises(ValueError) as ctx:
            Interpreter.interpret(prog)
        self.assertIn("inconsistent", str(ctx.exception).lower())

    def test_consistent_param_count_same(self):
        """Multiple definitions with same param count is OK."""
        src = """
        rule r(a) maxdepth 1 { box }
        rule r(a) { sphere }
        r(1)
        """
        prog = parse(src)
        # Should not raise — both have 1 parameter
        result = Interpreter.interpret(prog)
        # Result has either box or sphere (weighted random)
        self.assertTrue(
            "box" in result.matrices or "sphere" in result.matrices
        )


# =========================================================================
# Serializer tests
# =========================================================================

class TestParamRuleSerialization(unittest.TestCase):
    """Test serialization of parameterized rules."""

    def test_serialize_rule_with_params(self):
        """Rule with params serializes correctly."""
        src = "rule my_box(w, ht) { box }"
        prog = parse(src)
        output = ast_to_string(prog)
        self.assertIn("rule my_box(w, ht)", output)

    def test_serialize_rule_call_with_args(self):
        """Rule call with args serializes correctly."""
        src = """
        rule r(w, ht) { box }
        r(2, 3)
        """
        prog = parse(src)
        output = ast_to_string(prog)
        self.assertIn("r(2, 3)", output)

    def test_serialize_roundtrip(self):
        """Parse → serialize → parse produces equivalent AST."""
        src = """
        rule my_box(w, ht) {
            {s w ht 1} box
        }
        my_box(2, 3)
        """
        prog1 = parse(src)
        output = ast_to_string(prog1)
        prog2 = parse(output)

        # Check rule params
        rule1 = [r for r in prog1.rules if r.name == "my_box"][0]
        rule2 = [r for r in prog2.rules if r.name == "my_box"][0]
        self.assertEqual(rule1.params, rule2.params)

        # Check call args
        start1 = [r for r in prog1.rules if r.name == IMPLICIT_START_RULE][0]
        start2 = [r for r in prog2.rules if r.name == IMPLICIT_START_RULE][0]
        ref1 = start1.body[0].terminal
        ref2 = start2.body[0].terminal
        self.assertEqual(len(ref1.args), len(ref2.args))

    def test_serialize_no_params(self):
        """Rule without params doesn't show empty parens."""
        src = "rule r { box }"
        prog = parse(src)
        output = ast_to_string(prog)
        self.assertIn("rule r", output)
        self.assertNotIn("rule r()", output)


# =========================================================================
# XML conversion tests
# =========================================================================

class TestParamRuleXml(unittest.TestCase):
    """Test that parameterized rules are rejected by XML conversion."""

    def test_xml_rejects_param_rule(self):
        """XML conversion rejects rules with parameters."""
        src = "rule r(w, ht) { box }"
        prog = parse(src)
        with self.assertRaises(ExpressionInXmlError) as ctx:
            ast_to_xml(prog)
        self.assertIn("parameters", str(ctx.exception).lower())

    def test_xml_rejects_param_call(self):
        """XML conversion rejects rule calls with arguments."""
        src = """
        rule r(w) { box }
        r(2)
        """
        prog = parse(src)
        with self.assertRaises(ExpressionInXmlError) as ctx:
            ast_to_xml(prog)
        # Error mentions either parameters or arguments
        msg = str(ctx.exception).lower()
        self.assertTrue("param" in msg or "argument" in msg)

    def test_xml_allows_non_param_rule(self):
        """XML conversion allows non-parameterized rules."""
        src = """
        rule r { box }
        r
        """
        prog = parse(src)
        # Should not raise
        xml_elem = ast_to_xml(prog)
        self.assertEqual(xml_elem.tag, "rules")


# =========================================================================
# Advanced tests
# =========================================================================

class TestParamRuleAdvanced(unittest.TestCase):
    """Advanced scenarios for parameterized rules."""

    def test_params_persist_through_rule_chain(self):
        """Parameters persist through a chain of rule calls."""
        src = """
        rule level2(w) {
            {s w 1 1} box
        }
        rule level1(w) {
            level2(w)
        }
        rule level0(w) {
            level1(w)
        }
        level0(7)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 7.0, places=4)

    def test_param_with_define_fallback(self):
        """Undefined param name falls back to #define."""
        src = """
        #define default_w 10
        rule r(ht) {
            {s default_w ht 1} box
        }
        r(3)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 10.0, places=4)
        self.assertAlmostEqual(m[1][1], 3.0, places=4)

    def test_param_in_nested_rule_shadows_outer(self):
        """Inner rule parameter shadows outer rule parameter."""
        src = """
        rule inner(sx) {
            {s sx 1 1} box
        }
        rule outer(sx) {
            inner(99)
        }
        outer(5)
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        # inner's sx = 99 (from the call), not 5 (from outer)
        self.assertAlmostEqual(m[0][0], 99.0, places=4)

    def test_multiple_params_with_mixed_types(self):
        """Parameters with mixed types: numbers, vars, expressions."""
        src = """
        #define val 10
        rule r(p1, p2, p3) {
            {s p1 p2 p3} box
        }
        r(2, val, (val / 2))
        """
        prog = parse(src)
        result = Interpreter.interpret(prog)
        m = result.matrices["box"][0]
        self.assertAlmostEqual(m[0][0], 2.0, places=4)
        self.assertAlmostEqual(m[1][1], 10.0, places=4)
        self.assertAlmostEqual(m[2][2], 5.0, places=4)

    def test_param_rule_with_retirement(self):
        """Parameterized rule with maxdepth retirement."""
        src2 = """
        rule tree(n) maxdepth 2 > tree_leaf {
            {s 0.5} tree((n - 1))
        }
        rule tree_leaf(n) {
            box
        }
        tree(5)
        """
        prog2 = parse(src2)
        result = Interpreter.interpret(prog2)
        self.assertIn("box", result.matrices)
        self.assertTrue(len(result.matrices["box"]) > 0)


if __name__ == "__main__":
    unittest.main()
