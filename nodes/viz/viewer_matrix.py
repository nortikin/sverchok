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


import bgl
import bpy

from sverchok.data_structure import node_id
from sverchok.ui import bgl_callback_3dview as v3dBGL
from sverchok.utils.sv_bgl_primitives import MatrixDraw

from bpy.props import FloatVectorProperty, IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.socket_conversions import is_matrix


def screen_v3dBGL(context, args):
    region = context.region
    region3d = context.space_data.region_3d
    
    matrices = args[0]
    colors = args[1]
    for m, col in zip(matrices, colors):
        mdraw = MatrixDraw()
        mdraw.draw_matrix(m, col)
    
    bgl.glDisable(bgl.GL_POINT_SMOOTH)
    bgl.glDisable(bgl.GL_POINTS)


def match_color_to_matrix(node):
    data = node.inputs['Matrix'].sv_get()

    if len(data) > 0:
        if is_matrix(data[0]):
            # this list likely stores [matrix, matrix, matrix, ..]
            for matrix in data:
                ...
        elif is_matrix(data[0][0]):
            # 1. this list likely stores [[matrix, matrix, matrix],[matrix, matrix, matrix],..]
            # 2. or stores [[matrix],[matrix],..]

            # 1.
            for matrix_list in data:
                for matrix in matrix_list:
                    ...
            
            # 2.
            # if each element in data is len 1

            



    vcol_start = Vector(node.color_start)
    vcol_end = Vector(node.color_end)


class SvMatrixViewer(bpy.types.Node, SverchCustomTreeNode):
    ''' View multi Matrices '''
    bl_idname = 'SvMatrixViewer'
    bl_label = 'Matrix View'

    color_start = FloatVectorProperty(subtype='COLOR', min=0, max=1, size=3, update=updateNode)
    color_end = FloatVectorProperty(subtype='COLOR', default=(1,1,1), min=0, max=1, size=3, update=updateNode)
    node_id = IntProperty()

    def sv_init(self, context):
        self.inputs.new('MatrixSocket', 'Matrix')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'color_start')
        row.prop(self, 'color_end')

    def process(self):
        self.n_id = node_id(self)
        v3dBGL.callback_disable(self.n_id)

        if self.inputs['Matrix'].is_linked:
            in_matrices, matrix_colors = match_color_to_matrix(self)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3dBGL,
                'args': (in_matrices, matrix_colors)
            }

            v3dBGL.callback_enable(self.n_id, draw_data, overlay='POST_VIEW')


def register():
    bpy.utils.register_class(option1)


def unregister():
    bpy.utils.unregister_class(option1)




