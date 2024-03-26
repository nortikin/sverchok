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
import inspect
import sys
from typing import Set

from mathutils import Matrix, Quaternion
import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty, FloatProperty, EnumProperty, \
    PointerProperty
from bpy.types import NodeTree, NodeSocket

from sverchok.core.socket_conversions import ConversionPolicies
from sverchok.core.socket_data import sv_get_socket, sv_set_socket, sv_forget_socket
from sverchok.core.sv_custom_exceptions import SvNoDataError

from sverchok.data_structure import (
    enum_item_4,
    get_other_socket, replace_socket,
    SIMPLE_DATA_TYPES,
    flatten_data, graft_data, map_at_level, wrap_data, unwrap_data)

from sverchok.settings import get_param

from sverchok.utils.handle_blender_data import get_func_and_args, BlDomains
from sverchok.utils.socket_utils import format_bpy_property, setup_new_node_location
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvVectorField
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.algorithms import reparametrize_curve
from sverchok.utils.surface import SvSurface

from sverchok.dependencies import FreeCAD

STANDARD_TYPES = SIMPLE_DATA_TYPES + (SvCurve, SvSurface)
if FreeCAD is not None:
    import Part
    STANDARD_TYPES = STANDARD_TYPES + (Part.Shape,)

InterfaceSocket = bpy.types.NodeTreeInterfaceSocket if bpy.app.version >= (4, 0) \
             else bpy.types.NodeSocketInterface


def process_from_socket(self, context):
    """Update function of exposed properties in Sockets"""
    if self.node is not None:  # https://developer.blender.org/T88587
        self.node.process_node(context)


def update_interface(self, context):
    """Update group node sockets and update it"""
    # For now I don't think that `hide value` property should call this function, but in some cases it could be useful
    # if interface socket will get min and max value parameter then probably Sv sockets also should get it
    if not self.id_data.group_node_name:  # initialization tree
        return
    self.id_data.update_sockets()
    group_tree = self.id_data
    group_node = group_tree.get_update_path()[-1]
    input_node = group_node.active_input()
    if input_node:
        group_tree.update_nodes([input_node])


def socket_type_names() -> Set[str]:
    names = set()
    for name, member in inspect.getmembers(sys.modules[__name__]):
        is_module_cls = inspect.isclass(member) and member.__module__ == __name__
        if is_module_cls:
            if NodeSocket in member.__bases__:
                names.add(member.bl_idname)
    return names


class SV_MT_AllSocketsOptionsMenu(bpy.types.Menu):
    bl_label = "Sockets Options"

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'node')# and hasattr(context, 'socket')

    def draw(self, context):
        node = context.active_node

        if not node:
            return
        layout = self.layout

        for s in node.outputs:
            if hasattr(s, 'draw_menu_items'):
                layout.context_pointer_set("socket", s)
                layout.context_pointer_set("node", node)
                layout.menu('SV_MT_SocketOptionsMenu', text=s.name)


class SV_MT_SocketOptionsMenu(bpy.types.Menu):
    bl_label = "Socket Options"

    def draw(self, context):
        node = context.node
        if not node:
            return
        layout = self.layout
        if hasattr(context.socket, 'draw_menu_items'):
            context.socket.draw_menu_items(context, layout)

