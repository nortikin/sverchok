
import numpy as np
import bpy
from bpy.props import FloatProperty, EnumProperty, IntProperty

from sverchok.core.sv_custom_exceptions import SvNoDataError
from sverchok.data_structure import ensure_nesting_level, zip_long_repeat, updateNode
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.algorithms import SvOffsetCurve
from sverchok.utils.math import (
    NORMAL_DIR, ZERO, TRACK_NORMAL, HOUSEHOLDER
)
from sverchok.utils.nodes_mixins.curve_offset import SvOffsetCurveNodeMixin


class SvOffsetCurveMk2Node(SverchCustomTreeNode, bpy.types.Node, SvOffsetCurveNodeMixin):
    """
    Triggers: Offset Curve
    Tooltip: Offset a Curve along it's normal, binormal or custom vector
    """
    bl_idname = 'SvOffsetCurveMk2Node'
    bl_label = 'Offset Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_OFFSET'

    def update_sockets(self, context):
        self.inputs['Offset'].hide_safe = not (self.offset_type == 'CONST' and (self.algorithm == NORMAL_DIR or self.mode != 'C'))
        self.inputs['Vector'].hide_safe = not (self.algorithm == NORMAL_DIR or self.mode == 'C')
        self.inputs['Resolution'].hide_safe = not (self.algorithm in {ZERO, TRACK_NORMAL} or (self.offset_type == 'CURVE' and self.offset_curve_type == SvOffsetCurve.BY_LENGTH))
        self.inputs['OffsetCurve'].hide_safe = not (self.offset_type == 'CURVE')
        updateNode(self, context)

    offset_types = [
            ('CONST', "Constant", "Specify constant offset by single number", 0),
            ('CURVE', "Variable", "Specify variable offset by providing T -> X curve", 1)
        ]

    offset_curve_types = [
            (SvOffsetCurve.BY_PARAMETER, "Curve parameter", "Use offset curve value according to curve's parameter", 0),
            (SvOffsetCurve.BY_LENGTH, "Curve length", "Use offset curve value according to curve's length", 1)
        ]

    offset_type : EnumProperty(
            name = "Offset type",
            description = "Specify how the offset values are provided",
            items = offset_types,
            default = 'CONST',
            update = update_sockets)

    offset_curve_type : EnumProperty(
            name = "Offset curve usage",
            description = "How offset curve is evaluated along the curve being offsetted",
            items = offset_curve_types,
            default = SvOffsetCurve.BY_PARAMETER,
            update = update_sockets)

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
        self.inputs.new('SvCurveSocket', "OffsetCurve")
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
        layout.prop(self, 'offset_type', expand=True)
        if self.offset_type == 'CURVE':
            layout.label(text="Offset curve use:")
            layout.prop(self, 'offset_curve_type', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()
        offset_s = self.inputs['Offset'].sv_get()
        offset_curve_s = self.inputs['OffsetCurve'].sv_get(default = [[None]])
        vector_s = self.inputs['Vector'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()

        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        offset_s = ensure_nesting_level(offset_s, 2)
        vector_s = ensure_nesting_level(vector_s, 3)
        resolution_s = ensure_nesting_level(resolution_s, 2)
        if self.inputs['OffsetCurve'].is_linked:
            offset_curve_s = ensure_nesting_level(offset_curve_s, 2, data_types=(SvCurve,))

        curve_out = []
        for curves, offsets, offset_curves, vectors, resolutions in zip_long_repeat(curve_s, offset_s, offset_curve_s, vector_s, resolution_s):
            new_curves = []
            for curve, offset, offset_curve, vector, resolution in zip_long_repeat(curves, offsets, offset_curves, vectors, resolutions):
                if self.algorithm != NORMAL_DIR:
                    if self.mode == 'X':
                        vector = [1, 0, 0]
                    elif self.mode == 'Y':
                        vector = [0, 1, 0]
                if vector is not None:
                    vector = np.array(vector)

                if self.offset_type == 'CONST':
                    new_curve = SvOffsetCurve(curve,
                                    offset_vector = vector,
                                    offset_amount = offset,
                                    algorithm = self.algorithm,
                                    resolution = resolution)
                else:
                    if offset_curve is None:
                        raise SvNoDataError(socket=self.inputs['OffsetCurve'], node=self)

                    new_curve = SvOffsetCurve(curve,
                                    offset_vector = vector,
                                    offset_curve = offset_curve,
                                    algorithm = self.algorithm,
                                    resolution = resolution)

                new_curves.append(new_curve)
            curve_out.append(new_curves)

        self.outputs['Curve'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvOffsetCurveMk2Node)

def unregister():
    bpy.utils.unregister_class(SvOffsetCurveMk2Node)

