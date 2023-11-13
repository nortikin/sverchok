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

import sverchok
from sverchok.utils import profile
from sverchok.ui.development import displaying_sverchok_nodes
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.handle_blender_data import BlTrees
from sverchok.utils.sv_update_utils import SvPrintCommits, SverchokUpdateAddon, SverchokCheckForUpgradesSHA


class SverchokPanels:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


class SV_PT_ToolsMenu(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ToolsMenu"
    bl_label = f"Tree properties"
    bl_options = {'DEFAULT_CLOSED'}
    use_pin = True

    def draw(self, context):
        col = self.layout.column()
        col.operator("node.sverchok_update_all", text="Update all")
        col.template_list("SV_UL_TreePropertyList", "", bpy.data, 'node_groups',
                          bpy.context.scene, "ui_list_selected_tree")


class SV_PT_ActiveTreePanel(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ActiveTreePanel"
    bl_label = "Active tree"

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.node_tree) if super().poll(context) else False

    def draw(self, context):
        ng = context.space_data.node_tree
        col = self.layout.column()

        col.operator('node.sverchok_update_current', text=f'Re-update all nodes').node_group = ng.name
        col.operator('node.sverchok_bake_all', text="Bake Viewer Draw nodes").node_tree_name = ng.name

        col.use_property_split = True
        col.prop(ng, 'sv_show', text="Viewers", icon=f"RESTRICT_VIEW_{'OFF' if ng.sv_show else 'ON'}")
        col.prop(ng, 'sv_animate', text="Animation", icon='ANIM')
        col.prop(ng, 'sv_scene_update', text="Scene", icon='SCENE_DATA')
        col.prop(ng, 'sv_process', text="Live update", toggle=True)
        col.prop(ng, "sv_draft", text="Draft mode", toggle=True)


class SV_PT_TreeTimingsPanel(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_TreeTimingsPanel"
    bl_label = "Node timings"
    bl_parent_id = 'SV_PT_ActiveTreePanel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        tree = context.space_data.node_tree
        row = self.layout.row()
        row.prop(tree, 'sv_show_time_nodes', text='')

    def draw(self, context):
        tree = context.space_data.node_tree
        row = self.layout.row()
        row.use_property_split = True
        row.prop(tree, 'show_time_mode', text="Update time", expand=True)


class SV_PT_ExtrTreeUserInterfaceOptions(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ExtrTreeUserInterfaceOptions"
    bl_label = "Tree UI options"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.node_tree) if super().poll(context) else False

    def draw(self, context):
        ng = context.space_data.node_tree
        col = self.layout.column(heading="Show")
        col.use_property_split = True
        col.prop(ng, 'sv_show_socket_menus', text="Socket menu")

        sv_settings = bpy.context.preferences.addons[sverchok.__name__].preferences
        col.prop(sv_settings, 'over_sized_buttons', text="Big buttons")
        col.prop(sv_settings, 'show_icons', text="Menu icons")
        col.prop(sv_settings, 'show_input_menus', text="Quick link")


class SV_PT_ProfilingPanel(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ProfilingPanel"
    bl_label = "Tree profiling"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 9

    @classmethod
    def poll(cls, context):
        with sv_preferences() as prefs:
            return super().poll(context) and prefs.developer_mode

    def draw_header(self, context):
        addon = context.preferences.addons.get(sverchok.__name__)
        row = self.layout.row()
        row.ui_units_x = 3
        row.prop(addon.preferences, 'profile_mode', text='')

    def draw(self, context):
        addon = context.preferences.addons.get(sverchok.__name__)
        col = self.layout.column()

        col_start_profiling = col.column()
        col_start_profiling.active = addon.preferences.profile_mode != "NONE"
        if profile.is_currently_enabled:
            col_start_profiling.operator("node.sverchok_profile_toggle", text="Stop profiling", icon="CANCEL")
        else:
            col_start_profiling.operator("node.sverchok_profile_toggle", text="Start profiling", icon="TIME")

        col_save = col.column()
        col_save.active = profile.have_gathered_stats()
        col_save.operator("node.sverchok_profile_dump", text="Dump data", icon="TEXT")
        col_save.operator("node.sverchok_profile_save", text="Save data", icon="FILE_TICK")
        col_save.operator("node.sverchok_profile_reset", text="Reset data", icon="X")


class SV_PT_SverchokUtilsPanel(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_SverchokUtilsPanel"
    bl_label = "General Utils"
    bl_order = 10
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout.column()
        col.operator(SvPrintCommits.bl_idname)
        with sv_preferences() as prefs:
            if prefs.developer_mode:
                col.operator("node.sv_run_pydoc")
            if prefs.available_new_version:
                col_alert = self.layout.column()
                col_alert.alert = True
                col_alert.operator(SverchokUpdateAddon.bl_idname, text='Upgrade Sverchok addon')
            else:
                col.operator(SverchokCheckForUpgradesSHA.bl_idname, text='Check for upgrades')


class SV_UL_TreePropertyList(bpy.types.UIList):
    """Show in node tree editor"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        tree = item

        row = layout.row(align=True)
        # tree name
        if context.space_data.node_tree and context.space_data.node_tree.name == tree.name:
            row.label(text=tree.name)
        else:
            row.operator('node.sv_switch_layout', text=tree.name).layout_name = tree.name

        # buttons
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.ui_units_x = 5.5
        row.operator('node.sverchok_bake_all', text='B').node_tree_name = tree.name
        row.prop(tree, 'sv_show', icon= f"RESTRICT_VIEW_{'OFF' if tree.sv_show else 'ON'}", text=' ')
        row.prop(tree, 'sv_animate', icon='ANIM', text=' ')
        row.prop(tree, 'sv_scene_update', icon='SCENE_DATA', text=' ')
        row.prop(tree, "sv_process", toggle=True, text="L")
        row.prop(tree, "sv_draft", toggle=True, text="D")

    def filter_items(self, context, data, prop_name):
        trees = getattr(data, prop_name)
        filter_name = self.filter_name
        filter_invert = self.use_filter_invert

        filter_tree_types = [tree.bl_idname == 'SverchCustomTreeType' for tree in trees]

        filter_tree_names = [filter_name.lower() in tree.name.lower() for tree in trees]
        filter_tree_names = [not f for f in filter_tree_names] if filter_invert else filter_tree_names

        combine_filter = [f1 and f2 for f1, f2 in zip(filter_tree_types, filter_tree_names)]
        # next code is needed for hiding wrong tree types
        combine_filter = [not f for f in combine_filter] if filter_invert else combine_filter
        combine_filter = [self.bitflag_filter_item if f else 0 for f in combine_filter]
        return combine_filter, []


class SverchokUpdateAll(bpy.types.Operator):
    """Update all Sverchok node trees"""
    bl_idname = "node.sverchok_update_all"
    bl_label = "Update all node trees"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            bpy.context.window.cursor_set("WAIT")
            for tree in BlTrees().sv_main_trees:
                tree.force_update()
        finally:
            bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}


class SverchokBakeAll(bpy.types.Operator):
    """Bake all nodes on this layout"""
    bl_idname = "node.sverchok_bake_all"
    bl_label = "Sverchok bake all"
    bl_options = {'REGISTER', 'UNDO'}

    node_tree_name: bpy.props.StringProperty(name='tree_name', default='')

    @classmethod
    def poll(cls, context):
        if bpy.data.node_groups.__len__():
            return True

    def execute(self, context):
        ng = bpy.data.node_groups[self.node_tree_name]

        for node in ng.nodes:
            if hasattr(node, 'bake'):
                if getattr(node, 'activate', getattr(node, 'show_objects', False)):
                    node.bake()

        return {'FINISHED'}


class SverchokUpdateCurrent(bpy.types.Operator):
    """Update current Sverchok node tree"""
    bl_idname = "node.sverchok_update_current"
    bl_label = "Update current node tree"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    node_group: bpy.props.StringProperty(default="")

    def execute(self, context):
        try:
            bpy.context.window.cursor_set("WAIT")
            bpy.data.node_groups.get(self.node_group).force_update()
        finally:
            bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

class SverchokUpdateContext(bpy.types.Operator):
    """Update current Sverchok node tree"""
    bl_idname = "node.sverchok_update_context"
    bl_label = "Update current node tree"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    force_mode: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        node_tree = context.space_data.node_tree
        if node_tree:
            if self.force_mode or node_tree.sv_process:
                try:
                    bpy.context.window.cursor_set("WAIT")
                    node_tree.force_update()
                finally:
                    bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

class SvSwitchToLayout(bpy.types.Operator):
    """Switch to exact layout, user friendly way"""
    bl_idname = "node.sv_switch_layout"
    bl_label = "switch layouts"
    bl_options = {'REGISTER', 'UNDO'}

    layout_name: bpy.props.StringProperty(
        default='', name='layout_name',
        description='layout name to change layout by button')

    @classmethod
    def poll(cls, context):
        if context.space_data.type == 'NODE_EDITOR':
            if bpy.context.space_data.tree_type == 'SverchCustomTreeType':
                return True
        else:
            return False

    def execute(self, context):
        ng = bpy.data.node_groups.get(self.layout_name)
        if ng:
            context.space_data.path.start(ng)
        else:
            return {'CANCELLED'}
        return {'FINISHED'}


def node_show_tree_mode(self, context):
    if not displaying_sverchok_nodes(context):
        return
    layout = self.layout
    node_tree = context.space_data.node_tree
    if hasattr(node_tree, 'sv_draft') and hasattr(node_tree, 'sv_process'):
        if not node_tree.sv_process:
            message = "Disabled"
            icon = 'X'
        elif node_tree.sv_draft:
            message = "DRAFT"
            icon = 'CHECKBOX_DEHLT'
        else:
            message = "Processing"
            icon = 'CHECKMARK'
        layout.label(text=message, icon=icon)


sv_tools_classes = [
    SV_PT_ToolsMenu,
    SV_PT_ActiveTreePanel,
    SV_PT_TreeTimingsPanel,
    SV_PT_ExtrTreeUserInterfaceOptions,
    SV_PT_ProfilingPanel,
    SV_PT_SverchokUtilsPanel,
    SV_UL_TreePropertyList,
    SverchokUpdateAll,
    SverchokBakeAll,
    SverchokUpdateCurrent,
    SverchokUpdateContext,
    SvSwitchToLayout
]


def register():
    for class_name in sv_tools_classes:
        bpy.utils.register_class(class_name)

    bpy.types.Scene.ui_list_selected_tree = bpy.props.IntProperty()  # Pointer to selected item in list of trees

    bpy.types.NODE_HT_header.append(node_show_tree_mode)


def unregister():
    del bpy.types.Scene.ui_list_selected_tree

    bpy.types.NODE_HT_header.remove(node_show_tree_mode)

    for class_name in reversed(sv_tools_classes):
        bpy.utils.unregister_class(class_name)
