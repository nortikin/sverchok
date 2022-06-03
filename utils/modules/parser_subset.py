"""
in Python 3.10 the parser module has been removed. some old nodes 
(namely: formula.py / formula2.py / profile_mk2.py) make light use of that module.

The main goal of this module is to suppress a startup import exception caused by 
the missing parser module, and at the same time offer the basic features of that
module as used by these nodes.
"""

try:
    import parser

except (ImportError, ModuleNotFoundError) as err:

    from dataclasses import dataclass

    @dataclass
    class Expr(str):
        str_formula: str
        def compile(self):
            # print('use mock')
            return compile(self.str_formula, '<string>', mode='eval')

    parser = lambda: None
    parser.expr = lambda str_formula: Expr(str_formula)

