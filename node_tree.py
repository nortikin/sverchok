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

import sys
import time
from contextlib import contextmanager

import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard
from mathutils import Matrix

from sverchok import data_structure
from sverchok.data_structure import get_other_socket

from sverchok.core.update_system import (
    build_update_list,
    process_from_node,
    process_tree,
    get_update_lists, update_error_nodes,
    get_original_node_color)

from sverchok.core.socket_conversions import DefaultImplicitConversionPolicy

from sverchok.core.node_defaults import set_defaults_if_defined

from sverchok.utils import get_node_class_reference
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.docstring import SvDocstring
import sverchok.utils.logging
from sverchok.utils.logging import debug

from sverchok.ui import color_def
from sverchok.ui.nodes_replacement import set_inputs_mapping, set_outputs_mapping


class SvLinkNewNodeInput(bpy.types.Operator):
    ''' Spawn and link new node to the left of the caller node'''
    bl_idname = "node.sv_quicklink_new_node_input"
    bl_label = "Add a new node to the left"

    socket_index: IntProperty()
    origin: StringProperty()
    new_node_idname: StringProperty()
    new_node_offsetx: IntProperty(default=-200)
    new_node_offsety: IntProperty(default=0)

    def execute(self, context):
        tree = context.space_data.edit_tree
        nodes, links = tree.nodes, tree.links

        caller_node = nodes.get(self.origin)
        new_node = nodes.new(self.new_node_idname)
        new_node.location[0] = caller_node.location[0] + self.new_node_offsetx
        new_node.location[1] = caller_node.location[1] + self.new_node_offsety
        links.new(new_node.outputs[0], caller_node.inputs[self.socket_index])

        if caller_node.parent:
            new_node.parent = caller_node.parent
            loc_xy = new_node.location[:]
            locx, locy = recursive_framed_location_finder(new_node, loc_xy)
            new_node.location = locx, locy

        new_node.process_node(context)

        return {'FINISHED'}


@contextmanager
def throttle_tree_update(node):
    """ usage
    from sverchok.node_tree import throttle_tree_update

    inside your node, f.ex inside a wrapped_update that creates a socket

    def wrapped_update(self, context):
        with throttle_tree_update(self):
            self.inputs.new(...)
            self.outputs.new(...)

    that's it. 

    """
    try:
        node.id_data.skip_tree_update = True
        yield node
    finally:
        node.id_data.skip_tree_update = False


class SvNodeTreeCommon(object):
    '''
    Common methods shared between Sverchok node trees
    '''

    has_changed: BoolProperty(default=False)
    limited_init: BoolProperty(default=False)
    skip_tree_update: BoolProperty(default=False)


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

    @property
    def sv_trees(self):
        res = []
        for ng in bpy.data.node_groups:
            if ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
                res.append(ng)
        return res






class SverchCustomTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Nodes'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        process_tree(self)

        # should turn off tree. for now it does by updating it whole
        # should work something like this
        # outputs = filter(lambda n: isinstance(n,SvOutput), self.nodes)
        # for node in outputs:
        #   node.disable()

    sv_animate: BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show: BoolProperty(name="Show", default=True, description='Show this layout', update=turn_off_ng)
    sv_bake: BoolProperty(name="Bake", default=True, description='Bake this layout')
    sv_process: BoolProperty(name="Process", default=True, description='Process layout')
    sv_user_colors: StringProperty(default="")

    tree_link_count: IntProperty(name='keep track of current link count', default=0)
    configuring_new_node: BoolProperty(name="indicate node initialization", default=False)

    @property
    def timestamp(self):
        return time.monotonic()

    @property
    def has_link_count_changed(self):
        link_count = len(self.links)
        if not link_count == self.tree_link_count: 
            # print('update event: link count changed', self.timestamp)
            self.tree_link_count = link_count
            return True

    def update(self):
        '''
        Tags tree for update for handle
        get update list for debug info, tuple (fulllist, dictofpartiallists)
        '''
        if self.skip_tree_update:
            # print('throttled update from context manager')
            return


        # print('svtree update', self.timestamp)
        self.has_changed = True
        # self.has_link_count_changed
        self.process()

    def process_ani(self):
        """
        Process the Sverchok node tree if animation layers show true.
        For animation callback/handler
        """
        if self.sv_animate:
            process_tree(self)

    def process(self):
        """
        process the Sverchok tree upon editor changes from handler
        """

        if self.configuring_new_node:
            # print('skipping global process during node init')
            return

        if self.has_changed:
            # print('processing build list: because has_changed==True')
            self.build_update_list()
            self.has_changed = False
        if self.is_frozen():
            # print('not processing: because self/tree.is_frozen') 
            return
        if self.sv_process:
            process_tree(self)

        self.has_changed = False


