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

from itertools import cycle
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon as tessellate, normal
from mathutils.noise import random, seed_set
import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, EnumProperty, BoolProperty, FloatVectorProperty

import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import sverchok
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_mesh_utils import polygons_to_edges
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, node_id, match_long_repeat, enum_item_5
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.utils.sv_shader_sources import dashed_vertex_shader, dashed_fragment_shader
from sverchok.utils.context_managers import hard_freeze
from sverchok.utils.geom import multiply_vectors_deep


socket_dict = {
    'vector_color': ('display_verts', 'UV_VERTEXSEL', 'color_per_point', 'vector_random_colors', 'random_seed'),
    'edge_color': ('display_edges', 'UV_EDGESEL', 'color_per_edge', 'edges_use_vertex_color'),
    'polygon_color': ('display_faces', 'UV_FACESEL', 'color_per_polygon', 'polygon_use_vertex_color'),
    }

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

def ensure_triangles(coords, indices, handle_concave_quads):
    """
    this fully tesselates the incoming topology into tris,
    not optimized for meshes that don't contain ngons
    """
    new_indices = []
    face_index = []
    concat = new_indices.append
    concat2 = new_indices.extend
    for idf, idxset in enumerate(indices):
        num_verts = len(idxset)
        if num_verts == 3:
            concat(tuple(idxset))
            face_index.append(idf)
        elif num_verts == 4 and not handle_concave_quads:
            # a b c d  ->  [a, b, c], [a, c, d]
            concat2([(idxset[0], idxset[1], idxset[2]), (idxset[0], idxset[2], idxset[3])])
            face_index.extend([idf, idf])
        else:
            subcoords = [Vector(coords[idx]) for idx in idxset]
            for pol in tessellate([subcoords]):
                concat([idxset[i] for i in pol])
                face_index.append(idf)
    return new_indices, face_index


def fill_points_colors(vectors_color, data, color_per_point, random_colors):
    points_color = []
    if color_per_point:
        for cols, sub_data in zip(cycle(vectors_color), data):
            if random_colors:
                for  n in sub_data:
                    points_color.append([random(), random(), random(), 1])
            else:
                for col, n in zip(cycle(cols), sub_data):
                    points_color.append(col)

    else:
        for nums, col in zip(data, cycle(vectors_color[0])):
            if random_colors:
                r_color = [random(), random(), random(), 1]
                for n in nums:
                    points_color.append(r_color)
            else:
                for n in nums:
                    points_color.append(col)

    return points_color

def draw_matrix(context, args):
    """ this takes one or more matrices packed into an iterable """
    matrices, scale = args

    mdraw = MatrixDraw28()
    for matrix in matrices:
        mdraw.draw_matrix(matrix, scale=scale)

def view_3d_geom(context, args):
    """
    draws the batches
    """

    geom, config = args

    bgl.glEnable(bgl.GL_BLEND)

    if config.draw_polys:
        if config.draw_gl_wireframe:
            bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_LINE)
        if config.draw_gl_polygonoffset:
            bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
            bgl.glPolygonOffset(1.0, 1.0)

        if config.shade_mode == 'fragment':
            p_batch = batch_for_shader(config.p_shader, 'TRIS', {"position": geom.p_vertices}, indices=geom.p_indices)
            config.p_shader.bind()
            matrix = context.region_data.perspective_matrix
            config.p_shader.uniform_float("viewProjectionMatrix", matrix)
            config.p_shader.uniform_float("brightness", 0.5)
        else:
            p_batch = batch_for_shader(config.p_shader, 'TRIS', {"pos": geom.p_vertices, "color": geom.p_vertex_colors}, indices=geom.p_indices)
            config.p_shader.bind()

        p_batch.draw(config.p_shader)

        if config.draw_gl_polygonoffset:
            bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)
        if config.draw_gl_wireframe:
            bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_FILL)


    if config.draw_edges:
        bgl.glLineWidth(config.line_width)

        if config.draw_dashed:
            shader = config.dashed_shader
            batch = batch_for_shader(shader, 'LINES', {"inPos" : geom.e_vertices}, indices=geom.e_indices)
            shader.bind()
            matrix = context.region_data.perspective_matrix
            shader.uniform_float("u_mvp", matrix)
            shader.uniform_float("u_resolution", config.u_resolution)
            shader.uniform_float("u_dashSize", config.u_dash_size)
            shader.uniform_float("u_gapSize", config.u_gap_size)
            shader.uniform_float("m_color", geom.e_vertex_colors[0])
            batch.draw(shader)
        else:
            e_batch = batch_for_shader(config.e_shader, 'LINES', {"pos": geom.e_vertices, "color": geom.e_vertex_colors}, indices=geom.e_indices)
            config.e_shader.bind()
            e_batch.draw(config.e_shader)

        bgl.glLineWidth(1)

    if config.draw_verts:
        bgl.glPointSize(config.point_size)
        v_batch = batch_for_shader(config.v_shader, 'POINTS', {"pos": geom.v_vertices, "color": geom.points_color})
        config.v_shader.bind()

        v_batch.draw(config.v_shader)
        bgl.glPointSize(1)

    bgl.glEnable(bgl.GL_BLEND)


