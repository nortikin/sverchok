# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi
from collections import defaultdict

import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, FloatVectorProperty, IntVectorProperty
from mathutils import Vector

import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.data_structure import updateNode, node_id
from sverchok.utils.modules.drawing_abstractions import drawing 
from sverchok.utils.modules.shader_utils import get_2d_smooth_color_shader, get_2d_uniform_color_shader
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as nvBGL
from sverchok.utils.mesh_functions import meshes_py, join_meshes, meshes_np, to_elements
from sverchok.utils.curve.bakery import curve_to_meshdata
from sverchok.utils.visualize_data_tree import nesting_circles, data_tree_lines, Line, Item
from sverchok.settings import get_params

def mesh_join(vertices, edges, polygons):
    is_py_input = isinstance(vertices[0], (list, tuple))
    meshes = (meshes_py if is_py_input else meshes_np)(vertices, edges, polygons)
    meshes = join_meshes(meshes)
    out_vertices, out_edges, out_polygons = to_elements(meshes)
    return out_vertices, out_edges, out_polygons

def curves_to_mesh(curves):
    verts = []
    edges = []
    for curve, samples in curves:
        curve_pts, curve_edges = curve_to_meshdata(curve, samples)
        verts.append(curve_pts)
        edges.append(curve_edges)
    verts, edges, _ = mesh_join(verts, edges, [])
    return verts[0], edges[0]

def background_rect(x, y, w, h, margin):
    background_coords = [
        (x, y + margin),
        (x + w + 2* margin, y + margin),
        (w + x + 2 * margin, y - h - margin),
        (x, y - h - margin)]
    background_indices = [(0, 1, 2), (0, 2, 3)]

    return background_coords, background_indices

def get_drawing_location(node):
    x, y = node.get_offset()
    return x * node.location_theta, y * node.location_theta

def create_filled_circle_geom(center, radius, samples=8):
    ts = np.linspace(0, 2*pi, num=samples)
    pts_x = radius * np.cos(ts) + center[0]
    pts_y = radius * np.sin(ts) + center[1]
    pts = np.stack((pts_x, pts_y)).T
    pts = np.insert(pts, 0, center, axis=0)
    tris = [(0, i, i+1) for i in range(1, samples)]
    tris.append((0, samples, 1))
    return pts.tolist(), tris

def create_empty_circle_geom(center, radius, samples=8):
    ts = np.linspace(0, 2*pi, num=samples)
    pts_x = radius * np.cos(ts) + center[0]
    pts_y = radius * np.sin(ts) + center[1]
    pts = np.stack((pts_x, pts_y)).T
    edges = [(i,i+1) for i in range(samples-1)]
    edges.append((samples-1, 0))
    return pts.tolist(), edges

def create_circle_batches(fill_shader, edge_shader, border_color, radius, samples=8):
    pts, tris = create_filled_circle_geom([0,0], radius, samples)
    fill_batch = batch_for_shader(fill_shader, 'TRIS', {"pos": pts}, indices=tris)
    pts, edges = create_empty_circle_geom([0,0], radius, samples)
    colors = [border_color for pt in pts]
    edge_batch = batch_for_shader(edge_shader, 'LINES', {"pos": pts, "color": colors}, indices=edges)
    return fill_batch, edge_batch

def draw_bordered(matrix, x, y, fill_shader, edge_shader, fill_batch, edge_batch, fill_color, edge_width):
    fill_shader.bind()
    fill_shader.uniform_float("color", fill_color)
    fill_shader.uniform_float("x_offset", x)
    fill_shader.uniform_float("y_offset", y)
    fill_shader.uniform_float("viewProjectionMatrix", matrix)
    fill_batch.draw(fill_shader)

    drawing.set_line_width(edge_width)
    edge_shader.bind()
    edge_shader.uniform_float("x_offset", x)
    edge_shader.uniform_float("y_offset", y)
    edge_shader.uniform_float("viewProjectionMatrix", matrix)
    edge_batch.draw(edge_shader)
    drawing.reset_line_width()
    edge_batch.draw(edge_shader)

