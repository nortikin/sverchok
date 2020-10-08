# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import ast
import inspect
from itertools import product
from mathutils.noise import seed_set, random
import bpy
from bpy.props import FloatVectorProperty, IntVectorProperty, IntProperty, BoolProperty, StringProperty, EnumProperty


from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import changable_sockets, dataCorrect, updateNode, zip_long_repeat


class SvvMultiCacheReset(bpy.types.Operator):
    '''Clear Cache'''
    bl_idname = "node.multy_cache_reset"
    bl_label = "Multi Cache Reset"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        node.fill_empty_dict()
        updateNode(node, context)
        return {'FINISHED'}

class SvMultiCacheNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Store List
    Tooltip: Stores a Numerical List in mutiple memory buckets
    """
    bl_idname = 'SvMultiCacheNode'
    bl_label = 'Multi Cache'
    bl_icon = 'RNA'
    sv_icon = 'SV_MULTI_CACHE'

    in_bucket: IntProperty(
        name='In Bucket', description="Identifier of the bucket where data will be strored",
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
        self.wrapper_tracked_ui_draw_op(layout, "node.multy_cache_reset", icon='X', text="RESET")


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
