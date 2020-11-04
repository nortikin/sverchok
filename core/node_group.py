# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# from __future__ import annotations <- Don't use it here, `group node` will loose its `group tree` attribute
import time
from collections import namedtuple
from contextlib import contextmanager
from functools import reduce
from typing import Tuple, List, Set, Dict, Iterator

import bpy
from sverchok.data_structure import extend_blender_class
from mathutils import Vector

from sverchok.core.group_handlers import MainHandler
from sverchok.core.events import GroupEvent
from sverchok.utils.tree_structure import Tree


class SvGroupTree(bpy.types.NodeTree):
    """Separate tree class for sub trees"""
    bl_idname = 'SvGroupTree'
    bl_icon = 'NODETREE'
    bl_label = 'Group tree'

    handler = MainHandler()

    tree_id_memory: bpy.props.StringProperty(default="")  # identifier of the tree, should be used via `tree_id`

    @property
    def tree_id(self):
        """Identifier of the tree"""
        if not self.tree_id_memory:
            self.tree_id_memory = str(hash(self) ^ hash(time.monotonic()))
        return self.tree_id_memory

    @classmethod
    def poll(cls, context):
        return False  # only for inner usage

    sv_show: bpy.props.BoolProperty(name="Show", default=True, description='Show group tree')
    description: bpy.props.StringProperty(name="Tree description", default="Group nodes don`t work at the moment")

    def upstream_trees(self) -> List['SvGroupTree']:
        """
        It will try to return all the tree sub trees (in case if there is group nodes)
        and sub trees of sub trees and so on
        The method can help to predict if linking new sub tree can lead to cyclic linking
        """
        next_group_nodes = [node for node in self.nodes if node.bl_idname == 'SvGroupTreeNode']
        trees = [self]
        safe_counter = 0
        while next_group_nodes:
            next_node = next_group_nodes.pop()
            if next_node.node_tree:
                trees.append(next_node.node_tree)
                next_group_nodes.extend([
                    node for node in next_node.node_tree.nodes if node.bl_idname == 'SvGroupTreeNode'])
            safe_counter += 1

            if safe_counter > 1000:
                raise RecursionError(f'Looks like group tree "{self}" has links to itself from other groups')
        return trees

    def can_be_linked(self):
        """trying to avoid creating loops of group trees to each other"""
        # upstream trees of tested treed should nad share trees with downstream trees of current tree
        tested_tree_upstream_trees = {t.name for t in self.upstream_trees()}
        current_tree_downstream_trees = {p.node_tree.name for p in bpy.context.space_data.path}
        shared_trees = tested_tree_upstream_trees & current_tree_downstream_trees
        return not shared_trees

    def update(self):
        """trigger on links or nodes collections changes"""
        # When group input or output nodes are connected some extra work should be done
        self.check_last_socket()  # Should not be too expensive to call it each update

        self.check_reroutes_sockets()
        self.update_sockets()  # probably more precise trigger could be found for calling this method
        self.handler.send(GroupEvent(GroupEvent.GROUP_TREE_UPDATE, self.name))

    def update_sockets(self):  # todo it lets simplify sockets API
        """Set properties of sockets of parent nodes and of output modes"""
        for node in self.parent_nodes():
            for n_in_s, t_in_s in zip(node.inputs, self.inputs):
                # also before getting data from socket `socket.use_prop` property should be set
                if hasattr(n_in_s, 'default_property'):
                    n_in_s.use_prop = not t_in_s.hide_value
                if hasattr(t_in_s, 'default_type'):
                    n_in_s.default_property_type = t_in_s.default_type
        for node in (n for n in self.nodes if n.bl_idname == 'NodeGroupOutput'):
            for n_in_s, t_out_s in zip(node.inputs, self.outputs):
                n_in_s.use_prop = not t_out_s.hide_value
                if hasattr(t_out_s, 'default_type'):
                    n_in_s.default_property_type = t_out_s.default_type

    def check_reroutes_sockets(self):
        """
        Fix reroute sockets type
        For now it does work properly in first update
        because all new sockets even if they have links have `is_linked` attribute with False value
        at next update events all works perfectly (skip first update?)

        There is hope this will be fixed https://developer.blender.org/T82390
        """
        tree = Tree(self)
        socket_job = []
        Requirements = namedtuple('Requirements', ['left_n_i', 'left_s_i', 'left_t', 'reroute_n_i',
                                                   'right_n_is', 'right_s_is'])
        # analytical part, it's impossible to use Tree structure and modify the tree
        for node in tree.sorted_walk(tree.output_nodes):
            # walk should be sorted in case if reroute nodes are going one after other
            if node.bl_tween.bl_idname == 'NodeReroute':
                rer_in_s = node.inputs[0]
                rer_out_s = node.outputs[0]
                if rer_in_s.links:
                    left_s = rer_in_s.linked_sockets[0]
                    left_type = left_s.type if hasattr(left_s, 'type') else left_s.bl_tween.bl_idname
                    if left_type != rer_in_s.bl_tween.bl_idname:
                        rer_out_s.type = left_type
                        socket_job.append(Requirements(left_s.node.index, left_s.index, left_type, node.index,
                                                       [s.node.index for s in rer_out_s.linked_sockets],
                                                       [s.index for s in rer_out_s.linked_sockets]))

        # regenerating sockets
        for props in socket_job:
            left_s = self.nodes[props.left_n_i].outputs[props.left_s_i]
            reroute = self.nodes[props.reroute_n_i]

            # handle input socket
            in_s = reroute.inputs.new(props.left_t, left_s.name)
            self.links.new(in_s, left_s)
            reroute.inputs.remove(reroute.inputs[0])

            # handle output sockets
            out_s = reroute.outputs.new(props.left_t, left_s.name)
            for right_n_i, right_s_i in zip(props.right_n_is, props.right_s_is):
                left_s = self.nodes[right_n_i].inputs[right_s_i]
                self.links.new(left_s, out_s)
            reroute.outputs.remove(reroute.outputs[0])
        
    def check_last_socket(self):
        """Override socket creation of standard operator in Node interface menu"""
        if self.inputs:
            if self.inputs[-1].bl_socket_idname == 'NodeSocketFloat':
                # This is wrong socket type -> fixing
                self.inputs.remove(self.inputs[-1])
                self.inputs.new('SvStringsSocket', 'Value')
        if self.outputs:
            if self.outputs[-1].bl_socket_idname == 'NodeSocketFloat':
                self.outputs.remove(self.outputs[-1])
                self.outputs.new('SvStringsSocket', 'Value')

    def update_nodes(self, nodes: list):
        """This method expect to get list of its nodes which should be updated"""
        self.handler.send(GroupEvent(GroupEvent.NODES_UPDATE, updated_tree=self.name,
                                     updated_nodes=[n.name for n in nodes]))

    def parent_nodes(self) -> Iterator['SvGroupTreeNode']:
        """Returns all parent nodes"""
        # todo optimisation?
        for tree in (t for t in bpy.data.node_groups if t.bl_idname in {'SverchCustomTreeType', 'SvGroupTree'}):
            for node in tree.nodes:
                if hasattr(node, 'node_tree') and node.node_tree.name == self.name:
                    yield node


