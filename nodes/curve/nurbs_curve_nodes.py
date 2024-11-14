# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, zip_long_repeat, ensure_nesting_level,
                                     get_data_nesting_level)
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve

class SvNurbsCurveNodesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS curve nodes (Greville points)
    Tooltip: Display nodes (a.k.a edit points or Greville points) of a NURBS curve
    """
    bl_idname = 'SvNurbsCurveNodesNode'
    bl_label = 'NURBS Curve Nodes'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_NODES'

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "Points")
        self.outputs.new('SvStringsSocket', "T")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curve'].sv_get()

        curves_level = get_data_nesting_level(curve_s, data_types=(SvCurve,))
        curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))

        points_out = []
        t_out = []
        for curves in curve_s:
            point_list = []
            t_list = []
            for curve in curves:
                curve = SvNurbsCurve.to_nurbs(curve)
                if curve is None:
                    raise Exception("Curve is not NURBS!")
                ts = curve.calc_greville_ts()
                pts = curve.evaluate_array(ts)
                t_list.append(ts.tolist())
                point_list.append(pts.tolist())

            if curves_level == 2:
                points_out.append(point_list)
                t_out.append(t_list)
            else:
                points_out.extend(point_list)
                t_out.extend(t_list)

        self.outputs['Points'].sv_set(points_out)
        self.outputs['T'].sv_set(t_out)
                
def register():
    bpy.utils.register_class(SvNurbsCurveNodesNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsCurveNodesNode)