def splitted_polygons_geom(polygon_indices, original_idx, v_path, cols, idx_offset):
    '''geometry of the splitted polygons (splitted to assign colors)'''
    total_p_verts = 0
    p_vertices, vertex_colors, indices = [], [], []

    for pol, idx in zip(polygon_indices, original_idx):
        p_vertices.extend([v_path[c] for c in pol])
        vertex_colors.extend([cols[idx % len(cols)] for c in pol])
        indices.append([c + idx_offset + total_p_verts for c in range(len(pol))])
        total_p_verts += len(pol)

    return p_vertices, vertex_colors, indices, total_p_verts


def splitted_facet_polygons_geom(polygon_indices, original_idx, v_path, cols, idx_offset, normals, light):
    '''geometry of the splitted polygons (splitted to assign colors* normals)'''
    total_p_verts = 0
    p_vertices, vertex_colors, indices = [], [], []

    for pol, idx in zip(polygon_indices, original_idx):
        p_vertices.extend([v_path[c] for c in pol])
        factor = (normals[idx].dot(light))*0.5+0.5
        colors = []

        for c in pol:
            col = cols[idx % len(cols)]
            colors.append([col[0]*factor, col[1]*factor, col[2]*factor, col[3]])

        vertex_colors.extend(colors)
        indices.append([c + idx_offset + total_p_verts for c in range(len(pol))])
        total_p_verts += len(pol)

    return p_vertices, vertex_colors, indices, total_p_verts


def splitted_facet_polygons_geom_v_cols(polygon_indices, original_idx, v_path, cols, idx_offset, normals, light):
    '''geometry of the splitted polygons (splitted to assign vertex_colors * face_normals)'''

    total_p_verts = 0
    p_vertices, vertex_colors, indices = [], [], []

    for pol, idx in zip(polygon_indices, original_idx):
        p_vertices.extend([v_path[c] for c in pol])
        factor = (normals[idx].dot(light)) * 0.5 + 0.5
        colors = []

        for c in pol:
            col = cols[c % len(cols)]
            colors.append([col[0] * factor, col[1] * factor, col[2] * factor, col[3]])

        vertex_colors.extend(colors)
        indices.append([c + idx_offset + total_p_verts for c in range(len(pol))])
        total_p_verts += len(pol)

    return p_vertices, vertex_colors, indices, total_p_verts


