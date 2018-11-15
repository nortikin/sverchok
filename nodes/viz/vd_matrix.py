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
from mathutils import Matrix, Vector, Color
from bpy.props import FloatVectorProperty, StringProperty, BoolProperty, FloatProperty
# from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d


from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.data_structure import node_id, updateNode
from sverchok.node_tree import SverchCustomTreeNode


def screen_v3dBGL_matrix(context, args):
    # region = context.region
    # region3d = context.space_data.region_3d
    cdat, simple, plane, grid, alpha = args
    for matrix, color in args[0]:
        mdraw = MatrixDraw28()
        show_plate = (color[0], color[1], color[2], alpha)  if alpha > 0.0  else False
        mdraw.draw_matrix(matrix, color, skip=simple, grid=grid, show_plate=show_plate)


def match_color_to_matrix(node):
    vcol_start = Vector(node.color_start)
    vcol_end = Vector(node.color_end)

    def element_iterated(matrix, theta, index):
        return matrix, Color(vcol_start.lerp(vcol_end, index*theta))[:]

    data = node.inputs['Matrix'].sv_get()
    data_out = []
    get_mat_theta_idx = data_out.append

    if len(data) > 0:
        theta = 1 / len(data)
        for idx, matrix in enumerate(data):
            get_mat_theta_idx([matrix, theta, idx])

    return [element_iterated(*values) for values in data_out]


class SvMatrixViewer28(bpy.types.Node, SverchCustomTreeNode):
    ''' mv - View Matrices '''
    bl_idname = 'SvMatrixViewer28'
    bl_label = 'Matrix View'

    color_start = FloatVectorProperty(subtype='COLOR', default=(1, 1, 1), min=0, max=1, size=3, update=updateNode)
    color_end = FloatVectorProperty(subtype='COLOR', default=(1, 0.02, 0.02), min=0, max=1, size=3, update=updateNode)
    n_id = StringProperty()

    simple = BoolProperty(name='simple', update=updateNode, default=True)
    grid = BoolProperty(name='grid', update=updateNode, default=True)
    plane = BoolProperty(name='plane', update=updateNode, default=True)
    alpha = FloatProperty(name='alpha', update=updateNode, min=0.0, max=1.0, subtype='FACTOR', default=0.13)
    show_options = BoolProperty(name='options', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('MatrixSocket', 'Matrix')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'color_start', text='')
        row.prop(self, 'color_end', text='')
        row.prop(self, 'show_options', text='', icon='SETTINGS')
        if self.show_options:
            row = col.row(align=True)
            row.prop(self, 'simple', toggle=True)
            row.prop(self, 'grid', toggle=True)
            row.prop(self, 'plane', toggle=True)
            row = col.row(align=True)
            row.prop(self, 'alpha')

    def process(self):
        self.n_id = node_id(self)
        self.free()

        if self.inputs['Matrix'].is_linked:
            cdat = match_color_to_matrix(self)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3dBGL_matrix,
                'args': (cdat, self.simple, self.plane, self.grid, self.alpha)
            }
            callback_enable(self.n_id, draw_data, overlay='POST_VIEW')


    def free(self):
        callback_disable(node_id(self))

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def update(self):
        if not ("Matrix" in self.inputs):
            return
        if not self.inputs[0].other:
            self.free()


def register():
    bpy.utils.register_class(SvMatrixViewer28)


def unregister():
    bpy.utils.unregister_class(SvMatrixViewer28)