class SvSocketProcessing():
    """
    Mixin class for data processing logic of a socket.
    """
    # These properties are to be set explicitly by node classes
    # for input sockets, if the node knows it can handle simplified data.
    # For outputs, these properties are not used.
    allow_flatten : BoolProperty(default = False)
    allow_flatten_topology : BoolProperty(default = False)
    allow_simplify : BoolProperty(default = False)
    allow_graft : BoolProperty(default = False)
    allow_unwrap : BoolProperty(default = False)
    allow_wrap : BoolProperty(default = False)

    # technical property
    skip_simplify_mode_update: BoolProperty(default=False)
    skip_wrap_mode_update: BoolProperty(default=False)

    use_graft : BoolProperty(
            name = "Graft",
            default = False,
            update = process_from_socket)

    def update_unwrap_flag(self, context):
        if self.skip_wrap_mode_update:
            return

        try:
            self.skip_wrap_mode_update = True
            if self.use_unwrap:
                self.use_wrap = False
        finally:
            self.skip_wrap_mode_update = False

        process_from_socket(self, context)

    def update_wrap_flag(self, context):
        if self.skip_wrap_mode_update:
            return

        try:
            self.skip_wrap_mode_update = True
            if self.use_wrap:
                self.use_unwrap = False
        finally:
            self.skip_wrap_mode_update = False

        process_from_socket(self, context)

    use_unwrap : BoolProperty(
            name = "Unwrap",
            default = False,
            update = update_unwrap_flag)

    use_wrap : BoolProperty(
            name = "Wrap",
            default = False,
            update = update_wrap_flag)

    def update_flatten_flag(self, context):
        if self.skip_simplify_mode_update:
            return

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

        try:
            self.skip_simplify_mode_update = True
            if self.use_simplify:
                self.use_flatten = False
        finally:
            self.skip_simplify_mode_update = False

        process_from_socket(self, context)

    use_flatten_topology : BoolProperty(
        name = "Flatten Topology",
        default = False,
        update = process_from_socket)
    # Only one of properties can be set to true: use_flatten or use_simplfy
    use_flatten : BoolProperty(
            name = "Flatten",
            default = False,
            update = update_flatten_flag)

    use_simplify : BoolProperty(
            name = "Simplify",
            default = False,
            update = update_simplify_flag)

    def get_mode_flags(self):
        flags = []
        if self.use_flatten:
            flags.append('F')
        if self.use_flatten_topology:
            flags.append('FT')
        if self.use_simplify:
            flags.append('S')
        if self.use_graft:
            flags.append('G')
        if self.use_unwrap:
            flags.append('U')
        if self.use_wrap:
            flags.append('W')
        return flags

    def can_flatten(self):
        return hasattr(self, 'do_flatten') and (self.allow_flatten or self.is_output)

    def can_flatten_topology(self):
        return hasattr(self, 'do_flat_topology') and (self.allow_flatten_topology or self.is_output)

    def can_simplify(self):
        return hasattr(self, 'do_simplify') and (self.allow_simplify or self.is_output)

    def can_graft(self):
        return hasattr(self, 'do_graft') and (self.is_output or self.allow_graft)

    def can_unwrap(self):
        return self.is_output or self.allow_unwrap

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
        if self.use_unwrap:
            result = unwrap_data(result, socket=self)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def postprocess_output(self, data):
        result = data
        if self.use_flatten_topology:
            result = self.do_flat_topology(data)
        if self.use_flatten:
            result = self.do_flatten(data)
        elif self.use_simplify:
            result = self.do_simplify(data)
        if self.use_graft:
            result = self.do_graft(result)
        if self.use_unwrap:
            result = unwrap_data(result, socket=self)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def has_simplify_modes(self, context):
        return self.can_flatten() or self.can_simplify()

    def has_menu(self, context):
        return self.has_simplify_modes(context) or self.can_graft() or self.can_wrap()

    def draw_menu_button(self, context, layout, node, text):
        if hasattr(node.id_data, 'sv_show_socket_menus') and node.id_data.sv_show_socket_menus:
            if (self.is_output or self.is_linked or not self.use_prop):
                layout.menu('SV_MT_SocketOptionsMenu', text='', icon='TRIA_DOWN')

    def draw_menu_items(self, context, layout):
        if self.can_flatten_topology():
            layout.prop(self, 'use_flatten_topology')
        self.draw_simplify_modes(layout)
        if self.can_graft():
            layout.prop(self, 'use_graft')
        if self.can_unwrap():
            layout.prop(self, 'use_unwrap')
        if self.can_wrap():
            layout.prop(self, 'use_wrap')

    def copy_options(self, other):
        for identifier, prop in SvSocketProcessing.__annotations__.items():
            if isinstance(prop, bpy.props._PropertyDeferred):
                setattr(self, identifier, getattr(other, identifier))


class SocketDomain:
    """Socket mix-in class to define domain options
    The option is shown when socket is connected
    and can be used for transferring data to certain elements of an object."""
    domain: EnumProperty(items=[(d.name, d.value, '') for d in BlDomains],
                         update=process_from_socket)
    show_domain: BoolProperty()


