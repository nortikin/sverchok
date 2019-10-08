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
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.utils.sv_shader_sources import dashed_vertex_shader, dashed_fragment_shader, screen_v3dBGL_dashed

vertex_shader = '''
    uniform mat4 u_ViewProjectionMatrix;

    in vec3 pos;
    in float arcLength;

    out float v_ArcLength;

    void main()
    {
        v_ArcLength = arcLength;
        gl_Position = u_ViewProjectionMatrix * vec4(pos, 1.0f);
    }
'''

fragment_shader = '''
    uniform float u_Scale;
    uniform vec4 m_color;

    in float v_ArcLength;

    void main()
    {
        if (step(sin(v_ArcLength * u_Scale), 0.5) == 1) discard;
        gl_FragColor = m_color;
    }
'''


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
    w_scale = args[3]

    # bgl.glLineWidth(3)
    matrix = context.region_data.perspective_matrix
    shader.bind()
    shader.uniform_float("m_color", line4f)
    shader.uniform_float("u_ViewProjectionMatrix", matrix)
    shader.uniform_float("u_Scale", w_scale)    
    batch.draw(shader)
    # bgl.glLineWidth(1)


class SvVDBasicDashedLines(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: basic dashed lines
    Tooltip: Basic GL Dashed line drawing
    
    not a very exciting node kids.
    """

    bl_idname = 'SvVDBasicDashedLines'
    bl_label = 'Basic DashLine viewer'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_LINE_VIEWER'

    n_id: StringProperty(default='')
    activate: BoolProperty(name='Show', description='Activate', default=True, update=updateNode)

    edge_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1,
        default=(0.3, 0.3, 0.3, 1.0), name='edge color', size=4, update=updateNode)

    world_scale: FloatProperty(default=1.0, min=0.0001, name="world scale", update=updateNode)
    u_dash_size: FloatProperty(default=0.03, min=0.0001, name="dash size", update=updateNode)
    u_gap_size: FloatProperty(default=0.18, min=0.0001, name="gap size", update=updateNode)

    mode_options = [(k, k, '', i) for i, k in enumerate(["dev", "default"])]
    selected_gl_mode: EnumProperty(
        items=mode_options, description="offers....", default="dev", update=updateNode)

    u_resolution: FloatVectorProperty(default=(25.0, 18.0), size=2, min=0.01, name="resolution", update=updateNode)

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
        
        col = layout.column()
        row = col.row()
        row.prop(self, "selected_gl_mode", expand=True)

        if self.selected_gl_mode == 'dev':
            row = col.row()
            row.prop(self, "u_dash_size"); row.prop(self, "u_gap_size")
            row = col.row()
            row.prop(self, "u_resolution", text='')

        else:
            col.prop(self, "world_scale")

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
            # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')


            if self.selected_gl_mode == 'default':
    
                arc_lengths = []
                for v in coords:
                    dist = Vector(v).length
                    arc_lengths.append(dist)

                shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
                shade_data_dict = {"pos" : coords, "arcLength": arc_lengths}
                batch = batch_for_shader(shader, 'LINES', shade_data_dict, indices=indices)

                line4f = self.edge_color[:]
                w_scale = self.world_scale

                draw_data = {
                    'tree_name': self.id_data.name[:],
                    'custom_function': screen_v3dBGL,
                    'args': (shader, batch, line4f, w_scale)
                }            

                callback_enable(n_id, draw_data)

            elif self.selected_gl_mode == 'dev':
    
                shader = gpu.types.GPUShader(dashed_vertex_shader, dashed_fragment_shader)
                shade_data_dict = {"inPos" : coords}
                batch = batch_for_shader(shader, 'LINES', shade_data_dict, indices=indices)

                args = lambda: None
                args.shader = shader
                args.batch = batch
                args.line4f = self.edge_color[:]
                args.u_dash_size = self.u_dash_size
                args.u_gap_size = self.u_gap_size
                args.u_resolution = self.u_resolution[:]

                draw_data = {
                    'tree_name': self.id_data.name[:],
                    'custom_function': screen_v3dBGL_dashed,
                    'args': args
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
    bpy.utils.register_class(SvVDBasicDashedLines)


def unregister():
    bpy.utils.unregister_class(SvVDBasicDashedLines)
