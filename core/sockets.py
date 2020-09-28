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
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty, FloatProperty, EnumProperty
from bpy.types import NodeTree, NodeSocket

from sverchok.core.socket_conversions import ConversionPolicies, is_vector_to_matrix, FieldImplicitConversionPolicy
from sverchok.core.socket_data import (
    SvGetSocketInfo, SvGetSocket, SvSetSocket, SvForgetSocket,
    SvNoDataError, sentinel)

from sverchok.data_structure import (
    get_other_socket,
    socket_id,
    replace_socket,
    SIMPLE_DATA_TYPES,
    flatten_data, graft_data, map_at_level, wrap_data)

from sverchok.utils.field.scalar import SvConstantScalarField
from sverchok.utils.field.vector import SvMatrixVectorField, SvConstantVectorField
from sverchok.utils.curve import SvCurve, SvReparametrizeCurve
from sverchok.utils.surface import SvSurface

from sverchok.utils.logging import warning

def process_from_socket(self, context):
    """Update function of exposed properties in Sockets"""
    self.node.process_node(context)

class SV_MT_SocketOptionsMenu(bpy.types.Menu):
    bl_label = "Socket Options"

    test : BoolProperty(name="Test")

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'node') and hasattr(context, 'socket')

    def draw(self, context):
        node = context.node
        if not node:
            return
        layout = self.layout
        if hasattr(context.socket, 'draw_menu_items'):
            context.socket.draw_menu_items(context, layout)

class SvSocketProcessing(object):
    # These properties are to be set explicitly by node classes
    # for input sockets, if the node knows it can handle simplified data.
    # For outputs, these properties are not used.
    allow_flatten : BoolProperty(default = False)
    allow_simplify : BoolProperty(default = False)
    allow_graft : BoolProperty(default = False)
    allow_wrap : BoolProperty(default = False)

    # technical property
    skip_simplify_mode_update: BoolProperty(default=False)

    use_graft : BoolProperty(
            name = "Graft",
            default = False,
            update = process_from_socket)

    use_wrap : BoolProperty(
            name = "Wrap",
            default = False,
            update = process_from_socket)

    def update_flatten_flag(self, context):
        if self.skip_simplify_mode_update:
            return

        with self.node.sv_throttle_tree_update():
            try:
                self.skip_simplify_mode_update = True
                if self.use_flatten:
                    self.use_simplify = False
            finally:
                self.skip_simplify_mode_update = False
                
        process_from_socket(self, context)

    def update_simplify_flag(self, context):
        if self.skip_simplify_mode_update:
            return

        with self.node.sv_throttle_tree_update():
            try:
                self.skip_simplify_mode_update = True
                if self.use_simplify:
                    self.use_flatten = False
            finally:
                self.skip_simplify_mode_update = False
                
        process_from_socket(self, context)

    # Only one of properties can be set to true: use_flatten or use_simplfy
    use_flatten : BoolProperty(
            name = "Flatten",
            default = False,
            update = update_flatten_flag)

    use_simplify : BoolProperty(
            name = "Simplify",
            default = False,
            update = update_simplify_flag)

    def can_flatten(self):
        return hasattr(self, 'do_flatten') and (self.allow_flatten or self.is_output)

    def can_simplify(self):
        return hasattr(self, 'do_simplify') and (self.allow_simplify or self.is_output)

    def can_graft(self):
        return self.is_output or self.allow_graft

    def can_wrap(self):
        return self.is_output or self.allow_wrap

    def draw_simplify_modes(self, layout):
        if self.can_flatten():
            layout.prop(self, 'use_flatten')
        if self.can_simplify():
            layout.prop(self, 'use_simplify')

    def preprocess_input(self, data):
        result = data
        if self.use_flatten:
            result = self.do_flatten(data)
        elif self.use_simplify:
            result = self.do_simplify(data)
        if self.use_graft:
            result = self.do_graft(result)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def postprocess_output(self, data):
        result = data
        if self.use_flatten:
            result = self.do_flatten(data)
        elif self.use_simplify:
            result = self.do_simplify(data)
        if self.use_graft:
            result = self.do_graft(result)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def has_simplify_modes(self, context):
        return self.can_flatten() or self.can_simplify()

    def has_menu(self, context):
        return self.has_simplify_modes(context) or self.can_graft() or self.can_wrap()

    def draw_menu_button(self, context, layout, node, text):
        pass

