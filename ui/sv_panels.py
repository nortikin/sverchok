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
from bpy.props import StringProperty, BoolProperty, FloatProperty


import sverchok
from sverchok.core.update_system import process_from_nodes, process_tree, build_update_list
from sverchok.utils import profile
from sverchok.utils.sv_update_utils import version_and_sha
from sverchok.ui.development import displaying_sverchok_nodes

objects_nodes_set = {'ObjectsNode', 'ObjectsNodeMK2', 'SvObjectsNodeMK3', 'SvExNurbsInNode', 'SvBezierInNode'}

def redraw_panels():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                for region in area.regions:
                    if region.type in {'HEADER', 'UI', 'WINDOW'}:
                        region.tag_redraw()

class SvToggleProcess(bpy.types.Operator):
    bl_idname = "node.sv_toggle_process"
    bl_label = "Toggle processing of the current node tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        layout = self.layout
        node_tree = context.space_data.node_tree
        node_tree.sv_process = not node_tree.sv_process
        if node_tree.sv_process:
            message = "Processing enabled for `%s'" % node_tree.name
        else:
            message = "Processing disabled for `%s'" % node_tree.name
        self.report({'INFO'}, message)
        redraw_panels()
        return {'FINISHED'}

class SvToggleDraft(bpy.types.Operator):
    bl_idname = "node.sv_toggle_draft"
    bl_label = "Toggle draft mode of the current node tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return displaying_sverchok_nodes(context)

    def execute(self, context):
        layout = self.layout
        node_tree = context.space_data.node_tree
        node_tree.sv_draft = not node_tree.sv_draft
        #node_tree.on_draft_mode_changed(context)

        if node_tree.sv_draft:
            message = "Draft mode set for `%s'" % node_tree.name
        else:
            message = "Draft mode disabled for `%s'" % node_tree.name
        self.report({'INFO'}, message)
        redraw_panels()
        return {'FINISHED'}

class SvRemoveStaleDrawCallbacks(bpy.types.Operator):
    """This will clear the opengl drawing if Sverchok didn't manage to correctly clear it on its own"""
    bl_idname = "node.remove_stale_draw_callbacks"
    bl_label = "Remove Stale drawing"

    def execute(self, context):
        
        from sverchok.core.handlers import sv_clean, sv_scene_handler
        scene = context.scene
        sv_clean(scene)
        sv_scene_handler(scene)
        return {'FINISHED'}


class Sv3DViewObjInUpdater(bpy.types.Operator, object):

    """Operator which runs its self from a timer"""
    bl_idname = "wm.sv_obj_modal_update"
    bl_label = "start n stop obj updating"

    _timer = None
    mode: StringProperty(default='toggle')
    node_name: StringProperty(default='')
    node_group: StringProperty(default='')
    speed: FloatProperty(default=1 / 13)

    def modal(self, context, event):

        if not context.scene.SvShowIn3D_active:
            self.cancel(context)
            return {'FINISHED'}

        if not (event.type == 'TIMER'):
            return {'PASS_THROUGH'}

        obj_nodes = []
        for ng in bpy.data.node_groups:
            if ng.bl_idname == 'SverchCustomTreeType':
                if ng.sv_process:
                    nodes = []
                    for n in ng.nodes:
                        if n.bl_idname in objects_nodes_set:
                            nodes.append(n)
                    if nodes:
                        obj_nodes.append(nodes)

        ''' reaches here only if event is TIMER and self.active '''
        for n in obj_nodes:
            # print('calling process on:', n.name, n.id_data)
            process_from_nodes(n)

        return {'PASS_THROUGH'}

    def start(self, context):
        context.scene.SvShowIn3D_active = True

        # rate can only be set in event_timer_add (I think...)
        # self.speed = 1 / context.node.updateRate

        wm = context.window_manager
        self._timer = wm.event_timer_add(self.speed, window=context.window)
        wm.modal_handler_add(self)
        self.report({'INFO'}, "Live Update mode enabled")

    def stop(self, context):
        context.scene.SvShowIn3D_active = False

    def toggle(self, context):
        if context.scene.SvShowIn3D_active:
            self.stop(context)
        else:
            self.start(context)

    def event_dispatcher(self, context, type_op):
        if type_op == 'start':
            self.start(context)
        elif type_op == 'end':
            self.stop(context)
        else:
            self.toggle(context)

    def execute(self, context):
        # n  = context.node
        # self.node_name = context.node.name
        # self.node_group = context.node.id_data.name

        self.event_dispatcher(context, self.mode)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.report({'INFO'}, "Live Update mode disabled")


