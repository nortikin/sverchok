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
from bpy.props import EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e)


class SvGetAssetProperties(bpy.types.Node, SverchCustomTreeNode):
    ''' Get Asset Props '''
    bl_idname = 'SvGetAssetProperties'
    bl_label = 'Asset / Properties'
    bl_icon = 'OUTLINER_OB_EMPTY'

    M = ['actions','brushes','filepath','grease_pencil','groups',
         'images','libraries','linestyles','masks','materials',
         'movieclips','node_groups','particles','scenes','screens','shape_keys',
         'sounds','speakers','texts','textures','worlds','objects']
    T = ['MESH','CURVE','SURFACE','META','FONT','ARMATURE','LATTICE','EMPTY','CAMERA','LAMP','SPEAKER']

    Mode = EnumProperty(name="getmodes", default="objects", items=e(M), update=updateNode)
    Type = EnumProperty(name="getmodes", default="MESH", items=e(T), update=updateNode)
    text_file_name = bpy.props.StringProperty(update=updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        layout.prop(self, "Mode", "mode")
        if self.Mode == 'objects':
            layout.prop(self, "Type", "type")
        elif self.Mode == 'texts':
            layout.prop_search(bpy.data, 'texts', self, 'text_file_name')

    def sv_init(self, context):
        self.outputs.new('StringsSocket', "Objects")

    def process(self):
        output_socket = self.outputs['Objects']

        if not output_socket.is_linked:
            return
        unfiltered_data_list = getattr(bpy.data, self.Mode)
        if self.Mode != 'objects':
            output_socket.sv_set(unfiltered_data_list[:])
        else:
            output_socket.sv_set([i for i in L if i.type == self.Type])


def register():
    bpy.utils.register_class(SvGetAssetProperties)


def unregister():
    bpy.utils.unregister_class(SvGetAssetProperties)