def view_2d_geom(x, y, args):
    """
    x and y are passed by default so you could add font content
    draws the batches
    """

    geom, config = args
    matrix = gpu.matrix.get_projection_matrix()
    fill_shader = get_2d_uniform_color_shader()
    if config.draw_background:
        background_color = config.background_color
        # draw background, this could be cached......

        batch = batch_for_shader(fill_shader, 'TRIS', {"pos": geom.background_coords}, indices=geom.background_indices)
        fill_shader.bind()
        fill_shader.uniform_float("color", background_color)
        fill_shader.uniform_float("x_offset", x)
        fill_shader.uniform_float("y_offset", y)
        fill_shader.uniform_float("viewProjectionMatrix", matrix)
        batch.draw(fill_shader)

    for key in geom.curves_by_width_and_color:
        edge_width, edge_color = key
        verts, edges = geom.curves_by_width_and_color[key]
        colors = [edge_color for pt in verts]
        drawing.set_line_width(edge_width)
        config.e_batch = batch_for_shader(config.e_shader, 'LINES', {"pos": verts, "color": colors}, indices=edges)
        config.e_shader.bind()
        config.e_shader.uniform_float("x_offset", x)
        config.e_shader.uniform_float("y_offset", y)
        config.e_shader.uniform_float("viewProjectionMatrix", matrix)
        config.e_batch.draw(config.e_shader)
        drawing.reset_line_width()

    for pt_size, pt_color in geom.points_by_size_and_color:
        pts = geom.points_by_size_and_color[(pt_size, pt_color)]
        drawing.set_point_size(pt_size)
        colors = [pt_color for pt in pts]
        vert_batch = batch_for_shader(config.v_shader, 'POINTS', {"pos": pts, "color": colors})
        config.v_shader.bind()
        config.v_shader.uniform_float("x_offset", x)
        config.v_shader.uniform_float("y_offset", y)
        config.v_shader.uniform_float("viewProjectionMatrix", matrix)
        vert_batch.draw(config.v_shader)
        drawing.reset_point_size()

    for pt_size, pt_color in geom.circles_by_size_and_color:
        verts = geom.circles_by_size_and_color[(pt_size, pt_color)]
        fill_batch, edge_batch = create_circle_batches(fill_shader, config.e_shader, config.edge_color, pt_size/2)
        for vert in verts:
            draw_bordered(matrix, x+vert[0], y+vert[1], fill_shader, config.e_shader, fill_batch, edge_batch, pt_color, config.edge_width)

def generate_graph_geom(config, data_curves, data_circles, data_items, nest_pts, dash_pts):

    geom = lambda: None
    x, y = config.loc
    scale = config.scale
    sys_scale = config.sys_scale

    data_curve_pts, data_curve_edges = curves_to_mesh(data_curves)
    data_circle_pts, data_circle_edges = curves_to_mesh(data_circles)

    all_vecs = np.array(data_curve_pts + data_circle_pts)
    maxmin = np.stack((all_vecs.max(axis=0), all_vecs.min(axis=0))).T
    axis1, axis2 = 0,1
    # background geom
    orig_size_x = maxmin[axis1][0]- maxmin[axis1][1]
    orig_size_y = maxmin[axis2][0]- maxmin[axis2][1]
    max_size = min([orig_size_x, orig_size_y])
    w = orig_size_x * scale / max_size
    h = orig_size_y * scale / max_size
    #w, h = scale, scale
    margin = 10 * sys_scale
    geom.background_coords, geom.background_indices = background_rect(x, y, w, h, margin)
    _x = x + margin

    data_curve_pts = transformed_verts(data_curve_pts, _x, y, maxmin, scale)
    data_circle_pts = transformed_verts(data_circle_pts, _x, y, maxmin, scale)

    geom.circles_by_size_and_color = dict()
    geom.circles_by_size_and_color[(config.point_size, config.point_color)] = transformed_verts(nest_pts, _x, y, maxmin, scale)
    center_pts = [(0,0,0)]
    geom.circles_by_size_and_color[(config.center_size, config.center_color)] = transformed_verts(center_pts, _x, y, maxmin, scale)

    geom.points_by_size_and_color = dict()
    geom.points_by_size_and_color[(config.dash_width, config.edge_color)] = transformed_verts(dash_pts, _x, y, maxmin, scale)

    data_items_by_color = defaultdict(list)
    for item in data_items:
        data_items_by_color[item.color].append(item.point)

    for color in data_items_by_color:
        verts = data_items_by_color[color]
        geom.circles_by_size_and_color[(config.point_size, item.color)] = transformed_verts(verts, _x, y, maxmin, scale)

    geom.curves_by_width_and_color = dict()
    if config.draw_circles:
        geom.curves_by_width_and_color[(config.circle_width, config.circle_color)] = (data_circle_pts, data_circle_edges)
    geom.curves_by_width_and_color[(config.edge_width, config.edge_color)] = (data_curve_pts, data_curve_edges)

    config.e_shader = get_2d_smooth_color_shader()
    config.v_shader = config.e_shader # get_2d_smooth_color_shader()

    return geom