class SverchCustomTreeNode:

    # A cache for get_docstring() method
    _docstring = None

    _implicit_conversion_policy = dict()

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname in ['SverchCustomTreeType', 'SverchGroupTreeType']

    @property
    def node_id(self):
        if not self.n_id:
            self.n_id = str(hash(self) ^ hash(time.monotonic()))
        return self.n_id

    def mark_error(self, err):
        """
        marks the with system error color
        will automaticly be cleared and restored to
        the old color
        """
        ng = self.id_data
        update_error_nodes(ng, self.name, err)

    def getLogger(self):
        if hasattr(self, "draw_label"):
            name = self.draw_label()
        else:
            name = self.label
        if not name:
            name = self.bl_label
        if not name:
            name = self.__class__.__name__
        return sverchok.utils.logging.getLogger(name)

    def debug(self, msg, *args, **kwargs):
        self.getLogger().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.getLogger().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.getLogger().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.getLogger().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.getLogger().exception(msg, *args, **kwargs)

    def set_implicit_conversions(self, input_socket_name, policy):
        """
        Set implicit conversion policy to be used by default for specified input socket.
        This policy will be used by default by subsequent .sv_get() calls to this socket.
        Policy can be passed as direct reference to the class, or as a class name.
        """
        if isinstance(policy, str):
            policy = getattr(sverchok.core.socket_conversions, policy)
        #self.debug("Set default conversion policy for socket %s to %s", input_socket_name, policy)
        self._implicit_conversion_policy[input_socket_name] = policy

    def get_implicit_conversions(self, input_socket_name, override=None):
        """
        Return implicit conversion policy that was set as default for specified socket
        by set_implicit_conversions() call.
        If override is specified, then it is returned in all cases.
        """
        if override is not None:
            return override
        return self._implicit_conversion_policy.get(input_socket_name, DefaultImplicitConversionPolicy)

    def set_color(self):
        color = color_def.get_color(self.bl_idname)
        if color:
            self.use_custom_color = True
            self.color = color

    def create_sockets(self):
        '''Create node input and output sockets from
        their descriptions in self.input_descriptors and self.output_descriptors.
        '''

        if hasattr(self, "input_descriptors"):
            for descriptor in self.input_descriptors:
                descriptor.create(self)
        if hasattr(self, "output_descriptors"):
            for descriptor in self.output_descriptors:
                descriptor.create(self)

    @classmethod
    def get_docstring(cls):
        """
        Get SvDocstring instance parsed from node's docstring.
        """
        docstring = cls._docstring
        if docstring is not None:
            return docstring
        else:
            cls._docstring = SvDocstring(cls.__doc__)
            return cls._docstring

    @classmethod
    def get_tooltip(cls):
        """
        Obtain tooltip for node for use in UI.

        This method is to be overriden in specific node class if node author
        does not like for some reason that tooltip is extracted from node's
        docstring.
        """

        return cls.get_docstring().get_tooltip()

    @classmethod
    def get_shorthand(cls):
        """
        Obtain node shorthand.

        This method is to be overriden in specific node class if node author
        does not like for some reason that shorthand is extracted from node's
        docstring.
        """

        return cls.get_docstring().get_shorthand()

    def node_replacement_menu(self, context, layout):
        """
        Draw menu items with node replacement operators.
        This is called from `rclick_menu()' method by default.
        Items are defined by `replacement_nodes' class property.
        Expected format is

            replacement_nodes = [
                (new_node_bl_idname, inputs_mapping_dict, outputs_mapping_dict)
            ]

        where new_node_bl_idname is bl_idname of replacement node class,
        inputs_mapping_dict is a dictionary mapping names of inputs of this node
        to names of inputs to new node, and outputs_mapping_dict is a dictionary
        mapping names of outputs of this node to names of outputs of new node.
        inputs_mapping_dict and outputs_mapping_dict can be None.
        """
        if hasattr(self, "replacement_nodes"):
            for bl_idname, inputs_mapping, outputs_mapping in self.replacement_nodes:
                node_class = get_node_class_reference(bl_idname)
                text = "Replace with {}".format(node_class.bl_label)
                op = layout.operator("node.sv_replace_node", text=text)
                op.old_node_name = self.name
                op.new_bl_idname = bl_idname
                set_inputs_mapping(op, inputs_mapping)
                set_outputs_mapping(op, outputs_mapping)

    def rclick_menu(self, context, layout):
        """
        Override this method to add specific items into
        node's right-click menu.
        Default implementation calls `node_replacement_menu'.
        """
        self.node_replacement_menu(context, layout)

    def migrate_from(self, old_node):
        """
        This method is called by node replacement operator.
        Override it to correctly copy settings from old_node
        to this (new) node.
        Default implementation does nothing.
        """
        pass

    def sv_init(self, context):
        self.create_sockets()

    def init(self, context):
        """
        this function is triggered upon node creation,
        - freezes the node
        - delegates further initialization information to sv_init
        - sets node color
        - unfreezes the node
        - sets custom defaults (nodes, and sockets)

        """
        ng = self.id_data

        ng.freeze()
        
        if hasattr(self, "sv_init"):

            try:
                ng.configuring_new_node = True
                self.sv_init(context)
            except Exception as err:
                print('nodetree.node.sv_init failure - stare at the error message below')
                sys.stderr.write('ERROR: %s\n' % str(err))

        ng.configuring_new_node = False
        self.set_color()
        ng.unfreeze()

        if not ng.limited_init:
            # print('applying default for', self.name)
            set_defaults_if_defined(self)

    def process_node(self, context):
        '''
        Doesn't work as intended, inherited functions can't be used for bpy.props
        update= ...
        Still this is called from updateNode
        '''
        if self.id_data.bl_idname == "SverchCustomTreeType":
            if self.id_data.is_frozen():
                return

            # self.id_data.has_changed = True

            if data_structure.DEBUG_MODE:
                a = time.perf_counter()
                process_from_node(self)
                b = time.perf_counter()
                debug("Partial update from node %s in %s", self.name, round(b - a, 4))
            else:
                process_from_node(self)
        elif self.id_data.bl_idname == "SverchGroupTreeType":
            monad = self.id_data
            for instance in monad.instances:
                instance.process_node(context)
        else:
            pass

    def copy(self, original):
        """
        This method is not supposed to be overriden in specific nodes.
        Override sv_copy() instead.
        """
        settings = get_original_node_color(self.id_data, original.name)
        if settings is not None:
            self.use_custom_color, self.color = settings
        self.sv_copy(original)

    def sv_copy(self, original):
        """
        Override this method to do anything node-specific
        at the moment of node being copied.
        """
        pass
        
    def free(self):
        """
        some nodes require additional operations upon node removal
        """

        if hasattr(self, "has_3dview_props"):
            print("about to remove this node's props from Sv3DProps")
            try:
                bpy.ops.node.sv_remove_3dviewpropitem(node_name=self.name, tree_name=self.id_data.name)
            except:
                print(f'failed to remove {self.name} from tree={self.id_data.name}')


    def wrapper_tracked_ui_draw_op(self, layout_element, operator_idname, **keywords):
        """
        this wrapper allows you to track the origin of a clicked operator, by automatically passing
        the idname and idtree of the tree.

        example usage:

            row.separator()
            self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')

        """
        op = layout_element.operator(operator_idname, **keywords)
        op.idname = self.name
        op.idtree = self.id_data.name


    def get_and_set_gl_scale_info(self, origin=None):
        """
        This function is called in sv_init in nodes that draw GL instructions to the nodeview, 
        the nodeview scale and dpi differs between users and must be queried to get correct nodeview
        x,y and dpi scale info.
        """
        print('get_and_set_gl_scale_info called from', origin or self.name)

        try:
            print('getting gl scale params')
            from sverchok.utils.context_managers import sv_preferences
            with sv_preferences() as prefs:
                getattr(prefs, 'set_nodeview_render_params')(None)
        except Exception as err:
            print('failed to get gl scale info', err)


classes = [
    SverchCustomTree, 
    SvLinkNewNodeInput
]


register, unregister = bpy.utils.register_classes_factory(classes)
