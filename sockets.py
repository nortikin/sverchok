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
from bpy.types import NodeSocket

from sverchok.data_structure import (SvGetSocketInfo, SvGetSocket,
                                     SvSetSocket, SvNoDataError)


sentinel = object()

def process_from_socket(self, context):
    self.node.process_node(context)

class SvSocketsBase:
    def sv_set(self, data):
        SvSetSocket(self, data)    
    
class SvObjectSocket(NodeSocket, SvSocketsBase):
    bl_idname = "SvObjectSocket"
    bl_label = "Object Socket"
    
    object_ref = StringProperty(update=process_from_socket)
    
    def sv_get(self, default=sentinel, deepcopy=False):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        elif self.object_ref:
            obj = bpy.data.objects.get(self.object_ref)
            if obj:
                return [obj]
            else:
                raise SvNoDataError
        else:
            raise SvNoDataError

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        elif self.is_output:
            layout.label(text)
        else:
            layout.prop_search(self, 'object_ref', bpy.data, 'objects', text=text)

    def draw_color(self, context, node):
        return(.9, .8, .8, 1.0)



class SvUndefTypeSocket(NodeSocket, SvSocketsBase):
    bl_idname = "SvUndefTypeSocket"
    bl_label = "UndefType Socket"

    def sv_get(self, default=sentinel, deepcopy=False):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        else:
            raise SvNoDataError

    def draw(self, context, layout, node, text):
        layout.label(text)


    def draw_color(self, context, node):
        return(1.0, 1.0, .0, 1.0)



class SvTextSocket(NodeSocket, SvSocketsBase):
    bl_idname = "SvTextSocket"
    bl_label = "Text Socket"
    
    text = StringProperty(update=process_from_socket)
    
    def sv_get(self, default=None, deepcopy=False):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        else:
            return [self.text]


    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        elif self.is_output:
            layout.label(text)
        else:
            layout.prop(self, "text")

    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return(.1, .1, .1, 1.0)
    
    
    
class MatrixSocket(NodeSocket, SvSocketsBase):
    '''4x4 matrix Socket_type'''
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    prop_name = StringProperty(default='')
    
    def sv_get(self, default=sentinel, deepcopy=False):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        elif default is sentinel:
            raise SvNoDataError
        else:
            return default

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return(.2, .8, .8, 1.0)


class VerticesSocket(NodeSocket, SvSocketsBase):
    '''String Vertices - one string'''
    bl_idname = "VerticesSocket"
    bl_label = "Vertices Socket"

    prop = FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)
    prop_name = StringProperty(default='')
    use_prop = BoolProperty(default=False)
    
    
    def sv_get(self, default=sentinel, deepcopy=False):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif self.use_prop:
            return [[self.prop[:]]]
        elif default is sentinel:
            raise SvNoDataError
        else:
            return default
            

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked:
            if self.prop_name:
                layout.template_component_menu(node, self.prop_name, name=self.name)
            elif self.use_prop:
                layout.template_component_menu(self, "prop", name=self.name)
            else:
                layout.label(text)
        elif self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        return(0.9, 0.6, 0.2, 1.0)


class StringsSocket(NodeSocket, SvSocketsBase):
    '''String any type - one string'''
    bl_idname = "StringsSocket"
    bl_label = "Strings Socket"

    prop_name = StringProperty(default='')

    prop_type = StringProperty(default='')
    prop_index = IntProperty()


    def sv_get(self, default=sentinel, deepcopy=False):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        elif self.prop_name:
            return [[getattr(self.node, self.prop_name)]]
        elif self.prop_type:
            return [[getattr(self.node, self.prop_type)[self.prop_index]]]
        elif default is not sentinel:
            return default
        else:
            raise SvNoDataError

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


def get_socket_types():
    """
    A central definition of socket types
    """
    return {'s': "StringsSocket",
            'm': "MatrixSocket",
            'v': "VerticesSocket",
            't': "SvTextSocket",
            'o': "SvObjectSocket",
            'u': "SvUndefTypeSocket"}

    """
    This could be done like this instead,
    also a good question if we should move to longer
    shortnames also, something like this could work
    obj, txt, vtx, num, mat
    
    {cls.short_name:cls.bl_idname for cls in SvSocketsBase.__subclasses__()}
    
    """        


def register():
    for class_name in SvSocketsBase.__subclasses__():
        bpy.utils.register_class(class_name)

def unregister():
    for class_name in reversed(SvSocketsBase.__subclasses__()):
        bpy.utils.unregister_class(class_name)
