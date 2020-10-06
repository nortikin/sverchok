# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import Tuple

import bpy


class SvGroupNode(bpy.types.NodeCustomGroup):
    """Node for keeping sub trees"""
    bl_idname = 'SvGroupNode'
    bl_label = 'Group node'


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
        tree = context.space_data.node_tree
        group_node = tree.nodes.new('SvGroupNode')
        group_node.location = context.space_data.cursor_location
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {'FINISHED'}

    @classmethod
    def can_be_added(cls, context) -> Tuple[bool, str]:
        tree = context.space_data.path[-1].node_tree
        if tree.bl_idname == 'SverchCustomTreeType':
            for node in tree.nodes:
                if node.bl_idname.startswith('SvGroupNodeMonad'):
                    return False, 'Either monad or group node should be used in the tree'
            return True, 'Add group node'
        elif tree.bl_idname == 'SverchGroupTreeType':
            return False, "Group node can't be used inside monad"
        else:
            return False, f"Can't add in '{tree.bl_idname}' type"


register, unregister = bpy.utils.register_classes_factory([SvGroupNode, AddGroupNode])
