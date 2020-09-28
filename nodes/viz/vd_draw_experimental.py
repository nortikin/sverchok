# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import pi

import bgl
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.props import (
    StringProperty, BoolProperty, FloatVectorProperty, EnumProperty, FloatProperty, IntProperty)

from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon as tessellate
from numpy import ndarray

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode, enum_item_5, match_long_repeat
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_shader_sources import dashed_vertex_shader, dashed_fragment_shader
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.geom import multiply_vectors_deep
from sverchok.utils.modules.geom_utils import obtain_normal3 as normal
from sverchok.utils.context_managers import hard_freeze
from sverchok.utils.sv_mesh_utils import mesh_join


default_vertex_shader = '''
    uniform mat4 viewProjectionMatrix;

    in vec3 position;
    out vec3 pos;

    void main()
    {
        pos = position;
        gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
    }
'''

default_fragment_shader = '''
    uniform float brightness;

    in vec3 pos;
    out vec4 FragColor;

    void main()
    {
        FragColor = vec4(pos * brightness, 1.0);
    }
'''

def edges_from_faces(indices):
    """ we don't want repeat edges, ever.."""
    out = set()
    concat = out.add
    for face in indices:
        for edge in zip(face, list(face[1:]) + list([face[0]])):
            concat(tuple(sorted(edge)))
    return list(out)


def ensure_triangles(coords, indices, handle_concave_quads):
    """
    this fully tesselates the incoming topology into tris,
    not optimized for meshes that don't contain ngons
    """
    new_indices = []
    concat = new_indices.append
    concat2 = new_indices.extend
    for idxset in indices:
        num_verts = len(idxset)
        if num_verts == 3:
            concat(tuple(idxset))
        elif num_verts == 4 and not handle_concave_quads:
            # a b c d  ->  [a, b, c], [a, c, d]
            concat2([(idxset[0], idxset[1], idxset[2]), (idxset[0], idxset[2], idxset[3])])
        else:
            subcoords = [Vector(coords[idx]) for idx in idxset]
            for pol in tessellate([subcoords]):
                concat([idxset[i] for i in pol])
    return new_indices


def generate_facet_data(verts, faces, face_color, vector_light):
    out_verts = []
    out_vcols = []
    concat_verts = out_verts.extend
    concat_vcols = out_vcols.extend
    for face in faces:
        vecs = [verts[j] for j in face]
        concat_verts(vecs)

        normal_no = Vector(normal(*vecs))
        normal_no = (normal_no.angle(vector_light, 0)) / pi

        r = (normal_no * face_color[0]) - 0.1
        g = (normal_no * face_color[1]) - 0.1
        b = (normal_no * face_color[2]) - 0.1
        vcol = (r+0.2, g+0.2, b+0.2, 1.0)
        concat_vcols([vcol, vcol, vcol])

    return out_verts, out_vcols


def generate_smooth_data(verts, faces, face_color, vector_light):
    """ this piggy backs off bmesh's automated normal calculation... """
    out_vcols = []
    concat_vcols = out_vcols.append

    bm = bmesh_from_pydata(verts, [], faces, normal_update=True)

    for vert in bm.verts:
        normal_no = (vert.normal.angle(vector_light, 0)) / pi
        r = (normal_no * face_color[0]) - 0.1
        g = (normal_no * face_color[1]) - 0.1
        b = (normal_no * face_color[2]) - 0.1
        vcol = (r+0.2, g+0.2, b+0.2, 1.0)
        concat_vcols(vcol)

    return out_vcols


def draw_matrix(context, args):
    """ this takes one or more matrices packed into an iterable """
    mdraw = MatrixDraw28()
    for matrix in args[0]:
        mdraw.draw_matrix(matrix)


def draw_uniform(GL_KIND, coords, indices, color, width=1, dashed_data=None):
    if GL_KIND == 'LINES':
        bgl.glLineWidth(width)
    elif GL_KIND == 'POINTS':
        bgl.glPointSize(width)

    params = dict(indices=indices) if indices else {}

    if GL_KIND == 'LINES' and dashed_data:

        shader = dashed_data.dashed_shader
        batch = batch_for_shader(shader, 'LINES', {"inPos" : coords}, **params)
        shader.bind()
        shader.uniform_float("u_mvp", dashed_data.matrix)
        shader.uniform_float("u_resolution", dashed_data.u_resolution)
        shader.uniform_float("u_dashSize", dashed_data.u_dash_size)
        shader.uniform_float("u_gapSize", dashed_data.u_gap_size)
        shader.uniform_float("m_color", dashed_data.m_color)
        batch.draw(shader)

    else:

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, GL_KIND, {"pos" : coords}, **params)
        shader.bind()
        shader.uniform_float("color", color)

        batch.draw(shader)

    if GL_KIND == 'LINES':
        bgl.glLineWidth(1)
    elif GL_KIND == 'POINTS':
        bgl.glPointSize(1)


