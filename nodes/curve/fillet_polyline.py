
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvLine
from sverchok.utils.fillet import calc_fillet
from sverchok.utils.curve.algorithms import concatenate_curves

class SvFilletPolylineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Arc Fillet Polyline
    Tooltip: Generate a polyline with arc fillets
    """
    bl_idname = 'SvExFilletPolylineNode'
    bl_label = 'Fillet Polyline'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FILLET_POLYLINE'

    factor : FloatProperty(
        name = "Factor",
        default = 1.0,
        update = updateNode)

    radius : FloatProperty(
        name = "Radius",
        min = 0.0,
        default = 0.2,
        update = updateNode)

    concat : BoolProperty(
        name = "Concatenate",
        default = True,
        update = updateNode)
    
    cyclic : BoolProperty(
        name = "Cyclic",
        default = False,
        update = updateNode)

    scale_to_unit : BoolProperty(
        name = "Even domains",
        description = "Give each segment and each arc equal T parameter domain of [0; 1]",
        default = False,
        update = updateNode)

    make_nurbs : BoolProperty(
        name = "NURBS output",
        description = "Generate a NURBS curve",
        default = False,
        update = updateNode)

    arc_modes = [
            ('ARC', "Circular arc", "Circular arc", 0),
            ('BEZIER2', "Quadratic Bezier arc", "Quadratic Bezier curve segment", 1)
        ]

    arc_mode : EnumProperty(
        name = "Fillet mode",
        description = "Type of curve to generate for fillets",
        items = arc_modes,
        default = 'ARC',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Fillet mode:')
        layout.prop(self, 'arc_mode', text='')
        layout.prop(self, "concat")
        if self.concat:
            layout.prop(self, "scale_to_unit")
        layout.prop(self, "cyclic")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'make_nurbs')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "Factor").prop_name = 'factor'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvMatrixSocket', "Centers")

    def make_curve(self, vertices, radiuses):
        if self.cyclic:
            if radiuses[-1] == 0 :
                last_fillet = None
            else:
                last_fillet = calc_fillet(vertices[-2], vertices[-1], vertices[0], radiuses[-1])
            vertices = [vertices[-1]] + vertices + [vertices[0]] 
            prev_edge_start = vertices[0] if last_fillet is None else last_fillet.p2
            corners = list(zip(vertices, vertices[1:], vertices[2:], radiuses))
        else:
            prev_edge_start = vertices[0]
            corners = zip(vertices, vertices[1:], vertices[2:], radiuses)

        curves = []
        centers = []
        for v1, v2, v3, radius in corners:
            if radius == 0 :
                fillet = None
            else:
                fillet = calc_fillet(v1, v2, v3, radius)

            if fillet is not None :
                edge_direction = np.array(fillet.p1) - np.array(prev_edge_start)
                edge_len = np.linalg.norm(edge_direction)
                if edge_len != 0 :
                    edge = SvLine(prev_edge_start, edge_direction / edge_len)
                    edge.u_bounds = (0.0, edge_len)
                    curves.append(edge)
                if self.arc_mode == 'ARC':
                    arc = fillet.get_circular_arc()
                else:
                    arc = fillet.get_bezier_arc()
                prev_edge_start = fillet.p2
                curves.append(arc)
                centers.append(fillet.matrix)
            else:
                edge = SvLine.from_two_points(prev_edge_start, v2)
                prev_edge_start = v2
                curves.append(edge)

        if not self.cyclic:
            edge_direction = np.array(vertices[-1]) - np.array(prev_edge_start)
            edge_len = np.linalg.norm(edge_direction)
            if edge_len != 0 :
                edge = SvLine(prev_edge_start, edge_direction / edge_len)
                edge.u_bounds = (0.0, edge_len)
                curves.append(edge)

        if self.make_nurbs:
            if self.concat:
                curves = [curve.to_nurbs().elevate_degree(target=2) for curve in curves]
            else:
                curves = [curve.to_nurbs() for curve in curves]
        if self.concat:
            concat = concatenate_curves(curves, scale_to_unit = self.scale_to_unit)
            return concat, centers
        else:
            return curves, centers

    def limit(self,vertices,radiuses,factors):
        if self.cyclic:
            vertices = [vertices[-1]]+ vertices + [vertices[0]] 
        limit_radiuses = []
        for v1,v2,v3,r,f in zip(vertices,vertices[1:],vertices[2:],radiuses,factors):
            v1,v2,v3 = np.array(v1), np.array(v2), np.array(v3)
            vector1,vector2 = v1-v2,v3-v2
            d1,d2 = np.linalg.norm(vector1),np.linalg.norm(vector2)
            min_length = d1 if d1<d2 else d2
            angle = np.arccos(np.dot(vector1,vector2)/(d1*d2))
            max_r = float(np.tan(angle/2)*min_length*f/2)
            r = max_r if r>max_r else r
            limit_radiuses.append(r)
        return limit_radiuses

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        factor_s = self.inputs['Factor'].sv_get()

        verts_s = ensure_nesting_level(verts_s, 3)
        radius_s = ensure_nesting_level(radius_s, 2)
        factor_s = ensure_nesting_level(factor_s,2)

        curves_out = []
        centers_out = []
        for vertices, radiuses,factors in zip_long_repeat(verts_s, radius_s,factor_s):
            if len(vertices) < 3:
                raise Exception("At least three vertices are required to make a fillet")
            radiuses = repeat_last_for_length(radiuses, len(vertices))
            factors = repeat_last_for_length(factors, len(vertices))
            radiuses = self.limit(vertices, radiuses,factors)
            curve, centers = self.make_curve(vertices, radiuses)
            curves_out.append(curve)
            centers_out.append(centers)
        
        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Centers'].sv_set(centers_out)

def register():
    bpy.utils.register_class(SvFilletPolylineNode)

def unregister():
    bpy.utils.unregister_class(SvFilletPolylineNode)

