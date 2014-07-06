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
from bpy.props import StringProperty, EnumProperty

from node_tree import SverchCustomTreeNode
from data_structure import updateNode, SvSetSocketAnyType


class svPlaneInputNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Generator for XY, XZ, and YZ Planes.

    This gives convenience in node view to make clear even in a minimized
    state which plane the node outputs. Especially useful for rotation input.

    outputs the vectors:
        XY: [0,0,1]
        XZ: [0,1,0]
        YZ: [1,0,0]
    '''

    bl_idname = 'svPlaneInputNode'
    bl_label = 'Plane input'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def mode_change(self, context):
        if not (self.selected_plane == self.current_plane):
            self.label = self.selected_plane
            self.current_plane = self.selected_plane
            updateNode(self, context)

    plane_options = [
        ("XY", "XY", "", 0),
        ("XZ", "XZ", "", 1),
        ("YZ", "YZ", "", 2)
    ]
    current_plane = StringProperty(default='XY')

    selected_plane = EnumProperty(
        items=plane_options,
        name="Type of plane",
        description="offers basic plane output vectors XY XZ YZ",
        default="XY",
        update=mode_change)

    def init(self, context):
        self.width = 100
        self.outputs.new('VerticesSocket', "Vectors", "Vectors")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'selected_plane', expand=True)

    def update(self):

        # outputs
        if 'Vectors' in self.outputs and self.outputs['Vectors'].links:

            planar_vector = {
                'XY': (0, 0, 1),
                'XZ': (0, 1, 0),
                'YZ': (1, 0, 0)
            }.get(self.current_plane, None)

            SvSetSocketAnyType(self, 'Vectors', [[planar_vector]])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(svPlaneInputNode)


def unregister():
    bpy.utils.unregister_class(svPlaneInputNode)
