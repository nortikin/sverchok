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

# class SvGenericCallbackWithParams() mixin  <- refresh


class SvGetAssetProperties(bpy.types.Node, SverchCustomTreeNode):
    ''' Get Asset Props '''
    bl_idname = 'SvGetAssetProperties'
    bl_label = 'Asset / Properties'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def pre_updateNode(self, context):
        ''' must rebuild for each update'''
        self.type_collection_name.clear()
        for o in bpy.data.objects:
            if o.type == self.Type:
                self.type_collection_name.add().name = o.name

        updateNode(self, context)

    type_collection_name = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)    

    M = ['actions', 'brushes', 'filepath', 'grease_pencil', 'groups',
         'images', 'libraries', 'linestyles', 'masks', 'materials',
         'movieclips', 'node_groups', 'particles', 'scenes', 'screens', 'shape_keys',
         'sounds', 'speakers', 'texts', 'textures', 'worlds', 'objects']
    T = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE',
         'LATTICE', 'EMPTY', 'CAMERA', 'LAMP', 'SPEAKER']

    Mode = EnumProperty(name="getmodes", default="objects", items=e(M), update=updateNode)
    Type = EnumProperty(name="getmodes", default="MESH", items=e(T), update=pre_updateNode)
    text_name = bpy.props.StringProperty(update=updateNode)
    object_name = bpy.props.StringProperty(update=updateNode)

    def draw_buttons(self, context, layout):
        # layout.operator('node.'   ,text='refresh from scene')

        row = layout.row()
        split = row.split(percentage=0.4)
        split.label("bpy.data.")
        split = split.split()
        split.prop(self, "Mode", text="")

        if self.Mode == 'objects':
            layout.prop(self, "Type", "type")
            layout.prop_search(self, 'object_name', self, 'type_collection_name', text='name', icon='OBJECT_DATA')
        elif self.Mode == 'texts':
            layout.prop_search(self, 'text_name', bpy.data, 'texts', text='name')
        elif self.Mode == 'images':
            layout.prop_search(self, 'image_name', bpy.data, 'images', text='name')


    def sv_init(self, context):
        self.Type = 'MESH'  # helps init the custom object prop_search
        self.outputs.new('StringsSocket', "Objects")

    def process(self):
        output_socket = self.outputs['Objects']
        if not output_socket.is_linked:
            return

        unfiltered_data_list = getattr(bpy.data, self.Mode)

        if self.Mode == 'objects':
            if self.object_name:
                output_socket.sv_set([bpy.data.objects[self.object_name]])
            else:
                output_socket.sv_set([i for i in unfiltered_data_list if i.type == self.Type])
        
        elif self.Mode == 'texts':
            if self.text_name:
                output_socket.sv_set([[bpy.data.texts[self.text_name].as_string()]])
            else:
                output_socket.sv_set(unfiltered_data_list[:])
        elif self.Mode == 'images':
            if self.image_name:
                output_socket.sv_set([[bpy.data.images[self.image_name].pixels[:]]])
                # output_socket.sv_set([[bpy.data.images[self.image_name].pixels[:]]])
            else:
                output_socket.sv_set(unfiltered_data_list[:])

        else:
            output_socket.sv_set(unfiltered_data_list[:])



def register():
    bpy.utils.register_class(SvGetAssetProperties)


def unregister():
    bpy.utils.unregister_class(SvGetAssetProperties)