def splitted_smooth_polygons_geom(polygon_indices, original_idx, v_path, cols, idx_offset, normals, light):
    '''geometry of the splitted polygons (splitted to assign face_colors * vertex_normals)'''

    total_p_verts = 0
    p_vertices, vertex_colors, indices = [], [], []

    for pol, idx in zip(polygon_indices, original_idx):
        p_vertices.extend([v_path[c] for c in pol])
        colors = []

        for c in pol:
            factor = (normals[c].dot(light)) * 0.5 + 0.5
            col = cols[idx % len(cols)]
            colors.append([col[0] * factor, col[1] * factor, col[2] * factor, col[3]])

        vertex_colors.extend(colors)
        indices.append([c + idx_offset + total_p_verts for c in range(len(pol))])
        total_p_verts += len(pol)

    return p_vertices, vertex_colors, indices, total_p_verts


def get_vertex_normals(vecs, polygons):
    mesh = bmesh_from_pydata(vecs, [], polygons, normal_update=True)
    return [vert.normal for vert in mesh.verts]


def polygons_geom(config, vecs, polygons, p_vertices, p_vertex_colors, p_indices, v_path, p_cols, idx_p_offset, points_colors):
    '''generates polygons geometry'''

    if (config.color_per_polygon and not config.polygon_use_vertex_color) or config.shade_mode == 'facet':
        polygon_indices, original_idx = ensure_triangles(vecs, polygons, config.handle_concave_quads)

        if config.shade_mode == 'facet':
            normals = [normal(*[Vector(vecs[c]) for c in p]) for p in polygons]

            if config.polygon_use_vertex_color:
                p_v, v_c, idx, total_p_verts = splitted_facet_polygons_geom_v_cols(polygon_indices, original_idx, v_path, points_colors, idx_p_offset[0], normals, config.vector_light)
            else:
                p_v, v_c, idx, total_p_verts = splitted_facet_polygons_geom(polygon_indices, original_idx, v_path, p_cols, idx_p_offset[0], normals, config.vector_light)

        elif config.shade_mode == 'smooth':
            normals = get_vertex_normals(vecs, polygons)
            p_v, v_c, idx, total_p_verts = splitted_smooth_polygons_geom(polygon_indices, original_idx, v_path, p_cols, idx_p_offset[0], normals, config.vector_light)

        else:
            p_v, v_c, idx, total_p_verts = splitted_polygons_geom(polygon_indices, original_idx, v_path, p_cols, idx_p_offset[0])

        p_vertices.extend(p_v)
        p_vertex_colors.extend(v_c)
        p_indices.extend(idx)
    else:
        polygon_indices, original_idx = ensure_triangles(vecs, polygons, config.handle_concave_quads)
        p_vertices.extend(v_path)

        if config.shade_mode == 'smooth':
            normals = get_vertex_normals(v_path, polygons)
            colors = []
            for normal_v in normals:
                col = p_cols
                factor = normal_v.dot(config.vector_light)*0.5+0.5
                colors.append([col[0]*factor, col[1]*factor, col[2]*factor, col[3]])
            p_vertex_colors.extend(colors)
        else:
            p_vertex_colors.extend([p_cols for v in v_path])
        p_indices.extend([[c + idx_p_offset[0] for c in p] for p in polygon_indices])
        total_p_verts = len(vecs)
    idx_p_offset[0] += total_p_verts


def edges_geom(config, edges, e_col, v_path, e_vertices, e_vertex_colors, e_indices, idx_e_offset):
    '''generates edges geometry'''
    if config.color_per_edge and not config.edges_use_vertex_color:
        for (idx0, idx1), col in zip(edges, cycle(e_col)):
            e_vertices.extend([v_path[idx0], v_path[idx1]])
            e_vertex_colors.extend([col, col])
            e_indices.append([len(e_vertices)-2, len(e_vertices)-1])

    else:
        e_vertices.extend(v_path)
        e_vertex_colors.extend([e_col for v in v_path])
        e_indices.extend([[c + idx_e_offset[0] for c in e] for e in edges])
        idx_e_offset[0] += len(v_path)


