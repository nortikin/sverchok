# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, map_at_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.algorithms import sort_curves_for_concat

class SvSortCurvesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sort Curves
    Tooltip: Sort a list of Curve objects so that they can be concatenated
    """
    bl_idname = 'SvSortCurvesNode'
    bl_label = 'Sort Curves'
    bl_icon = 'OUTLINER_OB_EMPTY'

    allow_flip : BoolProperty(
            name = "Allow Reverse",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curves")
        self.outputs.new('SvCurveSocket', "Curves")

    def draw_buttons(self, context, layout):
        layout.prop(self, "allow_flip")

    def _process(self, curves):
        return sort_curves_for_concat(curves, allow_flip=self.allow_flip)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve_s = self.inputs['Curves'].sv_get()
        curve_out = map_at_level(self._process, curve_s, item_level=1, data_types=(SvCurve,))
        self.outputs['Curves'].sv_set(curve_out)

def register():
    bpy.utils.register_class(SvSortCurvesNode)

def unregister():
    bpy.utils.unregister_class(SvSortCurvesNode)

