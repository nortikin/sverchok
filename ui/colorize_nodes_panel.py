# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from typing import Union

import bpy

import sverchok.node_tree as nt


class NodeColorizePanel(bpy.types.Panel):
    bl_idname = "SV_PT_node_colorize_panel"
    bl_label = "Colorize nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        active_tree = context.space_data.edit_tree
        self.layout.prop(active_tree, 'use_colorizing_algorithm')
        self.layout.prop(active_tree, 'colorizing_method', text="Method")
        if active_tree.colorizing_method == 'Slow nodes':
            self.layout.prop(active_tree, 'update_time', slider=True)
            self.layout.prop(active_tree, 'colorizing_color', text="Node")
        elif active_tree.colorizing_method == 'Last updated nodes':
            self.layout.prop(active_tree, 'last_updated_color', text="Node")

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.edit_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False


def register():
    bpy.utils.register_class(NodeColorizePanel)


def unregister():
    bpy.utils.unregister_class(NodeColorizePanel)