def generate_mesh_geom(config, vecs_in):
    '''generates drawing from mesh data'''
    geom = lambda: None

    if config.color_per_polygon:
        pol_color = config.poly_color
    else:
        if config.shade_mode == 'facet':
            pol_color = [[c] for c in config.poly_color[0]]
        else:
            pol_color = config.poly_color[0]

    if config.color_per_edge:
        edge_color = config.edge_color
    else:
        edge_color = config.edge_color[0]
    edges_s = config.edges
    polygons_s = config.polygons

    v_vertices = []
    e_vertices, e_vertex_colors, e_indices = [], [], []
    p_vertices, p_vertex_colors, p_indices = [], [], []

    idx_p_offset = [0]
    idx_e_offset = [0]

    if config.matrix[0]:
        vecs_in, mats_in = match_long_repeat([vecs_in, config.matrix])
        use_matrix = True
    else:
        mats_in = cycle(config.matrix)
        use_matrix = False

    if config.draw_verts or (config.draw_edges and config.edges_use_vertex_color) or (config.draw_polys and config.polygon_use_vertex_color):
        points_color = fill_points_colors(config.vector_color, vecs_in, config.color_per_point, config.random_colors)
    else:
        points_color = []

    for vecs, mat, polygons, edges, p_cols, e_col in zip(vecs_in, mats_in, cycle(polygons_s), cycle(edges_s), cycle(pol_color), cycle(edge_color)):
        if use_matrix:
            v_path = [(mat @ Vector(v))[:] for v in vecs]
        else:
            v_path = vecs
        v_vertices.extend(v_path)
        if config.draw_edges:
            edges_geom(config, edges, e_col, v_path, e_vertices, e_vertex_colors, e_indices, idx_e_offset)
        if config.draw_polys:
            polygons_geom(config, vecs, polygons, p_vertices, p_vertex_colors, p_indices, v_path, p_cols, idx_p_offset, points_color)

    if config.draw_verts:

        config.v_shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
        geom.v_vertices, geom.points_color = v_vertices, points_color

    if config.draw_edges:
        if config.edges_use_vertex_color and e_vertices:
            e_vertex_colors = points_color

        config.e_shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
        geom.e_vertices, geom.e_vertex_colors, geom.e_indices = e_vertices, e_vertex_colors, e_indices


    if config.draw_polys and config.shade_mode != 'fragment':
        if config.polygon_use_vertex_color and config.shade_mode != 'facet':
            p_vertex_colors = points_color
        config.p_shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
        geom.p_vertices, geom.p_vertex_colors, geom.p_indices = p_vertices, p_vertex_colors, p_indices

    elif config.shade_mode == 'fragment' and config.draw_polys:

        config.draw_fragment_function = None

        # double reload, for testing.
        ND = config.node.node_dict.get(hash(config.node))
        if not ND:
            if config.node.custom_shader_location in bpy.data.texts:
                config.node.populate_node_with_custom_shader_from_text()
                ND = config.node.node_dict.get(hash(config.node))

        if ND and ND.get('draw_fragment'):
            config.draw_fragment_function = ND.get('draw_fragment')
            config.p_shader = gpu.types.GPUShader(config.node.custom_vertex_shader, config.node.custom_fragment_shader)
        else:
            config.p_shader = gpu.types.GPUShader(default_vertex_shader, default_fragment_shader)
        geom.p_vertices, geom.p_vertex_colors, geom.p_indices = p_vertices, p_vertex_colors, p_indices

    return geom


def get_shader_data(named_shader=None):
    source = bpy.data.texts[named_shader].as_string()
    exec(source)
    local_vars = vars().copy()
    names = ['vertex_shader', 'fragment_shader', 'draw_fragment']
    return [local_vars.get(name) for name in names]

def add_dashed_shader(config):
    config.dashed_shader = gpu.types.GPUShader(dashed_vertex_shader, dashed_fragment_shader)


