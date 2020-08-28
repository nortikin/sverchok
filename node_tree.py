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

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import NodeTree

from sverchok import data_structure
from sverchok.data_structure import classproperty

from sverchok.core.update_system import (
    build_update_list,
    process_from_node, process_from_nodes,
    process_tree,
    get_original_node_color,
    is_first_run,)
from sverchok.core.links import (
    SvLinks)
from sverchok.core.node_id_dict import SvNodesDict

from sverchok.core.socket_conversions import DefaultImplicitConversionPolicy
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
    skip_tree_update: BoolProperty(default=False)
    tree_id_memory: StringProperty(default="")  # identifier of the tree, should be used via `tree_id` property
    sv_links = SvLinks()  # cached Python links
    nodes_dict = SvNodesDict()  # cached Python nodes

    @property
    def tree_id(self):
        """Identifier of the tree"""
        if not self.tree_id_memory:
            self.tree_id_memory = str(hash(self) ^ hash(time.monotonic()))
        return self.tree_id_memory

    def freeze(self, hard=False):
        """Temporary prevent tree from updating nodes"""
        if hard:
            self["don't update"] = 1
        elif not self.is_frozen():
            self["don't update"] = 0

    def is_frozen(self):
        """Nodes of the tree won't be updated during changes events"""
        return "don't update" in self

    def unfreeze(self, hard=False):
        """
        Remove freeze mode from tree.
        If freeze mode was in hard mode `hard` argument should be True to unfreeze tree
        """
        if self.is_frozen():
            if hard or self["don't update"] == 0:
                del self["don't update"]

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
        process_tree(self)

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
            try:
                bpy.context.window.cursor_set("WAIT")
                was_frozen = self.is_frozen()
                self.unfreeze(hard=True)
                process_from_nodes(draft_nodes)
            finally:
                if was_frozen:
                    self.freeze(hard=True)
                bpy.context.window.cursor_set("DEFAULT")

    sv_animate: BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show: BoolProperty(name="Show", default=True, description='Show this layout', update=turn_off_ng)

    # something related with heat map feature
    # looks like it keeps dictionary of nodes and their user defined colors in string format
    sv_user_colors: StringProperty(default="")

    # option whether error message of nodes should be shown in tree space or not
    # for showing error message all tree should be reevaluated what is not nice
    sv_show_error_in_tree: BoolProperty(
        description="use bgl to draw the error to the nodeview",
        name="Show error in tree", default=False, update=lambda s, c: process_tree(s))

    # if several nodes are disconnected this option determine order of their evaluation
    sv_subtree_evaluation_order: EnumProperty(
        name="Subtree eval order",
        items=[(k, k, '', i) for i, k in enumerate(["X", "Y", "None"])],
        description=textwrap.dedent("""\
            1) X, Y modes evaluate subtrees in sequence of lowest absolute node location, useful when working with real geometry
            2) None does no sorting
        """),
        default="None", update=lambda s, c: process_tree(s)
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
        if self.is_frozen() or not self.sv_process:
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

    def process(self):  # todo looks like this method is not used any more
        """
        process the Sverchok tree upon editor changes from handler
        """

        if self.has_changed:
            # print('processing build list: because has_changed==True')
            build_update_list(self)
            self.has_changed = False
        if self.is_frozen():
            # print('not processing: because self/tree.is_frozen') 
            return
        if self.sv_process:
            process_tree(self)

        self.has_changed = False


class SverchCustomTreeNode:

    _docstring = None  # A cache for docstring property

    _implicit_conversion_policy = dict()

    n_id : StringProperty(default="")
    
    def update(self):
        CurrentEvents.new_event(BlenderEventsTypes.node_update, self)
        self.sv_update()

    def sv_update(self):
        """
        This method can be overridden in inherited classes.
        It will be triggered upon any `node tree` editor changes (new/copy/delete links/nodes).
        Calling of this method is unordered among other calls of the method of other nodes in a tree.
        """
        pass

    def insert_link(self, link):
        CurrentEvents.new_event(BlenderEventsTypes.add_link_to_node, self)

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname in ['SverchCustomTreeType', 'SverchGroupTreeType']

    @property
    def node_id(self):
        if not self.n_id:
            self.n_id = str(hash(self) ^ hash(time.monotonic()))
        return self.n_id

    @property
    def absolute_location(self):
        """ does not return a vactor, it returns a:  tuple(x, y) """
        return recursive_framed_location_finder(self, self.location[:])

    def sv_throttle_tree_update(self):
        return data_structure.throttle_tree_update(self)

    def sv_setattr_with_throttle(self, prop_name, prop_data):
        with self.sv_throttle_tree_update():
            setattr(self, prop_name, prop_data)

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

    def set_implicit_conversions(self, input_socket_name, policy):  # <- is not used now
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

    def set_color(self):  # todo set_default_color ?
        color = color_def.get_color(self.bl_idname)
        if color:
            self.use_custom_color = True
            self.color = color

    @classproperty
    def docstring(cls):
        """
        Get SvDocstring instance parsed from node's docstring.
        """
        if cls._docstring is None:
            cls._docstring = SvDocstring(cls.__doc__)
        return cls._docstring

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

    def rclick_menu(self, context, layout):
        """
        Override this method to add specific items into
        node's right-click menu.
        Default implementation calls `node_replacement_menu'.
        """
        self.node_replacement_menu(context, layout)

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

    def sv_init(self, context):
        pass

    def init(self, context):
        """
        this function is triggered upon node creation,
        - freezes the node
        - delegates further initialization information to sv_init
        - sets node color
        - unfreezes the node
        """
        CurrentEvents.new_event(BlenderEventsTypes.add_node, self)
        ng = self.id_data

        ng.freeze()
        ng.nodes_dict.load_node(self)
        if hasattr(self, "sv_init"):

            try:
                self.sv_init(context)
            except Exception as err:
                print('nodetree.node.sv_init failure - stare at the error message below')
                sys.stderr.write('ERROR: %s\n' % str(err))

        self.set_color()
        ng.unfreeze()

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
        CurrentEvents.new_event(BlenderEventsTypes.copy_node, self)
        settings = get_original_node_color(self.id_data, original.name)
        if settings is not None:
            self.use_custom_color, self.color = settings
        self.sv_copy(original)
        self.n_id = ""
        self.id_data.nodes_dict.load_node(self)

    def sv_copy(self, original):
        """
        Override this method to do anything node-specific
        at the moment of node being copied.
        """
        pass
        
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

    def sv_free(self):
        """
        Override this method to do anything node-specific upon node removal

        """
        pass

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

    def get_bpy_data_from_name(self, identifier, bpy_data_kind):
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
                return bpy_data_kind.get(identifier.name)
            
            elif isinstance(identifier, str):
                if identifier in bpy_data_kind:
                    return bpy_data_kind.get(identifier)
                elif identifier[3:] in bpy_data_kind:
                    return bpy_data_kind.get(identifier[3:])
                return identifier

        except Exception as err:
             self.error(f"identifier '{identifier}' not found in {bpy_data_kind} - with error {err}")

        return None


classes = [SverchCustomTree]


register, unregister = bpy.utils.register_classes_factory(classes)