class BaseNode:
    n_id: bpy.props.StringProperty(options={'SKIP_SAVE'})

    @property
    def node_id(self):
        """Identifier of the node"""
        if not self.n_id:
            self.n_id = str(hash(self) ^ hash(time.monotonic()))
        return self.n_id

    def process_node(self, context):
        """update properties of socket of the node trigger this method"""
        self.id_data.update_nodes([self])

    def pass_socket_data(self, inputs: bpy.types.NodeInputs, outputs: bpy.types.NodeOutputs):
        """Should be used for passing data from/to group nodes to/from input/output nodes"""
        for in_s, out_s in zip(inputs, outputs):
            if out_s.identifier == '__extend__' or in_s.identifier == '__extend__':  # virtual socket
                break
            out_s.sv_set(in_s.sv_get(deepcopy=False))


class SvGroupTreeNode(BaseNode, bpy.types.NodeCustomGroup):
    """Node for keeping sub trees"""
    bl_idname = 'SvGroupTreeNode'
    bl_label = 'Group node (mockup)'

    def nested_tree_filter(self, context):
        """Define which tree we would like to use as nested trees."""
        tested_tree = context
        if tested_tree.bl_idname == SvGroupTree.bl_idname:  # It should be our dedicated to this class
            return tested_tree.can_be_linked()
        else:
            return False

    def update_group_tree(self, context):
        """Apply filtered tree to `node_tree` attribute.
        By this attribute Blender is aware of linking between the node and nested tree."""
        self.node_tree: SvGroupTree = self.group_tree
        # also default values should be fixed
        if self.node_tree:
            for node_sock, interface_sock in zip(self.inputs, self.node_tree.inputs):
                if hasattr(interface_sock, 'default_value') and hasattr(node_sock, 'default_property'):
                    node_sock.default_property = interface_sock.default_value
                self.node_tree.update_sockets()  # properties of input socket properties should be updated
        else:  # in case if None is assigned to node_tree
            self.inputs.clear()
            self.outputs.clear()

    group_tree: bpy.props.PointerProperty(type=SvGroupTree, poll=nested_tree_filter, update=update_group_tree)

    def toggle_active(self, state: bool, to_update: bool = True):
        """This function can change state of `is_active` attribute without node updating"""
        if 'toggle_active' in self:
            # avoiding recursion
            del self['toggle_active']
            return
        else:
            self['toggle_active'] = True
            self.is_active = state  # it will call the method again and will delete 'toggle_active' key
            if state and to_update:
                self.id_data.update_nodes([self])

    is_active: bpy.props.BoolProperty(name="Live", description='Update realtime if active', default=True,
                                      update=lambda s, c: s.toggle_active(s.is_active))

    def draw_buttons(self, context, layout):
        if self.node_tree:
            row_description = layout.row()

            row = row_description.row(align=True)
            row.scale_x = 5
            row.alignment = 'RIGHT'
            row.prop(self, 'is_active', toggle=True)
            row.prop(self.node_tree, 'sv_show', text="",
                     icon=f'RESTRICT_VIEW_{"OFF" if self.node_tree.sv_show else "ON"}')
            row.prop(self.node_tree, 'use_fake_user', text="")

            add_description = row_description.operator('node.add_tree_description', text='', icon='QUESTION')
            add_description.tree_name = self.node_tree.name
            add_description.description = self.node_tree.description

        col = layout.column()
        # col.template_ID(self, 'group_tree')
        row_name = col.row()
        row_ops = col.row()
        row_search = row_ops.row(align=True)
        row_search.operator('node.search_group_tree', text='', icon='VIEWZOOM')
        if self.group_tree:
            row_name.prop(self.group_tree, 'name', text='')
            row_search.operator('node.edit_group_tree', text='Edit', icon='FILE_PARENT')
            row_ops.operator('node.ungroup_group_tree', text='', icon='MOD_PHYSICS')
        else:
            row_search.operator('node.add_group_tree', text='New', icon='ADD')

    def process(self):
        if not self.node_tree or not self.is_active:
            return

        self.node_tree: SvGroupTree
        self.node_tree.handler.send(GroupEvent(GroupEvent.GROUP_NODE_UPDATE, updated_tree=self.node_tree.name))


