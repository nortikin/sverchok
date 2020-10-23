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

# by Alexander Nedovizin

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode
from sverchok.data_structure import handle_read, handle_write

from random import uniform
from copy import deepcopy
from cmath import exp


class SvNeuroElman:
    """ A set of functions for working with a neuron """

    def init_w(self, number, ext, treshold):
        out = []
        for _ in range(number):
            tmp = [uniform(-treshold, treshold) for _ in range(ext)]
            out.append(tmp)

        return out

    def sigmoida(self, signal):
        result = (exp(signal).real - exp(-signal).real) / (exp(signal).real + exp(-signal).real + 1e-8)
        return result

    def neuro(self, list_in, etalon, maxim, is_learning, prop):
        """ The function calculates the output values depending on the input """

        _list_in = [signal_a/maxim for signal_a in list_in]
        out_a = self.layer_a(_list_in, prop)
        out_b = self.layer_b(out_a, prop)
        out_c = self.layer_c(out_b, prop)

        if is_learning:
            len_etalon = len(etalon)
            if len_etalon < prop['InC']:
                d = prop['InC'] - len_etalon
                etalon = etalon + [0] * d
            _etalon = list(map(lambda x: x / maxim, etalon))
            self.learning(out_a, out_b, out_c, _etalon, maxim, prop)

        _out_c = list(map(lambda x: x * maxim, out_c))
        return _out_c

    def layer_a(self, list_in, prop):
        out_a = deepcopy(list_in)
        len_outa = len(out_a)
        if len_outa < prop['InA']:
            ext_list_in = prop['InA'] - len_outa
            out_a.extend([1] * ext_list_in)
        return out_a

    def layer_b(self, outA, prop):
        out_b = [0] * prop['InB']
        for idx_a, weights_a in enumerate(prop['wA']):
            for idx_b, wa in enumerate(weights_a):
                signal_a = wa * outA[idx_a]
                out_b[idx_b] += signal_a

        _out_b = [self.sigmoida(signal_b) for signal_b in out_b]
        return _out_b

    def layer_c(self, outB, prop):
        out_c = [0] * prop['InC']
        for idx_b, weights_b in enumerate(prop['wB']):
            for idx_c, wb in enumerate(weights_b):
                signal_b = wb * outB[idx_b]
                out_c[idx_c] += signal_b
        return out_c

    # **********************
    @staticmethod
    def sigma(ej, f_vj):
        return ej * f_vj

    @staticmethod
    def f_vj_sigmoida(a, yj):
        if a == 0:
            b = 1
        else:
            b = 1 / a
        return b * yj * (1 - yj)

    @staticmethod
    def func_ej_last(dj, yj):
        return dj - yj

    @staticmethod
    def func_ej_inner(e_sigma_k, wkj):
        return e_sigma_k * wkj

    @staticmethod
    def delta_wji(sigma_j, yi, prop):
        return prop['k_learning'] * sigma_j * yi

    @staticmethod
    def func_w(w, dw, prop):
        return (1 - prop['k_lambda']) * w + dw

    def learning(self, out_a, out_b, out_c, etalon, maxim, prop):
        weights_a = deepcopy(prop['wA'])
        weights_b = deepcopy(prop['wB'])
        _out_a = deepcopy(out_a)
        for idx, native_signal_a in enumerate(out_a):
            processed_signal_a = deepcopy(native_signal_a)
            _out_b = deepcopy(out_b)
            _out_c = deepcopy(out_c)
            for _ in range(prop['cycles']):
                in_b = [0] * prop['InB']
                in_a = [0] * prop['InA']
                for idc, signal_c in enumerate(_out_c):
                    c_ = self.sigmoida(signal_c)
                    e_c = self.func_ej_last(etalon[idc], signal_c)
                    f_vc = self.f_vj_sigmoida(prop['InC'], c_)
                    sigma_c = self.sigma(e_c, f_vc)

                    for idb, signal_b in enumerate(_out_b):
                        dwji = self.delta_wji(sigma_c, signal_b, prop)
                        weights_b[idb][idc] = self.func_w(weights_b[idb][idc], dwji, prop)
                        in_b[idb] += sigma_c * dwji

                for idb, signal_b in enumerate(_out_b):
                    f_vb = self.f_vj_sigmoida(prop['InB'], signal_b)
                    sigma_b = self.sigma(in_b[idb], f_vb)

                    for ida, signal_a in enumerate(out_a):
                        dwji = self.delta_wji(sigma_b, signal_a, prop)
                        weights_a[ida][idb] = self.func_w(weights_a[ida][idb], dwji, prop)
                        in_a[ida] += sigma_b * dwji

                processed_signal_a -= prop['epsilon'] * processed_signal_a * (maxim - processed_signal_a)
                absdx = abs(native_signal_a - processed_signal_a)
                if absdx <= prop['trashold'] or absdx > abs(maxim / 2):
                    break
                _out_a[idx] = processed_signal_a

                _out_b = self.layer_b(_out_a, prop)
                _out_c = self.layer_c(out_b, prop)

        prop['wA'] = weights_a
        prop['wB'] = weights_b


