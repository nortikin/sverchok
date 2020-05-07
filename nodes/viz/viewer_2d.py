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
from mathutils import Vector
from mathutils.geometry import tessellate_polygon as tessellate
from mathutils.noise import random, seed_set
from numpy import float64 as np_float64, linspace as np_linspace
import bpy
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty, FloatVectorProperty, IntVectorProperty

import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.utils.context_managers import sv_preferences
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as nvBGL
from sverchok.utils.sv_mesh_utils import polygons_to_edges



socket_dict = {
    'vector_color': ('vector_toggle', 'UV_VERTEXSEL', 'color_per_point', 'vector_random_colors', 'random_seed'),
    'edge_color': ('edge_toggle', 'UV_EDGESEL', 'color_per_edge', 'edges_use_vertex_color'),
    'polygon_color': ('polygon_toggle', 'UV_FACESEL', 'color_per_polygon', 'polygon_use_vertex_color'),
    }

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

def background_rect(x, y, w, h, margin):
    background_coords = [
        (x, y + margin),
        (x + w + 2* margin, y + margin),
        (w + x + 2 * margin, y - h - margin),
        (x, y - h - margin)]
    background_indices = [(0, 1, 2), (0, 2, 3)]

    return background_coords, background_indices

def fill_points_colors(vectors_color, data, color_per_point, random_colors):
    points_color = []
    if color_per_point:
        for cols, sub_data in zip(cycle(vectors_color), data):
            if random_colors:
                for  n in sub_data:
                    points_color.append([random(), random(), random(), 1])
            else:
                for c, n in zip(cycle(cols), sub_data):
                    points_color.append(c)
    else:
        for nums, col in zip(data, cycle(vectors_color[0])):
            if random_colors:
                r_color = [random(),random(),random(),1]
                for n in nums:
                    points_color.append(r_color)
            else:
                for n in nums:
                    points_color.append(col)

    return points_color


def view_2d_geom(x, y, args):
    """
    x and y are passed by default so you could add font content
    draws the batches
    """

    geom, config = args
    if config.draw_background:
        background_color = config.background_color
        # draw background, this could be cached......
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": geom.background_coords}, indices=geom.background_indices)
        shader.bind()
        shader.uniform_float("color", background_color)
        batch.draw(shader)

    if config.draw_polys and config.mode == 'Mesh':
        config.p_batch.draw(config.p_shader)

    if config.draw_edges:
        bgl.glLineWidth(config.edge_width)
        config.e_batch.draw(config.e_shader)
        bgl.glLineWidth(1)

    if config.draw_verts:
        bgl.glPointSize(config.point_size)
        config.v_batch.draw(config.v_shader)
        bgl.glPointSize(1)


def path_from_nums(nums, x, y, num_width, num_height, maxmin, sys_scale):
    v_path = []
    for i, n in enumerate(nums):
        _px = x + (i * num_width) * sys_scale
        _py = y + ((n - maxmin[1])* num_height) * sys_scale
        v_path.append([_px, _py])
    return v_path

