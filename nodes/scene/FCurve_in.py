# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
from bpy.props import IntProperty, StringProperty, EnumProperty  # FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_operator_mixins import SvGenericCallbackWithParams


class SvFCurveMK1CB(bpy.types.Operator, SvGenericCallbackWithParams):
    bl_idname = "node.sv_fcurvenodemk1_callback_with_params"
    bl_label = "Callback for fcurve sampler node mk1"
    bl_options = {'INTERNAL'}

class SvFCurveInNodeMK1(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''
    Triggers: FCurve In
    Tooltip: Get result of curve evaluated at frame x

    allows for some motion graphics control by FCurve

    '''
    bl_idname = 'SvFCurveInNodeMK1'
    bl_label = 'F-Curve In'
    bl_icon = 'FCURVE'

    def wrapped_update(self, context):

        if not self.new_prop_name:
            # avoid recursion
            return
        else:
            obj = bpy.data.objects[self.object_name]
            obj[self.new_prop_name] = 1.0
            obj.keyframe_insert(data_path='["{}"]'.format(self.new_prop_name))

        self.new_prop_name = ""

    array_index: IntProperty(default=0, min=0, name="array index", update=updateNode)
    fcurve_datapath: StringProperty(name="fcurve", default="", update=updateNode)
    warning_msg: StringProperty(name="node warning")
    object_name: StringProperty(name="object name", update=updateNode)

    new_prop_name: StringProperty(name="new prop name", update=wrapped_update)

    def add_empty(self, context):
        empty = bpy.data.objects.new("sv_fcurve_empty", None)
        scene = bpy.context.scene
        collection = scene.collection
        collection.objects.link(empty)
        scene.update()

        self.object_name = empty.name

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "Frame")
        self.outputs.new("SvStringsSocket", "Evaluated")

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        row = layout.row(align=True)
        row.prop_search(self, 'object_name', bpy.data, 'objects', text='', icon='OBJECT_DATA')
        row.operator("node.sv_fcurvenodemk1_callback_with_params", text='', icon="ZOOM_IN").fn_name="add_empty"
        if not self.object_name:
            return

        obj = self.get_object_reference()
        if not obj or not obj.animation_data:
            layout.label(text="no animation data, add a named prop")
            layout.prop(self, "new_prop_name", text="custom prop")
            return

        action = obj.animation_data.action
        if not action:
            layout.label(text="{} has no action".format(self.object_name))
            return

        r = layout.row()
        r.prop(self, "array_index", text="property index")


    def get_object_reference(self):
        return self.get_bpy_data_from_name(self.object_name, bpy.data.objects)

    def evaluate(self, frames):
        """
        takes a single value or a nested list of values (frame and subframe)
        """

        obj = self.get_object_reference()
        if not obj:
            self.warning_msg = "no object picked, or stored"
            print(self.warning_msg)
            return [[0]]

        action = obj.animation_data.action
        if not action:
            self.warning_msg = "object has no animation data associated"
            print(self.warning_msg)
            return [[0]]

        fcurve = action.fcurves[self.array_index]
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


classes = [SvFCurveMK1CB, SvFCurveInNodeMK1]
register, unregister = bpy.utils.register_classes_factory(classes)
