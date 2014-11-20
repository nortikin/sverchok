# -*- coding: utf-8 -*-
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

import time


import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard

from sverchok import data_structure
from sverchok.data_structure import (updateNode,
                                     get_other_socket, SvNoDataError)

# only import these to keep compability for now
from sverchok.sockets import MatrixSocket, VerticesSocket, StringsSocket

from sverchok.core.update_system import (build_update_list, process_from_node,
                                         process_tree, get_update_lists)
from sverchok.ui import color_def




# this property group is only used by the old viewer draw
class SvColors(bpy.types.PropertyGroup):
    """ Class for colors CollectionProperty """
    color = FloatVectorProperty(
        name="svcolor", description="sverchok color",
        default=(0.055, 0.312, 0.5), min=0, max=1,
        step=1, precision=3, subtype='COLOR_GAMMA', size=3,
        update=updateNode)




# Node tree 

class SvNodeTreeCommon(object):
    '''
    Common methods shared between Sverchok node trees
    '''
    def build_update_list(self):
        build_update_list(self)

    def adjust_reroutes(self):

        reroutes = [n for n in self.nodes if n.bl_idname == 'NodeReroute']
        if not reroutes:
            return
        for n in reroutes:
            s = n.inputs[0]
            if s.links:
                self.freeze(True)

                other = get_other_socket(s)
                s_type = other.bl_idname
                if n.outputs[0].bl_idname != s_type:
                    out_socket = n.outputs.new(s_type, "Output")
                    in_sockets = [l.to_socket for l in n.outputs[0].links]
                    n.outputs.remove(n.outputs[0])
                    for i_s in in_sockets:
                        l = self.links.new(i_s, out_socket)

                self.unfreeze(True)

    def freeze(self, hard=False):
        if hard:
            self["don't update"] = 1
        elif not self.is_frozen():
            self["don't update"] = 0

    def is_frozen(self):
        return "don't update" in self

    def unfreeze(self, hard=False):
        if self.is_frozen():
            if hard or self["don't update"] == 0:
                del self["don't update"]

    def get_update_lists(self):
        return get_update_lists(self)


class SverchCustomTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        process_tree(self)

        #should turn off tree. for now it does by updating it whole
        # should work something like this
        # outputs = filter(lambda n: isinstance(n,SvOutput), self.nodes)
        # for node in outputs:
        #   node.disable()

    sv_animate = BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show = BoolProperty(name="Show", default=True, description='Show this layout',
                           update=turn_off_ng)
    sv_bake = BoolProperty(name="Bake", default=True, description='Bake this layout')
    sv_process = BoolProperty(name="Process", default=True, description='Process layout')
    sv_user_colors = StringProperty(default="")

    # get update list for debug info, tuple (fulllist,dictofpartiallists)

    def update(self):
        '''
        Rebuild and update the Sverchok node tree, used at editor changes
        '''
        # startup safety net, a lot things will just break if this isn't
        # stopped...
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except:
            return
        if self.is_frozen():
            print("Skippiping update of {}".format(self.name))
            return

        self.adjust_reroutes()

        self.build_update_list()
        if self.sv_process:
            process_tree(self)

    def update_ani(self):
        """
        Updates the Sverchok node tree if animation layers show true. For animation callback
        """
        if self.sv_animate:
            process_tree(self)


class SverchGroupTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - groups '''
    bl_idname = 'SverchGroupTreeType'
    bl_label = 'Sverchok Group Node Tree'
    bl_icon = 'NONE'

    def update(self):
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except:
            return
        if self.is_frozen():
            return
        self.adjust_reroutes()

    @classmethod
    def poll(cls, context):
        return False


class SverchCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname in ['SverchCustomTreeType', 'SverchGroupTreeType']

    def set_color(self):
        color = color_def.get_color(self.bl_idname)
        if color:
            self.use_custom_color = True
            self.color = color

    def init(self, context):
        ng = self.id_data
        ng.freeze()
        # color
        if hasattr(self, "sv_init"):
            self.sv_init(context)
        self.set_color()
        ng.unfreeze()

    def process_node(self, context):
        '''
        Doesn't work as intended, inherited functions can't be used for bpy.props
        update=
        Still this is called from updateNode
        '''
        if self.id_data.is_frozen():
            return
        if data_structure.DEBUG_MODE:
            a = time.perf_counter()
            process_from_node(self)
            b = time.perf_counter()
            print("Partial update from node", self.name, "in", round(b-a, 4))
        else:
            process_from_node(self)


classes = [
    SvColors,
    SverchCustomTree,
    SverchGroupTree,
]

def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)

def unregister():
    for class_name in reversed(classes):
        bpy.utils.unregister_class(class_name)