class SvSocketCommon(SvSocketProcessing):
    """
    Base class for all Sockets

    'SKIP_SAVE' in properties means skipping them during saving in JSON format
    some of the properties can be skipped because they are static, they are always set only in sv_init method
    """

    color = (1, 0, 0, 1)  # base color, other sockets should override the property, use FloatProperty for dynamic
    default_conversion_name = ConversionPolicies.DEFAULT.conversion_name
    label: StringProperty()  # It will be drawn instead of name if given
    quick_link_to_node = str()  # sockets which often used with other nodes can fill its `bl_idname` here
    link_menu_handler : StringProperty(default='') # To specify additional entries in the socket link menu
    enable_input_link_menu : BoolProperty(default = True)

    # set True to use default socket property if it has got it
    use_prop: BoolProperty(default=False)
    custom_draw: StringProperty(description="For name of method which will draw socket UI (optionally)")
    prop_name: StringProperty(default='', description="For displaying node property in socket UI")

    # utility field for showing number of objects in sockets data
    objects_number: IntProperty(min=0, options={'SKIP_SAVE'})

    description : StringProperty()
    is_mandatory: BoolProperty(default=False)
    nesting_level: IntProperty(default=2)
    default_mode: EnumProperty(items=enum_item_4(['NONE', 'EMPTY_LIST', 'MATRIX', 'MASK']), default='EMPTY_LIST')
    pre_processing: EnumProperty(items=enum_item_4(['NONE', 'ONE_ITEM']), default='NONE')
    s_id: StringProperty(options={'SKIP_SAVE'})

    def get_link_parameter_node(self):
        return self.quick_link_to_node

    def setup_parameter_node(self, param_node):
        pass

    def get_prop_name(self):
        """
        Intended to return name of property related with socket owned by its node
        Name can be replaced by twin property name in draft mode of a tree
        """
        node = self.node
        if node and hasattr(node, 'does_support_draft_mode') and node.does_support_draft_mode() and hasattr(node.id_data, 'sv_draft') and node.id_data.sv_draft:
            prop_name_draft = self.node.draft_properties_mapping.get(self.prop_name, None)
            if prop_name_draft:
                return prop_name_draft
            return self.prop_name

        return self.prop_name

    @property
    def other(self):
        """Returns opposite linked socket, if socket is outputs it will return one random opposite linked socket"""
        return get_other_socket(self)

    @property
    def socket_id(self):
        """Id of socket used by data_cache"""
        _id = self.s_id
        if not _id:
            self.s_id = str(hash(self.node.node_id + self.identifier + ('o' if self.is_output else 'i')))
            _id = self.s_id
        return _id

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
                self.id_data.links.remove(link)

        self.hide = value

    def sv_get(self, default=..., deepcopy=True):
        """
        The method is used for getting socket data
        In most cases the method should not be overridden
        Also a socket can use its default_property
        Order of getting data (if available):
        1. written socket data
        2. node default property
        3. socket default property
        4. script default property
        5. Raise no data error
        :param default: script default property
        :param deepcopy: in most cases should be False for efficiency but not in cases if input data will be modified
        :return: data bound to the socket
        """
        if self.is_output:
            return sv_get_socket(self, False)

        if self.is_linked:
            return sv_get_socket(self, deepcopy)

        prop_name = self.get_prop_name()
        if prop_name:
            prop = getattr(self.node, prop_name)
            return format_bpy_property(prop)

        if self.use_prop and hasattr(self, 'default_property') and self.default_property is not None:
            default_property = self.default_property
            return format_bpy_property(default_property)

        if default is not ...:
            return default

        raise SvNoDataError(self)

    def sv_set(self, data):
        """Set data, provide context in case the node can be evaluated several times in different context"""
        if self.is_output:
            data = self.postprocess_output(data)

        # it's expensive to call sv_get method to update the number in other places
        self.objects_number = len(data)

        sv_set_socket(self, data)

    def sv_forget(self):
        """Delete socket memory"""
        sv_forget_socket(self)

    def replace_socket(self, new_type, new_name=None):
        """Replace a socket with a socket of new_type and keep links,
        return the new socket, the old reference might be invalid"""
        self.sv_forget()
        return replace_socket(self, new_type, new_name)

    def draw_property(self, layout, prop_origin=None, prop_name='default_property'):
        """
        This method can be overridden for showing property in another way
        Property will be shown only if socket is unconnected input
        If prop_origin is None then the default socket property should be shown
        """
        if prop_origin is None and hasattr(self, prop_name):
            layout.prop(self, 'default_property', text=self.label or None)
        else:
            layout.prop(prop_origin, prop_name, text=self.label or None)

    def draw_quick_link(self, context, layout, node):
        """
        Will draw button for creating new node which is often used with such type of sockets
        The socket should have `bl_idname` of other node in `quick_link_to_node` attribute for using this UI
        """
        if self.quick_link_to_node:
            layout.operator('node.sv_quicklink_new_node_input', text="", icon="PLUGIN")

    def does_support_link_input_menu(self, context, layout, node):
        if not self.enable_input_link_menu:
            return False
        param_node = self.get_link_parameter_node()
        if not param_node:
            return False
        return True

    def draw_link_input_menu(self, context, layout, node):
        if not self.does_support_link_input_menu(context, layout, node):
            return
        op = layout.operator('node.sv_input_link_menu_popup', text="", icon="PLUGIN")
        op.tree_name = node.id_data.name
        op.node_name = node.name
        op.input_name = self.name


    def draw(self, context, layout, node, text):

        def draw_label(text):
            flags = self.get_mode_flags()
            if flags:
                text = text + " [" + ",".join(flags) + "]"
            if self.description:
                layout.operator('node.sv_socket_show_help', text=text, emboss=False).text = self.description
            else:
                if hasattr(self, 'show_domain') and self.show_domain:
                    row = layout.row()
                    row.label(text=text)
                    row.prop(self, 'domain', text='')
                else:
                    layout.label(text=text)

        menu_option = get_param('show_input_menus', 'QUICKLINK')

        # just handle custom draw..be it input or output.
        if self.custom_draw:
            # does the node have the draw function referred to by
            # the string stored in socket's custom_draw attribute
            if hasattr(node, self.custom_draw):
                getattr(node, self.custom_draw)(self, context, layout)

        elif self.is_linked:  # linked INPUT or OUTPUT
            draw_label((self.label or text) + f". {self.objects_number or ''}")

        elif self.is_output:  # unlinked OUTPUT
            draw_label(self.label or text)

        else:  # unlinked INPUT
            prop_name = self.get_prop_name()
            if prop_name:  # has property
                if menu_option == 'ALL':
                    self.draw_link_input_menu(context, layout, node)
                self.draw_property(layout, prop_origin=node, prop_name=prop_name)

            elif node.bl_idname == 'SvGroupTreeNode' and hasattr(self, 'draw_group_property'):  # group node
                if node.node_tree:  # when tree is removed from node sockets still exist
                    interface_socket = list(node.node_tree.sockets('INPUT'))[self.index]
                    self.draw_group_property(layout, text, interface_socket)

            elif node.bl_idname == 'NodeGroupOutput' and hasattr(self, 'draw_group_property'):  # group out node
                if self.index < len(node.outputs):  # in case of last socket of the node which is virtual
                    interface_socket = node.outputs[self.index]
                    self.draw_group_property(layout, text, interface_socket)

            elif self.use_prop:  # no property but use default prop
                if menu_option == 'ALL':
                    self.draw_link_input_menu(context, layout, node)
                self.draw_property(layout)

            else:  # no property and not use default prop
                if menu_option == 'QUICKLINK':
                    self.draw_quick_link(context, layout, node)
                elif menu_option == 'ALL':
                    self.draw_link_input_menu(context, layout, node)
                draw_label(self.label or text)

        if self.has_menu(context):
            self.draw_menu_button(context, layout, node, text)

    # https://wiki.blender.org/wiki/Reference/Release_Notes/4.0/Python_API#Node_Groups
    if bpy.app.version >= (4, 0):
        @classmethod
        def draw_color_simple(cls):
            return cls.color
    else:
        def draw_color(self, context, node):
            return self.color


class SvObjectSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvObjectSocket"
    bl_label = "Object Socket"

    def filter_kinds(self, objs):
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
            if objs.type in set(kinds):
                return True
        if objs.type == kind:
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
            layout.prop(prop_origin, prop_name, text=self.label or None)  # need for consistency, probably will never be used
        else:
            layout.prop_search(self, 'object_ref_pointer', bpy.data, 'objects', text=self.label or self.name)


class SvFormulaSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvFormulaSocket"
    bl_label = "Formula Socket"

    color = (0.68, 0.85, 0.90, 1)

    depth: IntProperty(
        description="Depth exposed to the formula",
        update=process_from_socket,
        default=1,
        min=1)

    def update_depth(self, context):
        if self.transform == 'Vector' and self.depth < 2:
            self.depth = 2
        else:
            process_from_socket(self, context)

    transform: EnumProperty(
        description='Transform before exposing to the formula',
        items=enum_item_4(['As is', 'Vector', 'Array', 'Set', 'String']),
        update=update_depth)
    default_conversion_name = ConversionPolicies.LENIENT.conversion_name

    def draw(self, context, layout, node, text):
        layout.label(text=self.name+ '. ' + str(self.objects_number))
        layout.prop(self,'depth',text='Depth')
        layout.prop(self,'transform',text='')


class SvTextSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvTextSocket"
    bl_label = "Text Socket"

    color = (0.68,  0.85,  0.90, 1)
    quick_link_to_node: StringProperty()

    default_property: StringProperty(update=process_from_socket)
    default_conversion_name = ConversionPolicies.LENIENT.conversion_name

class SvMatrixSocket(NodeSocket, SvSocketCommon):
    '''4x4 matrix Socket type'''

    bl_idname = "SvMatrixSocket"
    bl_label = "Matrix Socket"

    color = (0.2, 0.8, 0.8, 1.0)
    quick_link_to_node = 'SvMatrixInNodeMK4'
    nesting_level: IntProperty(default=1)

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(Matrix,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(Matrix,))

class SvVerticesSocket(SocketDomain, NodeSocket, SvSocketCommon):
    '''For vertex data'''
    bl_idname = "SvVerticesSocket"
    bl_label ="Vertices Socket"

    color = (0.9, 0.6, 0.2, 1.0)
    quick_link_to_node = 'GenVectorsNode'
    nesting_level: IntProperty(default=3)
    def setup_parameter_node(self, param_node):
        if self.use_prop or self.get_prop_name():
            value = self.sv_get()[0][0]
            param_node.x_ = value[0]
            param_node.y_ = value[1]
            param_node.z_ = value[2]


    # this property is needed for back capability, after renaming prop to default_property
    # should be removed after https://github.com/nortikin/sverchok/issues/3514
    # using via default_property property
    prop: FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)

    expanded: BoolProperty(default=False)  # for minimizing showing socket property

    def do_simplify(self, data):
        return flatten_data(data, 2)

    def do_flat_topology(self, data):
        return flatten_data(data, 3)

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
            row.template_component_menu(prop_origin, prop_name, name=self.label or self.name)

    def do_graft(self, data):
        return graft_data(data, item_level=1)

    def draw_group_property(self, layout, text, interface_socket):
        if not interface_socket.hide_value:
            layout.template_component_menu(self, 'prop', name=text)
        else:
            layout.label(text=text)

    def does_support_link_input_menu(self, context, layout, node):
        ok = super().does_support_link_input_menu(context, layout, node)
        if not ok:
            return False
        return self.name not in {'Vertices', 'Verts'}


class SvVerticesSocketInterface(InterfaceSocket):
    """
    This socket will be created in tree.inputs to tree.outputs collection
    when normal socket will be connected to input or output group nodes
    """
    # The only reason of existing this class
    # is that `prop` attribute of VerticesSocket can't be renamed to `default_property
    bl_idname = "SvVerticesSocketInterface"
    bl_socket_idname = "SvVerticesSocket"
    bl_label = "Vertices"
    color = SvVerticesSocket.color

    default_value: FloatVectorProperty(name="Default value", default=(0, 0, 0), size=3)

    def draw_color(self, context):
        return self.color

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, 'default_value')
        col.prop(self, 'hide_value')

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
            row.template_component_menu(prop_origin, prop_name, name=self.label or self.name)

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(Quaternion,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(Quaternion,))

    def draw_group_property(self, layout, text, interface_socket):
        if not interface_socket.hide_value:
            layout.template_component_menu(self, 'default_property', name=text)
        else:
            layout.label(text=text)


