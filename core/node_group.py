# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# from __future__ import annotations <- Don't use it here, `group node` will loose its `group tree` attribute
from functools import reduce
from typing import Tuple, List

import bpy
from sverchok.utils.tree_structure import Tree


class SvGroupTree(bpy.types.NodeTree):
    bl_idname = 'SvGroupTree'
    bl_icon = 'NODETREE'
    bl_label = 'Group tree'

    @classmethod
    def poll(cls, context):
        return False  # only for inner usage

    sv_show: bpy.props.BoolProperty(name="Show", default=True, description='Show group tree')
    description: bpy.props.StringProperty(name="Tree description", default="Group nodes don`t work at the moment")

    def upstream_trees(self) -> List['SvGroupTree']:
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
        # trying to avoid creating loops of group trees to each other
        # upstream trees of tested treed should nad share trees
        # with downstream trees of current tree
        tested_tree_upstream_trees = {t.name for t in self.upstream_trees()}
        current_tree_downstream_trees = {p.node_tree.name for p in bpy.context.space_data.path}
        shared_trees = tested_tree_upstream_trees & current_tree_downstream_trees
        return not shared_trees


class SvGroupTreeNode(bpy.types.NodeCustomGroup):
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
        self.node_tree = self.group_tree
        # also default values should be fixed
        if self.node_tree:
            for node_sock, interface_sock in zip(self.inputs, self.node_tree.inputs):
                if hasattr(interface_sock, 'default_value') and hasattr(node_sock, 'default_property'):
                    node_sock.default_property = interface_sock.default_value
        else:  # in case if None is assigned to node_tree
            self.inputs.clear()
            self.outputs.clear()

    group_tree: bpy.props.PointerProperty(type=SvGroupTree, poll=nested_tree_filter, update=update_group_tree)

    def draw_buttons(self, context, layout):
        if self.node_tree:
            row_description = layout.row()

            row = row_description.row(align=True)
            row.scale_x = 5
            row.alignment = 'RIGHT'
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
            row_search.operator('node.edit_group_tree', text=' ', icon='FILE_PARENT')
            row_ops.operator('node.ungroup_group_tree', text='', icon='MOD_PHYSICS')
        else:
            row_search.operator('node.add_group_tree', text='New', icon='ADD')

    def process_node(self, context):
        # update properties of socket of the node trigger this method
        pass


class PlacingNodeOperator:
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
    bl_idname = "node.add_group_tree"
    bl_label = "Add group tree"

    def execute(self, context):
        sub_tree = bpy.data.node_groups.new('Sverchok group', 'SvGroupTree')  # creating sub tree
        context.node.group_tree = sub_tree  # link sub tree to group node
        sub_tree.nodes.new('NodeGroupInput').location = (-250, 0)  # create node for putting data into sub tree
        sub_tree.nodes.new('NodeGroupOutput').location = (250, 0)  # create node for getting data from sub tree
        context.space_data.path.append(sub_tree, node=context.node)  # notify window that to edit the sub tree
        return {'FINISHED'}


