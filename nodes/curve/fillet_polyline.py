
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvLine, SvConcatCurve
from sverchok.utils.fillet import calc_fillet

class SvFilletPolylineNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Arc Fillet Polyline
    Tooltip: Generate a polyline with arc fillets
    """
    bl_idname = 'SvExFilletPolylineNode'
    bl_label = 'Fillet Polyline'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FILLET_POLYLINE'

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

    def draw_buttons(self, context, layout):
        layout.prop(self, "concat", toggle=True)
        if self.concat:
            layout.prop(self, "scale_to_unit", toggle=True)
        layout.prop(self, "cyclic", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvMatrixSocket', "Centers")

    def make_curve(self, vertices, radiuses):
        if self.cyclic:
            last_fillet = calc_fillet(vertices[-1], vertices[0], vertices[1], radiuses[0])
            prev_edge_start = last_fillet.p2
            radiuses = radiuses[1:] + [radiuses[0]]
            corners = list(zip(vertices, vertices[1:], vertices[2:], radiuses))
            corners.append((vertices[-2], vertices[-1], vertices[0], radiuses[-1]))
            corners.append((vertices[-1], vertices[0], vertices[1], radiuses[0]))
        else:
            prev_edge_start = vertices[0]
            corners = zip(vertices, vertices[1:], vertices[2:], radiuses)

        curves = []
        centers = []
        for v1, v2, v3, radius in corners:
            fillet = calc_fillet(v1, v2, v3, radius)
            edge_direction = np.array(fillet.p1) - np.array(prev_edge_start)
            edge_len = np.linalg.norm(edge_direction)
            edge = SvLine(prev_edge_start, edge_direction / edge_len)
            edge.u_bounds = (0.0, edge_len)
            arc = fillet.get_curve()
            prev_edge_start = fillet.p2
            curves.append(edge)
            curves.append(arc)
            centers.append(fillet.matrix)

        if not self.cyclic:
            edge_direction = np.array(vertices[-1]) - np.array(prev_edge_start)
            edge_len = np.linalg.norm(edge_direction)
            edge = SvLine(prev_edge_start, edge_direction / edge_len)
            edge.u_bounds = (0.0, edge_len)
            curves.append(edge)

        if self.concat:
            concat = SvConcatCurve(curves, scale_to_unit = self.scale_to_unit)
            return concat, centers
        else:
            return curves, centers

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()

        verts_s = ensure_nesting_level(verts_s, 3)
        radius_s = ensure_nesting_level(radius_s, 2)

        curves_out = []
        centers_out = []
        for vertices, radiuses in zip_long_repeat(verts_s, radius_s):
            if len(vertices) < 3:
                raise Exception("At least three vertices are required to make a fillet")
            radiuses = repeat_last_for_length(radiuses, len(vertices))
            curve, centers = self.make_curve(vertices, radiuses)
            curves_out.append(curve)
            centers_out.append(centers)
        
        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Centers'].sv_set(centers_out)

def register():
    bpy.utils.register_class(SvFilletPolylineNode)

def unregister():
    bpy.utils.unregister_class(SvFilletPolylineNode)

