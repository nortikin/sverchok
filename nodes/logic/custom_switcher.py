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


test = [('1', 'Box', ''),
        ('2', 'Circle', ''),
        ('3', 'Plane', '')]


class SvCustomSwitcher(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: project point to line
    If there are point and line the node will find closest point on the line to point

    You can use number of points and lines as many as you wish
    """
    bl_idname = 'SvCustomSwitcher'
    bl_label = 'Switcher'
    bl_icon = 'HAND'

    user_list = bpy.props.EnumProperty(name='Custom list', items=test, update=updateNode)

    def sv_init(self, context):
        self.outputs.new('StringsSocket', 'Item')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "user_list", expand=True)

    def process(self):
        self.outputs['Item'].sv_set([[int(self.user_list) - 1]])


def register():
    bpy.utils.register_class(SvCustomSwitcher)


def unregister():
    bpy.utils.unregister_class(SvCustomSwitcher)