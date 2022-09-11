# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Matrix, Vector
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatVectorProperty
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, get_data_nesting_level, ensure_nesting_level, zip_long_repeat, node_id
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.modules.polygon_utils import pols_normals
from sverchok.utils.modules.vertex_utils import np_vertex_normals
from sverchok.utils.math import np_dot
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable

def draw_edges(shader, points, edges, line_width, color):
    bgl.glLineWidth(line_width)
    batch = batch_for_shader(shader, 'LINES', {"pos": points}, indices=edges)
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    bgl.glLineWidth(1)

def draw_points(shader, points, size, color):
    bgl.glPointSize(size)
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    bgl.glPointSize(1)

def draw_polygons(shader, points, tris, vertex_colors):
    batch = batch_for_shader(shader, 'TRIS', {"pos": points, 'color': vertex_colors}, indices=tris)
    shader.bind()
    batch.draw(shader)

def make_quad_edges(n_u, n_v):
    edges = []
    for row in range(n_v):
        e_row = [(i + n_u * row, (i+1) + n_u * row) for i in range(n_u-1)]
        edges.extend(e_row)
        if row < n_v - 1:
            e_col = [(i + n_u * row, i + n_u * (row+1)) for i in range(n_u)]
            edges.extend(e_col)
    return edges

def make_tris(n_u, n_v):
    def calc_idx(row_idx, column_idx):
        return n_u * row_idx + column_idx

    tris = []
    for row_idx in range(n_v-1):
        for column_idx in range(n_u-1):
            pt1 = calc_idx(row_idx, column_idx)
            pt2 = calc_idx(row_idx, column_idx+1)
            pt3 = calc_idx(row_idx+1, column_idx+1)
            pt4 = calc_idx(row_idx+1, column_idx)
            #tri1 = [pt1, pt2, pt3]
            #tri2 = [pt1, pt3, pt4]
            tri1 = [pt1, pt3, pt2]
            tri2 = [pt1, pt4, pt3]
            tris.append(tri1)
            tris.append(tri2)
    return tris

def vert_light_factor(vecs, polygons, light):
    return (np_dot(np_vertex_normals(vecs, polygons, output_numpy=True), light)*0.5+0.5).tolist()

def calc_surface_data(light_vector, surface_color, n_u, n_v, points):
    #points = points.reshape((n_u*n_v, 3))
    tris = make_tris(n_u, n_v)
    n_tris = len(tris)
    light_factor = vert_light_factor(points, tris, light_vector)
    colors = []
    col = surface_color
    for l_factor in light_factor:
        colors.append([col[0]*l_factor, col[1]*l_factor, col[2]*l_factor, col[3]])
    return tris, colors

class SurfaceData(object):
    def __init__(self, node, surface, resolution_u, resolution_v):
        self.node = node
        self.surface = surface
        self.resolution_u = resolution_u
        self.resolution_v = resolution_v

        u_min, u_max = surface.get_u_bounds()
        v_min, v_max = surface.get_v_bounds()
        us = np.linspace(u_min, u_max, num=resolution_u)
        vs = np.linspace(v_min, v_max, num=resolution_v)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()
        self.points = surface.evaluate_array(us, vs)#.tolist()
        self.points_list = self.points.reshape((resolution_u*resolution_v, 3)).tolist()

        if hasattr(surface, 'get_control_points'):
            self.cpts = surface.get_control_points()
            n_v, n_u, _ = self.cpts.shape
            self.cpts_list = self.cpts.reshape((n_u*n_v, 3)).tolist()
            self.control_net = make_quad_edges(n_u, n_v)

        self.edges = make_quad_edges(resolution_u, resolution_v)
        self.tris, self.tri_colors = calc_surface_data(node.light_vector, node.surface_color, resolution_u, resolution_v, self.points)

def draw_surfaces(context, args):
    node, draw_inputs, v_shader, e_shader, p_shader = args

    bgl.glEnable(bgl.GL_BLEND)

    for item in draw_inputs:

        if node.draw_surface:
            draw_polygons(p_shader, item.points_list, item.tris, item.tri_colors)

        if node.draw_edges:
            draw_edges(e_shader, item.points_list, item.edges, node.edges_line_width, node.edges_color)

        if node.draw_control_net:
            draw_edges(e_shader, item.cpts_list, item.control_net, node.control_net_line_width, node.control_net_color)

        if node.draw_control_points:
            draw_points(v_shader, item.cpts_list, node.control_points_size, node.control_points_color)

        if node.draw_verts:
            draw_points(v_shader, item.points_list, node.verts_size, node.verts_color)

    bgl.glEnable(bgl.GL_BLEND)

class SvSurfaceViewerDrawNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: preview surface
    Tooltip: drawing surfaces on 3d view
    """

    bl_idname = 'SvSurfaceViewerDrawNode'
    bl_label = 'Viewer Draw Surface'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_DRAW_VIEWER'

    resolution_u : IntProperty(
            name = "Resolution U",
            min = 1,
            default = 50,
            update = updateNode)

    resolution_v : IntProperty(
            name = "Resolution V",
            min = 1,
            default = 50,
            update = updateNode)

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode)

    draw_verts: BoolProperty(
        update=updateNode, name='Display Vertices', default=False)

    verts_color: FloatVectorProperty(
            name = "Vertices Color",
            default = (0.9, 0.9, 0.95, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    verts_size : IntProperty(
            name = "Vertices Size",
            min = 1, default = 3,
            update = updateNode)

    draw_surface : BoolProperty(
            name = "Display Surface",
            default = True,
            update = updateNode)

    surface_color: FloatVectorProperty(
            name = "Surface Color",
            default = (0.8, 0.8, 0.95, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    draw_edges : BoolProperty(
            name = "Display Edges",
            default = False,
            update = updateNode)

    edges_line_width : IntProperty(
            name = "Edges Line Width",
            min = 1, default = 1,
            update = updateNode)

    edges_color: FloatVectorProperty(
            name = "Edges Color",
            default = (0.22, 0.22, 0.27, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    draw_control_net : BoolProperty(
            name = "Display Control Net",
            default = False,
            update = updateNode)

    control_net_line_width : IntProperty(
            name = "Control Net Line Width",
            min = 1, default = 1,
            update = updateNode)

    control_net_color: FloatVectorProperty(
            name = "Control Net Color",
            default = (0.9, 0.8, 0.3, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    draw_control_points: BoolProperty(
        update=updateNode, name='Display control points', default=False)

    control_points_color: FloatVectorProperty(
            name = "Control Points Color",
            default = (1.0, 0.5, 0.1, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    control_points_size : IntProperty(
            name = "Control Points Size",
            min = 1, default = 3,
            update = updateNode)

    light_vector: FloatVectorProperty(
        name='Light Direction', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4), update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', 'Surface')
        self.inputs.new('SvStringsSocket', 'ResolutionU').prop_name = 'resolution_u'
        self.inputs.new('SvStringsSocket', 'ResolutionV').prop_name = 'resolution_v'

    def draw_buttons(self, context, layout):
        layout.prop(self, "activate", text="", icon="HIDE_" + ("OFF" if self.activate else "ON"))

        grid = layout.column(align=True)

        row = grid.row(align=True)
        row.prop(self, 'draw_verts', icon='UV_VERTEXSEL', text='')
        row.prop(self, 'verts_color', text="")
        row.prop(self, 'verts_size', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_edges', icon='UV_EDGESEL', text='')
        row.prop(self, 'edges_color', text="")
        row.prop(self, 'edges_line_width', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_surface', icon='OUTLINER_OB_SURFACE', text='')
        row.prop(self, 'surface_color', text="")

        row = grid.row(align=True)
        row.prop(self, 'draw_control_points', icon='DECORATE_KEYFRAME', text='')
        row.prop(self, 'control_points_color', text="")
        row.prop(self, 'control_points_size', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_control_net', icon='GRID', text='')
        row.prop(self, 'control_net_color', text="")
        row.prop(self, 'control_net_line_width', text="px")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'light_vector')
        self.draw_buttons(context, layout)

    def draw_all(self, draw_inputs):

        v_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        e_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        p_shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')

        draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_surfaces,
                'args': (self, draw_inputs, v_shader, e_shader, p_shader)
            }
        
        callback_enable(node_id(self), draw_data)

    def process(self):
        if bpy.app.background:
            return
        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return
        n_id = node_id(self)
        callback_disable(n_id)

        # end early
        if not self.activate:
            return

        if not self.inputs['Surface'].is_linked:
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        resolution_u_s = self.inputs['ResolutionU'].sv_get()
        resolution_v_s = self.inputs['ResolutionV'].sv_get()

        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        resolution_u_s = ensure_nesting_level(resolution_u_s, 2)
        resolution_v_s = ensure_nesting_level(resolution_v_s, 2)

        draw_inputs = []
        for params in zip_long_repeat(surfaces_s, resolution_u_s, resolution_v_s):
            for surface, resolution_u, resolution_v in zip_long_repeat(*params):
                t_surface = SvNurbsSurface.get(surface)
                if t_surface is None:
                    t_surface = surface
                draw_inputs.append(SurfaceData(self, t_surface, resolution_u, resolution_v))
        self.draw_all(draw_inputs)

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

    def sv_free(self):
        callback_disable(node_id(self))


classes = [SvSurfaceViewerDrawNode]
register, unregister = bpy.utils.register_classes_factory(classes)