class PlacingNodeOperator:
    """Helper class for locating nodes in a node tree"""
    # quite basic operator can be moved to some more general module
    @staticmethod
    def placing_node(context, node_type: str):
        tree = context.space_data.path[-1].node_tree
        bpy.ops.node.select_all(action='DESELECT')
        group_node = tree.nodes.new(node_type)
        group_node.location = context.space_data.cursor_location

    @staticmethod
    def store_mouse_cursor(context, event):
        # convert mouse position to the View2D for later node placement
        space = context.space_data
        space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)

    # Default invoke stores the mouse position to place the node correctly
    # and invokes the transform operator
    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        result = self.execute(context)

        if 'FINISHED' in result:
            # removes the node again if transform is canceled
            bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')

        return result


class AddGroupNode(PlacingNodeOperator, bpy.types.Operator):
    """Creating just group node without linking any sub tree to it"""
    bl_idname = "node.add_group_node"
    bl_label = "Add group node"

    def execute(self, context):
        self.placing_node(context, 'SvGroupTreeNode')
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return cls.can_be_added(context)[0]

    @classmethod
    def description(cls, context, properties):
        return cls.can_be_added(context)[1]

    @classmethod
    def can_be_added(cls, context) -> Tuple[bool, str]:
        path = context.space_data.path[-1] if len(context.space_data.path) else None
        if not path:
            return False, ''
        tree = path.node_tree
        if tree.bl_idname == 'SverchCustomTreeType':
            for node in tree.nodes:
                if node.bl_idname.startswith('SvGroupNodeMonad'):
                    return False, 'Either monad or group node should be used in the tree'
            return True, 'Add group node'
        elif tree.bl_idname == 'SvGroupTree':
            return True, "Add group node"
        else:
            return False, f"Can't add in '{tree.bl_idname}' type"


