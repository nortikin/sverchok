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


class SvCopySelectionFromObject(bpy.types.Operator):

    bl_idname = "node.copy_selection_from_object"
    bl_label = "Copy selection"

    def execute(self, context):
        return {'FINISHED'}


class SvSelectionGraber(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: name
    tip

    tip
    """
    bl_idname = 'SvSelectionGraber'
    bl_label = 'Selection Graber'
    bl_icon = 'FACESEL'

    def sv_init(self, context):
        self.outputs.new('StringsSocket', 'Vertex mask')
        self.outputs.new('StringsSocket', 'Edge mask')
        self.outputs.new('StringsSocket', 'Face mask')

    def draw_buttons(self, context, layout):
        layout.operator('node.copy_selection_from_object', text='Get from selected', icon='EYEDROPPER')


classes = [SvCopySelectionFromObject, SvSelectionGraber]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes[::-1]]