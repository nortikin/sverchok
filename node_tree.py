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

import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard
from nodeitems_utils import NodeCategory, NodeItem

import data_structure
from data_structure import (SvGetSocketInfo, SvGetSocket,
                            SvSetSocket,  updateNode)
from core.update_system import (build_update_list, sverchok_update,
                                get_update_lists)
from core import upgrade_nodes


class SvColors(bpy.types.PropertyGroup):
    """ Class for colors CollectionProperty """
    color = FloatVectorProperty(
        name="svcolor", description="sverchok color",
        default=(0.055, 0.312, 0.5), min=0, max=1,
        step=1, precision=3, subtype='COLOR_GAMMA', size=3,
        update=updateNode)


class MatrixSocket(NodeSocket):
    '''4x4 matrix Socket_type'''
    # ref: http://urchn.org/post/nodal-transform-experiment
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    prop_name = StringProperty(default='')

    # beta interface only use for debug, might change
    def sv_get(self, default=None, deepcopy=False):
        if self.links and not self.is_output:
            return SvGetSocket(self, deepcopy)
        else:
            return default

    def sv_set(self, data):
        SvSetSocket(self, data)

    def draw(self, context, layout, node, text):
    #    if not self.is_output and not self.is_linked and self.prop_name:
    #        layout.prop(node,self.prop_name,expand=False)
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return(.2, .8, .8, 1.0)

'''
class ObjectSocket(NodeSocket):
        'ObjectSocket'
        bl_idname = "ObjectSocket"
        bl_label = "Object Socket"

        ObjectProperty = StringProperty(name= "ObjectProperty", update=updateSlot)

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text)
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(self, 'ObjectProperty', text=text)

        def draw_color(self, context, node):
            return(0.8,0.8,0.2,1.0)
'''


class VerticesSocket(NodeSocketStandard):
    '''String Vertices - one string'''
    bl_idname = "VerticesSocket"
    bl_label = "Vertices Socket"
    prop_name = StringProperty(default='')

    # beta interface only use for debug, might change
    def sv_get(self, default=None, deepcopy=False):
        if self.links and not self.is_output:
            return SvGetSocket(self, deepcopy)
        else:
            return default

    def sv_set(self, data):
        SvSetSocket(self, data)

    def draw(self, context, layout, node, text):
    #    if not self.is_output and not self.is_linked and self.prop_name:
    #        layout.prop(node,self.prop_name,expand=False)
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        return(0.9, 0.6, 0.2, 1.0)


class StringsSocket(NodeSocketStandard):
    '''String any type - one string'''
    bl_idname = "StringsSocket"
    bl_label = "Strings Socket"

    prop_name = StringProperty(default='')
    
    prop_type = StringProperty(default='')
    prop_index = IntProperty()

    def sv_get(self, default=None, deepcopy=False):
        if self.links and not self.is_output:
            out = SvGetSocket(self, deepcopy)
            if out:
                return out
        if self.prop_name:
            return [[getattr(self.node, self.prop_name)]]
        if self.prop_type:
            return [[getattr(self.node, self.prop_type)[self.prop_index]]]
        return default
        

    def sv_set(self, data):
        SvSetSocket(self, data)

    def draw(self, context, layout, node, text):
        if self.prop_name:
            if self.is_output:
                t = text
                msg = "Warning output socket: {name} in node: {node} has property attached"
                print(msg.format(name=self.name, node=node.name))
            else:
                prop = node.rna_type.properties.get(self.prop_name, None)
                t = prop.name if prop else text
        else:
            t = text

        if not self.is_output and not self.is_linked:
            if self.prop_name and not self.prop_type:
                layout.prop(node, self.prop_name)
            elif self.prop_type:
                layout.prop(node, self.prop_type, index=self.prop_index, text=self.name)
            else:
                layout.label(t)
        elif self.is_linked:
            layout.label(t + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(t)

    def draw_color(self, context, node):
        return(0.6, 1.0, 0.6, 1.0)


class SverchCustomTree(NodeTree):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        sverchok_update(tree=self)
        #should turn off tree. for now it does by updating it

    sv_animate = BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show = BoolProperty(name="Show", default=True, description='Show this layout', update=turn_off_ng)
    sv_bake = BoolProperty(name="Bake", default=True, description='Bake this layout')
    sv_user_colors = StringProperty(default="")

    # get update list for debug info, tuple (fulllist,dictofpartiallists)
    def get_update_lists(self):
        return get_update_lists(self)

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

        build_update_list(tree=self)
        sverchok_update(tree=self)

    def update_ani(self):
        """
        Updates the Sverchok node tree if animation layers show true. For animation callback
        """
        if self.sv_animate:
            sverchok_update(tree=self)


class SverchCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'SverchCustomTreeType'
    #def draw_buttons(self, context, layout):
    #    layout.label('sverchok')


class SverchNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


def register():
    bpy.utils.register_class(SvColors)
    bpy.utils.register_class(SverchCustomTree)
    bpy.utils.register_class(MatrixSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(VerticesSocket)


def unregister():
    bpy.utils.unregister_class(VerticesSocket)
    bpy.utils.unregister_class(StringsSocket)
    bpy.utils.unregister_class(MatrixSocket)
    bpy.utils.unregister_class(SverchCustomTree)
    bpy.utils.unregister_class(SvColors)






