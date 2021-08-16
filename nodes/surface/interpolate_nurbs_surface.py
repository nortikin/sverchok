
import numpy as np

import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, split_by_count
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.surface.nurbs import SvGeomdlSurface, interpolate_nurbs_surface
from sverchok.utils.math import supported_metrics
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import fitting
    
class SvExInterpolateNurbsSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Surface Interpolate
    Tooltip: Interpolate NURBS Surface
    """
    bl_idname = 'SvExInterpolateNurbsSurfaceNode'
    bl_label = 'Interpolate NURBS Surface'
    bl_icon = 'SURFACE_NSURFACE'

    input_modes = [
            ('1D', "Single list", "List of all control points (concatenated)", 1),
            ('2D', "Separated lists", "List of lists of control points", 2)
        ]

    def update_sockets(self, context):
        self.inputs['USize'].hide_safe = self.input_mode == '2D'
        updateNode(self, context)

    input_mode : EnumProperty(
            name = "Input mode",
            default = '1D',
            items = input_modes,
            update = update_sockets)

    u_size : IntProperty(
            name = "U Size",
            default = 5,
            min = 3,
            update = updateNode)

    degree_u : IntProperty(
            name = "Degree U",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    degree_v : IntProperty(
            name = "Degree V",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            default = False,
            update = updateNode)

    metric : EnumProperty(
            name = "Metric",
            description = "Metric to be used for interpolation",
            items = supported_metrics,
            default = 'DISTANCE',
            update = updateNode)

    def get_implementations(self, context):
        items = []
        i = 0
        if geomdl is not None:
            item = (SvNurbsMaths.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation",i)
            i += 1
            items.append(item)
        item = (SvNurbsMaths.NATIVE, "Sverchok", "Sverchok built-in implementation", i)
        items.append(item)
        return items

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "USize").prop_name = 'u_size'
        self.inputs.new('SvStringsSocket', "DegreeU").prop_name = 'degree_u'
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "KnotsU")
        self.outputs.new('SvStringsSocket', "KnotsV")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')
        if self.nurbs_implementation == SvNurbsMaths.GEOMDL:
            layout.prop(self, 'centripetal')
        else:
            layout.prop(self, 'metric')
        layout.prop(self, "input_mode")

    def process(self):
        vertices_s = self.inputs['Vertices'].sv_get()
        u_size_s = self.inputs['USize'].sv_get()
        degree_u_s = self.inputs['DegreeU'].sv_get()
        degree_v_s = self.inputs['DegreeV'].sv_get()

        if self.input_mode == '1D':
            vertices_s = ensure_nesting_level(vertices_s, 3)
        else:
            vertices_s = ensure_nesting_level(vertices_s, 4)
        
        surfaces_out = []
        points_out = []
        knots_u_out = []
        knots_v_out = []
        for vertices, degree_u, degree_v, u_size in zip_long_repeat(vertices_s, degree_u_s, degree_v_s, u_size_s):
            if isinstance(degree_u, (tuple, list)):
                degree_u = degree_u[0]
            if isinstance(degree_v, (tuple, list)):
                degree_v = degree_v[0]
            if isinstance(u_size, (tuple, list)):
                u_size = u_size[0]

            if self.input_mode == '1D':
                n_u = u_size
                n_v = len(vertices) // n_u
            else:
                n_u = len(vertices[0])
                for i, verts_i in enumerate(vertices):
                    if len(verts_i) != n_u:
                        raise Exception("Number of vertices in row #{} is not the same as in the first ({} != {})!".format(i, n_u, len(verts_i)))
                vertices = sum(vertices, [])
                n_v = len(vertices) // n_u

            if geomdl is not None and self.nurbs_implementation == SvNurbsMaths.GEOMDL:
                surf = fitting.interpolate_surface(vertices, n_u, n_v, degree_u, degree_v, centripetal=self.centripetal)
                surf = SvGeomdlSurface(surf)
            else:
                vertices_np = np.array(split_by_count(vertices, n_v))
                vertices_np = np.transpose(vertices_np, axes=(1,0,2))
                surf = interpolate_nurbs_surface(degree_u, degree_v, vertices_np, metric=self.metric)

            points_out.append(surf.get_control_points().tolist())
            knots_u_out.append(surf.get_knotvector_u().tolist())
            knots_v_out.append(surf.get_knotvector_v().tolist())
            surfaces_out.append(surf)

        self.outputs['Surface'].sv_set(surfaces_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['KnotsU'].sv_set(knots_u_out)
        self.outputs['KnotsV'].sv_set(knots_v_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExInterpolateNurbsSurfaceNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExInterpolateNurbsSurfaceNode)

