# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
import numpy as np
import wave

import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

MAX_SOCKETS = 6
DATA_SOCKET = 'SvStringsSocket'


class SvWaveformViewerOperator(bpy.types.Operator):
    bl_idname = "node.waveform_viewer_callback"
    bl_label = "Waveform Viewer Operator"

    idname: bpy.props.StringProperty(default='')
    idtree: bpy.props.StringProperty(default='')
    fn_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        getattr(node, self.fn_name)()
        return {'FINISHED'}


class SvWaveformViewerOperatorDP(bpy.types.Operator):
    bl_idname = "node.waveform_viewer_dirpick"
    bl_label = "Waveform Viewer Directory Picker"

    idname: bpy.props.StringProperty(default='')
    idtree: bpy.props.StringProperty(default='')
    filepath: bpy.props.StringProperty(
        name="File Path", description="Filepath used for writing waveform files",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        node.set_dir(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvWaveformViewer(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvWaveformViewer
    Tooltip: 
    
    A short description for reader of node code
    """


    bl_idname = 'SvWaveformViewer'
    bl_label = 'SvWaveformViewer'
    bl_icon = 'FORCE_HARMONIC'


    def update_socket_count(self, context):
        ... # if self.num_channels < MAX_SOCKETS 


    num_channels: bpy.props.IntProperty(
        name='num channels', default=1, min=1, max=MAX_SOCKETS,
        description='num channels interleaved', update=updateNode)

    bits: bpy.props.IntProperty(name='bit rate', default=16, min=4, max=192)

    sample_rate: bpy.props.IntProperty(
        name="sample rate", min=8000, default=48000)

    auto_normalize: bpy.props.BoolProperty(
        name="normalize")

    colour_limits: bpy.props.BoolProperty(
        name="color limits")

    multi_channel_sockets: bpy.props.BoolProperty(
        name="multiplex", update=updateNode, description="sockets carry multiple layers of data")

    dirname: bpy.props.StringProperty()
    filename: bpy.props.StringProperty()

    def sv_init(self, context):
        self.inputs.new(DATA_SOCKET, 'channel 0')
        self.inputs.new(DATA_SOCKET, 'channel 1')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        
        col.prop(self, 'num_channels')
        col.prop(self, 'sample_rate')
        col.prop(self, 'bits')
        
        col.separator()
        row1 = col.row()
        row1.prop(self, 'auto_normalize', toggle=True)
        row1.prop(self, 'multi_channel_sockets', toggle=True)
        
        col.separator()
        col.prop(self, 'colour_limits')

        col.separator()
        row = col.row(align=True)
        row.prop(self, 'dirname', text='')
        cb = "node.waveform_viewer_dirpick"
        self.wrapper_tracked_ui_draw_op(row, cb, icon='FILE', text='')
        col.prop(self, "filename")

        if (self.filename and self.dirname):
            col.separator()
            cb = "node.waveform_viewer_callback"
            op = self.wrapper_tracked_ui_draw_op(col, cb, icon='CURSOR', text='WRITE')
            op.fn_name = "process_wave"

    def process(self):
        ...

    def process_wave(self):
        print('process wave pressed')
        if not self.dirname and self.filename:
            return
        
        #
        # get safe filename, do not overwrite existing? - TODO
        #
        wave_params = self.get_waveparams()
      
        filepath = os.path.join(self.dirname, self.filename)
        filetype = "wav"

        full_filepath_with_ext = f"{filepath}.{filetype}"
        with wave.open(full_filepath_with_ext, 'wb') as write_wave:
            write_wave.setparams(wave_params)
            write_wave.writeframes(self.get_wavedata(wave_params))

    def get_waveparams(self):
        # (nchannels, sampwidth, framerate, nframes, comptype, compname)
        return (self.num_channels, self.bits, self.sample_rate, self.num_frames, None, None)

    def get_wavedata(self, wave_params):
        """
        do they match? what convention to use to fill up one if needed..
        - copy opposite channel if channel data is short
        - repeat last channel value until data length matches longest
        """
        if self.multi_channel_sockets:
            data = self.inputs[0].get()
            if self.num_channels == 2 and len(data) == 2:
                data = self.interleave(data)
        else:
            if self.num_channels == 2:
                data_left = self.inputs[0].get()[0]
                data_right = self.inputs[1].get()[0]
                data = self.interleave([data_left, data_right])
            elif self.num_channels == 1:
                data = self.inputs[0].get()[0]
        
        return data

    def interleave(data_left, data_right):
        # if type data is two numpy arrays:
        # ..
        # else
        flat_list = []
        flat_add = flat_list.extend
        _ = [flat_add((l, r)) for zip(data_left, data_right)]
        return flat_list

    def set_dir(self, dirname):
        self.dirname = dirname
        print(self.dirname, dirname)


classes = [SvWaveformViewer, SvWaveformViewerOperator, SvWaveformViewerOperatorDP]
register, unregister = bpy.utils.register_classes_factory(classes)
