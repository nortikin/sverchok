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

import math

import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty, FloatProperty
from bpy.types import NodeTree, NodeSocket

from sverchok.core.socket_conversions import DefaultImplicitConversionPolicy, is_vector_to_matrix

from sverchok.core.socket_data import (
    SvGetSocketInfo, SvGetSocket, SvSetSocket,
    SvNoDataError, sentinel)

from sverchok.data_structure import (
    updateNode,
    get_other_socket,
    socket_id,
    replace_socket)

socket_colors = {
    "StringsSocket": (0.6, 1.0, 0.6, 1.0),
    "VerticesSocket": (0.9, 0.6, 0.2, 1.0),
    "SvQuaternionSocket": (0.9, 0.4, 0.7, 1.0),
    "SvColorSocket": (0.9, 0.8, 0.0, 1.0),
    "MatrixSocket": (0.2, 0.8, 0.8, 1.0),
    "SvDummySocket": (0.8, 0.8, 0.8, 0.3),
    "SvObjectSocket": (0.69, 0.74, 0.73, 1.0),
    "SvTextSocket": (0.68, 0.85, 0.90, 1)
}

def process_from_socket(self, context):
    """Update function of exposed properties in Sockets"""
    self.node.process_node(context)


class SvSocketCommon:
    """ Base class for all Sockets """
    use_prop: BoolProperty(default=False)

    use_expander: BoolProperty(default=True)
    use_quicklink: BoolProperty(default=True)
    expanded: BoolProperty(default=False)

    quicklink_func_name: StringProperty(default="", name="quicklink_func_name")    

    @property
    def other(self):
        return get_other_socket(self)

    def set_default(self, value):
        if self.prop_name:
            setattr(self.node, self.prop_name, value)

    @property
    def socket_id(self):
        """Id of socket used by data_cache"""
        return str(hash(self.id_data.name + self.node.name + self.identifier))

    @property
    def index(self):
        """Index of socket"""
        node = self.node
        sockets = node.outputs if self.is_output else node.inputs
        for i, s in enumerate(sockets):
            if s == self:
                return i

    @property
    def hide_safe(self):
        return self.hide

    @hide_safe.setter
    def hide_safe(self, value):
        # handles both input and output.
        if self.is_linked:
            for link in self.links:
                self.id_data.links.remove(link)

        self.hide = value

    def sv_set(self, data):
        """Set output data"""
        SvSetSocket(self, data)

    def replace_socket(self, new_type, new_name=None):
        """Replace a socket with a socket of new_type and keep links,
        return the new socket, the old reference might be invalid"""
        return replace_socket(self, new_type, new_name)

    @property
    def extra_info(self):
        # print("getting base extra info")
        return ""

    def get_socket_info(self):
        """ Return Number of encapsulated data lists, or empty str  """
        try:
            return SvGetSocketInfo(self)
        except:
            return ''

    def draw_expander_template(self, context, layout, prop_origin, prop_name="prop"):

        if self.bl_idname == "StringsSocket":
            layout.prop(prop_origin, prop_name)
        else:
            if self.use_expander:
                split = layout.split(factor=.2, align=True)
                c1 = split.column(align=True)
                c2 = split.column(align=True)

                if self.expanded:
                    c1.prop(self, "expanded", icon='TRIA_UP', text='')
                    c1.label(text=self.name[0])
                    c2.prop(prop_origin, prop_name, text="", expand=True)
                else:
                    c1.prop(self, "expanded", icon='TRIA_DOWN', text="")
                    row = c2.row(align=True)
                    if self.bl_idname == "SvColorSocket":
                        row.prop(prop_origin, prop_name)
                    else:
                        row.template_component_menu(prop_origin, prop_name, name=self.name)

            else:
                layout.template_component_menu(prop_origin, prop_name, name=self.name)

    def draw_quick_link(self, context, layout, node):

        if self.use_quicklink:
            if self.bl_idname == "MatrixSocket":
                new_node_idname = "SvMatrixGenNodeMK2"
            elif self.bl_idname == "VerticesSocket":
                new_node_idname = "GenVectorsNode"
            else:
                return

            op = layout.operator('node.sv_quicklink_new_node_input', text="", icon="PLUGIN")
            op.socket_index = self.index
            op.origin = node.name
            op.new_node_idname = new_node_idname
            op.new_node_offsetx = -200 - 40 * self.index
            op.new_node_offsety = -30 * self.index

    def draw(self, context, layout, node, text):

        # just handle custom draw..be it input or output.
        # hasattr may be excessive here
        if self.bl_idname == 'StringsSocket':
            if hasattr(self, 'custom_draw') and self.custom_draw:

                # does the node have the draw function referred to by 
                # the string stored in socket's custom_draw attribute
                if hasattr(node, self.custom_draw):
                    getattr(node, self.custom_draw)(self, context, layout)
                    return

            if node.bl_idname in {'SvScriptNodeLite', 'SvScriptNode'}:
                if not self.is_output and not self.is_linked and self.prop_type:
                    layout.prop(node, self.prop_type, index=self.prop_index, text=self.name)
                    return
            elif node.bl_idname in {'SvSNFunctor'} and not self.is_output:
                if not self.is_linked:
                    layout.prop(node, self.prop_name, text=self.name)
                    return

        if self.is_linked:  # linked INPUT or OUTPUT
            t = text
            if not self.is_output:
                if self.prop_name:
                    prop = node.rna_type.properties.get(self.prop_name, None) 
                    t = prop.name if prop else text
            info_text = t + '. ' + SvGetSocketInfo(self)
            info_text += self.extra_info
            layout.label(text=info_text)

        elif self.is_output:  # unlinked OUTPUT
            layout.label(text=text)

        else:  # unlinked INPUT
            if self.prop_name:  # has property
                self.draw_expander_template(context, layout, prop_origin=node, prop_name=self.prop_name)

            elif self.use_prop:  # no property but use default prop
                self.draw_expander_template(context, layout, prop_origin=self)

            elif self.quicklink_func_name:
                try:
                    getattr(node, self.quicklink_func_name)(self, context, layout, node)
                except Exception as e:
                    self.draw_quick_link(context, layout, node)
                layout.label(text=text)

            else:  # no property and not use default prop
                self.draw_quick_link(context, layout, node)
                layout.label(text=text)

    def draw_color(self, context, node):
        return socket_colors[self.bl_idname]

    def needs_data_conversion(self):
        if not self.is_linked:
            return False
        return self.other.bl_idname != self.bl_idname

    def convert_data(self, source_data, implicit_conversions=None):
        if not self.needs_data_conversion():
            return source_data
        else:
            policy = self.node.get_implicit_conversions(self.name, implicit_conversions)
            self.node.debug(f"Trying to convert data for input socket {self.name} by {policy}")
            return policy.convert(self, source_data)


