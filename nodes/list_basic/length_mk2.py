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

import itertools

import bpy
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


class ListLengthNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' List Length MK2 '''
    bl_idname = 'ListLengthNodeMK2'
    bl_label = 'List Length MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    level = IntProperty(name='level_to_count',
                        default=1, min=0,
                        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "level", text="level")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Data", "Data")
        self.outputs.new('StringsSocket', "Length", "Length")

    def process(self):
        # достаём два слота - вершины и полики
        if 'Length' in self.outputs and self.outputs['Length'].is_linked:
            if 'Data' in self.inputs and self.inputs['Data'].is_linked:
                data = SvGetSocketAnyType(self, self.inputs['Data'])

                if not self.level:
                    out = [[len(data)]]
                elif self.level == 1:
                    out = [self.count(data, self.level+1)]
                else:
                    out = self.count(data, self.level+1)

                SvSetSocketAnyType(self, 'Length', out)

    def count(self, data, level):
        if isinstance(data, (float, int)):
            return 1
        if level == 1:
            return [self.count(obj, level-1) for obj in data]
        elif level == 2:
            out = [self.count(obj, level-1) for obj in data]
            return out
        elif level > 2:  # flatten all but last level, we should preserve more detail than this
            out = [self.count(obj, level-1) for obj in data]
            return [list(itertools.chain.from_iterable(obj)) for obj in out]
        else:
            return len(data)


def register():
    bpy.utils.register_class(ListLengthNodeMK2)


def unregister():
    bpy.utils.unregister_class(ListLengthNodeMK2)


if __name__ == '__main__':
    register()