class SvViewerDrawMk4(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: vd geometry preview
    Tooltip: drawing preview on 3d scene, with experimental features

    """
    bl_idname = 'SvViewerDrawMk4'
    bl_label = 'Viewer Draw'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_DRAW_VIEWER'

    node_dict = {}

    selected_draw_mode: EnumProperty(
        items=enum_item_5(["flat", "facet", "smooth", "fragment"], ['SNAP_VOLUME', 'ALIASED', 'ANTIALIASED', 'SCRIPTPLUGINS']),
        description="pick how the node will draw faces",
        default="flat", update=updateNode
    )

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode
        )
    draw_gl_polygonoffset: BoolProperty(
        name="Draw gl polygon offset",
        default=True,
        update=updateNode
        )
    draw_gl_wireframe: BoolProperty(
        name="Draw gl wireframe",
        default=False,
        update=updateNode)
    vector_light: FloatVectorProperty(
        name='vector light', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4), update=updateNode)
    extended_matrix: BoolProperty(
        default=False,
        description='Allows mesh.transform(matrix) operation, quite fast!')

    handle_concave_quads: BoolProperty(
        name='Handle Concave Quads', default=False, update=updateNode,
        description='tessellate quads using geometry.tessellate_polygon, expect some speed impact')

    point_size: IntProperty(
        min=1, default=4, name='Verts Size',
        description='Point Size', update=updateNode
    )
    line_width: IntProperty(
        min=1, default=1, name='Edge Width',
        description='Edge Width', update=updateNode
    )

    curve_samples: IntProperty(
        min=2, default=25, name='Samples',
        description='Curve Resolution', update=updateNode
    )
    vector_color: FloatVectorProperty(
        update=updateNode, name='Vertices Color', default=(.9, .9, .95, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    display_verts: BoolProperty(
        update=updateNode, name='Display Vertices', default=True
        )
    vector_random_colors: BoolProperty(
        update=updateNode, name='Random Vertices Color', default=False
        )
    random_seed: IntProperty(
        min=1, default=1, name='Random Seed',
        description='Seed of random colors', update=updateNode
    )
    color_per_point: BoolProperty(
        update=updateNode, name='Color per point', default=False,
        description='Toggle between color per point or per object'
        )
    color_per_edge: BoolProperty(
        update=updateNode, name='Color per edge', default=False,
        description='Toggle between color per edge or per object'
        )
    color_per_polygon: BoolProperty(
        update=updateNode, name='Color per polygon', default=False,
        description='Toggle between color per polygon or per object'
        )
    polygon_use_vertex_color: BoolProperty(
        update=updateNode, name='Polys Vertex Color', default=False,
        description='Colorize polygons using vertices color'
        )
    edges_use_vertex_color: BoolProperty(
        update=updateNode, name='Edges Vertex Color', default=False,
        description='Colorize edges using vertices color'
        )

    edge_color: FloatVectorProperty(
        update=updateNode, name='Edges Color', default=(.9, .9, .35, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    display_edges: BoolProperty(
        update=updateNode, name='Display Edges', default=True
        )

    polygon_color: FloatVectorProperty(
        update=updateNode, name='Ploygons Color', default=(0.14, 0.54, 0.81, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    display_faces: BoolProperty(
        update=updateNode, name='Display Polygons', default=True
        )

    matrix_draw_scale: FloatProperty(default=1, min=0.0001, name="Drawing matrix scale", update=updateNode)

    # dashed line props
    use_dashed: BoolProperty(name='Dashes Edges', update=updateNode)
    u_dash_size: FloatProperty(default=0.12, min=0.0001, name="dash size", update=updateNode)
    u_gap_size: FloatProperty(default=0.19, min=0.0001, name="gap size", update=updateNode)
    u_resolution: FloatVectorProperty(default=(25.0, 18.0), size=2, min=0.01, name="resolution", update=updateNode)

    # custom shader props
    def populate_node_with_custom_shader_from_text(self):
        if self.custom_shader_location in bpy.data.texts:
            try:
                vertex_shader, fragment_shader, draw_fragment = get_shader_data(named_shader=self.custom_shader_location)

                self.custom_vertex_shader = vertex_shader
                self.custom_fragment_shader = fragment_shader
                self.node_dict[hash(self)] = {'draw_fragment': draw_fragment}

            except Exception as err:
                print(err)


                # reset custom shader
                self.custom_vertex_shader = ''
                self.custom_fragment_shader = ''
                self.node_dict[hash(self)] = {}

    def wrapped_update(self, context=None):
        self.populate_node_with_custom_shader_from_text()
        if context:
            self.process_node(context)

    custom_vertex_shader: StringProperty(default=default_vertex_shader, name='vertex shader')
    custom_fragment_shader: StringProperty(default=default_fragment_shader, name='fragment shader')
    custom_shader_location: StringProperty(update=wrapped_update, name='custom shader location')

    # attributes socket props
    def configureAttrSocket(self, context):
        self.inputs['attrs'].hide_safe = not self.node_ui_show_attrs_socket

    node_ui_show_attrs_socket: BoolProperty(default=False, name='Show attributes socket', update=configureAttrSocket)

    def draw_buttons(self, context, layout):
        addon = context.preferences.addons.get(sverchok.__name__)
        over_sized_buttons = addon.preferences.over_sized_buttons
        r0 = layout.row()
        r0.prop(self, "activate", text="", icon="HIDE_" + ("OFF" if self.activate else "ON"))
        r0.separator()
        r0.prop(self, "selected_draw_mode", expand=True, text='')
        if self.selected_draw_mode == 'fragment':
            layout.prop(self, "custom_shader_location", icon='TEXT', text='')

        row = layout.row(align=True)
        row.prop(self, "point_size")
        row.prop(self, "line_width")
        row = layout.row(align=True)
        row.scale_y = 4.0 if over_sized_buttons else 1
        self.wrapper_tracked_ui_draw_op(row, "node.sverchok_mesh_baker_mk3", icon='OUTLINER_OB_MESH', text="B A K E")
        row.separator()
        self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')


    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.label(text='Light Direction')
        layout.prop(self, 'vector_light', text='')
        self.draw_additional_props(context, layout)
        if self.use_dashed:
            layout.prop(self, "u_dash_size")
            layout.prop(self, "u_gap_size")
            layout.prop(self, "u_resolution")

    def draw_additional_props(self, context, layout):
        layout.prop(self, 'draw_gl_polygonoffset')
        layout.prop(self, 'draw_gl_wireframe')
        layout.prop(self, 'handle_concave_quads')
        layout.prop(self, 'node_ui_show_attrs_socket')
        layout.prop(self, 'matrix_draw_scale')
        layout.prop(self, "use_dashed")

    def rclick_menu(self, context, layout):
        self.draw_additional_props(context, layout)

    def bake(self):
        with self.sv_throttle_tree_update():
            bpy.ops.node.sverchok_mesh_baker_mk3(
                idname=self.name, idtree=self.id_data.name
            )

    def sv_init(self, context):
        new_input = self.inputs.new
        new_input('SvVerticesSocket', "Vertices")
        new_input('SvStringsSocket', "Edges")
        new_input('SvStringsSocket', "Polygons")
        new_input('SvMatrixSocket', 'Matrix')

        v_col = new_input('SvColorSocket', "Vector Color")
        v_col.prop_name = 'vector_color'
        v_col.custom_draw = 'draw_color_socket'
        e_col = new_input('SvColorSocket', "Edge Color")
        e_col.prop_name = 'edge_color'
        e_col.custom_draw = 'draw_color_socket'
        p_col = new_input('SvColorSocket', "Polygon Color")
        p_col.prop_name = 'polygon_color'
        p_col.custom_draw = 'draw_color_socket'

        attr_socket = new_input('SvStringsSocket', 'attrs')
        attr_socket.hide = True
        attr_socket.quick_link_to_node = "SvVDAttrsNodeMk2"


    def migrate_from(self, old_node):
        self.vector_color = old_node.vert_color
        self.polygon_color = old_node.face_color

    def draw_color_socket(self, socket, context, layout):
        socket_info = socket_dict[socket.prop_name]
        layout.prop(self, socket_info[0], text="", icon=socket_info[1])
        layout.prop(self, socket_info[2], text="", icon='COLOR')
        display_color = not socket.is_linked
        draw_name = True
        if len(socket_info) < 5:
            layout.prop(self, socket_info[3], text="", icon='VPAINT_HLT')

        else:
            layout.prop(self, socket_info[3], text="", icon='MOD_NOISE')
            if socket_info[3] in self and self[socket_info[3]]:
                layout.prop(self, socket_info[4], text="Seed")
                draw_name = False

        if socket_info[3] in self:
            display_color = display_color and  not self[socket_info[3]]


        if display_color:
            layout.prop(self, socket.prop_name, text="")
        else:
            if draw_name:
                reduced_name = socket.name[:2] + ". Col"
                layout.label(text=reduced_name+ '. ' + SvGetSocketInfo(socket))


    def create_config(self):
        config = lambda: None

        config.draw_verts = self.display_verts
        config.draw_edges = self.display_edges
        config.draw_polys = self.display_faces and self.inputs['Polygons'].is_linked
        config.point_size = self.point_size
        config.line_width = self.line_width
        config.color_per_point = self.color_per_point
        config.color_per_edge = self.color_per_edge
        config.color_per_polygon = self.color_per_polygon
        config.polygon_use_vertex_color = self.polygon_use_vertex_color
        config.edges_use_vertex_color = self.edges_use_vertex_color
        config.random_colors = self.vector_random_colors

        config.vector_light = Vector(self.vector_light)
        config.shade_mode = self.selected_draw_mode
        config.draw_gl_polygonoffset = self.draw_gl_polygonoffset
        config.draw_gl_wireframe = self.draw_gl_wireframe
        config.handle_concave_quads = self.handle_concave_quads

        config.draw_dashed = self.use_dashed
        config.u_dash_size = self.u_dash_size
        config.u_gap_size = self.u_gap_size
        config.u_resolution = self.u_resolution[:]

        config.node = self


        return config


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

    def process(self):
        if bpy.app.background:
            return
        self.handle_attr_socket()
        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return
        n_id = node_id(self)
        callback_disable(n_id)
        inputs = self.inputs
        # end early
        if not self.activate:
            return


        if not any([inputs['Vertices'].is_linked, inputs['Matrix'].is_linked]):
            return

        if inputs['Vertices'].is_linked:
            vecs = inputs['Vertices'].sv_get(default=[[]])

            edges = inputs['Edges'].sv_get(default=[[]])
            polygons = inputs['Polygons'].sv_get(default=[[]])
            matrix = inputs['Matrix'].sv_get(default=[[]])
            vector_color = inputs['Vector Color'].sv_get(default=[[self.vector_color]])
            edge_color = inputs['Edge Color'].sv_get(default=[[self.edge_color]])
            poly_color = inputs['Polygon Color'].sv_get(default=[[self.polygon_color]])
            seed_set(self.random_seed)
            config = self.create_config()

            config.vector_color = vector_color
            config.edge_color = edge_color
            config.poly_color = poly_color
            config.edges = edges

            if self.use_dashed:
                add_dashed_shader(config)

            config.polygons = polygons
            config.matrix = matrix
            if not inputs['Edges'].is_linked and self.display_edges:
                config.edges = polygons_to_edges(polygons, unique_edges=True)

            geom = generate_mesh_geom(config, vecs)


            draw_data = {

                'tree_name': self.id_data.name[:],
                'custom_function': view_3d_geom,
                'args': (geom, config)
            }
            callback_enable(n_id, draw_data)

        elif inputs['Matrix'].is_linked:
            matrices = inputs['Matrix'].sv_get(deepcopy=False, default=[Matrix()])

            gl_instructions = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_matrix,
                'args': (matrices, self.matrix_draw_scale)}
            callback_enable(n_id, gl_instructions)

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



classes = [SvViewerDrawMk4,]
register, unregister = bpy.utils.register_classes_factory(classes)
