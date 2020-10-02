# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, map_at_level, unzip_dict_recursive
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.algorithms import sort_curves_for_concat, SvCurvesSortResult

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
        self.outputs.new('SvStringsSocket', "Indexes")
        self.outputs.new('SvStringsSocket', "FlipMask")
        self.outputs.new('SvStringsSocket', "SumError")

    def draw_buttons(self, context, layout):
        layout.prop(self, "allow_flip")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        def to_dict(r):
            return dict(Curves=r.curves,
                    Indexes=r.indexes,
                    FlipMask=r.flips,
                    SumError=[r.sum_error])

        def _process(curves):
            return sort_curves_for_concat(curves, allow_flip=self.allow_flip)

        curve_s = self.inputs['Curves'].sv_get()
        results = map_at_level(_process, curve_s, item_level=1, data_types=(SvCurve,))
        results = unzip_dict_recursive(results, item_type = SvCurvesSortResult, to_dict=to_dict)

        self.outputs['Curves'].sv_set(results['Curves'])
        self.outputs['Indexes'].sv_set(results['Indexes'])
        self.outputs['FlipMask'].sv_set(results['FlipMask'])
        self.outputs['SumError'].sv_set(results['SumError'])

def register():
    bpy.utils.register_class(SvSortCurvesNode)

def unregister():
    bpy.utils.unregister_class(SvSortCurvesNode)