class SvSocketCommon(SvSocketProcessing):
    """ Base class for all Sockets """
    color = (1, 0, 0, 1)  # base color, other sockets should override the property, use FloatProperty for dynamic
    label: StringProperty()  # It will be drawn instead of name if given
    quick_link_to_node = str()  # sockets which often used with other nodes can fill its `bl_idname` here

    use_prop: BoolProperty(default=False)  # set True to use default socket property if it has got it
    custom_draw: StringProperty(description="For name of method which will draw socket UI (optionally)")
    prop_name: StringProperty(default='', description="For displaying node property in socket UI")

    objects_number: IntProperty(min=0)  # utility field for showing number of objects in sockets data

    def get_prop_name(self):
        """
        Intended to return name of property related with socket owned by its node
        Name can be replaced by twin property name in draft mode of a tree
        If does not have 'missing_dependecy' attribute it can return empty list, reasons unknown
        """
        if hasattr(self.node, 'missing_dependecy'):
            return []
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
        """Returns opposite liked socket, if socket is outputs it will return one random opposite linked socket"""
        return get_other_socket(self)

    @property
    def socket_id(self):
        """Id of socket used by data_cache"""
        return str(hash(self.node.node_id + self.identifier))

    @property
    def index(self):
        """Index of socket, hidden sockets are also taken into account"""
        node = self.node
        sockets = node.outputs if self.is_output else node.inputs
        for i, s in enumerate(sockets):
            if s == self:
                return i

    @property
    def hide_safe(self):
        """It will hide even linked sockets"""
        return self.hide

    @hide_safe.setter
    def hide_safe(self, value):
        # handles both input and output.
        if self.is_linked and value:
            for link in self.links:
                self.id_data.sv_links.remove(self.id_data, link)
                self.id_data.links.remove(link)

        self.hide = value

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        """
        The method is used for getting input socket data
        In most cases the method should not be overridden
        If socket uses custom implicit_conversion it should implements default_conversion_name attribute
        Also a socket can use its default_property
        Order of getting data (if available):
        1. writen socket data
        2. node default property
        3. socket default property
        4. script default property
        5. Raise no data error
        :param default: script default property
        :param deepcopy: in most cases should be False for efficiency but not in cases if input data will be modified
        :param implicit_conversions: if needed automatic conversion data from one socket type to another
        :return: data bound to the socket
        """
        if implicit_conversions is None:
            if hasattr(self, 'default_conversion_name'):
                implicit_conversions = ConversionPolicies.get_conversion(self.default_conversion_name)
            else:
                implicit_conversions = ConversionPolicies.DEFAULT.conversion

        if self.is_linked and not self.is_output:
            return self.convert_data(SvGetSocket(self, deepcopy), implicit_conversions)
        elif self.get_prop_name():
            prop = getattr(self.node, self.get_prop_name())
            if isinstance(prop, (str, int, float)):
                return [[prop]]
            elif hasattr(prop, '__len__'):
                # it looks like as some BLender property array - convert to tuple
                return [[prop[:]]]
            else:
                return [prop]
        elif self.use_prop and hasattr(self, 'default_property') and self.default_property is not None:
            default_property = self.default_property
            if isinstance(default_property, (str, int, float)):
                return [[default_property]]
            elif hasattr(default_property, '__len__'):
                # it looks like as some BLender property array - convert to tuple
                return [[default_property[:]]]
            else:
                return [default_property]
        elif default is not sentinel:
            return default
        else:
            raise SvNoDataError(self)

    def sv_set(self, data):
        """Set output data"""
        data = self.postprocess_output(data)
        SvSetSocket(self, data)

    def sv_forget(self):
        """Delete socket memory"""
        SvForgetSocket(self)

    def replace_socket(self, new_type, new_name=None):
        """Replace a socket with a socket of new_type and keep links,
        return the new socket, the old reference might be invalid"""
        return replace_socket(self, new_type, new_name)

    def draw_property(self, layout, prop_origin=None, prop_name='default_property'):
        """
        This method can be overridden for showing property in another way
        Property will be shown only if socket is unconnected input
        If prop_origin is None then the default socket property should be shown
        """
        if prop_origin is None and hasattr(self, prop_name):
            layout.prop(self, 'default_property')
        else:
            layout.prop(prop_origin, prop_name)

    def draw_quick_link(self, context, layout, node):
        """
        Will draw button for creating new node which is often used with such type of sockets
        The socket should have `bl_idname` of other node in `quick_link_to_node` attribute for using this UI
        """
        if self.quick_link_to_node:
            layout.operator('node.sv_quicklink_new_node_input', text="", icon="PLUGIN")

    def draw(self, context, layout, node, text):

        # just handle custom draw..be it input or output.
        if self.custom_draw:
            # does the node have the draw function referred to by
            # the string stored in socket's custom_draw attribute
            if hasattr(node, self.custom_draw):
                getattr(node, self.custom_draw)(self, context, layout)

        elif self.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=(self.label or text) + f". {self.objects_number or ''}")

        elif self.is_output:  # unlinked OUTPUT
            layout.label(text=self.label or text)

        else:  # unlinked INPUT
            if self.get_prop_name():  # has property
                self.draw_property(layout, prop_origin=node, prop_name=self.get_prop_name())

            elif self.use_prop:  # no property but use default prop
                self.draw_property(layout)

            else:  # no property and not use default prop
                self.draw_quick_link(context, layout, node)
                layout.label(text=self.label or text)

        if self.has_menu(context):
            self.draw_menu_button(context, layout, node, text)

    def draw_color(self, context, node):
        return self.color

    def needs_data_conversion(self):
        """True if other socket has got different type"""
        if not self.is_linked:
            return False
        return self.other.bl_idname != self.bl_idname

    def convert_data(self, source_data, implicit_conversions=ConversionPolicies.DEFAULT.conversion):
        if not self.needs_data_conversion():
            return source_data
        else:
            self.node.debug(f"Trying to convert data for input socket {self.name} by {implicit_conversions}")
            return implicit_conversions.convert(self, source_data)

    def update_objects_number(self):
        """
        Should be called each time after process method of the socket owner
        It will update number of objects to show in socket labels
        """
        try:
            if self.is_output:
                objects_info = SvGetSocketInfo(self)
                self.objects_number = int(objects_info) if objects_info else 0
            else:
                data = self.sv_get(deepcopy=False, default=[])
                self.objects_number = len(data) if data else 0
        except Exception as e:
            warning(f"Socket='{self.name}' of node='{self.node.name}' can't update number of objects on the label. "
                    f"Cause is '{e}'")
            self.objects_number = 0

    @property
    def properties_to_skip_iojson(self):
        """
        Used during serialization process
        Should be overridden in this way: return super().properties_to_skip_iojson + ['my_property']
        """
        skip_serialization_attributes = {
            # all this attributes can be skipped because they are static, they are always set only in sv_init method
            # but the attribute should be removed from this list if its value is changed outside sv_init method
            'quick_link_to_node', 'custom_draw', 'prop_name', 'use_prop',
            # utils attributes, Sverchok itself knows what to put in them
            'objects_number'
        }
        return skip_serialization_attributes


class SvObjectSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvObjectSocket"
    bl_label = "Object Socket"

    def filter_kinds(self, object):
        """
        object_kinds could be any of these:
         [‘MESH’, ‘CURVE’, ‘SURFACE’, ‘META’, ‘FONT’, ‘VOLUME’, ‘ARMATURE’, ‘LATTICE’,
         ‘EMPTY’, ‘GPENCIL’, ‘CAMERA’, ‘LIGHT’, ‘SPEAKER’, ‘LIGHT_PROBE’, ‘EMPTY’

        for example
            socket.object_kinds = "MESH"
        or if you want various kinds
            socket.object_kinds = "MESH,CURVE"
        """
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

    color = (0.69, 0.74, 0.73, 1.0)
    use_prop: BoolProperty(default=True)

    object_kinds: StringProperty(default='ALL')  # use for filtering objects, see filter_kinds method
    object_ref: StringProperty(update=process_from_socket)
    object_ref_pointer: bpy.props.PointerProperty(
        name="Object Reference",
        poll=filter_kinds,  # seld.object_kinds can be "MESH" or "MESH,CURVE,.."
        type=bpy.types.Object, # what kind of objects are we showing
        update=process_from_socket)

    @property
    def default_property(self):
        # this can be more granular and even attempt to set object_ref_points from object_ref, and then wipe object_ref
        return self.node.get_bpy_data_from_name(self.object_ref or self.object_ref_pointer, bpy.data.objects)

    def draw_property(self, layout, prop_origin=None, prop_name='default_property'):
        if prop_origin:
            layout.prop(prop_origin, prop_name)  # need for consistency, probably will never be used
        else:
            layout.prop_search(self, 'object_ref_pointer', bpy.data, 'objects', text=self.name)


class SvTextSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvTextSocket"
    bl_label = "Text Socket"

    color = (0.68,  0.85,  0.90, 1)

    default_property: StringProperty(update=process_from_socket)

class SvMatrixSocket(NodeSocket, SvSocketCommon):
    '''4x4 matrix Socket type'''

    bl_idname = "SvMatrixSocket"
    bl_label = "Matrix Socket"

    color = (0.2, 0.8, 0.8, 1.0)
    quick_link_to_node = 'SvMatrixInNodeMK4'

class SvVerticesSocket(NodeSocket, SvSocketCommon):
    '''For vertex data'''
    bl_idname = "SvVerticesSocket"
    bl_label ="Vertices Socket"

    color = (0.9, 0.6, 0.2, 1.0)
    quick_link_to_node = 'GenVectorsNode'

    # this property is needed for back capability, after renaming prop to default_property
    # should be removed after https://github.com/nortikin/sverchok/issues/3514
    # using via default_property property
    prop: FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)

    expanded: BoolProperty(default=False)  # for minimizing showing socket property

    def draw_menu_button(self, context, layout, node, text):
        if (self.is_output or self.is_linked or not self.use_prop):
            layout.menu('SV_MT_SocketOptionsMenu', text='', icon='TRIA_DOWN')

    def draw_menu_items(self, context, layout):
        self.draw_simplify_modes(layout)
        if self.can_graft():
            layout.prop(self, 'use_graft')
        if self.can_wrap():
            layout.prop(self, 'use_wrap')

    def do_simplify(self, data):
        return flatten_data(data, 2)

    @property
    def default_property(self):
        return self.prop

    @default_property.setter
    def default_property(self, value):
        self.prop = value

    def draw_property(self, layout, prop_origin=None, prop_name='prop'):
        if prop_origin is None:
            prop_origin = self

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
            row.template_component_menu(prop_origin, prop_name, name=self.name)

    def do_graft(self, data):
        return graft_data(data, item_level=1)

class SvQuaternionSocket(NodeSocket, SvSocketCommon):
    '''For quaternion data'''
    bl_idname = "SvQuaternionSocket"
    bl_label = "Quaternion Socket"

    color = (0.9, 0.4, 0.7, 1.0)

    default_property: FloatVectorProperty(default=(1, 0, 0, 0), size=4, subtype='QUATERNION',
                                          update=process_from_socket)
    expanded: BoolProperty(default=False)  # for minimizing showing socket property

    def draw_property(self, layout, prop_origin=None, prop_name='prop'):
        if prop_origin is None:
            prop_origin = self

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
            row.template_component_menu(prop_origin, prop_name, name=self.name)

class SvColorSocket(NodeSocket, SvSocketCommon):
    '''For color data'''
    bl_idname = "SvColorSocket"
    bl_label = "Color Socket"

    color = (0.9, 0.8, 0.0, 1.0)

    default_property: FloatVectorProperty(default=(0, 0, 0, 1), size=4, subtype='COLOR', min=0, max=1,
                                          update=process_from_socket)
    expanded: BoolProperty(default=False)  # for minimizing showing socket property

    def draw_property(self, layout, prop_origin=None, prop_name='default_property'):
        if prop_origin is None:
            prop_origin = self

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
            row.prop(prop_origin, prop_name)

class SvDummySocket(NodeSocket, SvSocketCommon):
    '''Dummy Socket for sockets awaiting assignment of type'''
    bl_idname = "SvDummySocket"
    bl_label = "Dummys Socket"

    color = (0.8, 0.8, 0.8, 0.3)

    def sv_get(self):
        if self.is_linked:
            return self.links[0].bl_idname


class SvSeparatorSocket(NodeSocket, SvSocketCommon):
    ''' Separator Socket used to separate groups of sockets '''
    bl_idname = "SvSeparatorSocket"
    bl_label = "Separator Socket"

    color = (0.0, 0.0, 0.0, 0.0)

    def draw(self, context, layout, node, text):
        # layout.label("")
        layout.label(text="——————")


