import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.surface import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface

class SvDeconstructSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Deconstruct Surface
    Tooltip: Output degrees, control points, weights, knot vectors of the surface (when they are defined)
    """
    bl_idname = 'SvDeconstructSurfaceNode'
    bl_label = 'Deconstruct Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DECONSTRUCT_CURVE'

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvStringsSocket', "DegreeU")
        self.outputs.new('SvStringsSocket', "DegreeV")
        self.outputs.new('SvStringsSocket', "KnotVectorU")
        self.outputs.new('SvStringsSocket', "KnotVectorV")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Weights")

    split_points : BoolProperty(
            name = "Split by row",
            description = "Split lists of control points and weights by row",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'split_points')

    def deconstruct(self, surface):
        nurbs = SvNurbsSurface.get(surface)
        if nurbs is None:
            nurbs = surface

        try:
            degree_u = nurbs.get_degree_u()
            degree_v = nurbs.get_degree_v()
        except:
            degree_u = None
            degree_v = None

        if hasattr(nurbs, 'get_knotvector_u'):
            knots_u = nurbs.get_knotvector_u().tolist()
            knots_v = nurbs.get_knotvector_v().tolist()
        else:
            knots_u = []
            knots_v = []

        try:
            points = nurbs.get_control_points()
            n_u,n_v,_ = points.shape
            if self.split_points:
                points = points.tolist()
            else:
                points = points.reshape((n_u*n_v, 3)).tolist()
        except Exception as e:
            points = []
            n_u = n_v = 0

        if hasattr(nurbs, 'get_weights'):
            weights = nurbs.get_weights()
            if self.split_points:
                weights = weights.flatten().tolist()
            else:
                weights = weights.tolist()
        else:
            weights = []

        return degree_u, degree_v, knots_u, knots_v, points, n_u, n_v, weights

    def make_edges(self, samples_u, samples_v):
        if self.split_points:
            row = [(i,i+1) for i in range(samples_u-1)]
            edges = [row] * samples_v
        else:
            edges = []
            for row in range(samples_v):
                e_row = [(i + samples_u * row, (i+1) + samples_u * row) for i in range(samples_u-1)]
                edges.extend(e_row)
                if row < samples_v - 1:
                    e_col = [(i + samples_u * row, i + samples_u * (row+1)) for i in range(samples_u)]
                    edges.extend(e_col)
        return edges

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        in_level = get_data_nesting_level(surface_s, data_types=(SvSurface,))
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))

        degree_u_out = []
        degree_v_out = []
        knots_u_out = []
        knots_v_out = []
        points_out = []
        edges_out = []
        weights_out = []

        for surfaces in surface_s:
            new_degrees_u = []
            new_degrees_v = []
            new_knots_u = []
            new_knots_v = []
            new_points = []
            new_edges = []
            new_weights = []
            for surface in surfaces:
                degree_u, degree_v, knots_u, knots_v, points, n_u, n_v, weights = self.deconstruct(surface)
                if points:
                    edges = self.make_edges(n_v, n_u)
                else:
                    edges = []
                new_degrees_u.append(degree_u)
                new_degrees_v.append(degree_v)
                new_knots_u.append(knots_u)
                new_knots_v.append(knots_v)
                new_points.append(points)
                new_weights.append(weights)
                new_edges.append(edges)
            if in_level == 2:
                degree_u_out.append(new_degrees_u)
                degree_v_out.append(new_degrees_v)
                knots_u_out.append(new_knots_u)
                knots_v_out.append(new_knots_v)
                points_out.append(new_points)
                weights_out.append(new_weights)
                edges_out.append(new_edges)
            else:
                degree_u_out.extend(new_degrees_u)
                degree_v_out.extend(new_degrees_v)
                knots_u_out.extend(new_knots_u)
                knots_v_out.extend(new_knots_v)
                points_out.extend(new_points)
                weights_out.extend(new_weights)
                edges_out.extend(new_edges)

        self.outputs['DegreeU'].sv_set(degree_u_out)
        self.outputs['DegreeV'].sv_set(degree_v_out)
        self.outputs['KnotVectorU'].sv_set(knots_u_out)
        self.outputs['KnotVectorV'].sv_set(knots_v_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Weights'].sv_set(weights_out)

def register():
    bpy.utils.register_class(SvDeconstructSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvDeconstructSurfaceNode)

