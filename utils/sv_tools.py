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
from data_structure import makeTreeUpdate2, speedUpdate
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
        makeTreeUpdate2()
        speedUpdate()
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
            report({'INFO'}, "There is new version.")
        else:
            report({'INFO'}, "You already have latest version of Sverchok, no need to upgrade.")
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
        try:
            # here change folder
            url = 'https://github.com/nortikin/sverchok/archive/master.zip'
            # here change folder
            file = urllib.request.urlretrieve(url, os.path.normpath(os.path.join(os.curdir, 'master.zip')))
        except:
            self.report({'ERROR'}, "Cannot get archive from Internet")
            return {'CANCELLED'}
        try:
            #os.removedirs(os.path.normpath(os.path.join(os.curdir, 'sverchok')))
            ZipFile(file[0]).extractall(path=os.curdir, members=None, pwd=None)
            os.remove(file[0])
            sv_new_version = False
            self.report({'INFO'}, "Unzipped, reload addons with F8 button")
        except:
            self.report({'ERROR'}, "Cannot extract files")
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
        layout = self.layout
        #layout.scale_y=1.1
        layout.active = True
        col = layout.column()
        col.scale_y = 3.0

        col.operator(SverchokUpdateAll.bl_idname, text="UPDATE")

        box = layout.box()
        #box.label(text="Layout manager")
        little_width = 0.12
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Layout')
        col1 = row.column(align=True)
        col1.scale_x = little_width
        col1.label(icon='RESTRICT_VIEW_OFF', text=' ')
        #row.label(text='Bake')
        col2 = row.column(align=True)
        col2.scale_x = little_width
        col2.label(icon='ANIM', text=' ')
        col2.icon

        ng = bpy.data.node_groups

        for name, tree in ng.items():
            if tree.bl_idname == 'SverchCustomTreeType':

                row = col.row(align=True)

                if name == context.space_data.node_tree.name:
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
        col.operator(SverchokUpdateAll.bl_idname, text="UPDATE")
        #box = layout.box()

        #col = box.column(align=True)
        #col.template_node_socket(color=(0.0, 0.9, 0.7, 1.0))
        #col.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        #col.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        #col.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        #col.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'

        lennon = len(bpy.data.node_groups[self.id_data.name].nodes)
        group = self.id_data.name
        tex = str(lennon) + ' | ' + str(group)
        layout.label(text=tex)
        #layout.template_color_ramp(self, 'color_', expand=True)

    def update(self):
        self.use_custom_color = True
        self.color = (1.0, 0.0, 0.0)

    def update_socket(self, context):
        pass


def register():
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
if __name__  ==  '__main__':
    register()





