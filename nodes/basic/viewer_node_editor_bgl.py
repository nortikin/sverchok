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
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty

from node_tree import SverchCustomTreeNode, MatrixSocket, VerticesSocket, StringsSocket
from data_structure import dataCorrect, node_id, updateNode, SvGetSocketAnyType
from utils import nodeview_bgl_viewer_draw as nvBGL
from mathutils import Vector

# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)


class BGL_demo_Node(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'BGLdemoNode'
    bl_label = 'BGL demo Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # node id
    n_id = StringProperty(default='', options={'SKIP_SAVE'})

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Show")

    def process_input(self, socket_data, socket_type):
        if socket_type == 'verts':
            # requires pprint processing step here? or in the node
            # .. probably here.
            return {
                'content': socket_data,
                'location': (self.location + Vector((self.width+20, 0)))[:]
            }

        elif socket_type == 'lists':
            pass

        else:  # 'matrices'
            pass

    def update(self):
        inputs = self.inputs
        n_id = node_id(self)

        # end early
        nvBGL.callback_disable(n_id)
        if not all([inputs[0], self.id_data.sv_show]):
            return

        in_links = inputs[0].links

        self.use_custom_color = True
        if self.activate and in_links:

            # gather vertices from input
            m = -1
            for i, Socket in enumerate([VerticesSocket, StringsSocket, MatrixSocket]):
                if isinstance(in_links[0].from_socket, Socket):
                    m = i
                    break

            socket_type = ['verts', 'lists', 'matrices', None][m]
            if not socket_type:
                return

            raw_data = SvGetSocketAnyType(self, inputs[0])
            socket_data = dataCorrect(raw_data)

            draw_data = self.process_input(socket_data, socket_type)
            nvBGL.callback_enable(n_id, draw_data)
            self.color = READY_COLOR
        else:
            self.color = FAIL_COLOR

    def update_socket(self, context):
        self.update()

    def free(self):
        nvBGL.callback_disable(node_id(self))


def register():
    bpy.utils.register_class(BGL_demo_Node)


def unregister():
    bpy.utils.unregister_class(BGL_demo_Node)