class SvSocketStandard(SvSocketCommon):
    def get_prop_data(self):
        return {"default_value" , default_value}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        else:
            return [[self.default_value]]

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        elif self.is_output:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)


class SvObjectSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvObjectSocket"
    bl_label = "Object Socket"

    object_ref: StringProperty(update=process_from_socket)

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked:
            layout.prop_search(self, 'object_ref', bpy.data, 'objects', text=self.name)
        elif self.is_linked:
            layout.label(text=text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text=text)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        elif self.object_ref:
            obj_ref = bpy.data.objects.get(self.object_ref)
            if not obj_ref:
                raise SvNoDataError(self)
            return [obj_ref]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class SvTextSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvTextSocket"
    bl_label = "Text Socket"

    text: StringProperty(update=process_from_socket)

    def draw(self, context, layout, node, text):
        if self.is_linked and not self.is_output:
            layout.label(text=text)
        if not self.is_linked and not self.is_output:
            layout.prop(self, 'text')

    def draw_color(self, context, node):
        return (0.68,  0.85,  0.90, 1)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        elif self.text:
            return [self.text]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class MatrixSocket(NodeSocket, SvSocketCommon):
    '''4x4 matrix Socket type'''
    
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"

    prop_name: StringProperty(default='')
    num_matrices: IntProperty(default=0)

    @property
    def extra_info(self):
        # print("getting matrix extra info")
        info = ""
        if is_vector_to_matrix(self):
            info = (" (" + str(self.num_matrices) + ")")

        return info

    def get_prop_data(self):
        return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        self.num_matrices = 0
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy = True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default