def transformed_verts(vecs, x, y, maxmin, scale, axis1=0, axis2=1):
    if not vecs:
        return []
    vecs = np.array(vecs)
    size_x = maxmin[axis1][0] - maxmin[axis1][1]
    size_y = maxmin[axis2][0] - maxmin[axis2][1]
    vecs[:,0] = x + (vecs[:,0] - maxmin[axis1][1]) * scale / size_x
    vecs[:,1] = y + (vecs[:,1] - maxmin[axis2][0]) * scale / size_y
    return vecs.tolist()

class SvDataTreeVizNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Data Tree
    Tooltip: Render data tree shape in the node view
    """
    bl_idname = 'SvDataTreeVizNode'
    bl_label = 'Data Tree Viz'
    bl_icon = 'NODETREE'

    activate: BoolProperty(
        name='Show',
        description='Activate drawing',
        default=True,
        update=updateNode
    )

    allow_skip: BoolProperty(
        name='Simplify',
        description='Allow to skip drawing of some items if they are too small to be drawn',
        default=True,
        update=updateNode
    )

    draw_scale: FloatProperty(
        min=10.0,
        default=250.0,
        name="Size",
        description="Drawing scale",
        update=updateNode,
    )

    drawing_size: IntVectorProperty(
        update=updateNode, name="Size", default=(150, 150), size=2
    )

    point_color: FloatVectorProperty(
        update=updateNode,
        name="Branching points color",
        default=(0.0, 0.57, 0.02, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    point_size: IntProperty(
        min=1, default=4, name="Points size", description="Point size", update=updateNode
    )

    edge_width: IntProperty(
        min=1, default=1, name="Branch line thickness", update=updateNode
    )

    curve_samples: IntProperty(
        min=2, default=25, name='Samples',
        description='Branch curve resolution', update=updateNode
    )

    edge_color: FloatVectorProperty(
        update=updateNode,
        name="Branch line color",
        default=(0.0, 0.01, 0.15, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    background_color: FloatVectorProperty(
        update=updateNode,
        name="Background color",
        default=(0.83, 0.83, 0.83, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    draw_background: BoolProperty(
        update=updateNode, name="Display background", default=True
    )

    draw_circles: BoolProperty(
        name = "Draw circles",
        description = "Display nesting level circles",
        default = True,
        update=updateNode
    )

    circle_color: FloatVectorProperty(
        update=updateNode,
        name="Circles color",
        default=(0.87, 0.89, 0.85, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    circle_width: IntProperty(
        min=1, default=2, name="Circles thickness", update=updateNode
    )

    location_theta: FloatProperty(name="location theta", default=1.0)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "curve_samples")

    def draw_buttons(self, context, layout):
        r0 = layout.row()
        r0.prop(self, "activate", text="Active", icon="HIDE_" + ("OFF" if self.activate else "ON"))
        layout.prop(self, "allow_skip")

        c0 = layout.column(align=True)
        row = c0.row(align=True)
        row.prop(self, "point_color", text='')
        row.prop(self, "point_size")

        row = c0.row(align=True)
        row.prop(self, "edge_color", text='')
        row.prop(self, "edge_width")

        row = c0.row(align=True)
        row.prop(self, "draw_circles", text='', icon='MESH_CIRCLE')
        if self.draw_circles:
            row.prop(self, "circle_color", text='')
            row.prop(self, "circle_width", text='')

        row = c0.row(align=True)
        row.prop(self, "draw_background", text='', icon='WORLD')
        if self.draw_background:
            row.prop(self, "background_color", text='')

        row = c0.row(align=True)
        c0.prop(self, "draw_scale")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.id_data.update_gl_scale_info()

    def get_drawing_attributes(self):
        """ obtain the dpi adjusted xy and scale factors, cache location_theta """
        scale, multiplier = get_params({
            'render_scale': 1.0, 'render_location_xy_multiplier': 1.0}, direct=True)
        self.location_theta = multiplier
        return scale

    def get_offset(self):
        return [int(j) for j in (Vector(self.absolute_location) + Vector((self.width + 20, 0)))[:]]

    def create_config(self):
        config = lambda: None
        scale = self.get_drawing_attributes()
        scale = 1.0
        margin = 10* scale
        config.loc = (0, 0 - margin)
        config.sys_scale = scale
        config.scale = scale * self.draw_scale
        config.background_color = self.background_color
        config.draw_background = self.draw_background
        config.edge_width = self.edge_width
        config.point_color = self.point_color
        config.point_size = self.point_size
        config.dash_width = 2
        config.center_size = 2*config.point_size
        config.center_color = (1.0, 0.5, 0.0, 1.0)
        config.edge_color = self.edge_color
        config.draw_circles = self.draw_circles
        config.circle_width = self.circle_width
        config.circle_color = self.circle_color

        return config

    def process(self):
        n_id = node_id(self)
        nvBGL.callback_disable(n_id)

        if not self.activate:
            return
        if not self.inputs['Data'].is_linked:
            return

        data_in = self.inputs['Data'].sv_get()

        max_level, data_lines = data_tree_lines(1.0, data_in, allow_skip = self.allow_skip)

        nest_pts = [(0,0,0)]
        dash_pts = []
        data_curves = []
        data_items = []
        for item in data_lines:
            if isinstance(item, Line):
                curve = item.curve
                if item.skip:
                    t1, t2 = curve.get_u_bounds()
                    ts = np.linspace(t1, t2, num=self.curve_samples)
                    pts = curve.evaluate_array(ts)
                    dash_pts.extend(pts.tolist())
                else:
                    t2 = curve.get_u_bounds()[1]
                    pt = curve.evaluate(t2)
                    nest_pts.append(pt)
                    data_curves.append((curve, self.curve_samples))
            elif isinstance(item, Item):
                data_items.append(item)
        
        circles = nesting_circles(1.0, max_level)
        data_circles = [(circle, self.curve_samples*12) for circle in circles]

        config = self.create_config()

        geom = generate_graph_geom(config, data_curves, data_circles, data_items, nest_pts, dash_pts)

        draw_data = {
            'mode': 'custom_function',
            'tree_name': self.id_data.name[:],
            'node_name': self.name[:],
            'loc': get_drawing_location,
            'custom_function': view_2d_geom,
            'args': (geom, config)
        }
        nvBGL.callback_enable(n_id, draw_data)

    def sv_free(self):
        nvBGL.callback_disable(node_id(self))

classes = [SvDataTreeVizNode,]
register, unregister = bpy.utils.register_classes_factory(classes)

