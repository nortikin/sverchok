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


class SvNeuro_Elman:

    def __init__(self):
        self.gister = 0.1
        self.k_learning = 0.1

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
        outA = self.layerA(list_in, prop)
        outB = self.layerB(outA, prop)
        outC = self.layerC(outB, prop)

        if is_learning:
            len_etalon = len(etalon)
            if len_etalon < prop['InC']:
                d = prop['InC'] - len_etalon
                etalon = etalon + [0] * d
            etalon_ = list(map(lambda x: x / maxim, etalon))
            self.learning(outA, outB, outC, etalon_, maxim, prop)

        outC_ = list(map(lambda x: x * maxim, outC))
        return outC_

    def layerA(self, list_in, prop):
        outA = deepcopy(list_in)
        len_outa = len(outA)
        if len_outa < prop['InA']:
            ext_list_in = prop['InA'] - len_outa
            outA.extend([1] * ext_list_in)
        return outA

    def layerB(self, outA, prop):
        outB = [0] * prop['InB']
        for idx_a, weights_a in enumerate(prop['wA']):
            for idx_b, wa in enumerate(weights_a):
                signal_a = wa * outA[idx_a]
                # TODO - Здесь можно поставить порог, ниже которого сигнал не пройдёт
                outB[idx_b] += signal_a

        outB_ = [self.sigmoida(signal_b) for signal_b in outB]
        return outB_

    def layerC(self, outB, prop):
        outC = [0] * prop['InC']
        for idx_b, weights_b in enumerate(prop['wB']):
            for idx_c, wb in enumerate(weights_b):
                signal_b = wb * outB[idx_b]
                # TODO - Здесь можно поставить порог, ниже которого сигнал не пройдёт
                outC[idx_c] += signal_b
        return outC

    # **********************
    def sigma(self, ej, f_vj):
        return ej * f_vj

    def f_vj_sigmoida(self, a, yj):
        if a == 0:
            b = 1
        else:
            b = 1 / a
        return b * yj * (1 - yj)

    def func_ej_last(self, dj, yj):
        return dj - yj

    def func_ej_inner(self, Esigmak, wkj):
        return Esigmak * wkj

    def delta_wji(self, sigmaj, yi, prop):
        return prop['k_learning'] * sigmaj * yi

    def func_w(self, w, dw, prop):
        return (1 - prop['k_lambda']) * w + dw

    def learning(self, outA, outB, outC, etalon, maxim, prop):
        weights_a = deepcopy(prop['wA'])
        weights_b = deepcopy(prop['wB'])
        outA_ = deepcopy(outA)
        for idx, native_signal_a in enumerate(outA):
            processed_signal_a = deepcopy(native_signal_a)
            outB_ = deepcopy(outB)
            outC_ = deepcopy(outC)
            for step in range(prop['cycles']):
                in_b = [0] * prop['InB']
                in_a = [0] * prop['InA']
                for idc, signal_c in enumerate(outC_):
                    c_ = self.sigmoida(signal_c)
                    eC = self.func_ej_last(etalon[idc], signal_c)
                    f_vC = self.f_vj_sigmoida(prop['InC'], c_)
                    sigmaC = self.sigma(eC, f_vC)

                    for idb, signal_b in enumerate(outB_):
                        dwji = self.delta_wji(sigmaC, signal_b, prop)
                        weights_b[idb][idc] = self.func_w(weights_b[idb][idc], dwji, prop)
                        in_b[idb] += sigmaC * dwji

                for idb, signal_b in enumerate(outB_):
                    f_vB = self.f_vj_sigmoida(prop['InB'], signal_b)
                    sigmaB = self.sigma(in_b[idb], f_vB)

                    for ida, signal_a in enumerate(outA):
                        dwji = self.delta_wji(sigmaB, signal_a, prop)
                        print(f"list_wA={weights_a}\tida={ida}\tidb={idb}\toutA={outA}")
                        weights_a[ida][idb] = self.func_w(weights_a[ida][idb], dwji, prop)
                        print("eA", in_a, "\tida=", ida)
                        in_a[ida] += sigmaB * dwji

                processed_signal_a -= prop['epsilon'] * processed_signal_a * (maxim - processed_signal_a)
                absdx = abs(native_signal_a - processed_signal_a)
                if absdx <= prop['trashold'] or absdx > abs(maxim / 2):
                    break
                outA_[idx] = processed_signal_a

                outB_ = self.layerB(outA_, prop)
                outC_ = self.layerC(outB, prop)

        prop['wA'] = weights_a
        prop['wB'] = weights_b