def generate_number_geom(config, numbers):
    geom = lambda: None
    x, y = config.loc
    sys_scale = config.sys_scale
    line_color = config.edge_color
    w, h = config.size
    all_numbers = [n for l in numbers for n in l]
    maxmin = [max(all_numbers), min(all_numbers)]
    margin = 10 * sys_scale
    geom.background_coords, geom.background_indices = background_rect(x, y, w, h, margin)
    v_vertices = []
    e_vertices = []
    vertex_colors = []
    indices = []
    num_height = h/(max(all_numbers)- min(all_numbers))
    idx_offset = 0

    _x = x + margin
    _y = y - h
    if config.color_per_edge and not config.edges_use_vertex_color:
        for nums, cols in zip(numbers, cycle(line_color)):
            num_width = w/(len(nums)-1)
            v_path = path_from_nums(nums, _x, _y, num_width, num_height, maxmin, sys_scale)
            v_vertices.extend(v_path)

            for v, v1, col in zip(v_path[:-1], v_path[1:], cycle(cols)):
                e_vertices.extend([v, v1])
                vertex_colors.extend([col, col])

            for i in range(len(nums)-1):
                indices.append([2*i + idx_offset, 2*i + 1 + idx_offset])
            idx_offset += 2*len(nums)
    else:
        for nums, col in zip(numbers, line_color[0]):
            num_width = w/(len(nums)-1)
            v_path = path_from_nums(nums, _x, _y, num_width, num_height, maxmin, sys_scale)
            e_vertices.extend(v_path)
            vertex_colors.extend([col for v in v_path])

            for i in range(len(nums)-1):
                indices.append([i + idx_offset, i + 1 + idx_offset])
            idx_offset += len(nums)

        v_vertices = e_vertices


    points_color = fill_points_colors(config.vector_color, numbers, config.color_per_point, config.random_colors)
    geom.points_color = points_color
    geom.points_vertices = v_vertices
    geom.vertices = e_vertices
    geom.vertex_colors = vertex_colors
    geom.indices = indices

    if config.draw_verts:
        config.v_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.v_batch = batch_for_shader(config.v_shader, 'POINTS', {"pos": v_vertices, "color": points_color})
    if config.draw_edges:
        if config.edges_use_vertex_color:
            vertex_colors = points_color
        config.e_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.e_batch = batch_for_shader(config.e_shader, 'LINES', {"pos": e_vertices, "color": vertex_colors}, indices=indices)

    return geom


def graph_edges(config, v_path, col, e_vertices, e_vertex_colors, e_indices, cyclic, idx_offset):

    offset = idx_offset[0]
    if config.color_per_edge and not config.edges_use_vertex_color:

        for v, v1, c in zip(v_path[:-1], v_path[1:], cycle(col)):
            e_vertices.extend([v, v1])
            e_vertex_colors.extend([c, c])

        for i in range(len(v_path)-1):
            e_indices.append([2*i + offset, 2*i + 1 + offset])
        if cyclic:

            e_indices.append([2 * len(v_path) - 2-1 + offset, 0 + offset])
        idx_offset[0] += 2 * len(v_path) - 2
    else:
        e_vertex_colors.extend([col for v in v_path])
        e_vertices.extend(v_path)

        for i in range(len(v_path)-1):
            e_indices.append([i + offset, i + 1 + offset])
        if cyclic:
            e_indices.append([len(v_path)-1 + offset, 0 + offset])
        idx_offset[0] += len(v_path)


def generate_graph_geom(config, paths):

    geom = lambda: None
    x, y = config.loc
    scale = config.scale
    cyclic = config.cyclic
    sys_scale = config.sys_scale
    if config.color_per_edge:
        edge_color = config.edge_color
    else:
        edge_color = config.edge_color[0]

    all_vecs = [v for vecs in paths for v in vecs]
    maxmin = list(zip(map(max, *all_vecs), map(min, *all_vecs)))
    axis1, axis2 = get_axis_index(config.plane)
    # background geom
    w = (maxmin[axis1][0]- maxmin[axis1][1]) * scale
    h = (maxmin[axis2][0]- maxmin[axis2][1]) * scale
    margin = 10 * sys_scale
    geom.background_coords, geom.background_indices = background_rect(x, y, w, h, margin)
    v_vertices = []
    e_vertices, e_vertex_colors, e_indices = [], [], []
    _x = x + margin

    idx_offset = [0]
    for vecs, col in zip(paths, cycle(edge_color)):
        v_path = transformed_verts(vecs, _x, y, maxmin, scale, axis1, axis2)
        v_vertices.extend(v_path)
        if config.draw_edges:
            graph_edges(config, v_path, col, e_vertices, e_vertex_colors, e_indices, cyclic, idx_offset)


    points_color = fill_points_colors(config.vector_color, paths, config.color_per_point, config.random_colors)

    if config.draw_verts:
        config.v_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.v_batch = batch_for_shader(config.v_shader, 'POINTS', {"pos": v_vertices, "color": points_color})

    if config.draw_edges:
        if config.edges_use_vertex_color:
            e_vertex_colors = points_color
        config.e_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.e_batch = batch_for_shader(config.e_shader, 'LINES', {"pos": e_vertices, "color": e_vertex_colors}, indices=e_indices)

    return geom


