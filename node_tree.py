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
import textwrap

import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty, EnumProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard
from mathutils import Matrix

from sverchok import data_structure
from sverchok.data_structure import get_other_socket

from sverchok.core.update_system import (
    build_update_list,
    process_from_node, process_from_nodes,
    process_tree,
    get_update_lists, update_error_nodes,
    get_original_node_color,
    is_first_run,
    reset_error_nodes)
from sverchok.core.links import (
    SvLinks)
from sverchok.core.node_id_dict import SvNodesDict

from sverchok.core.socket_conversions import DefaultImplicitConversionPolicy
from sverchok.core.node_defaults import set_defaults_if_defined
import sverchok.core.events as ev

from sverchok.utils import get_node_class_reference
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.docstring import SvDocstring
import sverchok.utils.logging
from sverchok.utils.logging import debug

from sverchok.ui import color_def
from sverchok.ui.nodes_replacement import set_inputs_mapping, set_outputs_mapping
from sverchok.utils.exception_drawing_with_bgl import clear_exception_drawing_with_bgl

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
            new_node.location = new_node.absolute_location

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


def throttled(func):
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


class ColorizeTree:
    """
    Methods of colorizing nodes of a node tree
    """
    def choose_colorizing_method(self, context):
        if self.colorizing_method == 'Slow nodes':
            self.colorize_slow_nodes()

    use_colorizing_algorithm: BoolProperty(
        name="Enable", description="To use colorize algorithm", update=choose_colorizing_method)
    colorizing_method: EnumProperty(items=[(i, i, '') for i in ['Slow nodes']], update=choose_colorizing_method)

    # Slow nodes method properties
    update_time: IntProperty(
        name="msec", min=0, max=1000, default=500, description="Time in milliseconds", update=choose_colorizing_method)
    colorizing_color: FloatVectorProperty(size=3, subtype='COLOR', default=(1, 1, 1), update=choose_colorizing_method)

    def colorize_slow_nodes(self):
        node: bpy.types.Node
        for node in self.nodes:
            if self.use_colorizing_algorithm and node.update_time >= self.update_time:
                node.use_custom_color = True
                node.color = self.colorizing_color
            else:
                node.use_custom_color = False


class SvNodeTreeCommon(object):
    '''
    Common methods shared between Sverchok node trees
    '''
    sv_process: BoolProperty(name="Process", default=True, description='Process layout')
    has_changed: BoolProperty(default=False)
    limited_init: BoolProperty(default=False)
    skip_tree_update: BoolProperty(default=False)
    configuring_new_node: BoolProperty(name="indicate node initialization", default=False)
    tree_id_memory: StringProperty(default="")
    sv_links = SvLinks()
    nodes_dict = SvNodesDict()

    @property
    def tree_id(self):
        if not self.tree_id_memory:
            self.tree_id_memory = str(hash(self) ^ hash(time.monotonic()))
        return self.tree_id_memory

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

    def update_sv_links(self):
        self.sv_links.create_new_links(self)

    def links_have_changed(self):
        return self.sv_links.links_have_changed(self)

    def store_links_cache(self):
        self.sv_links.store_links_cache(self)

    def get_nodes(self):
        return self.sv_links.get_nodes(self)

    def get_groups(self):
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
        self.update_sv_links()
        if self.links_have_changed():
            self.has_changed = True
            build_update_list(self)
            process_from_nodes(self.get_nodes())
            self.store_links_cache()
        else:
            process_from_nodes(self.get_groups())

class SvGenericUITooltipOperator(bpy.types.Operator):
    arg: StringProperty()
    bl_idname = "node.sv_generic_ui_tooltip"
    bl_label = "tip"

    @classmethod
    def description(cls, context, properties):
        return properties.arg


class SverchCustomTree(NodeTree, SvNodeTreeCommon, ColorizeTree):
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

    def sv_process_tree_callback(self, context):
        process_tree(self)    

    sv_animate: BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show: BoolProperty(name="Show", default=True, description='Show this layout', update=turn_off_ng)
    sv_bake: BoolProperty(name="Bake", default=True, description='Bake this layout')

    sv_user_colors: StringProperty(default="")

    sv_show_error_in_tree: BoolProperty(
        description="use bgl to draw the error to the nodeview",
        name="Show error in tree", default=False, update=sv_process_tree_callback)

    sv_subtree_evaluation_order: EnumProperty(
        name="Subtree eval order",
        items=[(k, k, '', i) for i, k in enumerate(["X", "Y", "None"])],
        description=textwrap.dedent("""\
            1) X, Y modes evaluate subtrees in sequence of lowest absolute node location, useful when working with real geometry
            2) None does no sorting
        """),
        default="None", update=sv_process_tree_callback
    )

    sv_toggle_nodetree_props: BoolProperty(name="Toggle visibility of props", description="Show more properties for this node tree")

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


    sv_draft : BoolProperty(
                name = "Draft",
                description="Draft (simplified processing) mode",
                default = False,
                update=on_draft_mode_changed)

    tree_link_count: IntProperty(name='keep track of current link count', default=0)


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
        ev.CurrentEvents.add_new_event(event_type=ev.BlenderEventsTypes.tree_update,
                                       node_tree=self)

        if False:  # get from preference
            # this is a no-op if there's no drawing
            clear_exception_drawing_with_bgl(self.nodes)
            if is_first_run():
                return
            if self.skip_tree_update:
                # print('throttled update from context manager')
                return
            if self.configuring_new_node or self.is_frozen() or not self.sv_process:
                return

            self.sv_update()
            self.has_changed = False

            # self.has_changed = True
            # self.process()

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

    def get_nodes_supporting_draft_mode(self):
        draft_nodes = []
        for node in self.nodes:
            if hasattr(node, 'does_support_draft_mode') and node.does_support_draft_mode():
                draft_nodes.append(node)
        return draft_nodes


