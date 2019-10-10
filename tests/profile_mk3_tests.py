
from pathlib import Path
from os.path import basename

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.utils.parsec import parse
from sverchok.utils.modules.profile_mk3.interpreter import *
from sverchok.utils.modules.profile_mk3.parser import *
from sverchok.nodes.generators_extended.profile_mk3 import profile_template_path

class SimpleTests(SverchokTestCase):
    def test_identifier(self):
        result = parse(parse_identifier, "z")
        self.assertEquals(result, "z")

    def test_expr(self):
        string = "{r+1}"
        result = parse(parse_value, string)
        expected = Expression.from_string(string)
        self.assertEquals(result, expected)

    def test_negated_var(self):
        string = "-x"
        result = parse(parse_value, string)
        expected = NegatedVariable("x")
        self.assertEquals(result, expected)

class StatementParseTests(SverchokTestCase):
    def test_parse_default(self):
        string = "default v1 = 5"
        result = parse(parse_statement, string)
        expected = Default("v1", Const(5))
        self.assertEquals(result, expected)

    def test_parse_assign(self):
        string = "let v2 = v1"
        result = parse(parse_statement, string)
        expected = Assign("v2", Variable("v1"))
        self.assertEquals(result, expected)

    def test_parse_moveto(self):
        string = "M x,y"
        result = parse(parse_statement, string)
        expected = MoveTo(True, Variable("x"), Variable("y"))
        self.assertEquals(result, expected)

    def test_parse_lineto(self):
        string = "L 1,2 3,4"
        result = parse(parse_statement, string)
        expected = LineTo(True, [(Const(1), Const(2)), (Const(3), Const(4))], None, False)
        self.assertEquals(result, expected)

    def test_parse_lineto_n(self):
        string = "L 1,2 3,4 n=10"
        result = parse(parse_statement, string)
        expected = LineTo(True, [(Const(1), Const(2)), (Const(3), Const(4))], Const(10), False)
        self.assertEquals(result, expected)

    def test_parse_hor_lineto(self):
        string = "H 1 2;"
        result = parse(parse_statement, string)
        expected = HorizontalLineTo(True, [Const(1), Const(2)], None)
        self.assertEquals(result, expected)

    def test_parse_hor_lineto_n(self):
        string = "H 1 2 n=10;"
        result = parse(parse_statement, string)
        expected = HorizontalLineTo(True, [Const(1), Const(2)], Const(10))
        self.assertEquals(result, expected)

    def test_parse_vert_lineto(self):
        string = "V 1 2;"
        result = parse(parse_statement, string)
        expected = VerticalLineTo(True, [Const(1), Const(2)], None)
        self.assertEquals(result, expected)

    def test_parse_vert_lineto_n(self):
        string = "V 1 2 n=10;"
        result = parse(parse_statement, string)
        expected = VerticalLineTo(True, [Const(1), Const(2)], Const(10))
        self.assertEquals(result, expected)

    def test_parse_curveto(self):
        string = "C 1,2 3,4 5,6"
        result = parse(parse_statement, string)
        expected = CurveTo(True, [CurveTo.Segment((Const(1), Const(2)), (Const(3), Const(4)), (Const(5), Const(6)))], None, False)
        self.assertEquals(result, expected)

    def test_close_path(self):
        string = "x"
        result = parse(parse_statement, string)
        expected = ClosePath()
        self.assertEquals(result, expected)

    def test_close_All(self):
        string = "X"
        result = parse(parse_statement, string)
        expected = CloseAll()
        self.assertEquals(result, expected)

    # Other statement types: to be implemented

class ExamplesParseTests(SverchokTestCase):
    """
    This does not actually *import* profile examples into node tree,
    it only checks that they parse successfully.
    """
    def test_import_examples(self):
        examples_set = Path(profile_template_path)
        for listed_path in examples_set.iterdir():
            path = str(listed_path)
            name = basename(path)

            with self.subTest(file=name):
                with open(path, 'r') as f:
                    info("Checking profile example: %s", name)
                    profile_text = f.read()
                    with self.assert_logs_no_errors():
                        parse_profile(profile_text)