class SvColorSocket(SocketDomain, NodeSocket, SvSocketCommon):
    '''For color data'''
    bl_idname = "SvColorSocket"
    bl_label = "Color Socket"

    color = (0.9, 0.8, 0.0, 1.0)

    default_property: FloatVectorProperty(default=(0, 0, 0, 1), size=4, subtype='COLOR', min=0, max=1,
                                          update=process_from_socket)
    expanded: BoolProperty(default=False)  # for minimizing showing socket property
    nesting_level: IntProperty(default=3)
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
            row.prop(prop_origin, prop_name, text=self.label or None)

    def draw_group_property(self, layout, text, interface_socket):
        if not interface_socket.hide_value:
            layout.prop(self, 'default_property', text=text)
        else:
            layout.label(text=text)

    def do_flat_topology(self, data):
        return flatten_data(data, 3)

class SvDummySocket(NodeSocket, SvSocketCommon):
    '''Dummy Socket for sockets awaiting assignment of type'''
    bl_idname = "SvDummySocket"
    bl_label = "Dummys Socket"

    color = (0.8, 0.8, 0.8, 0.3)

    def sv_get(self, deepcopy=False, default=[]):
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


class SvStringsSocket(SocketDomain, NodeSocket, SvSocketCommon):
    '''Generic, mostly numbers, socket type'''
    bl_idname = "SvStringsSocket"
    bl_label = "Strings Socket"

    color = (0.6, 1.0, 0.6, 1.0)

    use_graft_2: BoolProperty(
        name="Graft Topology",
        default=False,
        update=process_from_socket)

    def get_mode_flags(self):
        flags = super().get_mode_flags()
        if self.use_graft_2:
            flags.append('G2')
        return flags

    def get_prop_data(self):
        prop_name = self.get_prop_name()
        if prop_name:
            return {"prop_name": prop_name}
        elif self.prop_type:
            return {"prop_type": self.prop_type,
                    "prop_index": self.prop_index}
        else:
            return {}

    quick_link_to_node: StringProperty()  # this can be overridden by socket instances

    default_property_type: bpy.props.EnumProperty(  # for internal usage
        description="Switch between float and int without node updating",
        items=[(i, i, '') for i in ['float', 'int']])

    default_float_property: bpy.props.FloatProperty(update=process_from_socket)
    default_int_property: bpy.props.IntProperty(update=process_from_socket)

    show_property_type: BoolProperty(
        description="Add icon to switch default type")

    def get_link_parameter_node(self):
        if self.quick_link_to_node:
            return self.quick_link_to_node
        return 'SvNumberNode'

    def does_support_link_input_menu(self, context, layout, node):
        ok = super().does_support_link_input_menu(context, layout, node)
        if not ok:
            return False
        return self.name not in {'Edges', 'Polygons', 'Edgs', 'Polys', 'Faces', 'EdgPol', 'Mask', 'EdgesMask', 'FaceMask'}

    def setup_parameter_node(self, param_node):
        if param_node.bl_idname == 'SvNumberNode':
            if self.use_prop or self.get_prop_name():
                value = self.sv_get()[0][0]
                print("V", value)
                if isinstance(value, int):
                    param_node.selected_mode = 'int'
                    param_node.int_ = value
                elif isinstance(value, float):
                    param_node.selected_mode = 'float'
                    param_node.float_ = value

    @property
    def default_property(self):
        return self.default_float_property if self.default_property_type == 'float' else self.default_int_property

    @default_property.setter
    def default_property(self, value):
        if hasattr(self.node, 'node_tree'):  # belong to group node
            interface_socket = self.node.node_tree.inputs[self.index]
            if interface_socket.default_type == 'float':
                self.default_float_property = value
            elif interface_socket.default_type == 'int':
                self.default_int_property = value
        else:
            if self.default_property_type == 'float':
                self.default_float_property = value
            else:
                self.default_int_property = value

    def draw_property(self, layout, prop_origin=None, prop_name=None):
        if prop_origin and prop_name:
            layout.prop(prop_origin, prop_name, text=self.label or None)
        elif self.use_prop:
            row = layout.row(align=True)
            if self.default_property_type == 'float':
                row.prop(self, 'default_float_property', text=self.label or self.name)
            elif self.default_property_type == 'int':
                row.prop(self, 'default_int_property', text=self.label or self.name)
            if self.show_property_type:
                icon = 'IPO_LINEAR' if self.default_property_type == 'float' else 'IPO_CONSTANT'
                row.operator(SvSwitchDefaultOp.bl_idname, icon=icon, text='')

    def draw_menu_items(self, context, layout):
        self.draw_simplify_modes(layout)
        if self.can_flatten_topology():
            layout.prop(self, 'use_flatten_topology')
        if self.can_graft():
            layout.prop(self, 'use_graft')
            if not self.use_flatten:
                layout.prop(self, 'use_graft_2')
        if self.can_unwrap():
            layout.prop(self, 'use_unwrap')
        if self.can_wrap():
            layout.prop(self, 'use_wrap')

    def do_flat_topology(self, data):
        return flatten_data(data, 3)

    def do_flatten(self, data):
        return flatten_data(data, 1)

    def do_simplify(self, data):
        return flatten_data(data, 2)

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types = STANDARD_TYPES)

    def do_graft_2(self, data):
        def to_zero_base(lst):
            m = min(lst)
            return [x - m for x in lst]

        result = map_at_level(to_zero_base, data, item_level=1, data_types = STANDARD_TYPES)
        result = graft_data(result, item_level=1, data_types = STANDARD_TYPES)
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
        if self.use_unwrap:
            result = unwrap_data(result, socket=self)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def postprocess_output(self, data):
        result = data

        if self.use_flatten_topology:
            result = self.do_flat_topology(data)
        if self.use_flatten:
            result = self.do_flatten(data)
        elif self.use_simplify:
            result = self.do_simplify(data)
        if self.use_graft:
            result = self.do_graft(result)
        elif self.use_graft_2:
            result = self.do_graft_2(result)
        if self.use_unwrap:
            result = unwrap_data(result, socket=self)
        if self.use_wrap:
            result = wrap_data(result)
        return result

    def draw_group_property(self, layout, text, interface_socket):
        # only for input sockets group node nodes with sub trees
        if not interface_socket.hide_value:
            if interface_socket.default_type == 'float':
                layout.prop(self, 'default_float_property', text=text)
            elif interface_socket.default_type == 'int':
                layout.prop(self, 'default_int_property', text=text)
        else:
            layout.label(text=text)


