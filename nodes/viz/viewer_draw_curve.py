# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Matrix, Vector
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatVectorProperty, FloatProperty

import gpu
from gpu_extras.batch import batch_for_shader
from types import SimpleNamespace

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, get_data_nesting_level, ensure_nesting_level, zip_long_repeat, node_id
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.bakery import CurveData
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_3dview_tools import Sv3DviewAlign
from sverchok.utils.modules.drawing_abstractions import drawing, shading_3d
from sverchok.utils.sv_idx_viewer28_draw import draw_indices_2D_wbg, TextInfo
from sverchok.utils.curve.nurbs import SvGeomdlCurve, SvNativeNurbsCurve, SvNurbsBasisFunctions, SvNurbsCurve

def draw_edges(shader, points, edges, line_width, color, is_smooth=False):
    if is_smooth:
        draw_edges_colored(shader, points, edges, line_width, [color for i in range(len(points))])
    else:
        drawing.set_line_width(line_width)
        batch = batch_for_shader(shader, 'LINES', {"pos": points}, indices=edges)
        shader.bind()
        shader.uniform_float('color', color)
        batch.draw(shader)
        drawing.reset_line_width()

def draw_arrows(shader, tips, pts1, pts2, line_width, color):
    n = len(tips)
    points = np.concatenate((tips, pts1, pts2))
    edges = [(i, i+n) for i in range(n-1)]
    edges.extend([(i, i+2*n) for i in range(n-1)])
    drawing.set_line_width(line_width)
    batch = batch_for_shader(shader, 'LINES', {"pos": points.tolist()}, indices=edges)
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    drawing.reset_line_width()

def draw_edges_colored(shader, points, edges, line_width, colors):
    drawing.set_line_width(line_width)
    batch = batch_for_shader(shader, 'LINES', {"pos": points, "color": colors}, indices=edges)
    shader.bind()
    batch.draw(shader)
    drawing.reset_line_width()

def draw_points(shader, points, size, color):
    drawing.set_point_size(size)
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    drawing.reset_point_size()

def draw_points_colored(shader, points, size, colors):
    drawing.set_point_size(size)
    batch = batch_for_shader(shader, 'POINTS', {"pos": points, "color": colors})
    shader.bind()
    batch.draw(shader)
    drawing.reset_point_size()

