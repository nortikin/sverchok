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

from itertools import accumulate

import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

def acc(l):
    return list(accumulate(l))

class ListFuncNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: List functions
    Tooltip: Operations with list, sum, average, min, max
    '''
    bl_idname = 'ListFuncNode'
    bl_label = 'List Math'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode_items = [
        ("MIN",         "Minimum",        "", 1),
        ("MAX",         "Maximum",        "", 2),
        ("AVR",         "Average",        "", 3),
        ("SUM",         "Sum",            "", 4)
        #("ACC",         "Accumulate",     "", 5),
    ]

    func_ = EnumProperty(
        name="Function", description="Function choice",
        default="AVR", items=mode_items, update=updateNode)
    
    level = IntProperty(
        name='level_to_count',
        default=1, min=0, update=updateNode)
    
    wrap = BoolProperty(
        name='wrap', description='extra level add', 
        default=False,update=updateNode)


    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")
        layout.prop(self, "func_", "Functions:")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "wrap")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Data")
        self.outputs.new('StringsSocket', "Function")

    def process(self):

        func_dict = {
            "MIN": min,
            "MAX": max,
            "AVR": self.avr,
            "SUM": sum 
        }

        if self.outputs['Function'].is_linked:
            if self.inputs['Data'].is_linked:
                data = self.inputs['Data'].sv_get()
                func = func_dict[self.func_]

                if not self.level:
                    out = [func(data)]
                else:
                    out = self.count(data, self.level, func)

                self.outputs['Function'].sv_set([out] if self.wrap else out)

    def count(self, data, level, func):
        out = []
        if level:
            for obj in data:
                out.append(self.count(obj, level-1, func))
        elif type(data) in [list, tuple] and len(data) > 0:
            if len(data) == 1:
                data.extend(data)
            out = func(data)
        else:
            pass
        return out

    def avr(self, data):
        sum_d = 0.0
        flag = True
        for d in data:
            if type(d) not in [float, int]:
                idx_avr = len(data)//2
                result = data[idx_avr]
                flag = False
                break

            sum_d += d

        if flag:
            result = sum_d / len(data)
        return result

def register():
    bpy.utils.register_class(ListFuncNode)


def unregister():
    bpy.utils.unregister_class(ListFuncNode)