class AddNodeOutputInput(PlacingNodeOperator, bpy.types.Operator):
    """Operator for creating output and input nodes in sub trees"""
    bl_idname = "node.add_node_output_input"
    bl_label = "Add output input nodes"

    node_type: bpy.props.EnumProperty(items=[(i, i, '') for i in ['input', 'output']])

    def execute(self, context):
        if self.node_type == 'input':
            node_type = 'NodeGroupInput'
        else:
            node_type = 'NodeGroupOutput'
        self.placing_node(context, node_type)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        path = context.space_data.path
        if len(path):
            if path[-1].node_tree.bl_idname == SvGroupTree.bl_idname:
                return True
        return False

    @classmethod
    def description(cls, context, properties):
        return f'Add group {properties.node_type} node'


class AddGroupTree(bpy.types.Operator):
    """Create empty sub tree for group node"""
    bl_idname = "node.add_group_tree"
    bl_label = "Add group tree"

    def execute(self, context):
        """Link new sub tree to group node, create input and output nodes in sub tree and go to edit one"""
        sub_tree = bpy.data.node_groups.new('Sverchok group', 'SvGroupTree')  # creating sub tree
        sub_tree.use_fake_user = True
        context.node.group_tree = sub_tree  # link sub tree to group node
        sub_tree.nodes.new('NodeGroupInput').location = (-250, 0)  # create node for putting data into sub tree
        sub_tree.nodes.new('NodeGroupOutput').location = (250, 0)  # create node for getting data from sub tree
        context.space_data.path.append(sub_tree, node=context.node)  # notify window that to edit the sub tree
        return {'FINISHED'}


