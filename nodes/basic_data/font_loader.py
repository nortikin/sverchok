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
from bpy.props import StringProperty, FloatVectorProperty

from node_tree import SverchCustomTreeNode
from data_structure import updateNode


class svFontImporterOp(bpy.types.Operator):

    bl_idname = "fonts.font_importer"
    bl_label = "sv Font Importer Operator"

    filepath = StringProperty(
        name="File Path",
        description="Filepath used for importing the font file",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob = StringProperty(default="*.ttf", options={'HIDDEN'})

    def execute(self, context):
        bpy.data.fonts.load(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class svFontLoader(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'svFontLoader'
    bl_label = 'sv Font Loader'
    bl_icon = 'OUTLINER_OB_EMPTY'

    fe_vec = FloatVectorProperty(
        name='fe_vec', size=3, default=(0.4, 0.4, 0.4), subtype='DIRECTION')

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator('fonts.font_importer', text='load font')
        row.template_curve_mapping([0,1,2,3,4,5], 'fe_vec', type='VECTOR')

    def update(self):
        pass

    #def update_socket(self, context):
    #    pass


def register():
    bpy.utils.register_class(svFontLoader)
    bpy.utils.register_class(svFontImporterOp)


def unregister():
    bpy.utils.unregister_class(svFontLoader)
    bpy.utils.unregister_class(svFontImporterOp)
