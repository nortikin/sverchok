# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
import numpy as np

def avr(data):
    sum_d = 0.0
    flag = True
    for d in data:
        if type(d) not in [float, int, np.float64, np.int32]:
            idx_avr = len(data)//2
            result = data[idx_avr]
            flag = False
            break

        sum_d += d

    if flag:
        result = sum_d / len(data)
    return result
def numpy_average(data):
    if data.ndim > 1:
        return data[data.shape[0] //2]
    return np.sum(data)/data.shape[0]

def numpy_max(data):
    if len(data.shape) > 1:
        return data[-1]
    return np.max(data)

def numpy_min(data):
    if len(data.shape) > 1:
        return data[0]
    return np.min(data)


func_dict = {
    "MIN": min,
    "MAX": max,
    "AVR": avr,
    "SUM": sum
}
numpy_func_dict = {
    "MIN": numpy_min,
    "MAX": numpy_max,
    "AVR": numpy_average,
    "SUM": lambda x: np.sum(x, axis=0)
}
class ListFuncNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Average, Sum, Min...
    Tooltip: Operations with list, sum, average, min, max
    '''
    bl_idname = 'ListFuncNode'
    bl_label = 'List Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_MATH'

    mode_items = [
        ("MIN",         "Minimum",        "", 1),
        ("MAX",         "Maximum",        "", 2),
        ("AVR",         "Average",        "", 3),
        ("SUM",         "Sum",            "", 4)
        #("ACC",         "Accumulate",     "", 5),
    ]

    func_: EnumProperty(
        name="Function", description="Function choice",
        default="AVR", items=mode_items, update=updateNode)

    level: IntProperty(
        name='level_to_count',
        default=1, min=0, update=updateNode)

    wrap: BoolProperty(
        name='wrap', description='extra level add',
        default=True, update=updateNode)


    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self, "func_", text="Functions:")
        layout.prop(self, "wrap", text="Warp")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.outputs.new('SvStringsSocket', "Function")

    def process(self):

        if self.outputs['Function'].is_linked and self.inputs['Data'].is_linked:
            data = self.inputs['Data'].sv_get()
            func = func_dict[self.func_]
            numpy_func = numpy_func_dict[self.func_]

            if not self.level:
                out = [func(data)]
            else:
                out = self.count(data, self.level, func, numpy_func)

            self.outputs['Function'].sv_set([out] if self.wrap else out)

    def count(self, data, level, func, numpy_func):
        out = []
        if level:
            for obj in data:
                out.append(self.count(obj, level-1, func, numpy_func))
        elif isinstance(data, (list, tuple)) and len(data) > 0:
            if len(data) == 1:
                data.extend(data)
            out = func(data)
        elif isinstance(data, np.ndarray):
            out = numpy_func(data)
        else:
            pass
        return out


def register():
    bpy.utils.register_class(ListFuncNode)


def unregister():
    bpy.utils.unregister_class(ListFuncNode)