class SverchCustomTreeNode:

    # A cache for get_docstring() method
    _docstring = None

    _implicit_conversion_policy = dict()

    # In node classes that support draft mode
    # and use separate properties in the draft mode,
    # this should contain mapping from "standard"
    # mode property names to draft mode property names.
    # E.g., draft_properties_mapping = dict(count = 'count_draft').
    draft_properties_mapping = dict()

    n_id : StringProperty(default="")

    # statistic
    updates_total: IntProperty(description="Number of node updates")
    last_update: StringProperty(description="Time of last update")
    update_time: IntProperty(description="How much time last update have taken in milliseconds")
    error: StringProperty(description="Error message of last update if exist")
    
    def update(self):
        # this signal method is absolutely useless
        pass

    def sv_update(self):
        """
        This method can be overridden in inherited classes.
        It will be triggered upon any `node tree` editor changes (new/copy/delete links/nodes).
        Calling of this method is unordered among other calls of the method of other nodes in a tree.
        """
        pass

    def insert_link(self, link):
        ev.CurrentEvents.add_new_event(event_type=ev.BlenderEventsTypes.add_link_to_node,
                                       node_tree=self.id_data,
                                       node=self,
                                       link=link)

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


    def ensure_enums_have_no_space(self, enums=None):
        """
        enums: a list of property names to check. like  self.current_op  

            self.ensure_enums_have_no_space(enums=[current_op])

        due to changes in EnumProperty defintion "laws" individual enum identifiers must not
        contain spaces. This function takes a list of enums that the node currently holds, and 
        makes sure the stored enum has no spaces.
        """
        for enum_property in enums:
            current_value = getattr(self, enum_property)
            if " " in current_value:
                with self.sv_throttle_tree_update():        
                    setattr(self, enum_property, data_structure.no_space(current_value))


    def does_support_draft_mode(self):
        """
        Nodes that either store separate property values
        for draft mode, or perform another version of
        algorithm in draft mode, should return True here.
        """
        return False

    def on_draft_mode_changed(self, new_draft_mode):
        """
        This is triggered when Draft mode of the tree is toggled.
        Nodes should not usually override this, but may override
        sv_draft_mode_changed() instead.
        """
        if self.does_support_draft_mode():
            if new_draft_mode == True:
                with self.sv_throttle_tree_update():
                    if not self.was_in_draft_mode():
                        # Copy values from standard properties
                        # to draft mode ones, when the node enters the
                        # draft mode first time.
                        for prop_name, draft_prop_name in self.draft_properties_mapping.items():
                            setattr(self, draft_prop_name, getattr(self, prop_name))
                    self['_was_in_draft_mode'] = True
        self.sv_draft_mode_changed(new_draft_mode)

    def sv_draft_mode_changed(self, new_draft_mode):
        """
        This is triggered when Draft mode of the tree is toggled.
        Nodes may override this if they need to do something specific
        on this event.
        """
        pass

    def was_in_draft_mode(self):
        """
        Whether this instance of the node ever has been in Draft mode.
        Nodes should not usually override this.
        """
        return self.get('_was_in_draft_mode', False)

    def sv_throttle_tree_update(self):
        return throttle_tree_update(self)

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
        ev.CurrentEvents.add_new_event(event_type=ev.BlenderEventsTypes.add_node,
                                       node_tree=self.id_data,
                                       node=self,
                                       call_function=self.sv_init,
                                       call_function_arguments=(context, ))
        if False:  # todo take from preference
            ng = self.id_data

            ng.freeze()
            ng.nodes_dict.load_node(self)
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
        ev.CurrentEvents.add_new_event(event_type=ev.BlenderEventsTypes.copy_node,
                                       node_tree=self.id_data,
                                       node=self,
                                       call_function=self.sv_copy,
                                       call_function_arguments=(original, ))
        if False:  # todo get this from preference
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
        ev.CurrentEvents.add_new_event(event_type=ev.BlenderEventsTypes.free_node,
                                       node_tree=self.id_data,
                                       node=self,
                                       call_function=self.sv_free)
        if False:  # todo get this from preference
            self.sv_free()

            for s in self.outputs:
                s.sv_forget()

            node_tree = self.id_data
            node_tree.nodes_dict.forget_node(self)

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


classes = [
    SverchCustomTree, 
    SvLinkNewNodeInput,
    SvGenericUITooltipOperator
]


register, unregister = bpy.utils.register_classes_factory(classes)
