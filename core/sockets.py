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

from sverchok.core.socket_conversions import (
        DefaultImplicitConversionPolicy,
        FieldImplicitConversionPolicy,
        is_vector_to_matrix
    )

from sverchok.core.socket_data import (
    SvGetSocketInfo, SvGetSocket, SvSetSocket, SvForgetSocket,
    SvNoDataError, sentinel)

from sverchok.data_structure import (
    updateNode,
    get_other_socket,
    socket_id,
    replace_socket)

from sverchok.utils.field.scalar import SvConstantScalarField
from sverchok.utils.field.vector import SvMatrixVectorField, SvConstantVectorField

socket_colors = {
    "SvStringsSocket": (0.6, 1.0, 0.6, 1.0),
    "SvVerticesSocket": (0.9, 0.6, 0.2, 1.0),
    "SvQuaternionSocket": (0.9, 0.4, 0.7, 1.0),
    "SvColorSocket": (0.9, 0.8, 0.0, 1.0),
    "SvMatrixSocket": (0.2, 0.8, 0.8, 1.0),
    "SvDummySocket": (0.8, 0.8, 0.8, 0.3),
    "SvSeparatorSocket": (0.0, 0.0, 0.0, 0.0),
    "SvObjectSocket": (0.69, 0.74, 0.73, 1.0),
    "SvTextSocket": (0.68, 0.85, 0.90, 1),
    "SvDictionarySocket": (1.0, 1.0, 1.0, 1.0),
    "SvFilePathSocket": (0.9, 0.9, 0.3, 1.0),

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
    custom_draw: StringProperty(description="For name of method which will draw socket UI (optionally)")
    prop_name: StringProperty(default='', description="For displaying node property in socket UI")

    quicklink_func_name: StringProperty(default="", name="quicklink_func_name")

    def get_prop_name(self):
        if self.node and hasattr(self.node, 'does_support_draft_mode') and self.node.does_support_draft_mode() and hasattr(self.node.id_data, 'sv_draft') and self.node.id_data.sv_draft:
            prop_name_draft = self.node.draft_properties_mapping.get(self.prop_name, None)
            if prop_name_draft:
                return prop_name_draft
            else:
                return self.prop_name
        else:
            return self.prop_name

    @property
    def other(self):
        return get_other_socket(self)

    def set_default(self, value):
        if self.get_prop_name():
            setattr(self.node, self.get_prop_name(), value)

    @property
    def socket_id(self):
        """Id of socket used by data_cache"""
        return str(hash(self.node.node_id + self.identifier))

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
        if self.is_linked and value:
            for link in self.links:
                self.id_data.sv_links.remove(self.id_data, link)
                self.id_data.links.remove(link)

        self.hide = value

    def sv_set(self, data):
        """Set output data"""
        SvSetSocket(self, data)

    def sv_forget(self):
        """Delete socket memory"""
        SvForgetSocket(self)

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

        if self.bl_idname == "SvStringsSocket":
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

    def infer_visible_location_of_socket(self, node):
        # currently only handles inputs.
        if self.is_output:
            return 0

        counter = 0
        for socket in node.inputs:
            if not socket.hide:
                if socket == self:
                    break
                counter += 1

        return counter

    def draw_quick_link(self, context, layout, node):

        if self.use_quicklink:
            if self.bl_idname == "SvMatrixSocket":
                new_node_idname = "SvMatrixInNodeMK4"
            elif self.bl_idname == "SvVerticesSocket":
                new_node_idname = "GenVectorsNode"
            else:
                return

            op = layout.operator('node.sv_quicklink_new_node_input', text="", icon="PLUGIN")
            op.socket_index = self.index
            op.origin = node.name
            op.new_node_idname = new_node_idname
            op.new_node_offsetx = -200 - 40 * self.index  ## this is not so useful, we should infer visible socket location
            op.new_node_offsety = -30 * self.index  ## this is not so useful, we should infer visible socket location

    def draw(self, context, layout, node, text):

        # just handle custom draw..be it input or output.
        # hasattr may be excessive here
        if hasattr(self, 'custom_draw') and self.custom_draw:
            # does the node have the draw function referred to by
            # the string stored in socket's custom_draw attribute
            if hasattr(node, self.custom_draw):
                getattr(node, self.custom_draw)(self, context, layout)
                return

        if self.bl_idname == 'SvStringsSocket':
            if node.bl_idname in {'SvScriptNodeLite', 'SvScriptNode'}:
                if not self.is_output and not self.is_linked and self.prop_type:
                    layout.prop(node, self.prop_type, index=self.prop_index, text=self.name)
                    return
            elif node.bl_idname in {'SvSNFunctor'} and not self.is_output:
                if not self.is_linked:
                    layout.prop(node, self.get_prop_name(), text=self.name)
                    return

        if self.is_linked:  # linked INPUT or OUTPUT
            t = text
            if not self.is_output:
                if self.get_prop_name():
                    prop = node.rna_type.properties.get(self.get_prop_name(), None)
                    t = prop.name if prop else text
            info_text = t + '. ' + SvGetSocketInfo(self)
            info_text += self.extra_info
            layout.label(text=info_text)

        elif self.is_output:  # unlinked OUTPUT
            layout.label(text=text)

        else:  # unlinked INPUT
            if self.get_prop_name():  # has property
                self.draw_expander_template(context, layout, prop_origin=node, prop_name=self.get_prop_name())

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

def filter_kinds(self, object):
    if self.object_kinds in {'ALL', ''}:
        return True

    if not self.object_kinds:
        return True
    kind = self.object_kinds
    if "," in kind:
        kinds = kind.split(',')
        if object.type in set(kinds):
            return True
    if object.type == kind:
        return True

class SvObjectSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvObjectSocket"
    bl_label = "Object Socket"

    """
    object_kinds could be any of these:
     [‘MESH’, ‘CURVE’, ‘SURFACE’, ‘META’, ‘FONT’, ‘VOLUME’, ‘ARMATURE’, ‘LATTICE’,
     ‘EMPTY’, ‘GPENCIL’, ‘CAMERA’, ‘LIGHT’, ‘SPEAKER’, ‘LIGHT_PROBE’, ‘EMPTY’

    for example
        socket.object_kinds = "MESH"
    or if you want various kinds
        socket.object_kinds = "MESH,CURVE"
    """
    object_kinds: StringProperty(default='ALL')
    object_ref: StringProperty(update=process_from_socket)
    object_ref_pointer: bpy.props.PointerProperty(
        name="Object Reference",
        poll=filter_kinds,  # seld.object_kinds can be "MESH" or "MESH,CURVE,.."
        type=bpy.types.Object, # what kind of objects are we showing
        update=process_from_socket)

    def draw(self, context, layout, node, text):
        if self.custom_draw:
            super().draw(context, layout, node, text)
        elif not self.is_output and not self.is_linked:
            layout.prop_search(self, 'object_ref_pointer', bpy.data, 'objects', text=self.name)
        elif self.is_linked:
            layout.label(text=text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text=text)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        elif self.object_ref or self.object_ref_pointer:
            # this can be more granular and even attempt to set object_ref_points from object_ref, and then wipe object_ref
            obj_ref = self.node.get_bpy_data_from_name(self.object_ref or self.object_ref_pointer, bpy.data.objects)
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

class SvMatrixSocket(NodeSocket, SvSocketCommon):
    '''4x4 matrix Socket type'''

    bl_idname = "SvMatrixSocket"
    bl_label = "Matrix Socket"

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


class SvVerticesSocket(NodeSocket, SvSocketCommon):
    '''For vertex data'''
    bl_idname = "SvVerticesSocket"
    bl_label ="Vertices Socket"

    prop: FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": socket.get_prop_name()}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy = True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.get_prop_name():
            return [[getattr(self.node, self.get_prop_name())[:]]]
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
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": socket.get_prop_name()}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy = True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.get_prop_name():
            return [[getattr(self.node, self.get_prop_name())[:]]]
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
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": socket.get_prop_name()}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)

        if self.get_prop_name():
            return [[getattr(self.node, self.get_prop_name())[:]]]
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
    use_prop: BoolProperty(default=False)

    def get_prop_data(self):
        return self.other.get_prop_data()

    def sv_get(self):
        if self.is_linked:
            return self.links[0].bl_idname

    def sv_type_conversion(self, new_self):
        self = new_self

class SvSeparatorSocket(NodeSocket, SvSocketCommon):
    ''' Separator Socket used to separate groups of sockets '''
    bl_idname = "SvSeparatorSocket"
    bl_label = "Separator Socket"

    def draw(self, context, layout, node, text):
        # layout.label("")
        layout.label(text="——————")

    def remove_links(self):
        # print("separator sockets removing links")
        for link in self.links:
            self.id_data.links.remove(link)


class SvStringsSocket(NodeSocket, SvSocketCommon):
    '''Generic, mostly numbers, socket type'''
    bl_idname = "SvStringsSocket"
    bl_label = "Strings Socket"

    prop_type: StringProperty(default='')
    prop_index: IntProperty()

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": self.get_prop_name()}
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
        elif self.get_prop_name():
            # to deal with subtype ANGLE, this solution should be considered temporary...
            _, prop_dict = getattr(self.node.rna_type, self.get_prop_name(), (None, {}))
            subtype = prop_dict.get("subtype", "")
            if subtype == "ANGLE":
                return [[math.degrees(getattr(self.node, self.get_prop_name()))]]
            return [[getattr(self.node, self.get_prop_name())]]
        elif self.prop_type:
            return [[getattr(self.node, self.prop_type)[self.prop_index]]]
        elif default is not sentinel:
            return default
        else:
            raise SvNoDataError(self)

class SvFilePathSocket(NodeSocket, SvSocketCommon):
    '''For file path data'''
    bl_idname = "SvFilePathSocket"
    bl_label = "File Path Socket"

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        else:
            return [[self.default_value]]

class SvDictionarySocket(NodeSocket, SvSocketCommon):
    '''For dictionary data'''
    bl_idname = "SvDictionarySocket"
    bl_label = "Dictionary Socket"

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": self.get_prop_name()}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.get_prop_name():
            return [[getattr(self.node, self.get_prop_name())[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default


class SvChameleonSocket(NodeSocket, SvSocketCommon):
    '''Using as input socket with color of other connected socket'''
    bl_idname = "SvChameleonSocket"
    bl_label = "Chameleon Socket"

    dynamic_color: FloatVectorProperty(default=(0.0, 0.0, 0.0, 0.0), size=4,
                                       description="For storing color of other socket via catch_props method")
    dynamic_type: StringProperty(default='SvChameleonSocket',
                                 description="For storing type of other socket via catch_props method")

    def catch_props(self):
        # should be called during update event of a node for catching its property
        other = self.other
        if other:
            self.dynamic_color = socket_colors[other.bl_idname]
            self.dynamic_type = other.bl_idname
        else:
            self.dynamic_color = (0.0, 0.0, 0.0, 0.0)
            self.dynamic_type = self.bl_idname

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": self.get_prop_name()}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)

        if self.get_prop_name():
            return [[getattr(self.node, self.get_prop_name())[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

    def draw_color(self, context, node):
        return self.dynamic_color

class SvSurfaceSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvSurfaceSocket"
    bl_label = "Surface Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.4, 0.2, 1.0, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class SvCurveSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvCurveSocket"
    bl_label = "Curve Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.5, 0.6, 1.0, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class SvScalarFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvScalarFieldSocket"
    bl_label = "Scalar Field Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.9, 0.4, 0.1, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if implicit_conversions is None:
            implicit_conversions = FieldImplicitConversionPolicy
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class SvVectorFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvVectorFieldSocket"
    bl_label = "Vector Field Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.1, 0.1, 0.9, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if implicit_conversions is None:
            implicit_conversions = FieldImplicitConversionPolicy
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

"""
type_map_to/from are used to get the bl_idname from a single letter

    sockets.type_map_to.get("v")
    >>> "SvVerticesSocket"

    sockets.type_map_from.get("SvVerticesSocket")
    >>> "v"

"""

type_map_to = {
    "v": SvVerticesSocket.bl_idname,
    "m": SvMatrixSocket.bl_idname,
    "s": SvStringsSocket.bl_idname,
    "ob": SvObjectSocket.bl_idname,
    "co": SvColorSocket.bl_idname,
    "d": SvDummySocket.bl_idname,
    "q": SvQuaternionSocket.bl_idname,
    "t": SvTextSocket.bl_idname,
    "f": SvFilePathSocket.bl_idname
}

type_map_from = {bl_idname: shortname for shortname, bl_idname in type_map_to.items()}



classes = [
    SvVerticesSocket, SvMatrixSocket, SvStringsSocket, SvFilePathSocket,
    SvColorSocket, SvQuaternionSocket, SvDummySocket, SvSeparatorSocket,
    SvTextSocket, SvObjectSocket, SvDictionarySocket, SvChameleonSocket,
    SvSurfaceSocket, SvCurveSocket, SvScalarFieldSocket, SvVectorFieldSocket
]

register, unregister = bpy.utils.register_classes_factory(classes)
