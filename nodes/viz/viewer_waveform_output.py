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

MAX_SOCKETS = 6
DATA_SOCKET = 'SvStringsSocket'


class SvWaveformViewer(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvWaveformViewer
    Tooltip: 
    
    A short description for reader of node code
    """


    bl_idname = 'SvWaveformViewer'
    bl_label = 'SvWaveformViewer'
    bl_icon = 'GREASEPENCIL'


    def update_socket_count(self, context):
        ... # if self.num_channels < MAX_SOCKETS 


    num_channels: bpy.props.IntProperty(
        name='num channels', default=1, min=1, max=MAX_SOCKETS,
        description='num channels interleaved', update=update_socket_count)

    bitrate: bpy.props.IntProperty(
        name="bitrate", min=8000, default=44100)

    auto_normalize: bpy.props.BoolProperty(
        name="normalize")

    colour_limits: bpy.props.BoolProperty(
        name="color limits")

    multi_channel_sockets: bpy.props.BoolProperty(
        name="multiplex", update=updateNode, description="sockets carry multiple layers of data")

    def sv_init(self, context):
        self.inputs.new(DATA_SOCKET, 'channel 0')
        self.inputs.new(DATA_SOCKET, 'channel 1')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        
        col.prop(self, 'num_channels')
        col.prop(self, 'bitrate')
        
        col.separator()
        row1 = col.row()
        row1.prop(self, 'auto_normalize', toggle=True)
        row1.prop(self, 'multi_channel_sockets', toggle=True)
        
        col.separator()
        col.prop(self, 'colour_limits')

    def process(self):
        ...


classes = [SvWaveformViewer, SvWaveformViewerOperator]
register, unregister = bpy.utils.register_classes_factory(classes)
