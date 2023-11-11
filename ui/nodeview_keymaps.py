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

import bpy

from sverchok.ui.development import displaying_sverchok_nodes
import sverchok.core.tasks as ts


class SvToggleProcess(bpy.types.Operator):
    bl_idname = "node.sv_toggle_process"
    bl_label = "Toggle processing of the current node tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        node_tree = context.space_data.node_tree
        node_tree.sv_process = not node_tree.sv_process
        if node_tree.sv_process:
            message = "Processing enabled for `%s'" % node_tree.name
        else:
            message = "Processing disabled for `%s'" % node_tree.name
        self.report({'INFO'}, message)
        self.redraw()
        return {'FINISHED'}

    @staticmethod
    def redraw():
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'NODE_EDITOR':
                    for region in area.regions:
                        if region.type in {'HEADER', 'UI', 'WINDOW'}:
                            region.tag_redraw()


class SvToggleDraft(bpy.types.Operator):
    bl_idname = "node.sv_toggle_draft"
    bl_label = "Toggle draft mode of the current node tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        node_tree = context.space_data.node_tree
        node_tree.sv_draft = not node_tree.sv_draft

        if node_tree.sv_draft:
            message = "Draft mode set for `%s'" % node_tree.name
        else:
            message = "Draft mode disabled for `%s'" % node_tree.name
        self.report({'INFO'}, message)
        self.redraw()
        return {'FINISHED'}

    @staticmethod
    def redraw():
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'NODE_EDITOR':
                    for region in area.regions:
                        if region.type in {'HEADER', 'UI', 'WINDOW'}:
                            region.tag_redraw()


class EnterExitGroupNodes(bpy.types.Operator):
    bl_idname = 'node.enter_exit_group_nodes'
    bl_label = "Enter exit from group nodes"

    def execute(self, context):
        node = context.active_node
        if node and hasattr(node, 'node_tree'):
            if bpy.app.version >= (3, 2):
                with context.temp_override(node=node):
                    bpy.ops.node.edit_group_tree()
            else:
                bpy.ops.node.edit_group_tree({'node': node})
        elif node and hasattr(node, 'gn_tree'):  # GN Viewer
            bpy.ops.node.sv_edit_gn_tree(
                tree_name=node.id_data.name, node_name=node.name)
        elif len(context.space_data.path) > 1:
            context.space_data.path.pop()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if getattr(context.space_data, 'tree_type', None) \
                in {'SverchCustomTreeType', 'SvGroupTree'}:
            return True
        else:
            return False


class PressingEscape(bpy.types.Operator):
    bl_idname = 'node.sv_abort_nodes_updating'
    bl_label = 'Abort nodes updating'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if ts.tasks:
            ts.tasks.cancel()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type in {'SverchCustomTreeType'}


nodeview_keymaps = []


