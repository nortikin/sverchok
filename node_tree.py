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
import textwrap
from contextlib import contextmanager

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import NodeTree

from sverchok import data_structure
from sverchok.data_structure import classproperty, post_load_call

from sverchok.core.update_system import (
    build_update_list,
    process_from_node, process_from_nodes,
    process_tree,
    get_original_node_color,
    is_first_run,)
from sverchok.core.links import (
    SvLinks)
from sverchok.core.node_id_dict import SvNodesDict

from sverchok.core.events import CurrentEvents, BlenderEventsTypes

from sverchok.utils import get_node_class_reference
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.docstring import SvDocstring
import sverchok.utils.logging
from sverchok.utils.logging import debug

from sverchok.ui import color_def
from sverchok.ui.nodes_replacement import set_inputs_mapping, set_outputs_mapping
from sverchok.utils.exception_drawing_with_bgl import clear_exception_drawing_with_bgl


def throttled(func):  # todo would be good to move it in data_structure module
    """
    use as a decorator

        from sverchok.node_tree import SverchCustomTreeNode, throttled

        class YourNode

            @throttled
            def mode_update(self, context):
                ...

    When a node has changed, like a mode-change leading to a socket change (remove, new)
    Blender will trigger nodetree.update. We want to ignore this trigger-event, and we do so by
    - first throttling the update system. 
    - then We execute the code that makes changes to the node/nodetree
    - then we end the throttle-state
    - we are then ready to process

    """
    def wrapper_update(self, context):
        with self.sv_throttle_tree_update():
            func(self, context)
        self.process_node(context)

    return wrapper_update


class SvNodeTreeCommon(object):
    '''
    Common methods shared between Sverchok node trees (normal and monad trees)
    '''

    # auto update toggle of the node tree
    sv_process: BoolProperty(name="Process", default=True, description='Process layout')
    has_changed: BoolProperty(default=False)  # "True if changes of links in tree was detected"

    # for throttle method usage when links are created in the tree via Python
    skip_tree_update: BoolProperty(default=False)  # usage only via throttle_update method
    tree_id_memory: StringProperty(default="")  # identifier of the tree, should be used via `tree_id` property
    sv_links = SvLinks()  # cached Python links
    nodes_dict = SvNodesDict()  # cached Python nodes

    @property
    def tree_id(self):
        """Identifier of the tree"""
        if not self.tree_id_memory:
            self.tree_id_memory = str(hash(self) ^ hash(time.monotonic()))
        return self.tree_id_memory

    def get_groups(self):
        """
        It gets monads of node tree,
        Update them (the sv_update method will check if anything changed inside the monad
        and will change the monad outputs in that case)
        Return the monads that have changed (
        to inform the caller function that the nodes downstream have to be updated with the new data)
        """
        affected_groups =[]
        for node in self.nodes:
            if 'SvGroupNode' in node.bl_idname:
                sub_tree = node.monad
                sub_tree.sv_update()
                if sub_tree.has_changed:
                    affected_groups.append(node)
                    sub_tree.has_changed = False
        return affected_groups

    def sv_update(self):
        """
        the method checks if anything changed inside the normal tree or monad
        and update them if necessary
        """
        self.sv_links.create_new_links(self)
        if self.sv_links.links_have_changed(self):
            self.has_changed = True
            build_update_list(self)
            process_from_nodes(self.sv_links.get_nodes(self))
            self.sv_links.store_links_cache(self)
        else:
            process_from_nodes(self.get_groups())

    def animation_update(self):
        """Find animatable nodes and update from them"""
        animated_nodes = []
        for node in self.nodes:
            if hasattr(node, 'is_animatable'):
                if node.is_animatable:
                    animated_nodes.append(node)
        process_from_nodes(animated_nodes)

    @contextmanager
    def throttle_update(self):
        """ usage
        with tree.throttle_update():
            tree.nodes.new(...)
            tree.links.new(...)
        tree should be updated manually if needed
        """
        previous_state = self.skip_tree_update
        self.skip_tree_update = True
        try:
            yield self
        finally:
            self.skip_tree_update = previous_state


class SverchCustomTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Nodes'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        """
        Turn on/off displaying objects in viewport generated by viewer nodes
        Viewer nodes should have `show_viewport` method which takes 'to_show' bool argument
        """
        for node in self.nodes:
            try:
                node.show_viewport(self.sv_show)
            except AttributeError:
                pass

    def on_draft_mode_changed(self, context):
        """
        This is triggered when Draft mode of the tree is toggled.
        """
        draft_nodes = []
        for node in self.nodes:
            if hasattr(node, 'does_support_draft_mode') and node.does_support_draft_mode():
                draft_nodes.append(node)
                node.on_draft_mode_changed(self.sv_draft)

        # From the user perspective, some of node parameters
        # got new parameter values, so the setup should be recalculated;
        # but techically, node properties were not changed
        # (only other properties were shown in UI), so enabling/disabling
        # of draft mode does not automatically trigger tree update.
        # Here we trigger it manually.

        if draft_nodes:
            process_from_nodes(draft_nodes)

    sv_animate: BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show: BoolProperty(name="Show", default=True, description='Show this layout', update=turn_off_ng)

    # something related with heat map feature
    # looks like it keeps dictionary of nodes and their user defined colors in string format
    sv_user_colors: StringProperty(default="")

    # option whether error message of nodes should be shown in tree space or not
    # for showing error message all tree should be reevaluated what is not nice
    sv_show_error_in_tree: BoolProperty(
        description="This will show Node Exceptions in the node view, right beside the node",
        name="Show error in tree", default=True, update=lambda s, c: process_tree(s), options=set())

    sv_show_error_details : BoolProperty(
            name = "Show error details",
            description = "Display exception stack in the node view as well",
            default = False, 
            update=lambda s, c: process_tree(s),
            options=set())

    sv_show_socket_menus : BoolProperty(
        name = "Show socket menus",
        description = "Display socket dropdown menu buttons. NOTE: options that are enabled in those menus will be effective regardless of this checkbox!",
        default = False,
        options=set())

    # if several nodes are disconnected this option determine order of their evaluation
    sv_subtree_evaluation_order: EnumProperty(
        name="Subtree eval order",
        items=[(k, k, '', i) for i, k in enumerate(["X", "Y", "None"])],
        description=textwrap.dedent("""\
            This will give you control over the order in which subset graphs are evaluated
            1) X, Y modes evaluate subtrees in sequence of lowest absolute node location, useful when working with real geometry
            2) None does no sorting
        """),
        default="None", update=lambda s, c: process_tree(s), options=set()
    )

    # this mode will replace properties of some nodes so they could have lesser values for draft mode
    sv_draft: BoolProperty(
        name="Draft",
        description="Draft (simplified processing) mode",
        default=False,
        update=on_draft_mode_changed)

    def update(self):
        """
        This method is called if collection of nodes or links of the tree was changed
        First of all it checks is it worth bothering and then gives initiative to `update system`
        """

        CurrentEvents.new_event(BlenderEventsTypes.tree_update, self)

        # this is a no-op if there's no drawing
        clear_exception_drawing_with_bgl(self.nodes)
        if is_first_run():
            return
        if self.skip_tree_update:
            return

        self.sv_update()
        self.has_changed = False

    def process_ani(self):
        """
        Process the Sverchok node tree if animation layers show true.
        For animation callback/handler
        """
        if self.sv_animate:
            self.animation_update()
            # process_tree(self)


class UpdateNodes:
    """Everything related with update system of nodes"""

    # identifier of the node, should be used via `node_id` property
    # overriding the property without `skip_save` option can lead to wrong importing bgl viewer nodes
    n_id: StringProperty(options={'SKIP_SAVE'})

    @property
    def node_id(self):
        """Identifier of the node"""
        if not self.n_id:
            self.n_id = str(hash(self) ^ hash(time.monotonic()))
        return self.n_id

    def sv_init(self, context):
        """
        This method will be called during node creation
        Typically it is used for socket creating and assigning properties to sockets
        """
        pass

    def sv_update(self):
        """
        This method can be overridden in inherited classes.
        It will be triggered upon any `node tree` editor changes (new/copy/delete links/nodes).
        Calling of this method is unordered among other calls of the method of other nodes in a tree.
        """
        pass

    def sv_copy(self, original):
        """
        Override this method to do anything node-specific
        at the moment of node being copied.
        """
        pass

    def sv_free(self):
        """
        Override this method to do anything node-specific upon node removal
        """
        pass

    def sv_throttle_tree_update(self):
        """
        It will temporary switch off updating node tree upon adding/removing node/links in a node tree

        class MyNode:
            def property_update(self, context):
                with self.throttle_tree_update():
                    self.inputs.remove('MySocket')
        """
        return data_structure.throttle_tree_update(self)

    def init(self, context):
        """
        this function is triggered upon node creation,
        - throttle the node
        - delegates further initialization information to sv_init
        - sets node color
        """
        CurrentEvents.new_event(BlenderEventsTypes.add_node, self)

        ng = self.id_data
        if ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
            ng.nodes_dict.load_node(self)
        with ng.throttle_update():
            try:
                self.sv_init(context)
            except Exception as err:
                print('nodetree.node.sv_init failure - stare at the error message below')
                sys.stderr.write('ERROR: %s\n' % str(err))
            self.set_color()

    def free(self):
        """
        This method is not supposed to be overriden in specific nodes.
        Override sv_free() instead
        """
        self.sv_free()

        for s in self.outputs:
            s.sv_forget()

        node_tree = self.id_data
        node_tree.nodes_dict.forget_node(self)

        CurrentEvents.new_event(BlenderEventsTypes.free_node, self)
        if hasattr(self, "has_3dview_props"):
            print("about to remove this node's props from Sv3DProps")
            try:
                bpy.ops.node.sv_remove_3dviewpropitem(node_name=self.name, tree_name=self.id_data.name)
            except:
                print(f'failed to remove {self.name} from tree={self.id_data.name}')

    def copy(self, original):
        """
        This method is not supposed to be overriden in specific nodes.
        Override sv_copy() instead.
        """
        CurrentEvents.new_event(BlenderEventsTypes.copy_node, self)
        settings = get_original_node_color(self.id_data, original.name)
        if settings is not None:
            self.use_custom_color, self.color = settings
        self.sv_copy(original)
        self.n_id = ""
        self.id_data.nodes_dict.load_node(self)

    def update(self):
        """
        The method will be triggered upon editor changes, typically before node tree update method.
        It is better to avoid using this trigger.
        """
        CurrentEvents.new_event(BlenderEventsTypes.node_update, self)
        self.sv_update()

    def insert_link(self, link):
        """It will be triggered only if one socket is connected with another by user"""
        CurrentEvents.new_event(BlenderEventsTypes.add_link_to_node, self)

    def process_node(self, context):
        '''
        Doesn't work as intended, inherited functions can't be used for bpy.props
        update= ...
        Still this is called from updateNode
        '''
        if self.id_data.bl_idname == "SverchCustomTreeType":
            if self.id_data.skip_tree_update:
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


class NodeUtils:
    """
    Helper methods.
    Most of them have nothing related with nodes and using as aliases of some functionality.
    The class can be surely ignored during creating of new nodes.
    """
    def get_logger(self):
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
        self.get_logger().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.get_logger().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.get_logger().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.get_logger().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.get_logger().exception(msg, *args, **kwargs)

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
        return op

    def get_bpy_data_from_name(self, identifier, bpy_data_kind):  # todo, method which have nothing related with nodes
        """
        fail gracefuly?
        This function acknowledges that the identifier being passed can be a string or an object proper.
        for a long time Sverchok stored the result of a prop_search as a StringProperty, and many nodes will
        be stored with that data in .blends, here we try to permit older blends having data stored as a string,
        but newly used prop_search results will be stored as a pointerproperty of type bpy.types.Object
        regarding the need to trim the first 3 chars of a stored StringProperty, best let Blender devs enlighten you
        https://developer.blender.org/T58641

        example usage inside a node:

            text = self.get_bpy_data_from_name(self.filename, bpy.data.texts)

        if the text does not exist you get None
        """

        try:
            if isinstance(identifier, bpy.types.Object) and identifier.name in bpy_data_kind:
                return bpy_data_kind.get(identifier.name)  # todo it looks ridiculous to search known object

            elif isinstance(identifier, str):
                if identifier in bpy_data_kind:
                    return bpy_data_kind.get(identifier)
                elif identifier[3:] in bpy_data_kind:
                    return bpy_data_kind.get(identifier[3:])
                return identifier

        except Exception as err:
            self.error(f"identifier '{identifier}' not found in {bpy_data_kind} - with error {err}")

        return None


class SverchCustomTreeNode(UpdateNodes, NodeUtils):
    """Base class for all nodes"""
    _docstring = None  # A cache for docstring property

    @classproperty
    def docstring(cls):
        """
        Get SvDocstring instance parsed from node's docstring.
        """
        if cls._docstring is None:
            cls._docstring = SvDocstring(cls.__doc__)
        return cls._docstring

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname in ['SverchCustomTreeType', 'SverchGroupTreeType']

    @property
    def absolute_location(self):
        """
        It can be useful in case if a node is in a frame node
        does not return a vactor, it returns a:  tuple(x, y)
        """
        return recursive_framed_location_finder(self, self.location[:])

    def set_color(self):  # todo set_default_color ?
        color = color_def.get_color(self.bl_idname)
        if color:
            self.use_custom_color = True
            self.color = color

    def rclick_menu(self, context, layout):
        """
        Override this method to add specific items into
        node's right-click menu.
        Default implementation calls `node_replacement_menu'.
        """
        self.node_replacement_menu(context, layout)

    # Replacing old nodes by new - functionality

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
                if node_class:
                    text = "Replace with {}".format(node_class.bl_label)
                    op = layout.operator("node.sv_replace_node", text=text)
                    op.old_node_name = self.name
                    op.new_bl_idname = bl_idname
                    set_inputs_mapping(op, inputs_mapping)
                    set_outputs_mapping(op, outputs_mapping)
                else:
                    self.error("Can't build replacement menu: no such node class: %s",bl_idname)

    def migrate_links_from(self, old_node, operator):
        """
        This method is called by node replacement operator.
        By default, it removes existing links from old_node
        and creates corresponding links for this (new) node.
        Override it to implement custom re-linking at node
        replacement.
        Most nodes do not have to override this method.
        """
        tree = self.id_data
        # Copy incoming / outgoing links
        old_in_links = [link for link in tree.links if link.to_node == old_node]
        old_out_links = [link for link in tree.links if link.from_node == old_node]

        for old_link in old_in_links:
            new_target_socket_name = operator.get_new_input_name(old_link.to_socket.name)
            if new_target_socket_name in self.inputs:
                new_target_socket = self.inputs[new_target_socket_name]
                new_link = tree.links.new(old_link.from_socket, new_target_socket)
            else:
                self.debug("New node %s has no input named %s, skipping", self.name, new_target_socket_name)
            tree.links.remove(old_link)

        for old_link in old_out_links:
            new_source_socket_name = operator.get_new_output_name(old_link.from_socket.name)
            # We have to remove old link before creating new one
            # Blender would not allow two links pointing to the same target socket
            old_target_socket = old_link.to_socket
            tree.links.remove(old_link)
            if new_source_socket_name in self.outputs:
                new_source_socket = self.outputs[new_source_socket_name]
                new_link = tree.links.new(new_source_socket, old_target_socket)
            else:
                self.debug("New node %s has no output named %s, skipping", self.name, new_source_socket_name)

    def migrate_from(self, old_node):
        """
        This method is called by node replacement operator.
        Override it to correctly copy settings from old_node
        to this (new) node.
        This is called after migrate_links_from().
        Default implementation does nothing.
        """
        pass

    # Methods for OpenGL viewers

    def get_and_set_gl_scale_info(self, origin=None):  # todo, probably openGL viewers should have its own mixin class
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
                prefs.set_nodeview_render_params(None)
        except Exception as err:
            print('failed to get gl scale info', err)


@post_load_call
def add_use_fake_user_to_trees():
    """When ever space node editor switches to another tree or creates new one,
    this function will set True to `use_fake_user` of all Sverchok trees"""
    def set_fake_user():
        [setattr(t, 'use_fake_user', True) for t in bpy.data.node_groups if t.bl_idname == 'SverchCustomTreeType']
    bpy.msgbus.subscribe_rna(key=(bpy.types.SpaceNodeEditor, 'node_tree'), owner=object(), args=(),
                             notify=set_fake_user)


def register():
    bpy.utils.register_class(SverchCustomTree)
    bpy.types.NodeReroute.absolute_location = property(
        lambda self: recursive_framed_location_finder(self, self.location[:]))


def unregister():
    del bpy.types.NodeReroute.absolute_location
    bpy.utils.unregister_class(SverchCustomTree)
