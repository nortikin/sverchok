# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# from __future__ import annotations <- Don't use it here, `group node` will loose its `group tree` attribute

from typing import Tuple, List

import bpy


class SvGroupTree(bpy.types.NodeTree):
    bl_idname = 'SvGroupTree'
    bl_icon = 'NODETREE'
    bl_label = 'Group tree'

    @classmethod
    def poll(cls, context):
        return False  # only for inner usage

    sv_show: bpy.props.BoolProperty(name="Show", default=True, description='Show group tree')
    sv_draft: bpy.props.BoolProperty(name="Draft",  description="Simplified processing mode")

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


class SvGroupTreeNode(bpy.types.NodeCustomGroup):
    """Node for keeping sub trees"""
    bl_idname = 'SvGroupTreeNode'
    bl_label = 'Group node (mockup)'

    def nested_tree_filter(self, context):
        """Define which tree we would like to use as nested trees."""
        tested_tree = context
        if tested_tree.bl_idname == 'SvGroupTree':  # It should be our dedicated to this class
            # trying to avoid creating loops of group trees to each other
            # upstream trees of tested treed should nad share trees
            # with downstream trees of current tree
            tested_tree_upstream_trees = {t.name for t in tested_tree.upstream_trees()}
            current_tree_downstream_trees = {p.node_tree.name for p in bpy.context.space_data.path}
            shared_trees = tested_tree_upstream_trees & current_tree_downstream_trees
            return not shared_trees
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
            row = layout.row(align=True)
            row.scale_x = 5
            row.alignment = 'RIGHT'
            row.prop(self.node_tree, 'sv_show', text="",
                     icon=f'RESTRICT_VIEW_{"OFF" if self.node_tree.sv_show else "ON"}')
            row.prop(self.node_tree, 'sv_draft', text="", icon='EVENT_D')
            row.prop(self.node_tree, 'use_fake_user', text="")

        row = layout.row(align=True)
        row.prop_search(self, 'group_tree', bpy.data, 'node_groups', text='')
        if self.group_tree:
            row.operator('node.edit_group_tree', text='', icon='FILE_PARENT')
        else:
            row.operator('node.add_group_tree', text='', icon='ADD')

    def process_node(self, context):
        # update properties of socket of the node trigger this method
        pass


class AddGroupNode(bpy.types.Operator):
    bl_idname = "node.add_group_node"
    bl_label = "Add group node"

    @classmethod
    def poll(cls, context):
        return cls.can_be_added(context)[0]

    @classmethod
    def description(cls, context, properties):
        return cls.can_be_added(context)[1]

    def execute(self, context):
        tree = context.space_data.path[-1].node_tree
        bpy.ops.node.select_all(action='DESELECT')
        group_node = tree.nodes.new('SvGroupTreeNode')
        group_node.location = context.space_data.cursor_location
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {'FINISHED'}

    @classmethod
    def can_be_added(cls, context) -> Tuple[bool, str]:
        tree = context.space_data.path[-1].node_tree
        if tree.bl_idname == 'SverchCustomTreeType':
            for node in tree.nodes:
                if node.bl_idname.startswith('SvGroupTreeNodeMonad'):
                    return False, 'Either monad or group node should be used in the tree'
            return True, 'Add group node'
        elif tree.bl_idname == 'SvGroupTree':
            return True, "Add group node"
        else:
            return False, f"Can't add in '{tree.bl_idname}' type"


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


class EditGroupTree(bpy.types.Operator):
    bl_idname = 'node.edit_group_tree'
    bl_label = 'Edit group tree'

    def execute(self, context):
        context.space_data.path.append(context.node.node_tree, node=context.node)
        return {'FINISHED'}


classes = [SvGroupTree, SvGroupTreeNode, AddGroupNode, AddGroupTree, EditGroupTree]


def register():
    [bpy.utils.register_class(cls) for cls in classes]
    bpy.types.NodeGroupOutput.process_node = lambda s, c: None  # this function is called during a socket value update


def unregister():
    del bpy.types.NodeGroupOutput.process_node
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]