class SverchokPanels:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


class SV_PT_ToolsMenu(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ToolsMenu"
    bl_label = f"Tree properties ({version_and_sha})"
    use_pin = True

    def draw(self, context):
        col = self.layout.column()
        col.operator("node.sverchok_update_all", text="Update all")
        col.template_list("SV_UL_TreePropertyList", "", bpy.data, 'node_groups',
                          bpy.context.scene.sverchok_panel_properties, "selected_tree")


class SV_PT_ActiveTreePanel(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ActiveTreePanel"
    bl_label = "Active tree"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SV_PT_ToolsMenu'

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.node_tree)

    def draw(self, context):
        ng = context.space_data.node_tree
        col = self.layout.column()

        col.operator("node.sverchok_update_current", text=f'Update "{ng.name}"').node_group = ng.name
        col.operator('node.remove_stale_draw_callbacks')

        col.use_property_split = True
        col.prop(ng, "sv_show_error_in_tree")
        col.prop(ng, "sv_subtree_evaluation_order", text="Eval order")


class SV_PT_ProfilingPanel(SverchokPanels, bpy.types.Panel):
    bl_idname = "SV_PT_ProfilingPanel"
    bl_label = "Tree profiling"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SV_PT_ToolsMenu'

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

    def draw(self, context):
        col = self.layout.column()
        col.operator('node.sv_show_latest_commits')

        if context.scene.sv_new_version:
            col_alert = self.layout.column()
            col_alert.alert = True
            col_alert.operator("node.sverchok_update_addon", text='Upgrade Sverchok addon')
        else:
            col.operator("node.sverchok_check_for_upgrades_wsha", text='Check for updates')


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
        row.prop(tree, "sv_process", toggle=True, text="P")
        row.prop(tree, "sv_draft", toggle=True, text="D")
        row.prop(tree, 'use_fake_user', toggle=True, text='F')

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


class SverchokPanelProperties(bpy.types.PropertyGroup):
    selected_tree: bpy.props.IntProperty()  # index for UIList


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

def view3d_show_live_mode(self, context):
    if context.scene.SvShowIn3D_active:
        layout = self.layout
        OP = 'wm.sv_obj_modal_update'
        layout.operator(OP, text='Stop Live Update', icon='CANCEL').mode = 'end'
        
sv_tools_classes = [
    Sv3DViewObjInUpdater,
    SV_PT_ToolsMenu,
    SvRemoveStaleDrawCallbacks,
    SvToggleProcess,
    SvToggleDraft,
    SV_PT_ActiveTreePanel,
    SV_PT_ProfilingPanel,
    SV_PT_SverchokUtilsPanel,
    SV_UL_TreePropertyList,
    SverchokPanelProperties
]


def register():
    bpy.types.Scene.SvShowIn3D_active = BoolProperty(
        name='update from 3dview',
        default=False,
        description='Allows updates directly to object-in nodes from 3d panel')

    for class_name in sv_tools_classes:
        bpy.utils.register_class(class_name)

    bpy.types.Scene.sverchok_panel_properties = bpy.props.PointerProperty(type=SverchokPanelProperties)

    bpy.types.NODE_HT_header.append(node_show_tree_mode)
    bpy.types.VIEW3D_HT_header.append(view3d_show_live_mode)

def unregister():
    del bpy.types.Scene.sverchok_panel_properties

    for class_name in reversed(sv_tools_classes):
        bpy.utils.unregister_class(class_name)

    del bpy.types.Scene.SvShowIn3D_active
    bpy.types.NODE_HT_header.remove(node_show_tree_mode)
    bpy.types.VIEW3D_HT_header.remove(view3d_show_live_mode)

