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

import parser

from bpy.props import StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode, VerticesSocket
from sverchok.data_structure import (updateNode, SvSetSocketAnyType)


class SvGetDataObjectNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Get Object Props '''
    bl_idname = 'SvGetDataObjectNode'
    bl_label = 'get_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("MESH",   "MESH",   "", 1),
        ("CURVE",   "CURVE",   "", 2),
        ("CAMERA",   "CAMERA",   "", 3),
        ("LAMP",   "LAMP",   "", 4),
        ("META",   "METABOL",   "", 5),
        ("EMPTY",   "EMPTY",   "", 6),
        ("FONT",   "FONT",   "", 7),
        ("selected_objects",   "Selected_objects",   "", 8),
        ("active",   "Active",   "", 9),
        ("in_group",   "In_Group",   "", 10),
    ]

    Modes = EnumProperty(name="getmodes", description="Get object modes",
                         default="MESH", items=modes, update=updateNode)

    group_name = StringProperty(
        default='',
        description='group of objects',
        update=updateNode)

    def draw_buttons(self, context, layout):

        row = layout.row(align=True)
        layout.prop(self, "Modes", "Get object modes")

        col = layout.column()
        if self.Modes == "in_group":
            col.prop_search(self, 'group_name', bpy.data, 'groups', text='', icon='HAND')

    def sv_init(self, context):
        self.outputs.new('VerticesSocket', "Objects", "Objects")

    def process(self):

        SSSAT = SvSetSocketAnyType
        outputs = self.outputs
        Objects = []

        if self.Modes == "in_group":
            if self.group_name in bpy.data.groups:
                for i in bpy.data.groups.get(self.group_name).objects:
                    Objects.append(i)

        elif self.Modes == "selected_objects":
            for i in bpy.context.selected_objects:
                Objects.append(i)

        elif self.Modes == "active":
            Objects.append(bpy.context.active_object)

        else:
            for i in bpy.data.objects:
                if i.type == self.Modes:
                    Objects.append(i)

        if outputs['Objects'].links:
            SSSAT(self, 'Objects', [Objects])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvGetDataObjectNode)


def unregister():
    bpy.utils.unregister_class(SvGetDataObjectNode)
