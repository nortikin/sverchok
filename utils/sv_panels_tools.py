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

import webbrowser

import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty

from sverchok.core.update_system import process_tree, build_update_list
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.logging import debug, info
from sverchok.ui.development import displaying_sverchok_nodes
import sverchok


class SverchokUpdateAll(bpy.types.Operator):
    """Update all Sverchok node trees"""
    bl_idname = "node.sverchok_update_all"
    bl_label = "Update all node trees"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            bpy.context.window.cursor_set("WAIT")
            sv_ngs = filter(lambda ng:ng.bl_idname == 'SverchCustomTreeType', bpy.data.node_groups)
            for ng in sv_ngs:
                ng.unfreeze(hard=True)
            build_update_list()
            process_tree()
        finally:
            bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

class SverchokBakeAll(bpy.types.Operator):
    """Bake all nodes on this layout"""
    bl_idname = "node.sverchok_bake_all"
    bl_label = "Sverchok bake all"
    bl_options = {'REGISTER', 'UNDO'}

    node_tree_name: StringProperty(name='tree_name', default='')

    @classmethod
    def poll(cls, context):
        if bpy.data.node_groups.__len__():
            return True

    def execute(self, context):
        ng = bpy.data.node_groups[self.node_tree_name]
        
        nodes = filter(lambda n: n.bl_idname == 'SvVDExperimental', ng.nodes)
        for node in nodes:
            if node.activate:
                node.bake() 

        return {'FINISHED'}


class SverchokUpdateCurrent(bpy.types.Operator):
    """Update current Sverchok node tree"""
    bl_idname = "node.sverchok_update_current"
    bl_label = "Update current node tree"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    node_group: StringProperty(default="")

    def execute(self, context):
        try:
            bpy.context.window.cursor_set("WAIT")
            ng = bpy.data.node_groups.get(self.node_group)
            if ng:
                ng.unfreeze(hard=True)
                build_update_list(ng)
                process_tree(ng)
        finally:
            bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

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
                ng.unfreeze(hard=True)
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
                    ng.unfreeze(hard=True)
                    build_update_list(ng)
                    process_tree(ng)
                finally:
                    ng.sv_process = prev_process_state
        except:
            pass
        finally:
            bpy.context.window.cursor_set("DEFAULT")

        return {'FINISHED'}

class SverchokPurgeCache(bpy.types.Operator):
    """Sverchok purge cache"""
    bl_idname = "node.sverchok_purge_cache"
    bl_label = "Sverchok purge cache"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        info(bpy.context.space_data.node_tree.name)
        return {'FINISHED'}


# USED IN CTRL+U PROPERTIES WINDOW
class SverchokHome(bpy.types.Operator):
    """Sverchok Home"""
    bl_idname = "node.sverchok_home"
    bl_label = "Sverchok go home"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        page = 'http://nikitron.cc.ua/blend_scripts.html'
        if context.scene.use_webbrowser:
            try:
                webbrowser.open_new_tab(page)
            except:
                self.report({'WARNING'}, "Error in opening the page %s." % (page))
        return {'FINISHED'}



class SvSwitchToLayout (bpy.types.Operator):
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


sv_tools_classes = [
    SverchokUpdateCurrent,
    SverchokUpdateContext,
    SverchokUpdateContextForced,
    SverchokUpdateAll,
    SverchokBakeAll,
    SverchokPurgeCache,
    SverchokHome,
    SvSwitchToLayout,
]


def register():
    for class_name in sv_tools_classes:
        bpy.utils.register_class(class_name)

    bpy.types.Scene.sv_new_version = BoolProperty(default=False)


def unregister():
    for class_name in reversed(sv_tools_classes):
        bpy.utils.unregister_class(class_name)
