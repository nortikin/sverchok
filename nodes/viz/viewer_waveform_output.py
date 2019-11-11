# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import numpy as np
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvWaveformViewerOperator(bpy.types.Operator):

    bl_idname = "node.waveform_viewer_callback"
    bl_label = "Waveform Viewer Operator"
    # bl_options = {'REGISTER', 'UNDO'}

    fn_name = bpy.props.StringProperty(default='')
    # obj_type = bpy.props.StringProperty(default='MESH')

    def dispatch(self, context, type_op):
        n = context.node

        if type_op == 'some_named_function':
            pass

        elif type_op == 'some_named_other_function':
            pass

    def execute(self, context):
        self.dispatch(context, self.fn_name)
        return {'FINISHED'}



class SvWaveformViewer(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvWaveformViewer
    Tooltip: 
    
    A short description for reader of node code
    """

    bl_idname = 'SvWaveformViewer'
    bl_label = 'SvWaveformViewer'
    bl_icon = 'GREASEPENCIL'

    def sv_init(self, context):
        ...

    def draw_buttons(self, context, layout):
        ...

    def process(self):
        ...


classes = [SvWaveformViewer, SvWaveformViewerOperator]
register, unregister = bpy.utils.register_classes_factory(classes)