def draw_smooth(coords, vcols, indices=None):
    shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
    params = dict(indices=indices) if indices else {}
    batch = batch_for_shader(shader, 'TRIS', {"pos" : coords, "color": vcols}, **params)
    batch.draw(shader)


def draw_verts(context, args):
    geom, config = args
    draw_uniform('POINTS', geom.verts, None, config.vcol, config.point_size)

def pack_dashed_config(config):
    dashed_config = lambda: None
    dashed_config.matrix = config.matrix
    dashed_config.u_resolution = config.u_resolution
    dashed_config.u_dash_size = config.u_dash_size
    dashed_config.u_gap_size = config.u_gap_size
    dashed_config.m_color = config.line4f
    dashed_config.dashed_shader = config.dashed_shader
    return dashed_config

def draw_lines_uniform(context, config, coords, indices, line_color, line_width):
    if config.draw_dashed:
        config.matrix = context.region_data.perspective_matrix
        dashed_config = pack_dashed_config(config)

    params = dict(dashed_data=dashed_config) if config.draw_dashed else {}
    draw_uniform('LINES', coords, indices, config.line4f, config.line_width, **params)

def draw_edges(context, args):
    geom, config = args
    coords, indices = geom.verts, geom.edges

    if config.display_edges:
        draw_lines_uniform(context, config, coords, indices, config.line4f, config.line_width)
    if config.display_verts:
        draw_verts(context, args)

def draw_fragment(context, args):
    geom, config = args
    batch = config.batch
    shader = config.shader

    shader.bind()
    matrix = context.region_data.perspective_matrix
    shader.uniform_float("viewProjectionMatrix", matrix)
    shader.uniform_float("brightness", 0.5)
    batch.draw(shader)

def draw_faces_uniform(context, args):
    geom, config = args

    if config.draw_gl_wireframe:
        bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_LINE)

    if config.draw_gl_polygonoffset:
        bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
        bgl.glPolygonOffset(1.0, 1.0)

    if config.shade == "flat":
        draw_uniform('TRIS', geom.verts, geom.faces, config.face4f)
    elif config.shade == "facet":
        draw_smooth(geom.facet_verts, geom.facet_verts_vcols)
    elif config.shade == "smooth":
        draw_smooth(geom.verts, geom.smooth_vcols, indices=geom.faces)
    elif config.shade == 'fragment':
        if config.draw_fragment_function:
            config.draw_fragment_function(context, args)
        else:
            draw_fragment(context, args)

    if config.draw_gl_wireframe:
        bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_FILL)

def draw_complex(context, args):
    geom, config = args

    if config.draw_gl_polygonoffset:
        bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)

    if config.display_edges:
        draw_lines_uniform(context, config, geom.verts, geom.edges, config.line4f, config.line_width)
    if config.display_faces:
        draw_faces_uniform(context, args)
    if config.display_verts:
        draw_uniform('POINTS', geom.verts, None, config.vcol, config.point_size)

    if config.draw_gl_polygonoffset:
        # or restore to the state found when entering this function. TODO!
        bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)

def get_shader_data(named_shader=None):
    source = bpy.data.texts[named_shader].as_string()
    exec(source)
    local_vars = vars().copy()
    names = ['vertex_shader', 'fragment_shader', 'draw_fragment']
    return [local_vars.get(name) for name in names]