def transformed_verts(vecs, x, y, maxmin, scale, axis1, axis2):
    v_path = []
    for v in vecs:
        _px = x + (v[axis1] - maxmin[axis1][1]) * scale
        _py = y + (v[axis2] - maxmin[axis2][0]) * scale
        v_path.append([_px, _py])
    return v_path


def splitted_polygons_geom(polygon_indices, original_idx, v_path, cols, idx_offset):
    total_p_verts = 0
    p_vertices, vertex_colors, indices = [], [], []
    for pol, idx in zip(polygon_indices, original_idx):
        p_vertices.extend([v_path[c] for c in pol])
        vertex_colors.extend([cols[idx % len(cols)] for c in pol])
        indices.append([c + idx_offset + total_p_verts for c in range(len(pol))])
        total_p_verts += len(pol)
    return p_vertices, vertex_colors, indices, total_p_verts


def get_axis_index(plane):
    if plane == 'XY':
        axis1 = 0
        axis2 = 1
    elif plane == 'XZ':
        axis1 = 0
        axis2 = 2
    elif plane == 'YZ':
        axis1 = 1
        axis2 = 2
    return axis1, axis2


def polygons_geom(config, vecs, polygons, p_vertices, p_vertex_colors, p_indices, v_path, p_cols, idx_p_offset):
    '''generates polygons geometry'''
    if config.color_per_polygon and not config.polygon_use_vertex_color:
        polygon_indices, original_idx = ensure_triangles(vecs, polygons, True)
        p_v, v_c, idx, total_p_verts = splitted_polygons_geom(polygon_indices, original_idx, v_path, p_cols, idx_p_offset[0])
        p_vertices.extend(p_v)
        p_vertex_colors.extend(v_c)
        p_indices.extend(idx)
    else:
        polygon_indices, original_idx = ensure_triangles(vecs, polygons, True)
        p_vertices.extend(v_path)
        p_vertex_colors.extend([p_cols for v in v_path])
        p_indices.extend([[c + idx_p_offset[0] for c in p] for p in polygon_indices])
        total_p_verts = len(vecs)
    idx_p_offset[0] += total_p_verts


def edges_geom(config, edges, e_col, v_path, e_vertices, e_vertex_colors, e_indices, idx_e_offset):
    '''generates edges geometry'''
    if config.color_per_edge and not config.edges_use_vertex_color:
        for (v, v1), col in zip(edges, cycle(e_col)):
            e_vertices.extend([v_path[v], v_path[v1]])
            e_vertex_colors.extend([col, col])
            e_indices.append([len(e_vertices)-2, len(e_vertices)-1])

    else:
        e_vertices.extend(v_path)
        e_vertex_colors.extend([e_col for v in v_path])
        e_indices.extend([[c + idx_e_offset[0] for c in e] for e in edges ])
        idx_e_offset[0] += len(v_path)