class AddGroupTreeFromSelected(bpy.types.Operator):
    """Create instead of select nodes group node and placing them into sub tree"""
    bl_idname = "node.add_group_tree_from_selected"
    bl_label = "Add group tree from selected"

    @classmethod
    def poll(cls, context):
        path = context.space_data.path
        if len(path):
            if path[-1].node_tree.bl_idname in {'SverchCustomTreeType', SvGroupTree.bl_idname}:
                return bool(cls.filter_selected_nodes(path[-1].node_tree))
        return False

    def execute(self, context):  # todo move main logic into separate method which could be tested
        """
        Add group tree from selected:
        01. Deselect group Input and Output nodes
        02. Copy nodes into clipboard
        03. Create group tree and move into one
        04. Past nodes from clipboard
        05. Move nodes into tree center
        06. Add group "input" and "output" outside of bounding box of the nodes
        07. Connect "input" and "output" sockets with group nodes
        08. Add Group tree node in center of selected node in initial tree
        09. Link the node with appropriate sockets
        10. Cleaning
        """
        # deselect group nodes if selected
        base_tree = context.space_data.path[-1].node_tree
        if not self.can_be_grouped(base_tree):
            self.report({'WARNING'}, 'Current selection can not be converted to group')
            return {'CANCELLED'}
        [setattr(n, 'select', False) for n in base_tree.nodes
         if n.select and n.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}]

        # Frames can't be just copied because they does not have absolute location, but they can be recreated
        frame_names = {n.name for n in base_tree.nodes if n.select and n.bl_idname == 'NodeFrame'}
        [setattr(n, 'select', False) for n in base_tree.nodes if n.bl_idname == 'NodeFrame']

        # copy and past nodes into group tree
        bpy.ops.node.clipboard_copy()
        sub_tree: SvGroupTree = bpy.data.node_groups.new('Sverchok group', SvGroupTree.bl_idname)
        context.space_data.path.append(sub_tree)
        bpy.ops.node.clipboard_paste()

        # move nodes in tree center
        sub_tree_nodes = self.filter_selected_nodes(sub_tree)
        center = reduce(lambda v1, v2: v1 + v2, [n.location for n in sub_tree_nodes]) / len(sub_tree_nodes)
        [setattr(n, 'location', n.location - center) for n in sub_tree_nodes]

        # recreate frames
        node_name_mapping = {n.name: n.name for n in sub_tree.nodes}  # all nodes have the same name as in base tree
        self.recreate_frames(base_tree, sub_tree, frame_names, node_name_mapping)

        # add group input and output nodes
        min_x = min(n.location[0] for n in sub_tree_nodes)
        max_x = max(n.location[0] for n in sub_tree_nodes)
        input_node = sub_tree.nodes.new('NodeGroupInput')
        input_node.location = (min_x - 250, 0)
        output_node = sub_tree.nodes.new('NodeGroupOutput')
        output_node.location = (max_x + 250, 0)

        # add group tree node
        initial_nodes = self.filter_selected_nodes(base_tree)
        center = reduce(lambda v1, v2: v1 + v2,
                        [Vector(n.absolute_location) for n in initial_nodes]) / len(initial_nodes)
        group_node = base_tree.nodes.new(SvGroupTreeNode.bl_idname)
        group_node.select = False
        group_node.group_tree = sub_tree
        group_node.location = center

        # linking, linking should be ordered from first socket to last (in case like `join list` nodes)
        py_base_tree = Tree(base_tree)
        input_node['connected_sockets'] = dict()  # Dict[node.name + socket.identifier, socket index of input node]
        for py_node in py_base_tree.nodes:  # is selected
            if not py_node.select:
                continue
            for in_py_socket in py_node.inputs:
                for out_py_socket in in_py_socket.linked_sockets:  # only one link always
                    if out_py_socket.node.select:
                        continue
                    out_py_s_key = out_py_socket.node.name + out_py_socket.identifier
                    if out_py_s_key in input_node['connected_sockets']:  # protect from creating extra input sockets
                        input_out_s_index = input_node['connected_sockets'][out_py_s_key]
                    else:
                        input_out_s_index = len(input_node.outputs) - 1
                        input_node['connected_sockets'][out_py_s_key] = input_out_s_index
                    sub_tree.links.new(in_py_socket.get_bl_socket(sub_tree), input_node.outputs[input_out_s_index])
                    base_tree.links.new(group_node.inputs[-1], out_py_socket.get_bl_socket(base_tree))

            for out_py_socket in py_node.outputs:
                if any(not s.node.select for s in out_py_socket.linked_sockets):
                    sub_tree.links.new(output_node.inputs[-1], out_py_socket.get_bl_socket(sub_tree))
                for in_py_socket in out_py_socket.linked_sockets:
                    if not in_py_socket.node.select:
                        base_tree.links.new(in_py_socket.get_bl_socket(base_tree), group_node.outputs[-1])

        # delete selected nodes and copied frames without children
        [base_tree.nodes.remove(n) for n in self.filter_selected_nodes(base_tree)]
        with_children_frames = {n.parent.name for n in base_tree.nodes if n.parent}
        [base_tree.nodes.remove(n) for n in base_tree.nodes
         if n.name in frame_names and n.name not in with_children_frames]

        return {'FINISHED'}

    @staticmethod
    def filter_selected_nodes(tree) -> list:
        """Avoiding selecting nodes which should not be copied into sub tree"""
        return [n for n in tree.nodes if n.select and n.bl_idname not in {'NodeGroupInput', 'NodeGroupOutput'}]

    @staticmethod
    def can_be_grouped(tree) -> bool:
        """True if selected nodes can be putted into group (does not produce cyclic links)"""
        # if there is one or more unselected nodes between nodes to be grouped
        # then current selection can't be grouped
        py_tree = Tree(tree)
        [setattr(py_tree.nodes[n.name], 'select', n.select) for n in tree.nodes]
        for node in py_tree.nodes:
            if not node.select:
                continue
            for neighbour_node in node.next_nodes:
                if neighbour_node.select:
                    continue
                for next_node in py_tree.bfs_walk([neighbour_node]):
                    if next_node.select:
                        return False
        return True

    @staticmethod
    def recreate_frames(from_tree: bpy.types.NodeTree,
                        to_tree: bpy.types.NodeTree,
                        frame_names: Set[str],
                        from_to_node_names: Dict[str, str]):
        """
        It will copy frames from one tree to another
        from_to_node_names - mapping of node names between two trees
        """
        new_frame_names = {n: to_tree.nodes.new('NodeFrame').name for n in frame_names}
        frame_attributes = ['label', 'use_custom_color', 'color', 'label_size', 'text']
        for frame_name in frame_names:
            old_frame = from_tree.nodes[frame_name]
            new_frame = to_tree.nodes[new_frame_names[frame_name]]
            for attr in frame_attributes:
                setattr(new_frame, attr, getattr(old_frame, attr))
        for from_node in from_tree.nodes:
            if from_node.name not in from_to_node_names:
                continue
            if from_node.parent and from_node.parent.name in new_frame_names:
                if from_node.bl_idname == 'NodeFrame':
                    to_node = to_tree.nodes[new_frame_names[from_node.name]]
                else:
                    to_node = to_tree.nodes[from_to_node_names[from_node.name]]
                to_node.parent = to_tree.nodes[new_frame_names[from_node.parent.name]]


