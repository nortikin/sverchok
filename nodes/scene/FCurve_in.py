# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
from bpy.props import IntProperty, StringProperty # FloatProperty, BoolProperty
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

    array_index = IntProperty(default=0, min=0, max=2, name="array index", update=updateNode)
    fcurve_datapath = StringProperty(name="fcurve", default="", update=updateNode)
    warning_msg = StringProperty(name="node warning")
    obj_name = StringProperty(name="object name", update=updateNode)

    def sv_init(self, context):
        self.inputs.new("StringsSocket", "Frame")
        self.outputs.new("StringsSocket", "Evaluated")

    def draw_buttons(self, context, layout):
        r = layout.row()
        # pick object
        # pick location x y z to use as evaluator

    def get_object_reference(self):
        ...

    def evaluate(self, frames):
        """
        takes a single values or a nested list of values (frame and subframe)
        """

        obj = self.get_object_reference()
        action = obj.animation_data.action
        
        if not action:
            self.warning_msg = "object has no animation data associated"
            return [[0]]

        fcurve = action.fcurve[self.array_index]
        return [[fcurve.evaluate(f) for f in frames_list] for frames_list in frames]


    def process(self):
        """
        - if no input is given then the node will use current frame in bpy.context.scene
        - if input is given, behaviour depends on 2 things:
            - the input is a single number (f.ex: [[x]] ) , this will generate a single value output evaluated at x
            - the input can be multiple lists, and evaluate multiple times (regardless of current frame number)
        """

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
