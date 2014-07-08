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
import os
import urllib
import urllib.request
from zipfile import ZipFile
import traceback

import bpy
from bpy.props import StringProperty

from core.update_system import sverchok_update, build_update_list
from node_tree import SverchCustomTreeNode


def sv_get_local_path():
    sv_script_paths = os.path.normpath(os.path.dirname(__file__))
    bl_addons_path = os.path.split(os.path.dirname(sv_script_paths))[0]
    sv_version = os.path.normpath(os.path.join(sv_script_paths, 'version'))
    with open(sv_version) as sv_local_file:
        sv_version_local = next(sv_local_file).strip()
    return sv_script_paths, bl_addons_path, sv_version_local, sv_version

# global veriables in tools
sv_script_paths, bl_addons_path, sv_version_local, sv_version = sv_get_local_path()
sv_new_version = False


class SverchokUpdateAll(bpy.types.Operator):
    """Sverchok update all"""
    bl_idname = "node.sverchok_update_all"
    bl_label = "Sverchok update all"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        build_update_list()
        sverchok_update()
        return {'FINISHED'}

class SverchokUpdateCurrent(bpy.types.Operator):
    """Sverchok update all"""
    bl_idname = "node.sverchok_update_current"
    bl_label = "Sverchok update all"
    bl_options = {'REGISTER', 'UNDO'}

    node_group = StringProperty(default="")

    def execute(self, context):
        ng = bpy.data.node_groups.get(self.node_group)
        if ng:
            build_update_list(tree=ng)
            sverchok_update(tree=ng)
        return {'FINISHED'}


class SverchokPurgeCache(bpy.types.Operator):
    """Sverchok purge cache"""
    bl_idname = "node.sverchok_purge_cache"
    bl_label = "Sverchok purge cache"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print(bpy.context.space_data.node_tree.name)
        return {'FINISHED'}


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


class SverchokCheckForUpgrades(bpy.types.Operator):
    """ Check if there new version on github """
    bl_idname = "node.sverchok_check_for_upgrades"
    bl_label = "Sverchok check for new version"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global sv_new_version
        os.curdir = sv_script_paths
        os.chdir(os.curdir)
        report = self.report
        try:
            with open(sv_version) as sv_local_file:
                version_local = next(sv_local_file).strip()
        except:
            report({'INFO'}, "Failed to read local version")
            return {'CANCELLED'}
        try:
            # here change folder
            url = 'https://raw.githubusercontent.com/nortikin/sverchok/master/utils/version'
            version_url = urllib.request.urlopen(url).read().strip().decode()
        except urllib.error.URLError:
            traceback.print_exc()
            report({'INFO'}, "Unable to contact github, or SSL not compiled.")
            return {'CANCELLED'}

        if version_local != version_url:
            sv_new_version = True
            report({'INFO'}, "New version {0}".format(version_url))
        else:
            report({'INFO'}, "Your version {0} is last.".format(version_local))
        return {'FINISHED'}


class SverchokUpdateAddon(bpy.types.Operator):
    """ Sverchok update addon without any browsing and so on. After - press F8 to reload addons """
    bl_idname = "node.sverchok_update_addon"
    bl_label = "Sverchok update addon"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global sv_new_version
        os.curdir = bl_addons_path
        os.chdir(os.curdir)
        bpy.data.window_managers[0].progress_begin(0,100)
        bpy.data.window_managers[0].progress_update(20)
        try:
            # here change folder
            url = 'https://github.com/nortikin/sverchok/archive/master.zip'
            # here change folder
            file = urllib.request.urlretrieve(url, os.path.normpath(os.path.join(os.curdir, 'master.zip')))
            bpy.data.window_managers[0].progress_update(50)
        except:
            self.report({'ERROR'}, "Cannot get archive from Internet")
            bpy.data.window_managers[0].progress_end()
            return {'CANCELLED'}
        try:
            #os.removedirs(os.path.normpath(os.path.join(os.curdir, 'sverchok')))
            err=0
            ZipFile(file[0]).extractall(path=os.curdir, members=None, pwd=None)
            bpy.data.window_managers[0].progress_update(90)
            err=1
            os.remove(file[0])
            err=2
            sv_new_version = False
            bpy.data.window_managers[0].progress_update(100)
            bpy.data.window_managers[0].progress_end()
            self.report({'INFO'}, "Unzipped, reload addons with F8 button")
        except:
            self.report({'ERROR'}, "Cannot extract files errno {0}".format(str(err)))
            bpy.data.window_managers[0].progress_end()
            os.remove(file[0])
            return {'CANCELLED'}

        return {'FINISHED'}