class AddGroupTreeFromSelected(bpy.types.Operator):
    bl_idname = "node.add_group_tree_from_selected"
    bl_label = "Add group tree from selected"

    @classmethod
    def poll(cls, context):
        path = context.space_data.path
        if len(path):
            if path[-1].node_tree.bl_idname in {'SverchCustomTreeType', SvGroupTree.bl_idname}:
                return bool(cls.filter_selected_nodes(path[-1].node_tree))
        return False

    def execute(self, context):
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
        10. Delete selected nodes in initial tree
        """
        # deselect group nodes if selected
        base_tree = context.space_data.path[-1].node_tree
        if not self.can_be_grouped(base_tree):
            self.report({'WARNING'}, 'Current selection can not be converted to group')
            return {'CANCELLED'}
        [setattr(n, 'select', False) for n in base_tree.nodes
         if n.select and n.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}]

        # copy and past nodes into group tree
        bpy.ops.node.clipboard_copy()
        sub_tree = bpy.data.node_groups.new('Sverchok group', SvGroupTree.bl_idname)
        context.space_data.path.append(sub_tree)
        bpy.ops.node.clipboard_paste()

        # move nodes in tree center
        sub_tree_nodes = self.filter_selected_nodes(sub_tree)
        center = reduce(lambda v1, v2: v1 + v2, [n.location for n in sub_tree_nodes]) / len(sub_tree_nodes)
        [setattr(n, 'location', n.location - center) for n in sub_tree_nodes]

        # add group input and output nodes
        min_x = min(n.location[0] for n in sub_tree_nodes)
        max_x = max(n.location[0] for n in sub_tree_nodes)
        input_node = sub_tree.nodes.new('NodeGroupInput')
        input_node.location = (min_x - 250, 0)
        output_node = sub_tree.nodes.new('NodeGroupOutput')
        output_node.location = (max_x + 250, 0)

        # add group tree node
        initial_nodes = self.filter_selected_nodes(base_tree)
        center = reduce(lambda v1, v2: v1 + v2, [n.location for n in initial_nodes]) / len(initial_nodes)
        group_node = base_tree.nodes.new(SvGroupTreeNode.bl_idname)
        group_node.select = False
        group_node.group_tree = sub_tree
        group_node.location = center

        # linking, linking should be ordered from first socket to last (in case like `join list` nodes)
        py_base_tree = Tree.from_bl_tree(base_tree)
        for py_node in py_base_tree.nodes.values():  # is selected
            if not py_node.select:
                continue
            for in_py_socket in py_node.inputs:
                for out_py_socket in in_py_socket.linked_sockets:  # only one link always
                    if out_py_socket.node.select:
                        continue
                    sub_tree.links.new(in_py_socket.get_bl_socket(sub_tree), input_node.outputs[-1])
                    base_tree.links.new(group_node.inputs[-1], out_py_socket.get_bl_socket(base_tree))

            for out_py_socket in py_node.outputs:
                if any(not s.node.select for s in out_py_socket.linked_sockets):
                    sub_tree.links.new(output_node.inputs[-1], out_py_socket.get_bl_socket(sub_tree))
                for in_py_socket in out_py_socket.linked_sockets:
                    if not in_py_socket.node.select:
                        base_tree.links.new(in_py_socket.get_bl_socket(base_tree), group_node.outputs[-1])

        # delete selected nodes
        [base_tree.nodes.remove(n) for n in self.filter_selected_nodes(base_tree)]

        return {'FINISHED'}

    @staticmethod
    def filter_selected_nodes(tree) -> list:
        return [n for n in tree.nodes if n.select and n.bl_idname not in {'NodeGroupInput', 'NodeGroupOutput'}]

    @staticmethod
    def can_be_grouped(tree) -> bool:
        # if there is one or more unselected nodes between nodes to be grouped
        # then current selection can't be grouped
        py_tree = Tree.from_bl_tree(tree)
        [setattr(py_tree.nodes[n.name], 'select', n.select) for n in tree.nodes]
        for node in py_tree.nodes.values():
            if not node.select:
                continue
            for neighbour_node in node.next_nodes:
                if neighbour_node.select:
                    continue
                for next_node in neighbour_node.bfs_walk():
                    if next_node.select:
                        return False
        return True


class UngroupGroupTree(bpy.types.Operator):
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
        for i, node in enumerate(group_nodes_filter):
            node.select = True
            node['ungroup order'] = i  # this will be copied within the nodes
        tree = context.space_data.path[-2].node_tree
        for node in tree.nodes:
            if 'ungroup order' in node:
                del node['ungroup order']

        # copy and past nodes into group tree
        bpy.ops.node.clipboard_copy()
        context.space_data.path.pop()
        bpy.ops.node.clipboard_paste()  # this will deselect all and select only pasted nodes

        # move nodes in group node center
        tree_select_nodes = [n for n in tree.nodes if n.select]
        center = reduce(lambda v1, v2: v1 + v2, [n.location for n in tree_select_nodes]) / len(tree_select_nodes)
        [setattr(n, 'location', n.location - (center - group_node.location)) for n in tree_select_nodes]

        # recreate py tree structure
        sub_py_tree = Tree.from_bl_tree(sub_tree)
        [setattr(sub_py_tree.nodes[n.name], 'type', n.bl_idname) for n in sub_tree.nodes]
        py_tree = Tree.from_bl_tree(tree)
        [setattr(py_tree.nodes[n.name], 'select', n.select) for n in tree.nodes]
        group_py_node = py_tree.nodes[group_node.name]
        sorted_sub_nodes = sorted([n for n in sub_tree.nodes if 'ungroup order' in n], 
                                  key=lambda n: n['ungroup order'])
        sorted_nodes = sorted([n for n in tree.nodes if 'ungroup order' in n], key=lambda n: n['ungroup order'])
        for sub_node, node in zip(sorted_sub_nodes, sorted_nodes):
            sub_py_tree.nodes[sub_node.name].twin = py_tree.nodes[node.name]
            py_tree.nodes[node.name].twin = sub_py_tree.nodes[sub_node.name]

        # create in links
        for group_input_py_node in [n for n in sub_py_tree.nodes.values() if n.type == 'NodeGroupInput']:
            for group_in_s, input_out_s in zip(group_py_node.inputs, group_input_py_node.outputs):
                if group_in_s.links and input_out_s.links:
                    link_out_s = group_in_s.linked_sockets[0]
                    for twin_in_s in input_out_s.linked_sockets:
                        link_in_s = twin_in_s.node.twin.inputs[twin_in_s.index]
                        tree.links.new(link_in_s.get_bl_socket(tree), link_out_s.get_bl_socket(tree))

        # create out links
        for group_output_py_node in [n for n in sub_py_tree.nodes.values() if n.type == 'NodeGroupOutput']:
            for group_out_s, output_in_s in zip(group_py_node.outputs, group_output_py_node.inputs):
                if group_out_s.links and output_in_s.links:
                    twin_out_s = output_in_s.linked_sockets[0]
                    for link_in_s in group_out_s.linked_sockets:
                        link_out_s = twin_out_s.node.twin.outputs[twin_out_s.index]
                        tree.links.new(link_in_s.get_bl_socket(tree), link_out_s.get_bl_socket(tree))

        # delete group node
        tree.nodes.remove(group_node)
        for node in tree.nodes:
            if 'ungroup order' in node:
                del node['ungroup order']

        return {'FINISHED'}


class EditGroupTree(bpy.types.Operator):
    bl_idname = 'node.edit_group_tree'
    bl_label = 'Edit group tree'

    def execute(self, context):
        context.space_data.path.append(context.node.node_tree, node=context.node)
        return {'FINISHED'}


class AddTreeDescription(bpy.types.Operator):
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


def register():
    [bpy.utils.register_class(cls) for cls in classes]
    bpy.types.NodeGroupOutput.process_node = lambda s, c: None  # this function is called during a socket value update


def unregister():
    del bpy.types.NodeGroupOutput.process_node
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]