class UngroupGroupTree(bpy.types.Operator):
    """Put sub nodes into current layout and delete current group node"""
    bl_idname = 'node.ungroup_group_tree'
    bl_label = "Ungroup group tree"

    @classmethod
    def poll(cls, context):
        if context.active_node and hasattr(context.active_node, 'node_tree'):
            return True
        elif context.node:
            return True
        return False

    def execute(self, context):
        """Similar to AddGroupTreeFromSelected operator but in backward direction (from sub tree to tree)"""

        # go to sub tree, select all except input and output groups and mark nodes to be copied
        group_node = context.node
        sub_tree = group_node.node_tree
        bpy.ops.node.edit_group_tree({'node': group_node})
        [setattr(n, 'select', False) for n in sub_tree.nodes]
        group_nodes_filter = filter(lambda n: n.bl_idname not in {'NodeGroupInput', 'NodeGroupOutput'}, sub_tree.nodes)
        for node in group_nodes_filter:
            node.select = True
            node['sub_node_name'] = node.name  # this will be copied within the nodes

        # the attribute should be empty in destination tree
        tree = context.space_data.path[-2].node_tree
        for node in tree.nodes:
            if 'sub_node_name' in node:
                del node['sub_node_name']

        # Frames can't be just copied because they does not have absolute location, but they can be recreated
        frame_names = {n.name for n in sub_tree.nodes if n.select and n.bl_idname == 'NodeFrame'}
        [setattr(n, 'select', False) for n in sub_tree.nodes if n.bl_idname == 'NodeFrame']

        if any(n for n in sub_tree.nodes if n.select):  # if no selection copy operator will raise error
            # copy and past nodes into group tree
            bpy.ops.node.clipboard_copy()
            context.space_data.path.pop()
            bpy.ops.node.clipboard_paste()  # this will deselect all and select only pasted nodes

            # move nodes in group node center
            tree_select_nodes = [n for n in tree.nodes if n.select]
            center = reduce(lambda v1, v2: v1 + v2,
                            [Vector(n.absolute_location) for n in tree_select_nodes]) / len(tree_select_nodes)
            [setattr(n, 'location', n.location - (center - group_node.location)) for n in tree_select_nodes]

            # recreate frames
            node_name_mapping = {n['sub_node_name']: n.name for n in tree.nodes if 'sub_node_name' in n}
            AddGroupTreeFromSelected.recreate_frames(sub_tree, tree, frame_names, node_name_mapping)
        else:
            context.space_data.path.pop()  # should exit from sub tree anywhere

        # recreate py tree structure
        sub_py_tree = Tree(sub_tree)
        [setattr(sub_py_tree.nodes[n.name], 'type', n.bl_idname) for n in sub_tree.nodes]
        py_tree = Tree(tree)
        [setattr(py_tree.nodes[n.name], 'select', n.select) for n in tree.nodes]
        group_py_node = py_tree.nodes[group_node.name]
        for node in tree.nodes:
            if 'sub_node_name' in node:
                sub_py_tree.nodes[node['sub_node_name']].twin = py_tree.nodes[node.name]
                py_tree.nodes[node.name].twin = sub_py_tree.nodes[node['sub_node_name']]

        # create in links
        for group_input_py_node in [n for n in sub_py_tree.nodes if n.type == 'NodeGroupInput']:
            for group_in_s, input_out_s in zip(group_py_node.inputs, group_input_py_node.outputs):
                if group_in_s.links and input_out_s.links:
                    link_out_s = group_in_s.linked_sockets[0]
                    for twin_in_s in input_out_s.linked_sockets:
                        if twin_in_s.node.type == 'NodeGroupOutput':  # node should be searched in above tree
                            group_out_s = group_py_node.outputs[twin_in_s.index]
                            for link_in_s in group_out_s.linked_sockets:
                                tree.links.new(link_in_s.get_bl_socket(tree), link_out_s.get_bl_socket(tree))
                        else:
                            link_in_s = twin_in_s.node.twin.inputs[twin_in_s.index]
                            tree.links.new(link_in_s.get_bl_socket(tree), link_out_s.get_bl_socket(tree))

        # create out links
        for group_output_py_node in [n for n in sub_py_tree.nodes if n.type == 'NodeGroupOutput']:
            for group_out_s, output_in_s in zip(group_py_node.outputs, group_output_py_node.inputs):
                if group_out_s.links and output_in_s.links:
                    twin_out_s = output_in_s.linked_sockets[0]
                    if twin_out_s.node.type == 'NodeGroupInput':
                        continue  # we already added this link
                    for link_in_s in group_out_s.linked_sockets:
                        link_out_s = twin_out_s.node.twin.outputs[twin_out_s.index]
                        tree.links.new(link_in_s.get_bl_socket(tree), link_out_s.get_bl_socket(tree))

        # delete group node
        tree.nodes.remove(group_node)
        for node in tree.nodes:
            if 'sub_node_name' in node:
                del node['sub_node_name']

        return {'FINISHED'}


