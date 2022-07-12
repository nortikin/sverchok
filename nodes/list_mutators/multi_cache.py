# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import ast
import inspect
from itertools import product

import bpy
from bpy.props import FloatVectorProperty, IntVectorProperty, IntProperty, BoolProperty, StringProperty, EnumProperty
from mathutils.noise import seed_set, random

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import changable_sockets, dataCorrect, updateNode, zip_long_repeat
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator


class SvvMultiCacheReset(bpy.types.Operator, SvGenericNodeLocator):
    '''Clear Cache'''
    bl_idname = "node.multi_cache_reset"
    bl_label = "Multi Cache Reset"

    def sv_execute(self, context, node):
        node.fill_empty_dict()
        updateNode(node, context)


class SvMultiCacheNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Store List
    Tooltip: Stores a Numerical List in multiple memory buckets
    """
    bl_idname = 'SvMultiCacheNode'
    bl_label = 'Multi Cache'
    bl_icon = 'RNA'
    sv_icon = 'SV_MULTI_CACHE'

    in_bucket: IntProperty(
        name='In Bucket', description="Identifier of the bucket where data will be stored",
        default=0,
        update=updateNode)
    out_bucket: IntProperty(
        name='Out Bucket', description="Identifier of the bucket that will be outputted",
        default=0,
        update=updateNode)


    def pause_recording_update(self, context):
        if not self.pause_recording:
            updateNode(self, context)

    pause_recording: BoolProperty(
        name='Pause',
        description='Pause Recording',
        default=False,
        update=pause_recording_update)
    unwrap: BoolProperty(
        name='Unwrap',
        default=True,
        update=pause_recording_update)

    node_mem = {}
    memory: StringProperty(default="")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'pause_recording')
        layout.prop(self, 'unwrap')
        self.wrapper_tracked_ui_draw_op(layout, "node.multi_cache_reset", icon='X', text="RESET")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.inputs.new('SvStringsSocket', 'In Bucket').prop_name = 'in_bucket'
        self.inputs.new('SvStringsSocket', 'Out Bucket').prop_name = 'out_bucket'
        self.outputs.new('SvStringsSocket', 'Data')
        self.fill_empty_dict()

    def write_memory_prop(self, data):
        '''write values to string property'''
        self.memory = ''.join(str(data))

    def check_memory_prop(self):
        tx = self.memory
        if len(tx) > 1:
            return ast.literal_eval(tx)
        return []

    def fill_empty_dict(self):
        self.node_mem[self.node_id] = {}

    def sv_update(self):
        '''adapt socket type to input type'''
        if 'Data' in self.inputs and self.inputs['Data'].links:
            inputsocketname = 'Data'
            outputsocketname = ['Data']
            changable_sockets(self, inputsocketname, outputsocketname)

    def process(self):
        if not self.outputs['Data'].is_linked:
            return

        in_bucket_s = self.inputs['In Bucket'].sv_get()[0]
        out_bucket_s = self.inputs['Out Bucket'].sv_get()[0]
        if not self.node_id in self.node_mem:
            text_memory = self.check_memory_prop()
            if text_memory:
                self.node_mem[self.node_id] = text_memory
            else:
                self.fill_empty_dict()

        data_out = []
        add = data_out.extend if self.unwrap else data_out.append
        if not self.pause_recording:
            data = self.inputs['Data'].sv_get()
            if len(in_bucket_s) > 1:
                for in_bucket, sub_list in zip_long_repeat(in_bucket_s, data):
                    self.node_mem[self.node_id][in_bucket] = sub_list
            else:
                self.node_mem[self.node_id][in_bucket_s[0]] = data
            self.write_memory_prop(self.node_mem[self.node_id])

        for out_bucket in out_bucket_s:
            if out_bucket in self.node_mem[self.node_id]:
                add(self.node_mem[self.node_id][out_bucket])
            else:
                self.node_mem[self.node_id][out_bucket] = [[]]


        self.outputs['Data'].sv_set(data_out)


classes = [SvMultiCacheNode, SvvMultiCacheReset]
register, unregister = bpy.utils.register_classes_factory(classes)