def add_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        # ctrl+G        | make node group from selected
        kmi = km.keymap_items.new("node.add_group_tree_from_selected", 'G', 'PRESS', ctrl=True)
        nodeview_keymaps.append((km, kmi))

        # TAB           | enter or exit node groups depending on selection and edit_tree type
        kmi = km.keymap_items.new('node.enter_exit_group_nodes', 'TAB', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # Shift + A     | show custom menu
        kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
        kmi.properties.name = "NODEVIEW_MT_SvCategoryAllCategories"  # ui/nodeview_space_menu.py:add_node_menu
        nodeview_keymaps.append((km, kmi))

        # numbers 1 to 5 for partial menus
        kmi = km.keymap_items.new('node.call_partial_menu', 'ONE', 'PRESS')
        kmi.properties.menu_name = 'BasicDataPartialMenu'
        nodeview_keymaps.append((km, kmi))
        kmi = km.keymap_items.new('node.call_partial_menu', 'TWO', 'PRESS')
        kmi.properties.menu_name = "MeshPartialMenu"
        nodeview_keymaps.append((km, kmi))
        kmi = km.keymap_items.new('node.call_partial_menu', 'THREE', 'PRESS')
        kmi.properties.menu_name = "AdvancedObjectsPartialMenu"
        nodeview_keymaps.append((km, kmi))
        kmi = km.keymap_items.new('node.call_partial_menu', 'FOUR', 'PRESS')
        kmi.properties.menu_name = "ConnectionPartialMenu"
        nodeview_keymaps.append((km, kmi))
        kmi = km.keymap_items.new('node.call_partial_menu', 'FIVE', 'PRESS')
        kmi.properties.menu_name = "UiToolsPartialMenu"
        nodeview_keymaps.append((km, kmi))

        # Shift + S     | show custom menu
        kmi = km.keymap_items.new('wm.call_menu', 'S', 'PRESS', shift=True)
        kmi.properties.name = "NODEVIEW_MT_node_category_menu"
        nodeview_keymaps.append((km, kmi))

        # alt + Space  | enter extra search operator
        kmi = km.keymap_items.new('node.sv_extra_search', 'SPACE', 'PRESS', alt=True)
        nodeview_keymaps.append((km, kmi))

        # F5 | Trigger update of context node tree
        kmi = km.keymap_items.new('node.sverchok_update_context', 'F5', 'PRESS')
        kmi.properties.force_mode = False
        nodeview_keymaps.append((km, kmi))

        # Ctrl-F5 | Trigger update of context node tree
        kmi = km.keymap_items.new('node.sverchok_update_context', 'F5', 'PRESS', ctrl=True)
        kmi.properties.force_mode = True
        nodeview_keymaps.append((km, kmi))

        # F6 | Toggle processing mode of the active node tree
        kmi = km.keymap_items.new('node.sv_toggle_process', 'F6', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # F7 | Toggle draft mode for the active node tree
        kmi = km.keymap_items.new('node.sv_toggle_draft', 'F7', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # Esc | Aborting nodes updating
        kmi = km.keymap_items.new('node.sv_abort_nodes_updating', 'ESC', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # Right Click   | show custom menu
        kmi = km.keymap_items.new('wm.call_menu', 'RIGHTMOUSE', 'RELEASE')
        kmi.properties.name = "NODEVIEW_MT_sv_rclick_menu"
        nodeview_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu', 'P', 'PRESS', shift=True)
        kmi.properties.name = "SV_MT_LoadPresetMenu"
        nodeview_keymaps.append((km, kmi))

        # Ctrl + Left Click   | Connect Temporal Viewer
        kmi = km.keymap_items.new('node.sv_temporal_viewer', 'LEFTMOUSE', 'RELEASE', ctrl=True)
        kmi.properties.force_stethoscope = False
        kmi.properties.cut_links = False
        nodeview_keymaps.append((km, kmi))

        # Ctrl + Shift + Left Click   | Connect Temporal Viewer with cutting links first
        kmi = km.keymap_items.new('node.sv_temporal_viewer', 'LEFTMOUSE', 'RELEASE', ctrl=True, shift=True)
        kmi.properties.force_stethoscope = False
        kmi.properties.cut_links = True
        nodeview_keymaps.append((km, kmi))

        # Ctrl + Right Click   | Connect Temporal Viewer with accumulative links
        kmi = km.keymap_items.new('node.sv_temporal_viewer', 'RIGHTMOUSE', 'RELEASE', ctrl=True)
        kmi.properties.force_stethoscope = True
        kmi.properties.cut_links = False
        nodeview_keymaps.append((km, kmi))

        # V   | Link selected nodes
        kmi = km.keymap_items.new('node.sv_node_connector', 'V', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # Ctrl+Z  | Zoom to node and vice versa
        kmi = km.keymap_items.new('node.zoom_to_node', 'Z', 'PRESS', alt=True)
        nodeview_keymaps.append((km, kmi))

        # Ctrl+Shift+H  | Hide and show Viewer Draw node
        kmi = km.keymap_items.new('node.sv_node_vd_toggle', 'H', 'PRESS', shift=True, ctrl=True)
        nodeview_keymaps.append((km, kmi))

def remove_keymap():

    for km, kmi in nodeview_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception as e:
            err = repr(e)
            if "cannot be removed from 'Node Editor'" in err:
                print('keymaps for Node Editor already removed by another add-on, sverchok will skip this step in unregister')
                break

    nodeview_keymaps.clear()


classes = [SvToggleProcess, SvToggleDraft, EnterExitGroupNodes,
           PressingEscape]


def register():
    [bpy.utils.register_class(cls) for cls in classes]

    add_keymap()


def unregister():
    remove_keymap()

    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]