class SvStringsSocketInterface(InterfaceSocket):
    """
    This socket will be created in tree.inputs to tree.outputs collection
    when normal socket will be connected to input or output group nodes
    """
    bl_idname = "SvStringsSocketInterface"
    bl_socket_idname = "SvStringsSocket"
    bl_label = "Number"
    color = SvStringsSocket.color

    default_float_value: bpy.props.FloatProperty(name='Default value')
    default_int_value: bpy.props.IntProperty(name='Default value')
    default_type: bpy.props.EnumProperty(items=[(i, i, '') for i in ['float', 'int']], update=update_interface)

    @property
    def default_value(self):
        return self.default_float_value if self.default_type == 'float' else self.default_int_value

    def draw_color(self, context):
        return self.color

    def draw(self, context, layout):
        layout.prop(self, 'hide_value')
        layout.prop(self, 'default_type', expand=True)
        if self.default_type == 'float':
            layout.prop(self, 'default_float_value')
        elif self.default_type == 'int':
            layout.prop(self, 'default_int_value')

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
        if "Pattern" in self.name:
            return "SvSvgPatternNode"

        return


class SvPulgaForceSocket(NodeSocket, SvSocketCommon):
    '''For Pulga forces data'''
    bl_idname = "SvPulgaForceSocket"
    bl_label = "Pulga Force Socket"

    color = (0.4, 0.3, 0.6, 1.0)

class SvLoopControlSocket(NodeSocket, SvSocketCommon):
    '''For loop in-loop out node pair'''
    bl_idname = "SvLoopControlSocket"
    bl_label = "Loop Control Socket"

    color = (0.1, 0.1, 0.1, 1.0)
    quick_link_to_node = 'SvLoopInNode'

class SvDictionarySocket(NodeSocket, SvSocketCommon):
    '''For dictionary data'''
    bl_idname = "SvDictionarySocket"
    bl_label = "Dictionary Socket"

    color = (1.0, 1.0, 1.0, 1.0)
    quick_link_to_node = 'SvDictionaryIn'

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(dict,))

    def do_simplify(self, data):
        return flatten_data(data, 2, data_types=(dict,))

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

    default_conversion_name = ConversionPolicies.LENIENT.conversion_name

class SvSurfaceSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvSurfaceSocket"
    bl_label = "Surface Socket"

    color = (0.4, 0.2, 1.0, 1.0)

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

    def get_mode_flags(self):
        flags = super().get_mode_flags()
        if self.reparametrize:
            flags.append('R')
        return flags

    def draw_menu_items(self, context, layout):
        super().draw_menu_items(context, layout)
        layout.prop(self, 'reparametrize')

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(SvCurve,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(SvCurve,))

    def preprocess_input(self, data):
        data = SvSocketCommon.preprocess_input(self, data)
        if self.reparametrize:
            data = map_at_level(reparametrize_curve, data, data_types=(SvCurve,))
        return data

    def postprocess_output(self, data):
        data = SvSocketCommon.postprocess_output(self, data)
        if self.reparametrize:
            data = map_at_level(reparametrize_curve, data, data_types=(SvCurve,))
        return data

class SvScalarFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvScalarFieldSocket"
    bl_label = "Scalar Field Socket"
    quick_link_to_node = 'SvNumberNode'

    color = (0.9, 0.4, 0.1, 1.0)
    default_conversion_name = ConversionPolicies.FIELD.conversion_name

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(SvScalarField,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(SvScalarField,))

class SvVectorFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvVectorFieldSocket"
    bl_label = "Vector Field Socket"
    quick_link_to_node = 'GenVectorsNode'

    color = (0.1, 0.1, 0.9, 1.0)
    default_conversion_name = ConversionPolicies.FIELD.conversion_name

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(SvVectorField,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(SvVectorField,))

class SvSolidSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvSolidSocket"
    bl_label = "Solid Socket"

    color = (0.0, 0.65, 0.3, 1.0)
    default_conversion_name = ConversionPolicies.SOLID.conversion_name

    def do_flatten(self, data):
        from sverchok.dependencies import FreeCAD
        import Part
        return flatten_data(data, 1, data_types=(Part.Shape,))

    def do_graft(self, data):
        from sverchok.dependencies import FreeCAD
        import Part
        return graft_data(data, item_level=0, data_types=(Part.Shape,))


class SvCollectionSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvCollectionSocket"
    bl_label = "Collection Socket"

    color = (0.96, 0.96, 0.96, 1.0)

    default_property: PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
        update=process_from_socket)


class SvMaterialSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvMaterialSocket"
    bl_label = "Material Socket"

    color = (0.92, 0.46, 0.51, 1.0)

    default_property: PointerProperty(
        name="Material",
        type=bpy.types.Material,
        update=process_from_socket)


class SvTextureSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvTextureSocket"
    bl_label = "Texture Socket"

    color = (0.62, 0.31, 0.64, 1.0)

    default_property: PointerProperty(
        name="Texture",
        type=bpy.types.Texture,
        update=process_from_socket)


class SvImageSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvImageSocket"
    bl_label = "Image Socket"

    color = (0.39, 0.22, 0.39, 1.0)

    default_property: PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=process_from_socket)


class SvLinkNewNodeInput(bpy.types.Operator):
    ''' Spawn and link new node to the left of the caller node'''
    bl_idname = "node.sv_quicklink_new_node_input"
    bl_label = "Add a new node to the left"

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'socket')

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

class SvSocketHelpOp(bpy.types.Operator):
    bl_idname = "node.sv_socket_show_help"
    bl_label = "Socket description"
    bl_options = {'INTERNAL', 'REGISTER'}

    text : StringProperty()

    @classmethod
    def description(cls, context, properties):
        return properties.text

    def execute(self, context):
        def draw(menu, context):
            col = menu.layout.column(align=True)
            for line in self.text.split('\n'):
                col.label(text=line)
        bpy.context.window_manager.popup_menu(draw, title="Socket description", icon='QUESTION')
        return {'FINISHED'}

class SvInputLinkMenuOp(bpy.types.Operator):
    "Opens a menu"
    bl_idname = "node.sv_input_link_menu_popup"
    bl_label = "Link to existing parameter or add a new one"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    def get_items(self, context):
        tree = context.space_data.node_tree
        node = tree.nodes[self.node_name]
        socket = node.inputs[self.input_name]

        items = []
        link_param_node = socket.get_link_parameter_node()
        i = 0
        if link_param_node:
            items.append(
                    ('__SV_PARAM_CREATE__', "Create new parameter", "Create new parameter node", i)
                )
            i += 1

            items.append(
                        ('__SV_WIFI_CREATE__', "Create new parameter via WiFi", "Create new parameter node and link it via WiFi pair", 1)
                    )
            i += 1

        for name, other_node in tree.nodes.items():
            if other_node.bl_idname == link_param_node:
                item = ('PARAM_' + other_node.name, f"Link to parameter: {other_node.label or other_node.name}", "Link to existing input node", i)
                items.append(item)
                i += 1

        for name, other_node in tree.nodes.items():
            if other_node.bl_idname == 'WifiInNode':
                for input_idx, wifi_input in enumerate(other_node.inputs):
                    linked = get_other_socket(wifi_input)
                    if linked is None:
                        continue
                    if linked.bl_idname != socket.bl_idname:
                        continue
                    item = (f"WIFI_{input_idx}_{other_node.var_name}", f"Link to WiFi: {other_node.label or other_node.name} - {other_node.var_name}[{input_idx}]", "Link to existing WiFi input node", i)
                    items.append(item)
                    i += 1

        # In the node class, it is possible to define
        # additional menu entries by specifying `link_menu_handler`
        # property of the socket. It should be name of a class with
        # two classmethods: get_items() and on_selected():
        #
        # class MyNode(...):
        #   class MenuHandler:
        #       @classmethod
        #       def get_items(cls, context):
        #           return [('MY_ENTRY', "My entry", "My entry description")]
        #
        #       @classmethod
        #       def on_selected(cls, tree, node, item, context):
        #           if item == 'MY_ENTRY':
        #               print("Hello world!")
        #
        #   def sv_init(self):
        #       self.inputs.new('SvVerticesSocket', 'Vertices').link_menu_handler = 'MenuHandler'
        #
        handler_name = socket.link_menu_handler
        if handler_name:
            handler = getattr(node, handler_name)
            for id, title, description in handler.get_items(socket, context):
                items.append((id, title, description, i))
                i += 1

        return items

    option : EnumProperty(name = "Action", description = "Action to be executed", items = get_items)
    tree_name : StringProperty()
    node_name : StringProperty()
    input_name : StringProperty()

    def execute(self, context):

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        socket = node.inputs[self.input_name]

        def is_linked(node1, node2):
            for link in tree.links:
                if link.from_node == node1 and link.to_node == node2:
                    return True
            return False

        if self.option == '__SV_PARAM_CREATE__':
            new_node = tree.nodes.new(socket.get_link_parameter_node())
            new_node.label = socket.label or socket.name
            socket.setup_parameter_node(new_node)
            links_number = len([s for s in node.inputs if s.is_linked])
            new_node.location = (node.location[0] - 200, node.location[1] - 100 * links_number)
            tree.links.new(new_node.outputs[0], socket)

            if node.parent:
                new_node.parent = node.parent
                new_node.location = new_node.absolute_location

            new_node.process_node(context)

        elif self.option == '__SV_WIFI_CREATE__':
            label = socket.label or socket.name
            param_node = tree.nodes.new(socket.get_link_parameter_node())
            param_node.label = label

            wifi_in_node = tree.nodes.new('WifiInNode')
            wifi_in_node.label = f"WiFi In - {label}"
            wifi_in_node.gen_var_name()
            wifi_var = wifi_in_node.var_name

            wifi_out_node = tree.nodes.new('WifiOutNode')
            wifi_out_node.label = f"WiFi Out - {label}"
            wifi_out_node.var_name = wifi_var

            socket.setup_parameter_node(param_node)

            tree.links.new(param_node.outputs[0], wifi_in_node.inputs[0])
            tree.links.new(wifi_out_node.outputs[0], socket)

            setup_new_node_location(wifi_out_node, node)
            setup_new_node_location(wifi_in_node, wifi_out_node)
            setup_new_node_location(param_node, wifi_in_node)

            param_node.process_node(context)

        elif self.option.startswith('PARAM_'):
            input_name = self.option[6:]
            param_node = tree.nodes[input_name]
            tree.links.new(param_node.outputs[0], socket)

        elif self.option.startswith('WIFI_'):
            prefix, socket_idx, wifi_var = self.option.split('_', maxsplit=2)
            socket_idx = int(socket_idx)

            found_existing = False
            for name, wifi_node in tree.nodes.items():
                if wifi_node.bl_idname == 'WifiOutNode' and is_linked(wifi_node, node):
                    if wifi_node.var_name == wifi_var:
                        tree.links.new(wifi_node.outputs[socket_idx], socket)
                        found_existing = True
                        break

            if not found_existing:
                new_node = tree.nodes.new('WifiOutNode')
                new_node.var_name = wifi_var
                new_node.set_var_name()
                links_number = len([s for s in node.inputs if s.is_linked])
                new_node.location = (node.location[0] - 200, node.location[1] - 100 * links_number)
                tree.links.new(new_node.outputs[socket_idx], socket)

                if node.parent:
                    new_node.parent = node.parent
                    new_node.location = new_node.absolute_location

                new_node.process_node(context)

        elif socket.link_menu_handler:
            handler = getattr(node, socket.link_menu_handler)
            handler.on_selected(tree, node, socket, self.option, context)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


