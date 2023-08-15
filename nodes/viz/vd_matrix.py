# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE



import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector, Color
from bpy.props import FloatVectorProperty, StringProperty, BoolProperty, FloatProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d

from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.data_structure import node_id, updateNode
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.modules.drawing_abstractions import drawing

if not bpy.app.background:
    shader_name = f'{"2D_" if bpy.app.version < (3, 4) else ""}SMOOTH_COLOR'
    smooth_2d_shader = gpu.shader.from_builtin(shader_name)
else:
    smooth_2d_shader = None

def screen_v3d_batch_matrix(context, args):
    cdat, simple, plane, grid = args
    for matrix, color in cdat:
        mdraw = MatrixDraw28()
        mdraw.draw_matrix(matrix, skip=simple, grid=grid)

def screen_v3d_batch_matrix_overlay(context, args):
    region = context.region
    region3d = context.space_data.region_3d
    cdat, alpha = args[0], args[1]
    if not alpha > 0.0:
        return

    pt = 0.5
    G = -0.001  # to z offset the plane from the axis
    coords = (-pt, pt, G), (pt, pt, G), (pt ,-pt, G), (-pt,-pt, G)
    indices_plane = [(0, 1, 2), (0, 2, 3)]

    # first calculate positions and lerp colors
    coords_transformed = []
    indices_shifted = []
    idx_offset = 0
    colors = []
    for i, (matrix, color) in enumerate(cdat):
        r, g, b = color
        for x, y, z in coords:
            vector3d = matrix @ Vector((x, y, z))
            vector2d = loc3d2d(region, region3d, vector3d)
            coords_transformed.append(vector2d)
            colors.append((r, g, b, alpha))

        for indices in indices_plane:
            indices_shifted.append(tuple(idx+idx_offset for idx in indices))

        idx_offset += 4

    batch = batch_for_shader(
        smooth_2d_shader, 'TRIS', {"pos" : coords_transformed, "color": colors},
        indices=indices_shifted)

    # smooth_2d_shader.bind()
    drawing.enable_blendmode()
    batch.draw(smooth_2d_shader)
    drawing.disable_blendmode()


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


class SvMatrixViewer28(SverchCustomTreeNode, bpy.types.Node):
    '''A quick way to represent matrices.
    In: Matrixes
    Params: Color start/end, simple On/Off, grid On/Off, plane On/Off, Alpha 0.0-1.0
    '''
    bl_idname = 'SvMatrixViewer28'
    bl_label = 'Matrix View'
    bl_icon = 'EMPTY_AXIS'
    sv_icon = 'SV_MATRIX_VIEWER'


    color_start: FloatVectorProperty(subtype='COLOR', default=(1, 1, 1), min=0, max=1, size=3, update=updateNode)
    color_end: FloatVectorProperty(subtype='COLOR', default=(1, 0.02, 0.02), min=0, max=1, size=3, update=updateNode)
    n_id: StringProperty()

    simple: BoolProperty(name='simple', update=updateNode, default=True)
    grid: BoolProperty(name='grid', update=updateNode, default=True)
    plane: BoolProperty(name='plane', update=updateNode, default=True)
    alpha: FloatProperty(name='alpha', update=updateNode, min=0.0, max=1.0, subtype='FACTOR', default=0.13)
    show_options: BoolProperty(name='options', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', 'Matrix')

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
        self.sv_free()

        if self.inputs['Matrix'].is_linked:
            cdat = match_color_to_matrix(self)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3d_batch_matrix,
                'args': (cdat, self.simple, self.plane, self.grid)
            }

            draw_data_2d = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3d_batch_matrix_overlay,
                'args': (cdat, self.alpha)
            }

            callback_enable(self.n_id, draw_data, overlay='POST_VIEW')
            callback_enable(self.n_id+'__2D', draw_data_2d, overlay='POST_PIXEL')

    def sv_free(self):
        callback_disable(node_id(self))
        callback_disable(node_id(self) + '__2D')

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''

    def sv_update(self):
        if not ("Matrix" in self.inputs):
            return
        if not self.inputs[0].other:
            self.sv_free()


def register():
    bpy.utils.register_class(SvMatrixViewer28)


def unregister():
    bpy.utils.unregister_class(SvMatrixViewer28)
