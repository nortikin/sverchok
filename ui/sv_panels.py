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
from sverchok.core.update_system import process_from_nodes
from sverchok.utils import profile
from sverchok.utils.sv_update_utils import version_and_sha
from sverchok.ui.development import displaying_sverchok_nodes

objects_nodes_set = {'ObjectsNode', 'ObjectsNodeMK2', 'SvObjectsNodeMK3'}

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
        if node_tree.sv_draft:
            message = "Draft mode set for `%s'" % node_tree.name
        else:
            message = "Draft mode disabled for `%s'" % node_tree.name
        self.report({'INFO'}, message)
        redraw_panels()
        return {'FINISHED'}

class SvRemoveStaleDrawCallbacks(bpy.types.Operator):

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
    mode: StringProperty(default='')
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

    def event_dispatcher(self, context, type_op):
        if type_op == 'start':
            context.scene.SvShowIn3D_active = True

            # rate can only be set in event_timer_add (I think...)
            # self.speed = 1 / context.node.updateRate

            wm = context.window_manager
            self._timer = wm.event_timer_add(self.speed, window=context.window)
            wm.modal_handler_add(self)

        if type_op == 'end':
            context.scene.SvShowIn3D_active = False

    def execute(self, context):
        # n  = context.node
        # self.node_name = context.node.name
        # self.node_group = context.node.id_data.name

        self.event_dispatcher(context, self.mode)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class SV_PT_3DPanel(bpy.types.Panel):
    ''' Panel to manipuplate parameters in Sverchok layouts '''

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_label = "Sverchok " + version_and_sha
    bl_options = {'DEFAULT_CLOSED'}
    # bl_category = 'Sverchok'

    def draw(self, context):
        layout = self.layout
        little_width = 0.32

        addon = context.preferences.addons.get(sverchok.__name__)
        if addon.preferences.enable_live_objin:

            # Live Update Modal trigger.
            row = layout.row()
            OP = 'wm.sv_obj_modal_update'
            if context.scene.SvShowIn3D_active:
                row.operator(OP, text='Stop live update', icon='CANCEL').mode = 'end'
            else:
                row.operator(OP, text='Start live update', icon='EDITMODE_HLT').mode = 'start'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 2.0
        row.operator('node.sv_scan_propertyes', text='Scan for props')
        row.operator("node.sverchok_update_all", text="Update all")
        row = col.row(align=True)
        row.prop(context.scene, 'sv_do_clear', text='hard clean', toggle=True)
        delley = row.operator(
            'node.sv_delete_nodelayouts',
            text='Clean layouts').do_clear = context.scene.sv_do_clear

        for tree in bpy.data.node_groups:
            if tree.bl_idname == 'SverchCustomTreeType':
                box = layout.box()
                col = box.column(align=True)
                row = col.row(align=True)

                split = row.column(align=True)
                split.scale_x = little_width
                icoco = 'DOWNARROW_HLT' if tree.SvShowIn3D else 'RIGHTARROW'
                split.prop(tree, 'SvShowIn3D', icon=icoco, emboss=False, text=' ')

                split = row.column(align=True)
                split.label(text=tree.name)

                # bakery
                split = row.column(align=True)
                split.scale_x = little_width
                baka = split.operator('node.sverchok_bake_all', text='B')
                baka.node_tree_name = tree.name

                # eye
                split = row.column(align=True)
                split.scale_x = little_width
                if tree.sv_show:
                    split.prop(tree, 'sv_show', icon='RESTRICT_VIEW_OFF', text=' ')
                else:
                    split.prop(tree, 'sv_show', icon='RESTRICT_VIEW_ON', text=' ')
                split = row.column(align=True)
                split.scale_x = little_width
                # if tree.sv_animate:
                split.prop(tree, 'sv_animate', icon='ANIM', text=' ')
                # else:
                #    split.prop(tree, 'sv_animate', icon='LOCKED', text=' ')

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, "sv_process", toggle=True, text="P")

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, "sv_draft", toggle=True, text="D")

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, 'use_fake_user', toggle=True, text='F')

                # variables
                if tree.SvShowIn3D:
                   
                    for item in tree.Sv3DProps:
                        no = item.node_name

                        # properties are not automatically removed from Sv3DProps when a node is deleted.
                        # temporary fix for ui.
                        node = tree.nodes.get(no, None)
                        if not node:
                            row = col.row()
                            row.alert = True
                            row.label(icon='ERROR', text=f'missing node: "{no}"')
                            op = row.operator('node.sv_remove_3dviewpropitem', icon='CANCEL', text='')
                            op.tree_name =  tree.name
                            op.node_name = no
                            continue

                        node.draw_buttons_3dpanel(col)


