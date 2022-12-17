
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, repeat_last_for_length, ensure_nesting_level
from sverchok.utils.curve.fillet import FILLET_ARC, FILLET_BEZIER, fillet_polyline_from_vertices

class SvFilletPolylineNode(SverchCustomTreeNode, bpy.types.Node):
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
        description = "Fillet arc radius",
        min = 0.0,
        default = 0.2,
        update = updateNode)

    clamp : BoolProperty(
        name = "Clamp",
        description = "If checked, fillet will be limited to the maximum radius",
        default = False,
        update = updateNode)

    concat : BoolProperty(
        name = "Concatenate",
        description = "If checked, then all straight and arc segments will be concatenated into a single curve. Otherwise, each segment will be output as a separate curve object",
        default = True,
        update = updateNode)
    
    cyclic : BoolProperty(
        name = "Cyclic",
        description = "If checked, the node will generate a cyclic (closed) curve",
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
            (FILLET_ARC, "Circular arc", "Circular arc", 0),
            (FILLET_BEZIER, "Quadratic Bezier arc", "Quadratic Bezier curve segment", 1)
        ]

    arc_mode : EnumProperty(
        name = "Fillet mode",
        description = "Type of curve to generate for fillets",
        items = arc_modes,
        default = FILLET_ARC,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Fillet mode:')
        layout.prop(self, 'arc_mode', text='')
        layout.prop(self, "concat")

        if self.concat:
            layout.prop(self, "scale_to_unit")
        layout.prop(self, "cyclic")

        layout.prop(self,'clamp')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'make_nurbs')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvMatrixSocket', "Centers")

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
            curve, centers, _ = fillet_polyline_from_vertices(vertices, radiuses,
                                cyclic = self.cyclic,
                                concat = self.concat,
                                clamp = self.clamp,
                                arc_mode = self.arc_mode,
                                scale_to_unit = self.scale_to_unit,
                                make_nurbs = self.make_nurbs)
            curves_out.append(curve)
            centers_out.append(centers)
        
        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Centers'].sv_set(centers_out)

def register():
    bpy.utils.register_class(SvFilletPolylineNode)

def unregister():
    bpy.utils.unregister_class(SvFilletPolylineNode)