class SvStringsSocket(NodeSocket, SvSocketCommon):
    '''Generic, mostly numbers, socket type'''
    bl_idname = "SvStringsSocket"
    bl_label = "Strings Socket"

    color = (0.6, 1.0, 0.6, 1.0)

    use_graft_2 : BoolProperty(
            name = "Graft Topology",
            default = False,
            update = process_from_socket)

    def get_prop_data(self):
        if self.get_prop_name():
            return {"prop_name": self.get_prop_name()}
        elif self.prop_type:
            return {"prop_type": self.prop_type,
                    "prop_index": self.prop_index}
        else:
            return {}

    quick_link_to_node: StringProperty()  # this can be overridden by socket instances

    default_property_type: bpy.props.EnumProperty(items=[(i, i, '') for i in ['float', 'int']])
    default_float_property: bpy.props.FloatProperty(update=process_from_socket)
    default_int_property: bpy.props.IntProperty(update=process_from_socket)

    @property
    def default_property(self):
        return self.default_float_property if self.default_property_type == 'float' else self.default_int_property

    def draw_property(self, layout, prop_origin=None, prop_name=None):
        if prop_origin and prop_name:
            layout.prop(prop_origin, prop_name)
        elif self.use_prop:
            if self.default_property_type == 'float':
                layout.prop(self, 'default_float_property', text=self.name)
            elif self.default_property_type == 'int':
                layout.prop(self, 'default_int_property', text=self.name)

    def draw_menu_button(self, context, layout, node, text):
        if (self.is_output or self.is_linked or not self.prop_name):
            layout.menu('SV_MT_SocketOptionsMenu', text='', icon='TRIA_DOWN')

    def draw_menu_items(self, context, layout):
        self.draw_simplify_modes(layout)
        if self.can_graft():
            layout.prop(self, 'use_graft')
            if not self.use_flatten:
                layout.prop(self, 'use_graft_2')
        if self.can_wrap():
            layout.prop(self, 'use_wrap')

    def do_flatten(self, data):
        return flatten_data(data, 1)

    def do_simplify(self, data):
        return flatten_data(data, 2)

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types = SIMPLE_DATA_TYPES + (SvCurve, SvSurface))

class SvFilePathSocket(NodeSocket, SvSocketCommon):
    '''For file path data'''
    bl_idname = "SvFilePathSocket"
    bl_label = "File Path Socket"

    color = (0.9, 0.9, 0.3, 1.0)
    quick_link_to_node = 'SvFilePathNode'


class SvSvgSocket(NodeSocket, SvSocketCommon):
    '''For file path data'''
    bl_idname = "SvSvgSocket"
    bl_label = "SVG Data Socket"

    color = (0.1, 0.5, 1, 1.0)

    @property
    def quick_link_to_node(self):
        if "Fill / Stroke" in self.name:
            return "SvSvgFillStrokeNodeMk2"
        elif "Pattern" in self.name:
            return "SvSvgPatternNode"
        else:
            return


    def do_flattern(self, data):
        return flattern_data(data, 1)

    def do_simplify(self, data):
        return flattern_data(data, 2)

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types = SIMPLE_DATA_TYPES + (SvCurve, SvSurface))

    def do_graft_2(self, data):
        def to_zero_base(lst):
            m = min(lst)
            return [x - m for x in lst]

        result = map_at_level(to_zero_base, data, item_level=1, data_types = SIMPLE_DATA_TYPES + (SvCurve, SvSurface))
        result = graft_data(result, item_level=1, data_types = SIMPLE_DATA_TYPES + (SvCurve, SvSurface))
        return result

    def preprocess_input(self, data):
        result = data
        if self.use_flatten:
            result = self.do_flatten(data)
        elif self.use_simplify:
            result = self.do_simplify(data)
        if self.use_graft:
            result = self.do_graft(result)
        elif not self.use_flatten and self.use_graft_2:
            result = self.do_graft_2(result)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def postprocess_output(self, data):
        result = data
        if self.use_flatten:
            result = self.do_flatten(data)
        elif self.use_simplify:
            result = self.do_simplify(data)
        if self.use_graft:
            result = self.do_graft(result)
        elif self.use_graft_2:
            result = self.do_graft_2(result)
        if self.use_wrap:
            result = wrap_data(result)
        return result

class SvDictionarySocket(NodeSocket, SvSocketCommon):
    '''For dictionary data'''
    bl_idname = "SvDictionarySocket"
    bl_label = "Dictionary Socket"

    color = (1.0, 1.0, 1.0, 1.0)

