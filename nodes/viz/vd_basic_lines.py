# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bgl
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

# import mathutils
from mathutils import Vector, Matrix
import sverchok
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28


def screen_v3dMatrix(context, args):
    mdraw = MatrixDraw28()
    for matrix in args[0]:
        mdraw.draw_matrix(matrix)

def screen_v3dBGL(context, args):
    # region = context.region
    # region3d = context.space_data.region_3d
    
    shader = args[0]
    batch = args[1]
    line4f = args[2]

    # bgl.glLineWidth(3)
    shader.bind()
    shader.uniform_float("color", line4f)
    batch.draw(shader)
    # bgl.glLineWidth(1)



class SvVDBasicLines(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: basic lines
    Tooltip: Basic GL line drawing
    
    not a very exciting node kids.
    """

    bl_idname = 'SvVDBasicLines'
    bl_label = 'Basic Line viewer'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_LINE_VIEWER'

    n_id: StringProperty(default='')
    activate: BoolProperty(name='Show', description='Activate', default=True, update=updateNode)

    edge_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1,
        default=(0.3, 0.3, 0.3, 1.0), name='edge color', size=4, update=updateNode)

    @property
    def fully_enabled(self):
        return "edges" in self.inputs

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', 'verts')
        inew('SvStringsSocket', 'edges')
        inew('SvMatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        layout.row().prop(self, "activate", text="ACTIVATE")
        r1 = layout.row(align=True)
        r1.label(icon="UV_EDGESEL")
        r1.prop(self, "edge_color", text='')

    def process(self):
        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return

        n_id = node_id(self)
        callback_disable(n_id)

        verts_socket, edges_socket = self.inputs[:2]

        if verts_socket.is_linked and edges_socket.is_linked:

            propv = verts_socket.sv_get(deepcopy=False, default=[])
            prope = edges_socket.sv_get(deepcopy=False, default=[])
      
            coords = propv[0]
            indices = prope[0]
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINES', {"pos" : coords}, indices=indices)

            line4f = self.edge_color[:]

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3dBGL,
                'args': (shader, batch, line4f)
            }            

            callback_enable(n_id, draw_data)
            return

        matrix_socket = self.inputs['matrix']
        if matrix_socket.is_linked:
            matrices = matrix_socket.sv_get(deepcopy=False, default=[Matrix()])

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3dMatrix,
                'args': (matrices,)
            }            

            callback_enable(n_id, draw_data)

    def copy(self, node):
        super().copy(node)
        self.n_id = ''

    def update(self):
        if not self.fully_enabled:
            return

        try:
            if not (self.inputs[0].other or self.inputs[1].other):
                callback_disable(node_id(self))
        except:
            print('vd basic lines update holdout', self.n_id)


def register():
    bpy.utils.register_class(SvVDBasicLines)


def unregister():
    bpy.utils.unregister_class(SvVDBasicLines)