class SvSwitchDefaultOp(bpy.types.Operator):
    """Either Float or Integer"""
    bl_idname = "node.sv_switch_default"
    bl_label = "Switch default value of string socket"
    bl_options = {'INTERNAL', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'socket')

    def execute(self, context):
        s = context.socket
        s.default_property_type = 'float' if s.default_property_type == 'int' else 'int'
        process_from_socket(s, context)
        return {'FINISHED'}


classes = [
    SV_MT_SocketOptionsMenu, SV_MT_AllSocketsOptionsMenu,
    SvVerticesSocket, SvMatrixSocket, SvStringsSocket, SvFilePathSocket,
    SvColorSocket, SvQuaternionSocket, SvDummySocket, SvSeparatorSocket,
    SvTextSocket, SvObjectSocket, SvDictionarySocket, SvChameleonSocket,
    SvSurfaceSocket, SvCurveSocket, SvScalarFieldSocket, SvVectorFieldSocket,
    SvSolidSocket, SvSvgSocket, SvPulgaForceSocket, SvFormulaSocket,
    SvLoopControlSocket, SvLinkNewNodeInput,
    SvStringsSocketInterface, SvVerticesSocketInterface,
    SvCollectionSocket,
    SvMaterialSocket,
    SvTextureSocket,
    SvImageSocket,
    SvSocketHelpOp, SvInputLinkMenuOp,
    SvSwitchDefaultOp,
]

def socket_interface_classes():
    """
    All sockets should have their twins - SocketInterface
    Tis function generate SocketInterface classes for Sockets for which interface sockets was not coded manually
    This function assume to find all socket and interface classes in classes variable of the current module

    If socket class has default property interface will also have this property named `default value`
    This value will be used for setting it to `default property` during connecting group tree to group node
    Also interface will get `show property` attribute which should hide property from group node
    Socket itself should track status of this property
    """
    sockets = {cls for cls in classes if hasattr(cls, 'links')}  # best test for now
    with_interface_sockets = {globals()[cls.bl_socket_idname] for cls in classes if hasattr(cls, 'bl_socket_idname')}
    for socket_cls in sockets - with_interface_sockets:
        socket_interface_attributes = {
            'bl_idname': f'{socket_cls.__name__}Interface',
            'bl_socket_idname': socket_cls.__name__,
            'bl_label': socket_cls.bl_label,
            'color': socket_cls.color,
            'draw_color': lambda self, context: self.color
        }
        if 'default_property' in socket_cls.__annotations__:
            prop_func, prop_args = get_func_and_args(socket_cls.__annotations__['default_property'])
            prop_args = {k: prop_args[k] for k in prop_args if k not in {'update', 'name'}}
            prop_args['name'] = "Default value"
            prop_args['update'] = lambda s, c: s.id_data.update_sockets()
            socket_interface_attributes['__annotations__'] = {}
            socket_interface_attributes['__annotations__']['default_value'] = socket_cls.__annotations__['default_property']

            def draw(self, context, layout):
                col = layout.column()
                col.prop(self, 'default_value')
                col.prop(self, 'hide_value')
        else:
            def draw(self, context, layout):
                pass

        socket_interface_attributes['draw'] = draw
        yield type(f'{socket_cls.__name__}Interface', (InterfaceSocket,), socket_interface_attributes)


register, unregister = bpy.utils.register_classes_factory(classes + list(socket_interface_classes()))