class SvNeuroElman1LNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Neuro Elman 1 Layer '''

    bl_idname = 'SvNeuroElman1LNode'
    bl_label = '*Neuro Elman 1 Layer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_NEURO'

    elman = None

    k_learning: FloatProperty(name='k_learning', default=0.1, update=updateNode, description="Коэффициент обучения")
    gisterezis: FloatProperty(name='gisterezis', default=0.1, min=0.0, update=updateNode,
                              description="Задаёт порог значений внутри алгоритма обучения (в планах)")
    maximum: FloatProperty(name='maximum', default=3.0, update=updateNode,
                           description="Максимальное значение входного и выходного слоя")
    menushka: BoolProperty(name='menushka', default=False, description="Дополнительные параметры")
    epsilon: FloatProperty(name='epsilon', default=1.0, update=updateNode,
                           description="Коэффициент участвует в функции оценки обучения")
    treshold: FloatProperty(name='treshold', default=0.01, update=updateNode, description="Участвует в оценке обучения")
    k_lambda: FloatProperty(name='k_lambda', default=0.0001, max=0.1, update=updateNode,
                            description="Шаг изменения веса при обучении")
    cycles: IntProperty(name='cycles', default=3, min=1, update=updateNode, description="Внутренние циклы обучения")
    lA: IntProperty(name='lA', default=1, min=0, update=updateNode,
                    description="Входной слой (должен соответствовать количеству элементов на входе)")
    lB: IntProperty(name='lB', default=5, min=0, update=updateNode,
                    description="Внутренний слой (больше узлов - точнее расчеты)")
    lC: IntProperty(name='lC', default=1, min=0, update=updateNode,
                    description="Выходной слой (должен соответствовать количеству элементов на выходе)")

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
        op_start = layout.operator('node.sverchok_neuro', text='Restart')
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
            elman = SvNeuro_Elman()
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
        self.elman.gister = abs(self.gisterezis)
        self.elman.k_learning = self.k_learning

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

                result.append([self.elman.neuro(data2, eta, self.maximum, is_learning, props)])
            result.append(result.pop(0))

        else:
            result = [[[]]]

        handle_write(handle_name, props)
        self.outputs['result'].sv_set(result)


# *********************************

class SvNeuroOps(bpy.types.Operator):
    """ Перезапуск узла """
    bl_idname = "node.sverchok_neuro"
    bl_label = "Sverchok Neuro operators"
    bl_options = {'REGISTER', 'UNDO'}

    typ: IntProperty(name='typ', default=0)
    handle_name: StringProperty(name='handle')

    def execute(self, context):
        if self.typ == 1:
            handle = handle_read(self.handle_name)
            prop = handle[1]
            elman = SvNeuro_Elman()
            if handle[0]:
                prop['wA'] = elman.init_w(prop['InA'], prop['InB'], prop['trashold'])
                prop['wB'] = elman.init_w(prop['InB'], prop['InC'], prop['trashold'])
                prop['Elman'] = elman
                handle_write(self.handle_name, prop)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SvNeuroOps)
    bpy.utils.register_class(SvNeuroElman1LNode)


def unregister():
    bpy.utils.unregister_class(SvNeuroElman1LNode)
    bpy.utils.unregister_class(SvNeuroOps)

# TODO - Не нравится, что структура выходных данных не соответсвует эталону
# TODO - Необходимо обрабатывать несколко объектов. Т.е. получил несколко объектов, так и выдавать несколько объектов
#  т.е. сколько объектов - столько обучений
# TODO - Добавить слот для обучения цепью узлов
