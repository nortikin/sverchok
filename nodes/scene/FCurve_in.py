# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvFCurveInNodeMK1(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: FCurve In
    Tooltip: Get result of curve evaluated at frame x

    allows for some motion graphics control by FCurve

    '''
    bl_idname = 'SvFCurveInNodeMK1'
    bl_label = 'F-Curve In'
    bl_icon = 'FCURVE'

    def sv_init(self, context):
        ...

    def draw_buttons(self, context, layout):
        ...

    def process(self):
        ...


def register():
    bpy.utils.register_class(SvFCurveInNodeMK1)


def unregister():
    bpy.utils.unregister_class(SvFCurveInNodeMK1)
