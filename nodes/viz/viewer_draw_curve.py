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
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.bakery import CurveData
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
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

def draw_curves(context, args):
    node, draw_inputs, v_shader, e_shader = args

    bgl.glEnable(bgl.GL_BLEND)

    for item in draw_inputs:

        if node.draw_line:
            draw_edges(e_shader, item.points, item.edges, node.line_width, node.line_color)

        if node.draw_control_polygon and item.control_points is not None:
            draw_edges(e_shader, item.control_points, item.control_polygon_edges, node.control_polygon_line_width, node.control_polygon_color)

        if node.draw_control_points and item.control_points is not None:
            draw_points(v_shader, item.control_points, node.control_points_size, node.control_points_color)

        if node.draw_nodes and item.node_points is not None:
            draw_points(v_shader, item.node_points, node.nodes_size, node.nodes_color)

        if node.draw_verts:
            draw_points(v_shader, item.points, node.verts_size, node.verts_color)

    bgl.glEnable(bgl.GL_BLEND)

class SvBakeCurveOp(bpy.types.Operator, SvGenericNodeLocator):
    """B A K E CURVES"""
    bl_idname = "node.sverchok_curve_baker"
    bl_label = "Bake Curves"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def sv_execute(self, context, node):
        curve_data = node.get_curve_data()
        for i, item in enumerate(curve_data):
            item.bake(f"Sv_Curve_{i}")
        return {'FINISHED'}

class SvCurveViewerDrawNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: preview curve
    Tooltip: Drawing curves on 3D view\n\tIn: Curve, Resolution\n\tParams: Display/Color/Size for Vertices, Edges, Curve Line, Control Points, Control Polygons, Curve Nodes
    """

    bl_idname = 'SvCurveViewerDrawNode'
    bl_label = 'Viewer Draw Curve'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_DRAW_VIEWER'

    resolution : IntProperty(
            name = "Resolution",
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

    draw_line: BoolProperty(
        update=updateNode, name='Display curve line', default=True)

    line_color: FloatVectorProperty(
            name = "Line Color",
            default = (0.5, 0.8, 1.0, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    line_width : IntProperty(
            name = "Line Width",
            min = 1, default = 2,
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

    draw_control_polygon: BoolProperty(
        update=updateNode, name='Display control polygon', default=False)

    control_polygon_color: FloatVectorProperty(
            name = "Control Polygon Color",
            default = (0.9, 0.8, 0.3, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    control_polygon_line_width : IntProperty(
            name = "Control Polygon Lines Width",
            min = 1, default = 1,
            update = updateNode)

    draw_nodes: BoolProperty(
        update=updateNode, name='Display curve nodes', default=False)

    nodes_color: FloatVectorProperty(
            name = "Nodes Color",
            default = (0.1, 0.1, 0.3, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    nodes_size : IntProperty(
            name = "Node Points Size",
            min = 1, default = 3,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "activate", icon="HIDE_" + ("OFF" if self.activate else "ON"))

        grid = layout.column(align=True)

        row = grid.row(align=True)
        row.prop(self, 'draw_verts', icon='SNAP_MIDPOINT', text='')
        row.prop(self, 'verts_color', text="")
        row.prop(self, 'verts_size', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_line', icon='MOD_CURVE', text='')
        row.prop(self, 'line_color', text="")
        row.prop(self, 'line_width', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_control_points', icon='DECORATE_KEYFRAME', text='')
        row.prop(self, 'control_points_color', text="")
        row.prop(self, 'control_points_size', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_control_polygon', icon='SNAP_EDGE', text='')
        row.prop(self, 'control_polygon_color', text="")
        row.prop(self, 'control_polygon_line_width', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_nodes', text="", icon='EVENT_N')
        row.prop(self, 'nodes_color', text="")
        row.prop(self, 'nodes_size', text="px")

        row = layout.row(align=True)
        row.scale_y = 4.0 if self.prefs_over_sized_buttons else 1
        self.wrapper_tracked_ui_draw_op(row, SvBakeCurveOp.bl_idname, icon='OUTLINER_OB_MESH', text="B A K E")
        row.separator()
        self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Curve')
        self.inputs.new('SvStringsSocket', 'Resolution').prop_name = 'resolution'

    def draw_all(self, draw_inputs):

        v_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        e_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

        draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_curves,
                'args': (self, draw_inputs, v_shader, e_shader)
            }
        
        callback_enable(node_id(self), draw_data)

    def get_curve_data(self):
        curves_s = self.inputs['Curve'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        resolution_s = ensure_nesting_level(resolution_s, 2)

        draw_inputs = []
        for params in zip_long_repeat(curves_s, resolution_s):
            for curve, resolution in zip_long_repeat(*params):
                t_curve = SvNurbsCurve.to_nurbs(curve)
                if t_curve is None:
                    t_curve = curve
                draw_inputs.append(CurveData(self, t_curve, resolution))
        return draw_inputs

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

        if not self.inputs['Curve'].is_linked:
            return

        draw_inputs = self.get_curve_data()
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

classes = [SvCurveViewerDrawNode, SvBakeCurveOp]
register, unregister = bpy.utils.register_classes_factory(classes)