class VerticesSocket(NodeSocket, SvSocketCommon):
    '''For vertex data'''
    bl_idname = "VerticesSocket"
    bl_label ="Vertices Socket"

    prop: FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)
    prop_name: StringProperty(default='')
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        if self.prop_name:
            return {"prop_name": socket.prop_name}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy = True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif self.use_prop:
            return [[self.prop[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default


class SvQuaternionSocket(NodeSocket, SvSocketCommon):
    '''For quaternion data'''
    bl_idname = "SvQuaternionSocket"
    bl_label = "Quaternion Socket"

    prop: FloatVectorProperty(default=(1, 0, 0, 0), size=4, subtype='QUATERNION', update=process_from_socket)
    prop_name: StringProperty(default='')
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        if self.prop_name:
            return {"prop_name": socket.prop_name}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy = True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif self.use_prop:
            return [[self.prop[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default


class SvColorSocket(NodeSocket, SvSocketCommon):
    '''For color data'''
    bl_idname = "SvColorSocket"
    bl_label = "Color Socket"

    prop: FloatVectorProperty(default=(0, 0, 0, 1), size=4, subtype='COLOR', min=0, max=1, update=process_from_socket)
    prop_name: StringProperty(default='')
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        if self.prop_name:
            return {"prop_name": socket.prop_name}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif self.use_prop:
            return [[self.prop[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default


class SvDummySocket(NodeSocket, SvSocketCommon):
    '''Dummy Socket for sockets awaiting assignment of type'''
    bl_idname = "SvDummySocket"
    bl_label = "Dummys Socket"

    prop: FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)
    prop_name: StringProperty(default='')
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        return self.other.get_prop_data()

    def sv_get(self):
        if self.is_linked:
            return self.links[0].bl_idname

    def sv_type_conversion(self, new_self):
        self = new_self


class StringsSocket(NodeSocket, SvSocketCommon):
    '''Generic, mostly numbers, socket type'''
    bl_idname = "StringsSocket"
    bl_label = "Strings Socket"

    prop_name: StringProperty(default='')
    prop_type: StringProperty(default='')
    prop_index: IntProperty()
    custom_draw: StringProperty()

    def get_prop_data(self):
        if self.prop_name:
            return {"prop_name": self.prop_name}
        elif self.prop_type:
            return {"prop_type": self.prop_type,
                    "prop_index": self.prop_index}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        # debug("Node %s, socket %s, is_linked: %s, is_output: %s",
        #         self.node.name, self.name, self.is_linked, self.is_output)

        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        elif self.prop_name:
            # to deal with subtype ANGLE, this solution should be considered temporary...
            _, prop_dict = getattr(self.node.rna_type, self.prop_name, (None, {}))
            subtype = prop_dict.get("subtype", "")
            if subtype == "ANGLE":
                return [[math.degrees(getattr(self.node, self.prop_name))]]
            return [[getattr(self.node, self.prop_name)]]
        elif self.prop_type:
            return [[getattr(self.node, self.prop_type)[self.prop_index]]]
        elif default is not sentinel:
            return default
        else:
            raise SvNoDataError(self)

"""
type_map_to/from are used to get the bl_idname from a single letter
    
    sockets.type_map_to.get("v")
    >>> "VerticesSocket"

    sockets.type_map_from.get("VerticesSocket")
    >>> "v"

"""

type_map_to = {
    "v": VerticesSocket.bl_idname,
    "m": MatrixSocket.bl_idname,
    "s": StringsSocket.bl_idname,
    "ob": SvObjectSocket.bl_idname,
    "co": SvColorSocket.bl_idname,
    "d": SvDummySocket.bl_idname,
    "q": SvQuaternionSocket.bl_idname,
    "t": SvTextSocket.bl_idname
}

type_map_from = {bl_idname: shortname for shortname, bl_idname in type_map_to.items()}



classes = [
    VerticesSocket, MatrixSocket, StringsSocket,
    SvColorSocket, SvQuaternionSocket, SvDummySocket,
    SvTextSocket, SvObjectSocket
]

register, unregister = bpy.utils.register_classes_factory(classes)
