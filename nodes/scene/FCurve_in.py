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

    fcurve_datapath = StringProperty(name="fcurve", default="", update=updateNode)

    def sv_init(self, context):
        self.inputs.new("StringsSocket", "Frame")
        self.outputs.new("StringsSocket", "Evaluated")

    def draw_buttons(self, context, layout):
        r = layout.row()

    def evaluate(self, frames):
        """ will return a double wrapped value if needed
        fcurve = actions[0].fcurve[0]
        """

        some_value = [[fcurve.evaluate(f) for f in frames_list] for frames_list in frames]
        return some_value

    def process(self):

        if self.inputs[0].is_linked:
            evaluated = self.evaluate(self.inputs[0].sv_get())
        else:
            # fall back to current frame in scene
            try:
                current_frame = bpy.context.scene.frame_current
                evaluated = self.evaluate([[current_frame]])
            except:
                ...

        self.outputs[0].sv_set(evaluated)


def register():
    bpy.utils.register_class(SvFCurveInNodeMK1)


def unregister():
    bpy.utils.unregister_class(SvFCurveInNodeMK1)