class EditGroupTree(bpy.types.Operator):
    """Go into sub tree to edit"""
    bl_idname = 'node.edit_group_tree'
    bl_label = 'Edit group tree'

    def execute(self, context):
        context.space_data.path.append(context.node.node_tree, node=context.node)
        return {'FINISHED'}


class AddTreeDescription(bpy.types.Operator):
    """UI for filling Group tree description"""
    bl_idname = 'node.add_tree_description'
    bl_label = "Tree description"

    tree_name: bpy.props.StringProperty(options={'HIDDEN'})

    from_file: bpy.props.BoolProperty()
    text_name: bpy.props.StringProperty(description="Text with description of the node")
    description: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return properties.description

    def execute(self, context):
        tree = bpy.data.node_groups[self.tree_name]
        if self.from_file:
            tree.description = bpy.data.texts[self.text_name].as_string()
        else:
            tree.description = self.description
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        row = col.row()
        row.active = not self.from_file
        row.prop(self, 'description')
        col.prop(self, 'from_file')
        row = col.row()
        row.active = self.from_file
        row.prop_search(self, 'text_name', bpy.data, 'texts', text="Description")


class SearchGroupTree(bpy.types.Operator):
    """Browse group trees to be linked"""
    bl_idname = 'node.search_group_tree'
    bl_label = 'Search group tree'
    bl_property = 'tree_name'

    def available_trees(self, context):
        linkable_trees = filter(lambda t: hasattr(t, 'can_be_linked') and t.can_be_linked(), bpy.data.node_groups)
        return [(t.name, t.name, '') for t in linkable_trees]

    tree_name: bpy.props.EnumProperty(items=available_trees)

    group_node_name: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        tree = context.space_data.path[-1].node_tree
        tree_to_link = bpy.data.node_groups[self.tree_name]
        group_node = tree.nodes[self.group_node_name]
        group_node.group_tree = tree_to_link
        return {'FINISHED'}

    def invoke(self, context, event):
        self.group_node_name = context.node.name  # execute context does not have the attribute -_-
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


