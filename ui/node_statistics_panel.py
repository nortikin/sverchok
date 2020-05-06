# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from typing import Union

import bpy

import sverchok.node_tree as nt


class NodeSettingsPanel(bpy.types.Panel):
    bl_idname = "SV_node_statistics_panel"
    bl_label = "Node statistics"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return isinstance(node, nt.SverchCustomTreeNode)

    def draw(self, context):
        node: Union[bpy.types.Node, nt.SverchCustomTreeNode] = context.active_node
        self.layout.label(text=f"Recalculations number: {node.updates_total}")
        self.layout.label(text=f"Last update: {node.last_update}")
        self.layout.label(text=f"Updating time: {node.update_time} ms")
        self.layout.label(text=f"Errors: {node.error or ''}")


def register():
    bpy.utils.register_class(NodeSettingsPanel)


def unregister():
    bpy.utils.unregister_class(NodeSettingsPanel)
