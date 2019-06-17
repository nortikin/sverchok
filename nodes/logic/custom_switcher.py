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


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvCustomSwitcher(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: project point to line
    If there are point and line the node will find closest point on the line to point

    You can use number of points and lines as many as you wish
    """
    bl_idname = 'SvCustomSwitcher'
    bl_label = 'Switcher'
    bl_icon = 'HAND'

    def draw_items_test1(self, context):
        if self.inputs['Data'].is_linked:
            data = self.inputs['Data'].sv_get()
            counter = 0
            out = []
            if isinstance(data[0], (list, tuple)):
                data = [i for l in data for i in l]
            #return [(str(i), str(i), '') for i in range(len(data)) if i < 32]
            return [(str(i), str(val), '') for i, val in enumerate(data) if i < 32]
            #for val in data:
            #    if counter == 31:
            #        break
            #    if hasattr(val, 'name'):
            #        val = val.name
            #    if isinstance(val, str):
            #        out.append(('{}'.format(counter), '{}'.format(val), ''))
            #    counter += 1
            #return out
        else:
            return [('1', 'link something', '')]

    def draw_items(self, context):
        if self.string_values:
            return [(str(i), s.name, '') for i, s in enumerate(self.string_values)]
        else:
            return [('1', 'link something', '')]

    string_values = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    user_list = bpy.props.EnumProperty(name='Custom list', items=draw_items, update=updateNode,  options={'ENUM_FLAG'})
    show_in_3d = bpy.props.BoolProperty(name='show in panel', default=True,
                                        description='Show properties in 3d panel or not')

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Data')
        self.outputs.new('StringsSocket', 'Item')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "user_list", expand=True)

    def process(self):
        if self.inputs['Data'].is_linked:
            data = self.inputs['Data'].sv_get()
            if isinstance(data[0], (list, tuple)):
                data = [i for l in data for i in l]
            if len(data) != len(self.string_values):
                self.string_values.clear()
                for i, val in enumerate(data):
                    if i == 32:
                        break
                    self.string_values.add().name = str(val)
            else:
                for val, str_val in zip(data, self.string_values):
                    str_val.name = str(val)
        else:
            self.string_values.clear()

        self.outputs['Item'].sv_set([sorted([int(i) for i in self.user_list])])

    def process_test1(self):
        self.outputs['Item'].sv_set([[int(i) for i in self.user_list]])


def register():
    bpy.utils.register_class(SvCustomSwitcher)


def unregister():
    bpy.utils.unregister_class(SvCustomSwitcher)