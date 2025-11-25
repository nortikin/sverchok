
import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty

from sverchok.data_structure import ensure_nesting_level, updateNode, zip_long_repeat
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.curve.core import (
    SvCurve,
    UnsupportedCurveTypeException,
)
from sverchok.utils.curve.algorithms import SvOffsetCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import offset_nurbs_curve
from sverchok.utils.math import (
    DIFF,
    FRENET,
    HOUSEHOLDER,
    NORMAL_DIR,
    TRACK,
    TRACK_NORMAL,
    ZERO,
)
from sverchok.utils.nodes_mixins.curve_offset import SvOffsetCurveNodeMixin

class SvLooseOffsetCurveNode(SverchCustomTreeNode, bpy.types.Node, SvOffsetCurveNodeMixin):
    """
    Triggers: Loose Offset Curve
    Tooltip: Offset a NURBS Curve, and generate a NURBS curve
    """
    bl_idname = 'SvLooseOffsetCurveNode'
    bl_label = 'Loose Offset NURBS Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_OFFSET'

    def update_sockets(self, context):
        self.inputs['Offset'].hide_safe = not (self.algorithm == NORMAL_DIR or self.mode != 'C')
        self.inputs['Vector'].hide_safe = not (self.algorithm == NORMAL_DIR or self.mode == 'C')
        self.inputs['Resolution'].hide_safe = not (self.algorithm in {ZERO, TRACK_NORMAL})
        updateNode(self, context)

    mode : EnumProperty(
            name = "Direction",
            items = SvOffsetCurveNodeMixin.modes,
            default = 'X',
            update = update_sockets)

    algorithm : EnumProperty(
            name = "Algorithm",
            items = SvOffsetCurveNodeMixin.algorithms,
            default = HOUSEHOLDER,
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        p = self.inputs.new('SvVerticesSocket', "Vector")
        p.use_prop = True
        p.default_property = (0.1, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "algorithm")
        if self.algorithm != NORMAL_DIR:
            layout.prop(self, "mode")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        offset_s = self.inputs['Offset'].sv_get()
        vector_s = self.inputs['Vector'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        offset_s = ensure_nesting_level(offset_s, 2)
        vector_s = ensure_nesting_level(vector_s, 3)
        resolution_s = ensure_nesting_level(resolution_s, 2)

        curve_out = []
        for params in zip_long_repeat(curve_s, offset_s, vector_s, resolution_s):
            new_curves = []
            for curve, offset, vector, resolution in zip_long_repeat(*params):
                if self.algorithm != NORMAL_DIR:
                    if self.mode == 'X':
                        offset_vector = [1, 0, 0]
                    elif self.mode == 'Y':
                        offset_vector = [0, 1, 0]
                    plane_normal = None
                else:
                    plane_normal = np.array(vector)
                    offset_vector = [-1.0, 0, 0]
                if offset_vector is not None:
                    offset_vector = np.array(offset_vector)
                    offset_vector /= np.linalg.norm(offset_vector)

                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise UnsupportedCurveTypeException("One of curves is not NURBS")
                new_curve = offset_nurbs_curve(curve,
                            offset_vector = offset * offset_vector,
                            plane_normal = plane_normal,
                            algorithm = self.algorithm,
                            algorithm_resolution = resolution)

                new_curves.append(new_curve)
            curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvLooseOffsetCurveNode)

def unregister():
    bpy.utils.unregister_class(SvLooseOffsetCurveNode)