def draw_curves(context, args):
    node, draw_inputs, v_shader, e_shader = args
    is_smooth = node.draw_curvature

    drawing.enable_blendmode()

    for obj in draw_inputs:
        for item in obj:

            if node.draw_line:
                if node.draw_curvature and item.curvature_point_colors is not None:
                    colors = item.curvature_point_colors.tolist()
                    draw_edges_colored(e_shader, item.points, item.edges, node.line_width, colors)
                elif item.edges is not None:
                    draw_edges(e_shader, item.points, item.edges, node.line_width, node.line_color, is_smooth)

            if node.draw_control_polygon and item.control_points is not None:
                draw_edges(e_shader, item.control_points, item.control_polygon_edges, node.control_polygon_line_width, node.control_polygon_color, is_smooth)

            if node.draw_control_points and item.control_points is not None:
                draw_points(v_shader, item.control_points, node.control_points_size, node.control_points_color)

            if node.draw_nodes and item.node_points is not None:
                draw_points(v_shader, item.node_points, node.nodes_size, node.nodes_color)

            if node.draw_comb and item.comb_edges is not None:
                draw_edges(e_shader, item.comb_points, item.comb_edges, node.comb_width, node.comb_color, is_smooth)

            if node.draw_verts and item.points is not None:
                draw_points(v_shader, item.points, node.verts_size, node.verts_color)

            if node.draw_arrows and item.arrow_pts1 is not None and item.arrow_pts2 is not None:
                draw_arrows(e_shader, item.np_points[1:], item.arrow_pts1, item.arrow_pts2, node.arrows_line_width, node.arrows_color)

    drawing.enable_blendmode()

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

    draw_arrows : BoolProperty(
            name = "Display arrows",
            default = False,
            update = updateNode)

    arrows_line_width : IntProperty(
            name = "Arrows Line Width",
            min = 1, default = 1,
            update = updateNode)

    arrows_color : FloatVectorProperty(
            name = "Arrows Color",
            default = (0.5, 0.8, 1.0, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    draw_control_points: BoolProperty(
        update=updateNode, name='Display control points', default=False)

    def make_color_prop(name, col):
        return FloatVectorProperty(
            name=name, description='', size=4, min=0.0, max=1.0,
            default=col, subtype='COLOR', update=updateNode)

    draw_control_points_background: BoolProperty(update=updateNode, name='Display control points indexes background', default=False)
    draw_control_points_indexes: BoolProperty(update=updateNode, name='Display control points indexes', default=False)
    control_points_indexes_fg: make_color_prop("Control Point Color", (0.6, 1, 0.3, 1.0))
    control_points_indexes_bg: make_color_prop("Control Point Background Color", (.2, .2, .2, 1.0))
    draw_segments_indexes: BoolProperty(update=updateNode, name='Display segments indexes', default=False)
    segments_indexes_fg: make_color_prop("Segments indexes Color", (1.0, 1.0, 0.349, 1.0))
    segments_indexes_bg: make_color_prop("Segments indexes Background Color", (.2, .2, .2, 1.0))
    control_points_indexes_scale: FloatProperty(default=1.0, name='Font scale', min=0.1, update=updateNode)

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

    draw_comb: BoolProperty(
        update=updateNode, name='Display curvature comb', default=False)

    comb_color: FloatVectorProperty(
            name = "Comb Color",
            default = (1.0, 0.9, 0.1, 0.5),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    comb_width : IntProperty(
            name = "Comb Line Width",
            min = 1, default = 1,
            update = updateNode)

    comb_scale : FloatProperty(
            name = "Comb Scale",
            min = 0.0, default = 1.0,
            update = updateNode)

    draw_curvature: BoolProperty(
        update=updateNode, name='Indicate Curvature', default=False)

    curvature_color : FloatVectorProperty(
            name = "Curvature Color",
            default = (1.0, 0.1, 0.1, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
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
        row.prop(self, 'draw_arrows', icon='FORWARD', text='')
        row.prop(self, 'arrows_color', text='')
        row.prop(self, 'arrows_line_width', text='px')

        row = grid.row(align=True)
        row.prop(self, 'draw_control_points', icon='DECORATE_KEYFRAME', text='')
        row.prop(self, 'control_points_color', text="")
        row.prop(self, 'control_points_size', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_control_points_indexes', icon='VERTEXSEL', text='')
        elem = row.split(factor=0.5, align=True)
        elem.prop(self, 'control_points_indexes_fg', text="")
        elem1 = elem.split(factor=0.7, align=True)
        elem1.prop(self, 'control_points_indexes_bg', text="")
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.draw_control_points_background else 'ON')
        elem1.column().prop(self, 'draw_control_points_background', text="", toggle=True, icon=view_icon)

        row = grid.row(align=True)
        row.prop(self, 'draw_segments_indexes', icon='EDGESEL', text='')
        elem = row.split(factor=0.5, align=True)
        elem.prop(self, 'segments_indexes_fg', text="")
        elem.prop(self, 'segments_indexes_bg', text="")


        row = grid.row(align=True)
        row.prop(self, 'draw_control_polygon', icon='SNAP_EDGE', text='')
        row.prop(self, 'control_polygon_color', text="")
        row.prop(self, 'control_polygon_line_width', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_nodes', text="", icon='EVENT_N')
        row.prop(self, 'nodes_color', text="")
        row.prop(self, 'nodes_size', text="px")

        row = grid.row(align=True)
        row.prop(self, 'draw_comb', text="", icon='EVENT_C')
        row.prop(self, 'comb_color', text="")
        row.prop(self, 'comb_width', text="px")

        if self.draw_comb:
            layout.prop(self, 'comb_scale', text='Scale')

        row = layout.row(align=True)
        row.prop(self, 'draw_curvature', text="", icon='EVENT_G')
        row.prop(self, 'curvature_color', text="")

        row = layout.row(align=True)
        row.scale_y = 4.0 if self.prefs_over_sized_buttons else 1
        self.wrapper_tracked_ui_draw_op(row, SvBakeCurveOp.bl_idname, icon='OUTLINER_OB_MESH', text="B A K E")
        row.separator()
        self.wrapper_tracked_ui_draw_op(row, Sv3DviewAlign.bl_idname, icon='CURSOR', text='')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "control_points_indexes_scale", icon="PLUGIN")
        pass

    # from nodes\viz\viewer_idx28.py
    def get_settings_dict(self):
        '''Produce a dict of settings for the callback'''
        # A copy is needed, we can't have reference to the
        # node in a callback, it will crash blender on undo
        return {
            'bg_edges_col'      : self.segments_indexes_bg[:], #self.bg_edges_col[:],
            'bg_faces_col'      : (.2, .2, .2, 1.0), #self.bg_faces_col[:],
            'bg_verts_col'      : self.control_points_indexes_bg[:],
            'numid_edges_col'   : self.segments_indexes_fg[:], #self.numid_edges_col[:],
            'numid_faces_col'   : (1.0, .8, .8, 1.0), #self.numid_faces_col[:],
            'numid_verts_col'   : self.control_points_indexes_fg[:], #self.numid_verts_col[:],
            'display_vert_index': self.draw_control_points_indexes, #.display_vert_index,
            'display_edge_index': self.draw_segments_indexes, #self.display_edge_index,
            'display_face_index': False, #self.display_face_index,
            'text_mode': 'INDEX_ONLY',
            'draw_obj_idx': True, #self.draw_obj_idx,
            'draw_bface': True, #self.draw_bface,
            'draw_bg': self.draw_control_points_background, #self.draw_bg,
            'scale': self.control_points_indexes_scale, #self.get_scale()
        }.copy()

    def bake(self, context):
        with context.temp_override(node=self):
                    bpy.ops.node.sverchok_curve_baker()

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', 'Curve')
        self.inputs.new('SvStringsSocket', 'Resolution').prop_name = 'resolution'

    def draw_all(self, draw_inputs):
        v_shader = gpu.shader.from_builtin(shading_3d.UNIFORM_COLOR)
        if self.draw_curvature:
            e_shader = gpu.shader.from_builtin(shading_3d.SMOOTH_COLOR)
        else:
            e_shader = gpu.shader.from_builtin(shading_3d.UNIFORM_COLOR)

        draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_curves,
                'args': (self, draw_inputs, v_shader, e_shader)
            }
        
        callback_enable(node_id(self), draw_data)

        if self.draw_control_points_indexes or self.draw_segments_indexes:
            config = self.get_settings_dict()
            geom = SimpleNamespace( **dict(vert_data=[], edge_data=[], face_data=[], text_data=[], verts=[], edges=[], faces=[],) )

            for I, obj in enumerate(draw_inputs):
                for IJ, curve_data in enumerate(obj):
                    if curve_data.control_points is not None:
                        vert_data = [(Vector(p)) for IJ, p in enumerate(curve_data.control_points) if IJ%3==0]
                        verts_info = [ TextInfo('', f'{IJ}/{I}', IJK, p) for IJK, p in enumerate(vert_data)]
                        # combine first and last indexes if curve is cyclic
                        if curve_data.curve.is_closed()==True and len(verts_info)>1:
                            verts_info.pop(0)
                            verts_info[-1].index = "0-"+str(verts_info[-1].index)
                        geom.vert_data.append( verts_info )
                        # calculate of segments points
                        if curve_data.curve.is_bezier():
                            lbs = curve_data.curve.to_bezier_segments()
                            edges_info = []
                            for IJK, bs in enumerate(lbs):
                                t_min, t_max = bs.get_u_bounds()
                                t_mid = (t_max-t_min)/2.0
                                mid_point = bs.evaluate(t_mid)
                                edges_info.append( TextInfo('', f'{IJ}/{I}', IJK, Vector(mid_point)) )
                                pass
                            geom.edge_data.append(edges_info)
                        

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_indices_2D_wbg,
                'args': (geom, config)}

            callback_enable(node_id(self)+'_2D', draw_data, overlay='POST_PIXEL')

    def get_curve_data(self):
        curves_s = self.inputs['Curve'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        if get_data_nesting_level(curves_s, data_types=(SvCurve,))==3:
            _curves = []
            for obj in curves_s:
                _obj = []
                for curve in obj:
                    _obj.extend( curve )
                _curves.append(_obj)
            curves_s = _curves
            pass
        else:
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        resolution_s = ensure_nesting_level(resolution_s, 2)

        draw_inputs = []
        for params in zip_long_repeat(curves_s, resolution_s):
            _obj = []
            for curve, resolution in zip_long_repeat(*params):
                t_curve = curve
                _obj.append(CurveData(self, t_curve, resolution))
            draw_inputs.append(_obj)
        return draw_inputs

    def process(self):
        if bpy.app.background:
            return
        n_id = node_id(self)
        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            callback_disable(n_id+'_2D')
            return
        callback_disable(n_id)
        callback_disable(n_id+'_2D')

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
                callback_disable(node_id(self)+'_2D')

    def sv_free(self):
        callback_disable(node_id(self))
        callback_disable(node_id(self)+'_2D')

    def toggle_viewer(self, context):
        self.activate = not self.activate

classes = [SvCurveViewerDrawNode, SvBakeCurveOp]
register, unregister = bpy.utils.register_classes_factory(classes)

