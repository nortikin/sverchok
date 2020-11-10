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
from sverchok.core.update_system import process_tree, build_update_list


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


class SverchokUpdateContext(bpy.types.Operator):
    """Update current Sverchok node tree"""
    bl_idname = "node.sverchok_update_context"
    bl_label = "Update current node tree"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        try:
            bpy.context.window.cursor_set("WAIT")
            ng = context.space_data.node_tree
            if ng:
                build_update_list(ng)
                process_tree(ng)
        except:
            pass
        finally:
            bpy.context.window.cursor_set("DEFAULT")

        return {'FINISHED'}


class SverchokUpdateContextForced(bpy.types.Operator):
    """Update current Sverchok node tree (even if it's processing is disabled)"""
    bl_idname = "node.sverchok_update_context_force"
    bl_label = "Update current node tree - forced mode"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        try:
            bpy.context.window.cursor_set("WAIT")
            ng = context.space_data.node_tree
            if ng:
                try:
                    prev_process_state = ng.sv_process
                    ng.sv_process = True
                    build_update_list(ng)
                    process_tree(ng)
                finally:
                    ng.sv_process = prev_process_state
        except:
            pass
        finally:
            bpy.context.window.cursor_set("DEFAULT")

        return {'FINISHED'}


class EnterExitGroupNodes(bpy.types.Operator):
    bl_idname = 'node.enter_exit_group_nodes'
    bl_label = "Enter exit from group nodes"

    def execute(self, context):
        node = context.active_node
        if node and hasattr(node, 'monad'):
            bpy.ops.node.sv_monad_enter()
        elif node and hasattr(node, 'node_tree'):
            bpy.ops.node.edit_group_tree({'node': node})
        elif len(context.space_data.path) > 1:
            context.space_data.path.pop()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if context.space_data.tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType', 'SvGroupTree'}:
            return True
        else:
            return False


nodeview_keymaps = []


def add_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        make_monad = 'node.sv_monad_from_selected'

        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        # ctrl+G        | make group from selected with periphery links
        kmi = km.keymap_items.new(make_monad, 'G', 'PRESS', ctrl=True)
        nodeview_keymaps.append((km, kmi))

        # ctrl+shift+G  | make group from selected without periphery links
        kmi = km.keymap_items.new(make_monad, 'G', 'PRESS', ctrl=True, shift=True)
        kmi.properties.use_relinking = False
        nodeview_keymaps.append((km, kmi))

        # TAB           | enter or exit monad depending on selection and edit_tree type
        kmi = km.keymap_items.new('node.enter_exit_group_nodes', 'TAB', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # alt + G       | expand current monad into original state
        kmi = km.keymap_items.new('node.sv_monad_expand', 'G', 'PRESS', alt=True)
        nodeview_keymaps.append((km, kmi))

        # Shift + A     | show custom menu
        kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
        kmi.properties.name = "NODEVIEW_MT_Dynamic_Menu"
        nodeview_keymaps.append((km, kmi))

        # Shift + S     | show custom menu
        kmi = km.keymap_items.new('wm.call_menu', 'S', 'PRESS', shift=True)
        kmi.properties.name = "NODEVIEW_MT_Solids_Special_Menu"
        nodeview_keymaps.append((km, kmi))

        # alt + Space  | enter extra search operator
        kmi = km.keymap_items.new('node.sv_extra_search', 'SPACE', 'PRESS', alt=True)
        nodeview_keymaps.append((km, kmi))

        # F5 | Trigger update of context node tree
        kmi = km.keymap_items.new('node.sverchok_update_context', 'F5', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # Ctrl + F5 | Trigger update of context node tree, forced mode
        kmi = km.keymap_items.new('node.sverchok_update_context_force', 'F5', 'PRESS', ctrl=True)
        nodeview_keymaps.append((km, kmi))

        # F6 | Toggle processing mode of the active node tree
        kmi = km.keymap_items.new('node.sv_toggle_process', 'F6', 'PRESS')
        nodeview_keymaps.append((km, kmi))

        # F7 | Toggle draft mode for the active node tree
        kmi = km.keymap_items.new('node.sv_toggle_draft', 'F7', 'PRESS')
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

        # 3D View
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.sv_obj_modal_update', 'F5', 'PRESS', ctrl=True, shift=True)
        kmi.properties.mode='toggle'
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


classes = [SvToggleProcess, SvToggleDraft, SverchokUpdateContext, SverchokUpdateContextForced, EnterExitGroupNodes]


def register():
    [bpy.utils.register_class(cls) for cls in classes]

    add_keymap()


def unregister():
    remove_keymap()

    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]