classes = [SvGroupTree, SvGroupTreeNode, AddGroupNode, AddGroupTree, EditGroupTree, AddTreeDescription,
           AddNodeOutputInput, AddGroupTreeFromSelected, SearchGroupTree, UngroupGroupTree]


class BaseInOutNodes:
    def pass_socket_data(self, inputs: bpy.types.NodeInputs, outputs: bpy.types.NodeOutputs):
        """Should be used for passing data from/to group nodes to/from input/output nodes"""
        for in_s, out_s in zip(inputs, outputs):
            if out_s.identifier == '__extend__' or in_s.identifier == '__extend__':  # virtual socket
                break
            out_s.sv_set(in_s.sv_get(deepcopy=False))


@extend_blender_class
class NodeGroupOutput(BaseInOutNodes, BaseNode):
    def process(self):
        # pass data to all parent group nodes
        for group_node in self.id_data.parent_nodes():
            # if socket was just linked it will have `is_linked` equal False https://developer.blender.org/T82318
            self.pass_socket_data(self.inputs, group_node.outputs)


@extend_blender_class
class NodeGroupInput(BaseInOutNodes, BaseNode):
    def process(self):
        # should grab data from parent nodes when it is connected
        for group_node in self.id_data.parent_nodes():
            self.pass_socket_data(group_node.inputs, self.outputs)


@extend_blender_class
class NodeReroute(BaseNode):
    def process(self):
        self.outputs[0].sv_set(self.inputs[0].sv_get(deepcopy=False))


register, unregister = bpy.utils.register_classes_factory(classes)
