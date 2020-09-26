# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve.biarc import SvBiArc

class SvBiArcNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bi Arc
    Tooltip: Generate a curve made of two circular arcs
    """
    bl_idname = 'SvBiArcNode'
    bl_label = 'Bi Arc'
    bl_icon = 'SPHERECURVE'
    sv_icon = 'SV_POLYARC'

    planar_tolerance : FloatProperty(
            name = "Planar Tolerance",
            description = "Tolerance value for checking if the curve is planar",
            default = 1e-6,
            precision = 8,
            update = updateNode)

    parameter : FloatProperty(
            name = "Parameter",
            description = "P parameter of biarc curves family",
            default = 1.0,
            update = updateNode)

    join : BoolProperty(
            name = "Join",
            description = "Output single flat list of curves",
            default = True,
            update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.outputs['Center1'].hide_safe = not self.show_details
        self.outputs['Center2'].hide_safe = not self.show_details
        self.outputs['Radius1'].hide_safe = not self.show_details
        self.outputs['Radius2'].hide_safe = not self.show_details
        self.outputs['Angle1'].hide_safe = not self.show_details
        self.outputs['Angle2'].hide_safe = not self.show_details
        self.outputs['Junction'].hide_safe = not self.show_details

    show_details : BoolProperty(
            name = "Show Details",
            description = "Show outputs with curve details",
            default = False,
            update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'show_details', toggle=True)
        layout.prop(self, "join")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'planar_tolerance')

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Point1")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Point2")
        p.use_prop = True
        p.default_property = (4.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Tangent1")
        p.use_prop = True
        p.default_property = (0.0, 1.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "Tangent2")
        p.use_prop = True
        p.default_property = (0.0, 1.0, 0.0)
        self.inputs.new('SvStringsSocket', "Parameter").prop_name = 'parameter'

        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "Arc1")
        self.outputs.new('SvCurveSocket', "Arc2")
        self.outputs.new('SvVerticesSocket', "Center1")
        self.outputs.new('SvVerticesSocket', "Center2")
        self.outputs.new('SvStringsSocket', 'Radius1')
        self.outputs.new('SvStringsSocket', 'Radius2')
        self.outputs.new('SvStringsSocket', 'Angle1')
        self.outputs.new('SvStringsSocket', 'Angle2')
        self.outputs.new('SvVerticesSocket', "Junction")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        point1_s = self.inputs['Point1'].sv_get()
        point2_s = self.inputs['Point2'].sv_get()
        tangent1_s = self.inputs['Tangent1'].sv_get()
        tangent2_s = self.inputs['Tangent2'].sv_get()
        param_s = self.inputs['Parameter'].sv_get()

        point1_s = ensure_nesting_level(point1_s, 3)
        point2_s = ensure_nesting_level(point2_s, 3)
        tangent1_s = ensure_nesting_level(tangent1_s, 3)
        tangent2_s = ensure_nesting_level(tangent2_s, 3)
        param_s = ensure_nesting_level(param_s, 2)

        curve_out = []
        arc1_out = []
        arc2_out = []
        center1_out = []
        center2_out = []
        radius1_out = []
        radius2_out = []
        angle1_out = []
        angle2_out = []
        junction_out = []
        for params in zip_long_repeat(point1_s, point2_s, tangent1_s, tangent2_s, param_s):
            curve_new = []
            arc1_new = []
            arc2_new = []
            center1_new = []
            center2_new = []
            radius1_new = []
            radius2_new = []
            angle1_new = []
            angle2_new = []
            junction_new = []

            for point1, point2, tangent1, tangent2, parameter in zip_long_repeat(*params):
                point1 = np.array(point1)
                point2 = np.array(point2)
                tangent1 = np.array(tangent1)
                tangent2 = np.array(tangent2)

                curve = SvBiArc.calc(point1, point2, tangent1, tangent2, parameter,
                            planar_tolerance = self.planar_tolerance)

                curve_new.append(curve)
                arc1_new.append(curve.arc1)
                arc2_new.append(curve.arc2)
                center1_new.append(tuple(curve.arc1.center))
                center2_new.append(tuple(curve.arc2.center))
                radius1_new.append(curve.arc1.radius)
                radius2_new.append(curve.arc2.radius)
                angle1_new.append(curve.arc1.get_u_bounds()[1])
                angle2_new.append(curve.arc2.get_u_bounds()[1])
                junction_new.append(tuple(curve.junction))

            curve_out.append(curve_new)
            arc1_out.append(arc1_new)
            arc2_out.append(arc2_new)
            center1_out.append(center1_new)
            center2_out.append(center2_new)
            radius1_out.append(radius1_new)
            radius2_out.append(radius2_new)
            angle1_out.append(angle1_new)
            angle2_out.append(angle2_new)
            junction_out.append(junction_new)

        if self.join:
            curve_out = sum(curve_out, [])
            arc1_out = sum(arc1_out, [])
            arc2_out = sum(arc2_out, [])
            center1_out = sum(center1_out, [])
            center2_out = sum(center2_out, [])
            radius1_out = sum(radius1_out, [])
            radius2_out = sum(radius2_out, [])
            angle1_out = sum(angle1_out, [])
            angle2_out = sum(angle2_out, [])
            junction_out = sum(junction_out, [])

        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['Arc1'].sv_set(arc1_out)
        self.outputs['Arc2'].sv_set(arc2_out)
        self.outputs['Center1'].sv_set(center1_out)
        self.outputs['Center2'].sv_set(center2_out)
        self.outputs['Radius1'].sv_set(radius1_out)
        self.outputs['Radius2'].sv_set(radius2_out)
        self.outputs['Angle1'].sv_set(angle1_out)
        self.outputs['Angle2'].sv_set(angle2_out)
        self.outputs['Junction'].sv_set(junction_out)

def register():
    bpy.utils.register_class(SvBiArcNode)

def unregister():
    bpy.utils.unregister_class(SvBiArcNode)

