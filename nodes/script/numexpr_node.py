# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import re
try:
    import numexpr as ne
except ImportError:
    ne = None

import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.vectorize import match_sockets


class SvNumExprNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: math formula script
    Tooltip: Node supplies routines for the fast evaluation of array expressions elementwise
    """
    bl_idname = 'SvNumExprNode'
    bl_label = 'Num Expression node'
    sv_icon = 'SV_FORMULA'
    sv_dependencies = ['numexpr']

    function_names = {
        'where', 'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2',
        'sinh', 'cosh', 'tanh', 'arcsinh', 'arccosh', 'arctanh', 'log',
        'log10', 'log1p', 'exp', 'expm1', 'sqrt', 'abs', 'conj', 'real',
        'imag', 'complex', 'contains', 'sum', 'prod', 'min', 'max', 'floor',
        'ceil', 'axis'}

    def expression_update(self, context):
        variables = set()
        invalid_names = set()
        for word in re.split(r'\W+', self.expression):  # https://regexr.com/
            if not word or word.isdigit() or word in self.function_names:
                continue
            if word.isidentifier():
                variables.add(word)
            else:
                invalid_names.add(word)
        self['variables'] = list(variables)
        self['invalid_names'] = list(invalid_names)
        self.sv_init(context)
        self.process_node(context)

    expression: StringProperty(update=expression_update)

    presets = [  # can be edited any way during live time of the node
        ("", "Scalar", "", custom_icon("SV_NUMBER"), 0),
        ("VALUE", "Value", "", "DOT", 1),
        ("MAP_RANGE", 'Map Range', "", "MOD_OFFSET", 2),
        ("MIX_NUMBERS", 'Mix Numbers', "", custom_icon('SV_MIX_INPUTS'), 3),
        ("CLAMP", "Clamp", "", "NOCURVE", 4),
        ("STEPPING", "Stepping", "Round value with step", "IPO_CONSTANT", 5),
        ("LENGTH", "Length", "Length of the array", custom_icon("SV_LIST_LEN"), 6),
        ("", "Vector", "", custom_icon("SV_VECTOR"), 7),
        ("VECTOR_VALUE", "Value", "", "DOT", 8),
        ("MOVE", "Move", "", custom_icon('SV_MOVE'), 9),
        ("VECTOR_SCALE", "Scale", "", custom_icon('SV_SCALE'), 10),
        ("", "Logic", "", custom_icon("SV_LOGIC"), 11),
        ("AND", "And", "", "", 12),
        ("OR", "Or", "", "", 13),
        ("NOT", "Not", "", "", 14),
        ("SWITCH", "Switch", "", "", 15),
    ]

    preset_formulas = {
        # Scalar
        "VALUE": 'value',
        "MAP_RANGE": "new_min+(__val-_old_min)*((new_max-new_min)/(_old_max-_old_min))",
        "MIX_NUMBERS": "(val2-val1)*factor+val1",
        "CLAMP": "where(__value>max_,max_, where(__value<_min,_min,__value))",
        "STEPPING": "floor(_value/step)*step",
        "LENGTH": "sum(floor(a==a))",
        # VECTOR
        "VECTOR_VALUE": "Value",
        "MOVE": "V1+V2*strength",
        "VECTOR_SCALE": "(V-VCenters)*(VScale*multiplier)+VCenters",
        # LOGIC
        "AND": "(a!=0) & (b!=0)",
        "OR": "(a!=0) | (b!=0)",
        "NOT": "~(a!=0)",
        "SWITCH": "where(_switch!=0,true,false)",
    }

    def apply_preset(self, context):
        self.expression = self.preset_formulas[self.preset]

    preset: EnumProperty(items=presets, update=apply_preset)

    def sv_draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'expression', text='')
        row.prop(self, 'preset', icon='PRESET', icon_only=True)

    def sv_init(self, context):
        expr_vars = sorted(self.get('variables', []))
        if not self.outputs:
            self.outputs.new('SvStringsSocket', 'Result')

        out_type = 'SvVerticesSocket' if any(v.startswith('V') for v in expr_vars) \
            else 'SvStringsSocket'

        # fix out type
        if out_type != self.outputs[0].bl_idname:
            self.outputs[0].replace_socket(out_type)

        # remove all sockets
        if not expr_vars:
            self.inputs.clear()

        # remove sockets which are not presented in the modifier
        for sv_s in self.inputs:
            if sv_s.identifier not in expr_vars:
                self.inputs.remove(sv_s)

        # add new sockets
        socks = {s.name: i for i, s in enumerate(self.inputs)}
        for var in expr_vars:
            if var in socks:
                continue
            if var.startswith('V'):
                self.inputs.new('SvVerticesSocket', var).use_prop = True
            else:
                s = self.inputs.new('SvStringsSocket', var)
                s.use_prop = True
                s.show_property_type = True

        # fix socket positions
        for _ in range(100):
            for pos, sock in enumerate(self.inputs):
                if pos != (to_pos := expr_vars.index(sock.name)):
                    self.inputs.move(pos, to_pos)
                    break
            else:
                break
        else:
            self.debug("It seems there is some problem in ordering sockets")

    def process(self):
        if not self.expression:
            self.outputs[0].sv_set([])
            return
        if invalid_names := self.get('invalid_names'):
            raise NameError(f"{invalid_names=}")
        inp_vars = [s.sv_get(deepcopy=False) for s in self.inputs]
        names = [s.name for s in self.inputs]
        out = []
        for data in match_sockets(*inp_vars):
            obj_vars = {n: d for n, d in zip(names, data)}
            result = ne.evaluate(self.expression, local_dict=obj_vars)
            out.append(result)
        self.outputs[0].sv_set(out)


register, unregister = bpy.utils.register_classes_factory([SvNumExprNode])
