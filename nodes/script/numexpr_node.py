# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import re

import numpy as np
try:
    import numexpr as ne
except ImportError:
    ne = None

import bpy
from bpy.props import StringProperty

from sverchok.data_structure import numpy_full_list
from sverchok.node_tree import SverchCustomTreeNode


class SvNumExprNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers:
    Tooltip:
    """
    bl_idname = 'SvNumExprNode'
    bl_label = 'Num Expression node'
    bl_icon = 'MOD_BOOLEAN'

    function_names = {
        'where', 'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2',
        'sinh', 'cosh', 'tanh', 'arcsinh', 'arccosh', 'arctanh', 'log',
        'log10', 'log1p', 'exp', 'expm1', 'sqrt', 'abs', 'conj', 'real',
        'imag', 'complex', 'contains', 'sum', 'prod'}

    def expression_update(self, context):
        variables = []
        invalid_names = []
        for word in re.split(r'\W+', self.expression):  # https://regexr.com/
            if not word or word.isdigit() or word in self.function_names:
                continue
            if word.isidentifier():
                variables.append(word)
            else:
                invalid_names.append(word)
        self['variables'] = variables
        self['invalid_names'] = invalid_names
        self.sv_init(context)
        self.process_node(context)

    expression: StringProperty(update=expression_update)

    def sv_draw_buttons(self, context, layout):
        row = layout.row()
        row.alert = bool(self.get('invalid_names'))
        row.prop(self, 'expression', text='')

    def sv_init(self, context):
        expr_vars = set(self.get('variables'))
        if not self.outputs:
            self.outputs.new('SvStringsSocket', 'Result')

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
            s = self.inputs.new('SvStringsSocket', var)
            s.use_prop = True
            s.show_property_type = True

    def process(self):
        if not self.expression:
            self.outputs[0].sv_set([])
            return
        if invalid_names := self.get('invalid_names'):
            raise NameError(f"{invalid_names=}")
        inp_vars = {s.name: np.asarray(s.sv_get(deepcopy=False)[0])
                    for s in self.inputs}
        data_len = max(len(d) for d in inp_vars.values())
        inp_vars = {n: numpy_full_list(d, data_len) if len(d) > 1 else d
                    for n, d in inp_vars.items()}
        result = ne.evaluate(self.expression, local_dict=inp_vars)
        self.outputs[0].sv_set([result])


register, unregister = bpy.utils.register_classes_factory(SvNumExprNode)