class SvChameleonSocket(NodeSocket, SvSocketCommon):
    '''Using as input socket with color of other connected socket'''
    bl_idname = "SvChameleonSocket"
    bl_label = "Chameleon Socket"

    color: FloatVectorProperty(default=(0.0, 0.0, 0.0, 0.0), size=4,
                               description="For storing color of other socket via catch_props method")
    dynamic_type: StringProperty(default='SvChameleonSocket',
                                 description="For storing type of other socket via catch_props method")

    def catch_props(self):
        # should be called during update event of a node for catching its property
        other = self.other
        if other:
            self.color = other.color
            self.dynamic_type = other.bl_idname
        else:
            self.color = (0.0, 0.0, 0.0, 0.0)
            self.dynamic_type = self.bl_idname

class SvSurfaceSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvSurfaceSocket"
    bl_label = "Surface Socket"

    color = (0.4, 0.2, 1.0, 1.0)

    def draw_menu_button(self, context, layout, node, text):
        layout.menu('SV_MT_SocketOptionsMenu', text='', icon='TRIA_DOWN')

    def draw_menu_items(self, context, layout):
        self.draw_simplify_modes(layout)
        if self.can_graft():
            layout.prop(self, 'use_graft')
        if self.can_wrap():
            layout.prop(self, 'use_wrap')

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(SvSurface,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(SvSurface,))

class SvCurveSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvCurveSocket"
    bl_label = "Curve Socket"

    color = (0.5, 0.6, 1.0, 1.0)

    reparametrize: BoolProperty(
            name = "Reparametrize",
            default = False,
            update = process_from_socket)

    def draw_menu_button(self, context, layout, node, text):
        layout.menu('SV_MT_SocketOptionsMenu', text='', icon='TRIA_DOWN')

    def draw_menu_items(self, context, layout):
        self.draw_simplify_modes(layout)
        if self.can_graft():
            layout.prop(self, 'use_graft')
        if self.can_wrap():
            layout.prop(self, 'use_wrap')
        layout.prop(self, 'reparametrize')

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(SvCurve,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(SvCurve,))

    def preprocess_input(self, data):
        data = SvSocketCommon.preprocess_input(self, data)
        if self.reparametrize:
            data = map_at_level(SvReparametrizeCurve, data, data_types=(SvCurve,))
        return data

    def postprocess_output(self, data):
        data = SvSocketCommon.postprocess_output(self, data)
        if self.reparametrize:
            data = map_at_level(SvReparametrizeCurve, data, data_types=(SvCurve,))
        return data

class SvScalarFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvScalarFieldSocket"
    bl_label = "Scalar Field Socket"

    color = (0.9, 0.4, 0.1, 1.0)
    default_conversion_name = ConversionPolicies.FIELD.conversion_name

class SvVectorFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvVectorFieldSocket"
    bl_label = "Vector Field Socket"

    color = (0.1, 0.1, 0.9, 1.0)
    default_conversion_name = ConversionPolicies.FIELD.conversion_name

class SvSolidSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvSolidSocket"
    bl_label = "Solid Socket"

    color = (0.0, 0.65, 0.3, 1.0)


class SvLinkNewNodeInput(bpy.types.Operator):
    ''' Spawn and link new node to the left of the caller node'''
    bl_idname = "node.sv_quicklink_new_node_input"
    bl_label = "Add a new node to the left"

    def execute(self, context):
        tree, node, socket = context.node.id_data, context.node, context.socket

        new_node = tree.nodes.new(socket.quick_link_to_node)
        links_number = len([s for s in node.inputs if s.is_linked])
        new_node.location = (node.location[0] - 200, node.location[1] - 100 * links_number)
        tree.links.new(new_node.outputs[0], socket)

        if node.parent:
            new_node.parent = node.parent
            new_node.location = new_node.absolute_location

        new_node.process_node(context)

        return {'FINISHED'}


classes = [
    SV_MT_SocketOptionsMenu,
    SvVerticesSocket, SvMatrixSocket, SvStringsSocket, SvFilePathSocket,
    SvColorSocket, SvQuaternionSocket, SvDummySocket, SvSeparatorSocket,
    SvTextSocket, SvObjectSocket, SvDictionarySocket, SvChameleonSocket,
    SvSurfaceSocket, SvCurveSocket, SvScalarFieldSocket, SvVectorFieldSocket,
    SvSolidSocket, SvSvgSocket, SvLinkNewNodeInput
]

register, unregister = bpy.utils.register_classes_factory(classes)
