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
import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, get_data_nesting_level, ensure_nesting_level, zip_long_repeat, node_id
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.surface.bakery import SurfaceData
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_3dview_tools import Sv3DviewAlign
from sverchok.utils.modules.drawing_abstractions import drawing, shading_3d


def draw_edges(shader, points, edges, line_width, color):
    drawing.set_line_width(line_width)
    batch = batch_for_shader(shader, 'LINES', {"pos": points}, indices=edges)
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    drawing.reset_line_width()

def draw_points(shader, points, size, color):
    drawing.set_point_size(size)
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
    drawing.reset_point_size()

def draw_polygons(shader, points, tris, vertex_colors):
    batch = batch_for_shader(shader, 'TRIS', {"pos": points, 'color': vertex_colors}, indices=tris)
    shader.bind()
    batch.draw(shader)

def draw_surfaces(context, args):
    node, draw_inputs, v_shader, e_shader, p_shader = args

    drawing.enable_blendmode()

    for item in draw_inputs:

        if node.draw_surface:
            draw_polygons(p_shader, item.points_list, item.tris, item.tri_colors)

        if node.draw_edges:
            draw_edges(e_shader, item.points_list, item.edges, node.edges_line_width, node.edges_color)

        if node.draw_node_lines and item.node_u_isoline_data is not None:
            for line in item.node_u_isoline_data:
                draw_edges(e_shader, line.points, line.edges, node.node_lines_width, node.node_lines_color)
            for line in item.node_v_isoline_data:
                draw_edges(e_shader, line.points, line.edges, node.node_lines_width, node.node_lines_color)

        if node.draw_control_net and item.cpts_list is not None:
            draw_edges(e_shader, item.cpts_list, item.control_net, node.control_net_line_width, node.control_net_color)

        if node.draw_control_points and item.cpts_list is not None:
            draw_points(v_shader, item.cpts_list, node.control_points_size, node.control_points_color)

        if node.draw_verts:
            draw_points(v_shader, item.points_list, node.verts_size, node.verts_color)

    drawing.disable_blendmode()

class SvBakeSurfaceOp(bpy.types.Operator, SvGenericNodeLocator):
    """B A K E SURFACES"""
    bl_idname = "node.sverchok_surface_baker"
    bl_label = "Bake Surfaces"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def sv_execute(self, context, node):
        surface_data = node.get_surface_data()
        for i, item in enumerate(surface_data):
            item.bake(f"Sv_Surface_{i}")
        return {'FINISHED'}

class SvSurfaceViewerDrawNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: preview surface
    Tooltip: Drawing surfaces on 3D view.\n\tIn: Surface, Resolution U/V\n\tParams: Display/Color/Size for Vertices, Edges, Surface, Control Points, Control Net
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

    draw_node_lines : BoolProperty(
            name = "Display node lines",
            default = False,
            update = updateNode)

    node_lines_color: FloatVectorProperty(
            name = "Node Lines Color",
            default = (0.2, 0.0, 0.0, 1.0),
            size = 4, min = 0.0, max = 1.0,
            subtype = 'COLOR',
            update = updateNode)

    node_lines_width : IntProperty(
            name = "Node Lines Width",
            min = 1, default = 2,
            update = updateNode)

    light_vector: FloatVectorProperty(
        name='Light Direction', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4), update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', 'Surface')
        self.inputs.new('SvStringsSocket', 'ResolutionU').prop_name = 'resolution_u'
        self.inputs.new('SvStringsSocket', 'ResolutionV').prop_name = 'resolution_v'

    def draw_buttons(self, context, layout):
        layout.prop(self, "activate", icon="HIDE_" + ("OFF" if self.activate else "ON"))

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

        row = grid.row(align=True)
        row.prop(self, 'draw_node_lines', icon='EVENT_N', text='')
        row.prop(self, 'node_lines_color', text="")
        row.prop(self, 'node_lines_width', text="px")

        row = layout.row(align=True)
        row.scale_y = 4.0 if self.prefs_over_sized_buttons else 1
        self.wrapper_tracked_ui_draw_op(row, SvBakeSurfaceOp.bl_idname, icon='OUTLINER_OB_MESH', text="B A K E")
        row.separator()
        self.wrapper_tracked_ui_draw_op(row, Sv3DviewAlign.bl_idname, icon='CURSOR', text='')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'light_vector')
        self.draw_buttons(context, layout)

    def draw_all(self, draw_inputs):
        v_shader = gpu.shader.from_builtin(shading_3d.UNIFORM_COLOR)
        e_shader = gpu.shader.from_builtin(shading_3d.UNIFORM_COLOR)
        p_shader = gpu.shader.from_builtin(shading_3d.SMOOTH_COLOR)

        draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_surfaces,
                'args': (self, draw_inputs, v_shader, e_shader, p_shader)
            }
        
        callback_enable(node_id(self), draw_data)

    def get_surface_data(self):
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

        if not self.inputs['Surface'].is_linked:
            return

        draw_inputs = self.get_surface_data()
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


classes = [SvSurfaceViewerDrawNode, SvBakeSurfaceOp]
register, unregister = bpy.utils.register_classes_factory(classes)