class SV_PT_ToolsMenu(bpy.types.Panel):
    bl_idname = "SV_PT_ToolsMenu"
    bl_label = "SV " + version_and_sha
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.edit_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False

    def draw_profiling_info_if_needed(self, layout, addon):
        if addon.preferences.profile_mode != "NONE":
            profile_col = layout.column(align=True)

            if profile.is_currently_enabled:
                profile_col.operator("node.sverchok_profile_toggle", text="Stop profiling", icon="CANCEL")
            else:
                profile_col.operator("node.sverchok_profile_toggle", text="Start profiling", icon="TIME")

            if profile.have_gathered_stats():
                row = profile_col.row(align=True)
                row.operator("node.sverchok_profile_dump", text="Dump data", icon="TEXT")
                row.operator("node.sverchok_profile_save", text="Save data", icon="FILE_TICK")
                profile_col.operator("node.sverchok_profile_reset", text="Reset data", icon="X")

    def draw_interaction_template(self, layout):
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Layout')

        col0 = row.column(align=True)
        col0.scale_x = little_width
        col0.label(text='B')

        col1 = row.column(align=True)
        col1.scale_x = little_width
        col1.label(icon='RESTRICT_VIEW_OFF', text=' ')

        col2 = row.column(align=True)
        col2.scale_x = little_width
        col2.label(icon='ANIM', text=' ')

        col3 = row.column(align=True)
        col3.scale_x = little_width
        col3.label(text='P')

        col4 = row.column(align=True)
        col4.scale_x = little_width
        col4.label(text='D')

        col5 = row.column(align=True)
        col5.scale_x = little_width
        col5.label(text='F')


    def draw(self, context):

        ng_name = context.space_data.node_tree.name
        layout = self.layout
        layout.active = True

        little_width = 0.32

        addon = context.preferences.addons.get(sverchok.__name__)

        self.draw_profiling_info_if_needed(layout, addon)

        row = layout.row(align=True)
        col = row.column(align=True)
        col.scale_y = 3.0
        col.scale_x = 0.5

        # two oversized buttons

        col.operator("node.sverchok_update_all", text="Update all")
        col = row.column(align=True)
        col.scale_y = 3.0

        op = col.operator("node.sverchok_update_current", text="Update {0}".format(ng_name))
        op.node_group = ng_name

        # end two oversized buttons
        
        box = layout.box()

        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Layout')

        col0 = row.column(align=True)
        col0.scale_x = little_width
        col0.label(text='B')

        col1 = row.column(align=True)
        col1.scale_x = little_width
        col1.label(icon='RESTRICT_VIEW_OFF', text=' ')

        col2 = row.column(align=True)
        col2.scale_x = little_width
        col2.label(icon='ANIM', text=' ')

        col3 = row.column(align=True)
        col3.scale_x = little_width
        col3.label(text='P')

        col4 = row.column(align=True)
        col4.scale_x = little_width
        col4.label(text='D')

        col5 = row.column(align=True)
        col5.scale_x = little_width
        col5.label(text='F')

        for name, tree in bpy.data.node_groups.items():
            if tree.bl_idname == 'SverchCustomTreeType':

                row = col.row(align=True)
                # tree name
                if name == ng_name:
                    row.label(text=name)
                else:
                    row.operator('node.sv_switch_layout', text=name).layout_name = name

                # bakery
                split = row.column(align=True)
                split.scale_x = little_width
                baka = split.operator('node.sverchok_bake_all', text='B')
                baka.node_tree_name = name

                # eye
                split = row.column(align=True)
                split.scale_x = little_width
                view_icon = 'RESTRICT_VIEW_' + ('OFF' if tree.sv_show else 'ON')
                split.prop(tree, 'sv_show', icon=view_icon, text=' ')

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, 'sv_animate', icon='ANIM', text=' ')

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, "sv_process", toggle=True, text="P")

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, "sv_draft", toggle=True, text="D")

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, 'use_fake_user', toggle=True, text='F')

        if context.scene.sv_new_version:
            row = layout.row()
            row.alert = True
            row.operator(
                "node.sverchok_update_addon", text='Upgrade Sverchok addon')
        else:
            sha_update = "node.sverchok_check_for_upgrades_wsha"
            layout.row().operator(sha_update, text='Check for updates')

        layout.row().operator('node.sv_show_latest_commits')
        layout.separator()
        layout.row().operator('node.remove_stale_draw_callbacks')

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
    Sv3DViewObjInUpdater,
    SV_PT_ToolsMenu,
    SV_PT_3DPanel,
    SvRemoveStaleDrawCallbacks,
    SvToggleProcess,
    SvToggleDraft
]


def register():
    bpy.types.NodeTree.SvShowIn3D = BoolProperty(
        name='show in panel',
        default=True,
        description='Show properties in 3d panel or not')

    bpy.types.Scene.SvShowIn3D_active = BoolProperty(
        name='update from 3dview',
        default=False,
        description='Allows updates directly to object-in nodes from 3d panel')

    for class_name in sv_tools_classes:
        bpy.utils.register_class(class_name)

    bpy.types.NODE_HT_header.append(node_show_tree_mode)

def unregister():
    for class_name in reversed(sv_tools_classes):
        bpy.utils.unregister_class(class_name)

    del bpy.types.NodeTree.SvShowIn3D
    del bpy.types.Scene.SvShowIn3D_active
    bpy.types.NODE_HT_header.remove(node_show_tree_mode)

