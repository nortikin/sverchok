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

from math import *

import bpy
from bpy. props import EnumProperty

from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import (updateNode, match_long_repeat,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class ScalarMathNode(bpy.types.Node, SverchCustomTreeNode):
    ''' ScalarMathNode '''
    bl_idname = 'ScalarMathNode'
    bl_label = 'function'
    bl_icon = 'OUTLINER_OB_EMPTY'


# Math functions from http://docs.python.org/3.3/library/math.html
# maybe this should be distilled to most common with the others available via Formula2 Node
# And some constants etc.
# Keep 4, columns number unchanged and only add new with unique number

    mode_items = [
        ("SINE",            "Sine",         "", 1),
        ("COSINE",          "Cosine",       "", 2),
        ("TANGENT",         "Tangent",      "", 3),
        ("ARCSINE",         "Arcsine",      "", 4),
        ("ARCCOSINE",       "Arccosine",    "", 5),
        ("ARCTANGENT",      "Arctangent",   "", 6),
        ("SQRT",            "Squareroot",   "", 11),
        ("NEG",             "Negate",       "", 12),
        ("DEGREES",         "Degrees",      "", 13),
        ("RADIANS",         "Radians",      "", 14),
        ("ABS",             "Absolute",     "", 15),
        ("CEIL",            "Ceiling",      "", 16),
        ("ROUND",           "Round",        "", 17),
        ("ROUND-N",         "Round N",      "", 18),
        ("FMOD",            "Fmod",         "", 19),
        ("MODULO",          "modulo",       "", 20),
        ("FLOOR",           "floor",        "", 21),
        ("EXP",             "Exponent",     "", 30),
        ("LN",              "log",          "", 31),
        ("LOG1P",           "log1p",        "", 32),
        ("LOG10",           "log10",        "", 33),
        ("ACOSH",           "acosh",        "", 40),
        ("ASINH",           "asinh",        "", 41),
        ("ATANH",           "atanh",        "", 42),
        ("COSH",            "cosh",         "", 43),
        ("SINH",            "sinh",         "", 44),
        ("TANH",            "tanh",         "", 45),
        ("ADD",              "+",           "", 50),
        ("SUB",              "-",           "", 51),
        ("MUL",              "*",           "", 52),
        ("DIV",              "/",           "", 53),
        ("INTDIV",           "//",          "", 54),
        ("POW",              "**",          "", 55),
        ("PI",               "pi",          "", 60),
        ("E",                "e",           "", 61),
        ("PHI",              "phi",         "", 62),
        ("TAU",              "tau",         "", 63),
        ("MIN",              "min",         "", 70),
        ("MAX",              "max",         "", 71),
        ("-1",               "x-1",         "", 80),
        ("+1",               "x+1",         "", 81),
        ("*2",               "x*2",         "", 82),
        ("/2",               "x/2",         "", 83),
        ("POW2",             "x**2",        "", 84),
        ]

    fx = {
        'SINE':       sin,
        'COSINE':     cos,
        'TANGENT':    tan,
        'ARCSINE':    asin,
        'ARCCOSINE':  acos,
        'ARCTANGENT': atan,
        'SQRT':       lambda x: sqrt(fabs(x)),
        'NEG':        lambda x: -x,
        'DEGREES':    degrees,
        'RADIANS':    radians,
        'ABS':        fabs,
        'FLOOR':      floor,
        'CEIL':       ceil,
        'EXP':        exp,
        'LN':         log,
        'LOG1P':      log1p,
        'LOG10':      log10,
        'ACOSH':      acosh,
        'ASINH':      asinh,
        'ATANH':      atanh,
        'COSH':       cosh,
        'SINH':       sinh,
        'TANH':       tanh,
        'ROUND':      round,
        '+1':         lambda x: x+1,
        '-1':         lambda x: x-1,
        '*2':         lambda x: x*2,
        '/2':         lambda x: x/2,
        'POW2':       lambda x: x**2,

    }

    fxy = {
        'ADD':      lambda x, y : x+y,
        'SUB':      lambda x, y : x-y,
        'DIV':      lambda x, y : x/y,
        'INTDIV':   lambda x, y : x//y,
        'MUL':      lambda x, y : x*y,
        'POW':      lambda x, y : x**y,
        'ROUND-N':  lambda x, y : round(x, y),
        'FMOD':     lambda x, y : fmod(x, y),
        'MODULO':   lambda x, y : x % y,
        'MIN':      lambda x, y : min(x, y),
        'MAX':      lambda x, y : max(x, y)
    }

    constant = {
        'PI':       pi,
        'TAU':      pi*2,
        'E':        e,
        'PHI':      1.61803398875,
    }

    items_ = EnumProperty(name="Function", description="Function choice",
                          default="SINE", items=mode_items,
                          update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "items_", "Functions:")

    def init(self, context):
        self.inputs.new('StringsSocket', "X", "x")
        self.outputs.new('StringsSocket', "float", "out")

    def update(self):

        # inputs
        nrInputs = 1
        if self.items_ in self.constant:
            nrInputs = 0
        elif self.items_ in self.fx:
            nrInputs = 1
        elif self.items_ in self.fxy:
            nrInputs = 2

        self.set_inputs(nrInputs)

        self.label = self.items_

        if 'X' in self.inputs and self.inputs['X'].links and \
           type(self.inputs['X'].links[0].from_socket) == StringsSocket:

            Number1 = SvGetSocketAnyType(self, self.inputs['X'])
        else:
            Number1 = []

        if 'Y' in self.inputs and self.inputs['Y'].links and \
           type(self.inputs['Y'].links[0].from_socket) == StringsSocket:

            Number2 = SvGetSocketAnyType(self, self.inputs['Y'])
        else:
            Number2 = []

        # outputs
        if 'float' in self.outputs and self.outputs['float'].links:
            result = []
            if nrInputs == 0:
                result = [[self.constant[self.items_]]]
            if nrInputs == 1:
                if len(Number1):
                    x = Number1
                    result = self.recurse_fx(x, self.fx[self.items_])
            if nrInputs == 2:
                if len(Number1) and len(Number2):
                    x = Number1
                    y = Number2
                    result = self.recurse_fxy(x, y, self.fxy[self.items_])
            SvSetSocketAnyType(self, 'float', result)

    def set_inputs(self, n):
        if n == len(self.inputs):
            return
        if n < len(self.inputs):
            while n < len(self.inputs):
                self.inputs.remove(self.inputs[-1])
        if n > len(self.inputs):
            if 'X' not in self.inputs:
                self.inputs.new('StringsSocket', "X", "x")
            if 'Y' not in self.inputs:
                self.inputs.new('StringsSocket', "Y", "y")

    # apply f to all values recursively
    def recurse_fx(self, l, f):
        if isinstance(l, (int, float)):
            return f(l)
        else:
            return [self.recurse_fx(i, f) for i in l]

    # match length of lists,
    # cases
    # [1,2,3] + [1,2,3] -> [2,4,6]
    # [1,2,3] + 1 -> [2,3,4]
    # [1,2,3] + [1,2] -> [2,4,5] , list is expanded to match length, [-1] is repeated
    # odd cases too.
    # [1,2,[1,1,1]] + [[1,2,3],1,2] -> [[2,3,4],3,[3,3,3]]
    def recurse_fxy(self, l1, l2, f):
        if (isinstance(l1, (int, float)) and
           isinstance(l2, (int, float))):
                return f(l1, l2)
        if (isinstance(l2, (list, tuple)) and
           isinstance(l1, (list, tuple))):
            data = zip(*match_long_repeat([l1, l2]))
            return [self.recurse_fxy(ll1, ll2, f) for ll1, ll2 in data]
        if isinstance(l1, (list, tuple)) and isinstance(l2, (int, float)):
            return self.recurse_fxy(l1, [l2], f)
        if isinstance(l1, (int, float)) and isinstance(l2, (list, tuple)):
            return self.recurse_fxy([l1], l2, f)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ScalarMathNode)


def unregister():
    bpy.utils.unregister_class(ScalarMathNode)