class SvNeuroElman1LNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Neuro Elman 1 Layer '''

    bl_idname = 'SvNeuroElman1LNode'
    bl_label = '*Neuro Elman 1 Layer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_NEURO'

    elman = None

    k_learning: FloatProperty(name='k_learning', default=0.1, update=updateNode, description="Learning rate")
    gisterezis: FloatProperty(name='gisterezis', default=0.1, min=0.0, update=updateNode,
                              description="Sets the threshold of values inside the learning algorithm (in plans)")
    maximum: FloatProperty(name='maximum', default=3.0, update=updateNode,
                           description="The maximum value of the input and output layer")
    menushka: BoolProperty(name='menushka', default=False, description="Extra options")
    epsilon: FloatProperty(name='epsilon', default=1.0, update=updateNode,
                           description="The coefficient participates in the learning assessment function")
    treshold: FloatProperty(name='treshold', default=0.01, update=updateNode,
                            description="Participates in learning assessment")
    k_lambda: FloatProperty(name='k_lambda', default=0.0001, max=0.1, update=updateNode,
                            description="Weight change step during training")
    cycles: IntProperty(name='cycles', default=3, min=1, update=updateNode, description="Internal Learning Loops")
    lA: IntProperty(name='lA', default=1, min=0, update=updateNode,
                    description="Input layer (must match the number of elements in the input)")
    lB: IntProperty(name='lB', default=5, min=0, update=updateNode,
                    description="Inner layer (more nodes - more accurate calculations)")
    lC: IntProperty(name='lC', default=1, min=0, update=updateNode,
                    description="Output layer (must match the number of elements in the output)")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "data")
        self.inputs.new('SvStringsSocket', "etalon")
        self.outputs.new('SvStringsSocket', "result")

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        handle_name = self.name + self.id_data.name

        col_top = layout.column(align=True)
        row = col_top.row(align=True)
        row.prop(self, "lA", text="A layer")
        row = col_top.row(align=True)
        row.prop(self, "lB", text="B layer")
        row = col_top.row(align=True)
        row.prop(self, "lC", text="C layer")

        layout.prop(self, "maximum", text="maximum")
        op_start = layout.operator('node.sverchok_neuro', text='Reset')
        op_start.typ = 1
        op_start.handle_name = handle_name
        layout.prop(self, "menushka", text="extend sets:")
        if self.menushka:
            layout.prop(self, "k_learning", text="koeff learning")
            layout.prop(self, "gisterezis", text="gisterezis")
            layout.prop(self, "cycles", text="cycles")
            col = layout.column(align=True)
            col.prop(self, "epsilon", text="epsilon")
            col = layout.column(align=True)
            col.prop(self, "k_lambda", text="lambda")
            col = layout.column(align=True)
            col.prop(self, "treshold", text="treshold")

    def process(self):
        handle_name = self.name + self.id_data.name
        handle = handle_read(handle_name)
        props = handle[1]
        if not handle[0]:
            elman = SvNeuroElman()
            props = {'InA': 2,
                     'InB': 5,
                     'InC': 1,
                     'wA': [],
                     'wB': [],
                     'gister': 0.01,
                     'k_learning': 0.1,
                     'epsilon': 1.3,
                     'cycles': 3,
                     'trashold': 0.01,
                     'k_lambda': 0.0001,
                     'Elman': elman,
                     }

        self.elman = props['Elman']
        result = []
        if self.outputs['result'].is_linked and self.inputs['data'].is_linked:

            if self.inputs['etalon'].is_linked:
                input_etalon = self.inputs['etalon'].sv_get()
                is_learning = True
            else:
                input_etalon = [[0]]
                is_learning = False

            if (props['InA'] != self.lA + 1) or props['InB'] != self.lB or props['InC'] != self.lC:
                props['InA'] = self.lA + 1
                props['InB'] = self.lB
                props['InC'] = self.lC
                props['wA'] = self.elman.init_w(props['InA'], props['InB'], props['trashold'])
                props['wB'] = self.elman.init_w(props['InB'], props['InC'], props['trashold'])

            props['gister'] = self.gisterezis
            props['k_learning'] = self.k_learning
            props['epsilon'] = self.epsilon
            props['k_lambda'] = self.k_lambda
            props['cycles'] = self.cycles
            props['trashold'] = self.treshold

            input_data = self.inputs['data'].sv_get()

            if type(input_etalon[0]) not in [list, tuple]:
                input_etalon = [input_etalon]
            if type(input_data[0]) not in [list, tuple]:
                input_data = [input_data]

            for idx, data in enumerate(input_data):
                let = len(input_etalon) - 1
                eta = input_etalon[min(idx, let)]
                data2 = [1.0] + data
                if type(eta) not in [list, tuple]:
                    eta = [eta]

                result.append(self.elman.neuro(data2, eta, self.maximum, is_learning, props))
        else:
            result = [[]]

        handle_write(handle_name, props)
        self.outputs['result'].sv_set(result)


# *********************************

class SvNeuroOps(bpy.types.Operator):
    """ Resetting weights """
    bl_idname = "node.sverchok_neuro"
    bl_label = "Sverchok Neuro operators"
    bl_options = {'REGISTER', 'UNDO'}

    typ: IntProperty(name='typ', default=0)
    handle_name: StringProperty(name='handle')

    def execute(self, context):
        if self.typ == 1:
            handle = handle_read(self.handle_name)
            prop = handle[1]
            if handle[0]:
                elman = prop['Elman']
                prop['wA'] = elman.init_w(prop['InA'], prop['InB'], prop['trashold'])
                prop['wB'] = elman.init_w(prop['InB'], prop['InC'], prop['trashold'])
                handle_write(self.handle_name, prop)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SvNeuroOps)
    bpy.utils.register_class(SvNeuroElman1LNode)


def unregister():
    bpy.utils.unregister_class(SvNeuroElman1LNode)
    bpy.utils.unregister_class(SvNeuroOps)