def generate_mesh_geom(config, vecs_in):
    '''generates drawing from mesh data'''
    geom = lambda: None
    x, y = config.loc
    scale = config.scale
    sys_scale = config.sys_scale
    if config.color_per_polygon:
        pol_color = config.poly_color
    else:
        pol_color = config.poly_color[0]

    if config.color_per_edge:
        edge_color = config.edge_color
    else:
        edge_color = config.edge_color[0]
    edges_s = config.edges
    polygons_s = config.polygons

    axis1, axis2 = get_axis_index(config.plane)
    all_vecs = [v for vecs in vecs_in for v in vecs ]
    maxmin = list(zip(map(max, *all_vecs), map(min, *all_vecs)))
    # background geom

    w = (maxmin[axis1][0]- maxmin[axis1][1]) * scale
    h = (maxmin[axis2][0]- maxmin[axis2][1]) * scale
    margin = 10 * sys_scale
    geom.background_coords, geom.background_indices = background_rect(x, y, w, h, margin)

    v_vertices = []
    e_vertices, e_vertex_colors, e_indices = [], [], []
    p_vertices, p_vertex_colors, p_indices = [], [], []

    _x = x + margin
    idx_p_offset = [0]
    idx_e_offset = [0]

    for vecs, polygons, edges, p_cols, e_col in zip(vecs_in, cycle(polygons_s), cycle(edges_s), cycle(pol_color), cycle(edge_color)):
        v_path = transformed_verts(vecs, _x, y, maxmin, scale, axis1, axis2)
        v_vertices.extend(v_path)
        if config.draw_edges:
            edges_geom(config, edges, e_col, v_path, e_vertices, e_vertex_colors, e_indices, idx_e_offset)
        if config.draw_polys:
            polygons_geom(config, vecs, polygons, p_vertices, p_vertex_colors, p_indices, v_path, p_cols, idx_p_offset)

    points_color = fill_points_colors(config.vector_color, vecs_in, config.color_per_point, config.random_colors)

    if config.draw_verts:
        config.v_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.v_batch = batch_for_shader(config.v_shader, 'POINTS', {"pos": v_vertices, "color": points_color})

    if config.draw_edges:
        if config.edges_use_vertex_color and e_vertices:
            e_vertex_colors = points_color
        config.e_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.e_batch = batch_for_shader(config.e_shader, 'LINES', {"pos": e_vertices, "color": e_vertex_colors}, indices=e_indices)

    if config.draw_polys:
        if config.polygon_use_vertex_color:
            p_vertex_colors = points_color
        config.p_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        config.p_batch = batch_for_shader(config.p_shader, 'TRIS', {"pos": p_vertices, "color": p_vertex_colors}, indices=p_indices)

    return geom