class SvVDExperimental(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: exp vd mk3
    Tooltip: drawing, with experimental features

    not a very exciting node.
    """

    bl_idname = 'SvVDExperimental'
    bl_label = 'Viewer Draw Mk3'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_DRAW_VIEWER'

    node_dict = {}

    def populate_node_with_custom_shader_from_text(self):
        if self.custom_shader_location in bpy.data.texts:
            try:
                vertex_shader, fragment_shader, draw_fragment = get_shader_data(named_shader=self.custom_shader_location)

                self.custom_vertex_shader = vertex_shader
                self.custom_fragment_shader = fragment_shader
                self.node_dict[hash(self)] = {'draw_fragment': draw_fragment}

            except Exception as err:
                print(err)
                print(traceback.format_exc())

                # reset custom shader
                self.custom_vertex_shader = ''
                self.custom_fragment_shader = ''
                self.node_dict[hash(self)] = {}

    def wrapped_update(self, context=None):
        self.populate_node_with_custom_shader_from_text()
        if context:
            self.process_node(context)

    activate: BoolProperty(name='Show', description='Activate', default=True, update=updateNode)

    vert_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.8, 0.8, 0.8, 1.0),
        name='vert color', size=4, update=updateNode)

    edge_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.5, 1.0, 0.5, 1.0),
        name='edge color', size=4, update=updateNode)

    face_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.14, 0.54, 0.81, 1.0),
        name='face color', size=4, update=updateNode)

    vector_light: FloatVectorProperty(
        name='vector light', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4), update=updateNode)

    extended_matrix: BoolProperty(
        default=False,
        description='Allows mesh.transform(matrix) operation, quite fast!')

    handle_concave_quads: BoolProperty(
        name='Handle Concave Quads', default=False, update=updateNode,
        description='tessellate quads using geometry.tessellate_polygon, expect some speed impact')

    # glGet with argument GL_POINT_SIZE_RANGE
    point_size: FloatProperty(description="glPointSize( GLfloat size)", update=updateNode, default=4.0, min=1.0, max=15.0)
    line_width: IntProperty(description="glLineWidth( GLfloat width)", update=updateNode, default=1, min=1, max=5)

    display_verts: BoolProperty(default=True, update=updateNode, name="display verts")
    display_edges: BoolProperty(default=True, update=updateNode, name="display edges")
    display_faces: BoolProperty(default=True, update=updateNode, name="display faces")
    draw_gl_wireframe: BoolProperty(default=False, update=updateNode, name="draw gl wireframe")
    draw_gl_polygonoffset: BoolProperty(default=True, update=updateNode, name="draw gl polygon offset")

    custom_vertex_shader: StringProperty(default=default_vertex_shader, name='vertex shader')
    custom_fragment_shader: StringProperty(default=default_fragment_shader, name='fragment shader')
    custom_shader_location: StringProperty(update=wrapped_update, name='custom shader location')

    selected_draw_mode: EnumProperty(
        items=enum_item_5(["flat", "facet", "smooth", "fragment"], ['SNAP_VOLUME', 'ALIASED', 'ANTIALIASED', 'SCRIPTPLUGINS']),
        description="pick how the node will draw faces",
        default="flat", update=updateNode
    )

    # dashed line props
    use_dashed: BoolProperty(name='use dashes', update=updateNode)
    u_dash_size: FloatProperty(default=0.12, min=0.0001, name="dash size", update=updateNode)
    u_gap_size: FloatProperty(default=0.19, min=0.0001, name="gap size", update=updateNode)
    u_resolution: FloatVectorProperty(default=(25.0, 18.0), size=2, min=0.01, name="resolution", update=updateNode)

    def configureAttrSocket(self, context):
        self.inputs['attrs'].hide_safe = not self.node_ui_show_attrs_socket

    node_ui_show_attrs_socket: BoolProperty(default=False, name='show attrs socket', update=configureAttrSocket)

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', 'verts')
        inew('SvStringsSocket', 'edges')
        inew('SvStringsSocket', 'faces')
        inew('SvMatrixSocket', 'matrix')

        attr_socket = inew('SvStringsSocket', 'attrs')
        attr_socket.hide = True
        attr_socket.quick_link_to_node = "SvVDAttrsNode"

        self.node_dict[hash(self)] = {}

    def draw_buttons(self, context, layout):
        r0 = layout.row()
        r0.prop(self, "activate", text="", icon="HIDE_" + ("OFF" if self.activate else "ON"))
        r0.separator()
        r0.prop(self, "selected_draw_mode", expand=True, text='')

        b1 = layout.column()
        if b1:
            inside_box = b1.row(align=True)
            button_column = inside_box.column(align=True)
            button_column.prop(self, "display_verts", text='', icon="UV_VERTEXSEL")
            button_column.prop(self, "display_edges", text='', icon="UV_EDGESEL")
            button_column.prop(self, "display_faces", text='', icon="UV_FACESEL")

            colors_column = inside_box.column(align=True)
            colors_column.prop(self, "vert_color", text='')
            colors_column.prop(self, "edge_color", text='')
            if not self.selected_draw_mode == 'fragment':
                colors_column.prop(self, "face_color", text='')
            else:
                colors_column.prop(self, "custom_shader_location", icon='TEXT', text='')

        row = layout.row(align=True)
        self.wrapper_tracked_ui_draw_op(row, "node.sverchok_mesh_baker_mk3", icon='OUTLINER_OB_MESH', text="B A K E")
        row.separator()
        self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        self.draw_additional_props(context, layout)
        layout.prop(self, "use_dashed")
        if self.use_dashed:
            layout.prop(self, "u_dash_size")
            layout.prop(self, "u_gap_size")
            layout.row().prop(self, "u_resolution")

    def bake(self):
        with self.sv_throttle_tree_update():
            bpy.ops.node.sverchok_mesh_baker_mk3(
                idname=self.name, idtree=self.id_data.name
            )

    def rclick_menu(self, context, layout):
        self.draw_additional_props(context, layout)

    def draw_additional_props(self, context, layout):
        layout.prop(self, 'vector_light', text='')
        layout.prop(self, 'point_size', text='Point Size')
        layout.prop(self, 'line_width', text='Edge Width')
        layout.separator()
        layout.prop(self, 'handle_concave_quads', toggle=True)
        layout.prop(self, 'draw_gl_wireframe', toggle=True)
        layout.prop(self, 'draw_gl_polygonoffset', toggle=True)
        layout.prop(self, 'node_ui_show_attrs_socket', toggle=True)
        layout.separator()

    def add_gl_stuff_to_config(self, config):
        config.dashed_shader = gpu.types.GPUShader(dashed_vertex_shader, dashed_fragment_shader)

    def fill_config(self):

        config = lambda: None
        config.vector_light = self.vector_light[:]
        config.vcol = self.vert_color[:]
        config.line4f = self.edge_color[:]
        config.face4f = self.face_color[:]
        config.display_verts = self.display_verts
        config.display_edges = self.display_edges
        config.display_faces = self.display_faces
        config.shade = self.selected_draw_mode
        config.draw_gl_wireframe = self.draw_gl_wireframe
        config.draw_gl_polygonoffset = self.draw_gl_polygonoffset
        config.point_size = self.point_size
        config.line_width = self.line_width
        config.extended_matrix = self.extended_matrix
        config.draw_dashed = self.use_dashed
        config.u_dash_size = self.u_dash_size
        config.u_gap_size = self.u_gap_size
        config.u_resolution = self.u_resolution[:]

        return config

    def get_data(self):
        verts_socket, edges_socket, faces_socket, matrix_socket = self.inputs[:4]
        edge_indices = [[]]
        face_indices = [[]]

        propv = verts_socket.sv_get(deepcopy=False, default=[[]])
        coords = propv

        if edges_socket.is_linked:
            prope = edges_socket.sv_get(deepcopy=False, default=[[]])
            edge_indices = prope

        if faces_socket.is_linked:
            propf = faces_socket.sv_get(deepcopy=False, default=[[]])
            face_indices = propf

        if matrix_socket.is_linked:
            m = matrix_socket.sv_get(deepcopy=False, default=[Matrix()])
            verts, matrix = match_long_repeat([propv, m])
            coords = [multiply_vectors_deep(mx, v) for mx, v in zip(matrix, verts)]
        else:
            matrix = [Matrix()]
            verts = coords
        return match_long_repeat([coords, edge_indices, face_indices, verts, matrix])

    def faces_diplay(self, geom, config):

        if self.selected_draw_mode == 'facet' and self.display_faces:
            facet_verts, facet_verts_vcols = generate_facet_data(geom.verts, geom.faces, config.face4f, config.vector_light)
            geom.facet_verts = facet_verts
            geom.facet_verts_vcols = facet_verts_vcols
        elif self.selected_draw_mode == 'smooth' and self.display_faces:
            geom.smooth_vcols = generate_smooth_data(geom.verts, geom.faces, config.face4f, config.vector_light)
        elif self.selected_draw_mode == 'fragment' and self.display_faces:

            config.draw_fragment_function = None

            # double reload, for testing.
            ND = self.node_dict.get(hash(self))
            if not ND:
                if self.custom_shader_location in bpy.data.texts:
                    self.populate_node_with_custom_shader_from_text()
                    ND = self.node_dict.get(hash(self))

            if ND and ND.get('draw_fragment'):
                config.draw_fragment_function = ND.get('draw_fragment')
                config.shader = gpu.types.GPUShader(self.custom_vertex_shader, self.custom_fragment_shader)
            else:
                config.shader = gpu.types.GPUShader(default_vertex_shader, default_fragment_shader)

            config.batch = batch_for_shader(config.shader, 'TRIS', {"position": geom.verts}, indices=geom.faces)

    def handle_attr_socket(self):
        """
        this socket expects input dictionary wrapped. once.

            [  {attr: attr_vale, attr2: attr2_value } ]

        """

        if self.node_ui_show_attrs_socket and not self.inputs['attrs'].hide and self.inputs['attrs'].is_linked:
            socket_acquired_attrs = self.inputs['attrs'].sv_get(default=[{'activate': False}])

            if socket_acquired_attrs:
                try:
                    with hard_freeze(self) as node:
                        for k, new_value in socket_acquired_attrs[0].items():
                            print(f"setattr(node, {k}, {new_value})")
                            setattr(node, k, new_value)
                except Exception as err:
                    print('error inside socket_acquired_attrs: ', err)
                    self.id_data.unfreeze(hard=True)  # ensure this thing is unfrozen

    def format_draw_data(self, func=None, args=None):
        return {
            'tree_name': self.id_data.name[:],
            'custom_function': func,
            'args': args}

    def process(self):

        self.handle_attr_socket()

        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return

        n_id = node_id(self)
        callback_disable(n_id)

        if not any([self.display_verts, self.display_edges, self.display_faces]):
            return

        verts_socket, edges_socket, faces_socket, matrix_socket = self.inputs[:4]

        if verts_socket.is_linked:

            display_faces = self.display_faces and faces_socket.is_linked
            display_edges = self.display_edges and (edges_socket.is_linked or faces_socket.is_linked)

            config = self.fill_config()
            data = self.get_data()
            if len(data[0]) > 1:
                coords, edge_indices, face_indices = mesh_join(data[0], data[1], data[2])
                if not coords:
                    return
            elif len(data[0][0]) > 0:
                coords, edge_indices, face_indices = [d[0].tolist() if type(d[0]) == ndarray else d[0] for d in data[:3]]
            else:
                return
            geom = lambda: None
            geom.verts = coords

            if self.display_verts and not any([display_edges, display_faces]):
                gl_instructions = self.format_draw_data(func=draw_verts, args=(geom, config))
                callback_enable(n_id, gl_instructions)
                return

            if edges_socket.is_linked and not faces_socket.is_linked:
                if self.use_dashed:
                    self.add_gl_stuff_to_config(config)

                geom.edges = edge_indices
                gl_instructions = self.format_draw_data(func=draw_edges, args=(geom, config))
                callback_enable(n_id, gl_instructions)
                return

            if faces_socket.is_linked:

                #  expecting mixed bag of tris/quads/ngons
                if self.display_faces:
                    geom.faces = ensure_triangles(coords, face_indices, self.handle_concave_quads)

                if self.display_edges:
                    if self.use_dashed:
                        self.add_gl_stuff_to_config(config)

                    # we don't want to draw the inner edges of triangulated faces; use original face_indices.
                    # pass edges from socket if we can, else we manually compute them from faces
                    geom.edges = edge_indices if edges_socket.is_linked else edges_from_faces(face_indices)

                if self.display_faces:
                    self.faces_diplay(geom, config)

                gl_instructions = self.format_draw_data(func=draw_complex, args=(geom, config))
                callback_enable(n_id, gl_instructions)
                return

            return

        elif matrix_socket.is_linked:
            matrices = matrix_socket.sv_get(deepcopy=False, default=[Matrix()])
            gl_instructions = self.format_draw_data(func=draw_matrix, args=(matrices, ))
            callback_enable(n_id, gl_instructions)

    def sv_copy(self, node):
        self.n_id = ''

    @property
    def fully_enabled(self):
        return "attrs" in self.inputs

    def sv_update(self):
        if not self.fully_enabled:
            return

        try:
            socket_one_has_upstream_links = self.inputs[0].other
            socket_two_has_upstream_links = self.inputs[1].other

            if not socket_one_has_upstream_links:
                callback_disable(node_id(self))
        except:
            self.debug(f'vd draw update holdout {self.n_id}')

    def sv_free(self):
        callback_disable(node_id(self))

    def show_viewport(self, is_show: bool):
        """It should be called by node tree to show/hide objects"""
        if not self.activate:
            # just ignore request
            pass
        else:
            if is_show:
                self.process()
            else:
                callback_disable(node_id(self))


classes = [SvVDExperimental]
register, unregister = bpy.utils.register_classes_factory(classes)
