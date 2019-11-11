# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import numpy as np
import wave
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

    MAX_SOCKETS = 6
    DATA_SOCKET = 'SvStringsSocket'

    def update_socket_count(self, context):
        ... # if self.num_channels < MAX_SOCKETS 


    num_channels: bpy.props.IntProperty(
        name='num channels', default=1, min=1, max=MAX_SOCKETS,
        description='num channels interleaved', update=update_socket_count)

    bitrate: bpy.props.IntProperty(
        name="bitrate", min=8000, default=441000)

    auto_normmalize: bpy.props.BoolProperty(
        name="auto normalize")

    colour_out_of_bounds_in_scope: bpy.props.BoolProperty(
        name="out_of_bounds")

    def sv_init(self, context):
        self.inputs.new(self.DATA_SOCKET, 'channel 0')
        self.inputs.new(self.DATA_SOCKET, 'channel 1')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'num_channels')
        layout.prop(self, 'bitrate')
        layout.prop(self, 'auto_normalize')
        layout.prop(self, 'colour_out_of_bounds_in_scope')

    def process(self):
        ...


classes = [SvWaveformViewer, SvWaveformViewerOperator]
register, unregister = bpy.utils.register_classes_factory(classes)