class SvViewer2D(bpy.types.Node, SverchCustomTreeNode):
    '''Curved interpolation'''
    bl_idname = 'SvViewer2D'
    bl_label = 'Viewer 2D'
    bl_icon = 'HIDE_OFF'
    sv_icon = 'SV_EASING'

    modes = [
        ('Number', 'Number', 'Input UV coordinates to evaluate texture', '', 1),
        ('Path', 'Path', 'Matrix to apply to verts before evaluating texture', '', 2),
        ('Curve', 'Curve', 'Matrix of texture (External Object matrix)', '', 3),
        ('Mesh', 'Mesh', 'Matrix of texture (External Object matrix)', '', 4),

    ]
    plane = [
        ('XY', 'XY', 'Input UV coordinates to evaluate texture', '', 1),
        ('XZ', 'XZ', 'Matrix to apply to verts before evaluating texture', '', 2),
        ('YZ', 'YZ', 'Matrix of texture (External Object matrix)', '', 3),


    ]

    def update_mode(self, context):
        self.update_sockets()
        updateNode(self, context)

    def update_sockets(self):
        self.inputs['Polygon Color'].hide_safe = self.mode != 'Mesh'
        self.inputs['Number'].hide_safe = not self.mode == 'Number'
        self.inputs['Curve'].hide_safe = not self.mode == 'Curve'
        self.inputs['Vecs'].hide_safe = self.mode in ['Number', 'Curve']
        self.inputs['Edges'].hide_safe = self.mode in ['Number', 'Path', 'Curve']
        self.inputs['Polygons'].hide_safe = self.mode in ['Number', 'Path', 'Curve']

    mode: EnumProperty(
        name='Mode',
        items=modes,
        default='Path',
        description="Display Mode",
        update=update_mode)

    working_plane: EnumProperty(
        name='Proyection Plane',
        items=plane,
        default='XY',
        description="2D plane where geometry will be projected",
        update=update_mode)

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode
    )
    cyclic: BoolProperty(
        name='Cycle', description='Activate drawing',
        default=True, update=updateNode
    )

    draw_scale: FloatProperty(
        min=0.0, default=10.0, name='Scale',
        description='Drawing Scale', update=updateNode
    )
    drawing_size: IntVectorProperty(
        update=updateNode, name='Size', default=(150, 150),
        size=2
        )
    draw_verts: BoolProperty(
        default=False, name='See Verts',
        description='Drawing Verts', update=updateNode
    )
    point_size: IntProperty(
        min=1, default=4, name='Verts Size',
        description='Point Size', update=updateNode
    )
    edge_width: IntProperty(
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
    vector_toggle: BoolProperty(
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
        update=update_mode, name='Polys Vertex Color', default=False,
        description='Colorize polygons using vertices color'
        )
    edges_use_vertex_color: BoolProperty(
        update=update_mode, name='Edges Vertex Color', default=False,
        description='Colorize edges using vertices color'
        )

    edge_color: FloatVectorProperty(
        update=updateNode, name='Edges Color', default=(.9, .9, .35, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    edge_toggle: BoolProperty(
        update=updateNode, name='Display Edges', default=True
        )
    polygon_color: FloatVectorProperty(
        update=updateNode, name='Ploygons Color', default=(.9, .9, .8, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    polygon_toggle: BoolProperty(
        update=updateNode, name='Display Polygons', default=True
        )
    background_color: FloatVectorProperty(
        update=updateNode, name='', default=(.01, .01, .01, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
        )
    draw_background: BoolProperty(
        update=updateNode, name='Display Background', default=True
        )

    def draw_buttons(self, context, layout):
        r0 = layout.row()
        r0.prop(self, "activate", text="", icon="HIDE_" + ("OFF" if self.activate else "ON"))
        r0.prop(self, "mode")
        c0 = layout.column(align=True)
        row = c0.row(align=True)
        row.prop(self, "draw_background", text='', icon='WORLD')
        if self.draw_background:
            row.prop(self, "background_color")


        if self.mode == 'Number':
            row = c0.row(align=True)
            for j in range(2):
                row.prop(self, 'drawing_size', index=j, text='XY'[j])
            row = c0.row(align=True)
            row.prop(self, "point_size")
            row.prop(self, "edge_width")

        else:
            row = c0.row(align=True)
            row.prop(self, "working_plane", expand=True)
            c0.prop(self, "draw_scale")
            row = c0.row(align=True)
            row.prop(self, "point_size")
            row.prop(self, "edge_width")

            if self.mode in ["Path", "Curve"]:
                layout.prop(self, "cyclic")
            if self.mode == "Curve":
                layout.prop(self, "curve_samples")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Number")
        self.inputs.new('SvVerticesSocket', "Vecs")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Polygons")
        self.inputs.new('SvCurveSocket', "Curve")
        vc0 = self.inputs.new('SvColorSocket', "Vector Color")
        vc0.prop_name = 'vector_color'
        vc0.custom_draw = 'draw_color_socket'
        vc = self.inputs.new('SvColorSocket', "Edge Color")
        vc.prop_name = 'edge_color'
        vc.custom_draw = 'draw_color_socket'
        vc2 = self.inputs.new('SvColorSocket', "Polygon Color")
        vc2.prop_name = 'polygon_color'
        vc2.custom_draw = 'draw_color_socket'
        self.get_and_set_gl_scale_info()
        self.update_sockets()

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
                layout.label(text=socket.name+ '. ' + SvGetSocketInfo(socket))

    def get_drawing_attributes(self):
        """
        adjust render location based on preference multiplier setting
        """
        x, y = [int(j) for j in (Vector(self.absolute_location) + Vector((self.width + 20, 0)))[:]]

        try:
            with sv_preferences() as prefs:
                multiplier = prefs.render_location_xy_multiplier
                scale = prefs.render_scale
        except:
            # print('did not find preferences - you need to save user preferences')
            multiplier = 1.0
            scale = 1.0
        x, y = [x * multiplier, y * multiplier]

        return x, y, scale, multiplier

    def create_config(self):
        config = lambda: None
        x, y, scale, _ = self.get_drawing_attributes()
        margin = 10* scale
        config.mode = self.mode
        config.loc = (x, y - margin)
        config.sys_scale = scale
        config.scale = scale * self.draw_scale
        config.cyclic = self.cyclic
        config.background_color = self.background_color
        config.draw_background = self.draw_background
        config.plane = self.working_plane
        config.draw_verts = self.vector_toggle
        config.draw_edges = self.edge_toggle
        config.draw_polys = self.polygon_toggle and self.inputs['Polygons'].is_linked
        config.point_size = self.point_size
        config.edge_width = self.edge_width
        config.color_per_point = self.color_per_point
        config.color_per_edge = self.color_per_edge
        config.color_per_polygon = self.color_per_polygon
        config.polygon_use_vertex_color = self.polygon_use_vertex_color
        config.edges_use_vertex_color = self.edges_use_vertex_color
        config.random_colors = self.vector_random_colors

        return x, y, config

    def process(self):
        n_id = node_id(self)
        nvBGL.callback_disable(n_id)
        inputs = self.inputs
        # end early
        if not self.activate:
            return

        if self.mode == 'Number':
            if not inputs['Number'].is_linked:
                return
            numbers = inputs['Number'].sv_get(default=[[]])
        elif self.mode == 'Curve':
            if not inputs['Curve'].is_linked:
                return
            curves = inputs['Curve'].sv_get(default=[[]])
        else:
            if not inputs['Vecs'].is_linked:
                return
            vecs = inputs['Vecs'].sv_get(default=[[]])

        edges = inputs['Edges'].sv_get(default=[[]])
        polygons = inputs['Polygons'].sv_get(default=[[]])
        vector_color = inputs['Vector Color'].sv_get(default=[[self.vector_color]])
        edge_color = inputs['Edge Color'].sv_get(default=[[self.edge_color]])
        poly_color = inputs['Polygon Color'].sv_get(default=[[self.polygon_color]])
        seed_set(self.random_seed)
        x, y, config = self.create_config()

        config.vector_color = vector_color
        config.edge_color = edge_color
        config.poly_color = poly_color
        config.edges = edges


        if self.mode == 'Number':
            config.size = self.drawing_size
            geom = generate_number_geom(config, numbers)
        elif self.mode == 'Path':
            geom = generate_graph_geom(config, vecs)
        elif self.mode == 'Curve':
            paths = []
            for curve in curves:
                t_min, t_max = curve.get_u_bounds()
                ts = np_linspace(t_min, t_max, num=self.curve_samples, dtype=np_float64)
                paths.append(curve.evaluate_array(ts).tolist())

            geom = generate_graph_geom(config, paths)

        else:
            config.polygons = polygons
            if not inputs['Edges'].is_linked and self.edge_toggle:
                config.edges = polygons_to_edges(polygons, unique_edges=True)

            geom = generate_mesh_geom(config, vecs)


        draw_data = {
            'mode': 'custom_function',
            'tree_name': self.id_data.name[:],
            'loc': (x, y),
            'custom_function': view_2d_geom,
            'args': (geom, config)
        }
        nvBGL.callback_enable(n_id, draw_data)

    def sv_free(self):
        nvBGL.callback_disable(node_id(self))

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''



classes = [SvViewer2D,]
register, unregister = bpy.utils.register_classes_factory(classes)