class SverchokToolsMenu(bpy.types.Panel):
    bl_idname = "Sverchok_tools_menu"
    bl_label = "Sverchok "+sv_version_local
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        ng_name = context.space_data.node_tree.name
        layout = self.layout
        #layout.scale_y=1.1
        layout.active = True
        col = layout.column()
        col.scale_y = 3.0
        u = "Update all"
        col.operator(SverchokUpdateAll.bl_idname, text=u)
        u = "Update {0}".format(ng_name)
        op = col.operator(SverchokUpdateCurrent.bl_idname, text = u)
        op.node_group = ng_name
        box = layout.box()
        little_width = 0.12
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Layout')
        col1 = row.column(align=True)
        col1.scale_x = little_width
        col1.label(icon='RESTRICT_VIEW_OFF', text=' ')
        col2 = row.column(align=True)
        col2.scale_x = little_width
        col2.label(icon='ANIM', text=' ')
        col2.icon

        for name, tree in bpy.data.node_groups.items():
            if tree.bl_idname == 'SverchCustomTreeType':

                row = col.row(align=True)

                if name == ng_name:
                    row.label(text=name, icon='LINK')
                else:
                    row.label(text=name)

                split = row.column(align=True)
                split.scale_x = little_width
                if tree.sv_show:
                    split.prop(tree, 'sv_show', icon='UNLOCKED', text=' ')
                else:
                    split.prop(tree, 'sv_show', icon='LOCKED', text=' ')
                split = row.column(align=True)
                split.scale_x = little_width
                if tree.sv_animate:
                    split.prop(tree, 'sv_animate', icon='UNLOCKED', text=' ')
                else:
                    split.prop(tree, 'sv_animate', icon='LOCKED', text=' ')

        if sv_new_version:
            layout.column().operator(SverchokUpdateAddon.bl_idname, text='Upgrade Sverchok addon')
        else:
            layout.column().operator(SverchokCheckForUpgrades.bl_idname, text='Check for new version')
        #       row.prop(tree, 'sv_bake',text=' ')

        #box = layout.box()
        #col = box.column(align=True)
        #col.label(text="Sverchok v_0.2.8")
        #col.label(text='layout: '+context.space_data.node_tree.name)
        #row = col.row(align=True)
        #row.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        #row.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        #row = col.row(align=True)
        #row.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        #row.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'


class ToolsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Tools for different purposes '''
    bl_idname = 'ToolsNode'
    bl_label = 'Tools node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    #bl_height_default = 110
    #bl_width_min = 20
    #color = (1,1,1)
    color_ = bpy.types.ColorRamp

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.scale_y = 15
        col.template_color_picker
        u = "Update "
        #col.operator(SverchokUpdateAll.bl_idname, text=u)
        op = col.operator(SverchokUpdateCurrent.bl_idname, text=u+self.id_data.name)
        op.node_group = self.id_data.name
        #box = layout.box()

        #col = box.column(align=True)
        #col.template_node_socket(color=(0.0, 0.9, 0.7, 1.0))
        #col.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        #col.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        #col.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        #col.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'

        node_count = len(self.id_data.nodes)
        tex = str(node_count) + ' | ' + str(self.id_data.name)
        layout.label(text=tex)
        #layout.template_color_ramp(self, 'color_', expand=True)

    def update(self):
        self.use_custom_color = True
        self.color = (1.0, 0.0, 0.0)

    def update_socket(self, context):
        pass


def register():
    bpy.utils.register_class(SverchokUpdateCurrent)
    bpy.utils.register_class(SverchokUpdateAll)
    bpy.utils.register_class(SverchokCheckForUpgrades)
    bpy.utils.register_class(SverchokUpdateAddon)
    bpy.utils.register_class(SverchokPurgeCache)
    bpy.utils.register_class(SverchokHome)
    bpy.utils.register_class(SverchokToolsMenu)
    bpy.utils.register_class(ToolsNode)


def unregister():
    bpy.utils.unregister_class(ToolsNode)
    bpy.utils.unregister_class(SverchokToolsMenu)
    bpy.utils.unregister_class(SverchokHome)
    bpy.utils.unregister_class(SverchokPurgeCache)
    bpy.utils.unregister_class(SverchokUpdateAddon)
    bpy.utils.unregister_class(SverchokCheckForUpgrades)
    bpy.utils.unregister_class(SverchokUpdateAll)
    bpy.utils.unregister_class(SverchokUpdateCurrent)

if __name__  ==  '__main__':
    register()


