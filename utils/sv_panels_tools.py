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
import collections

import bpy
from bpy.props import StringProperty, CollectionProperty

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


class SverchokBakeAll(bpy.types.Operator):
    """Bake all nodes on this layout"""
    bl_idname = "node.sverchok_bake_all"
    bl_label = "Sverchok bake all"
    bl_options = {'REGISTER', 'UNDO'}

    node_tree_name = StringProperty(name='tree_name', default='')

    @classmethod
    def poll(cls, context):
        if bpy.data.node_groups.__len__():
            return True
        else:
            return False

    def execute(self, context):
        ng = bpy.data.node_groups[self.node_tree_name]
        nodes = filter(lambda n: hasattr(n, "bake"), ng.nodes)
        for node in nodes:
            if node.bakebuttonshow:
                node.bake()

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
        bpy.data.window_managers[0].progress_begin(0, 100)
        bpy.data.window_managers[0].progress_update(20)
        try:
            # here change folder
            url = 'https://github.com/nortikin/sverchok/archive/master.zip'
            # here change folder
            to_path = os.path.normpath(os.path.join(os.curdir, 'master.zip'))
            file = urllib.request.urlretrieve(url, to_path)
            bpy.data.window_managers[0].progress_update(50)
        except:
            self.report({'ERROR'}, "Cannot get archive from Internet")
            bpy.data.window_managers[0].progress_end()
            return {'CANCELLED'}
        try:
            #os.removedirs(os.path.normpath(os.path.join(os.curdir, 'sverchok')))
            err = 0
            ZipFile(file[0]).extractall(path=os.curdir, members=None, pwd=None)
            bpy.data.window_managers[0].progress_update(90)
            err = 1
            os.remove(file[0])
            err = 2
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


class SvSwitchToLayout (bpy.types.Operator):
    """Switch to exact layout, user friendly way"""
    bl_idname = "node.sv_switch_layout"
    bl_label = "switch layouts"
    bl_options = {'REGISTER', 'UNDO'}

    layout_name = bpy.props.StringProperty(
        default='', name='layout_name',
        description='layout name to change layout by button')

    @classmethod
    def poll(cls, self):
        if bpy.context.space_data.type == 'NODE_EDITOR':
            if bpy.context.space_data.node_tree.bl_rna.name == 'Sverchok Node Tree':
                return 1
        else:
            return 0

    def execute(self, context):
        if context.space_data.node_tree.name != self.layout_name:
            context.space_data.node_tree = bpy.data.node_groups[self.layout_name]
        else:
            return {'CANCELLED'}
        return {'FINISHED'}




class SvClearNodesLayouts (bpy.types.Operator):
    """Clear node layouts sverchok and blendgraph, when no nodes editor opened"""
    bl_idname = "node.sv_delete_nodelayouts"
    bl_label = "del layouts"
    bl_options = {'REGISTER', 'UNDO'}

    do_clear = bpy.props.BoolProperty(
        default=False, name='even used',
        description='remove even if layout has one user (not fake user)')

    @classmethod
    def poll(cls, self):
        for area in bpy.context.window.screen.areas:
            if area.type == 'NODE_EDITOR':
                return False
        return True

    def execute(self, context):
        trees = bpy.data.node_groups
        for T in trees:
            if T.bl_rna.name in ['Shader Node Tree']:
                continue
            if trees[T.name].users > 1 and T.use_fake_user:
                print('Layout '+str(T.name)+' protected by fake user.')
            if trees[T.name].users >= 1 and self.do_clear and not T.use_fake_user:
                print('cleaning user: '+str(T.name))
                trees[T.name].user_clear()
            if trees[T.name].users == 0:
                print('removing layout: '+str(T.name)+' | '+str(T.bl_rna.name))
                bpy.data.node_groups.remove(T)

        return {'FINISHED'}


class Sv3dPropItem(bpy.types.PropertyGroup):
    node_name = StringProperty()
    prop_name = StringProperty()


class SvLayoutScanProperties(bpy.types.Operator):
    ''' scan layouts of sverchok for properties '''

    bl_idname = "node.sv_scan_propertyes"
    bl_label = "scan for propertyes in sverchok leyouts"

    def execute(self, context):
        for tree in bpy.data.node_groups:
            tna = tree.name
            if tree.bl_idname == 'SverchCustomTreeType':
                templist = []
                for no in tree.nodes:
                    print(no.bl_idname)
                    if no.bl_idname == "IntegerNode":
                        if no.inputs and no.outputs:
                            if not no.inputs[0].links \
                                    and no.outputs[0].links and no.to3d:
                                templist.append([no. label, no.name, 'int_'])
                    if no.bl_idname == "FloatNode":
                        if no.inputs and no.outputs:
                            if not no.inputs[0].links \
                                    and no.outputs[0].links and no.to3d:
                                templist.append([no.label, no.name, 'float_'])
                    if no.bl_idname == "ObjectsNode":
                        if any((s.links for s in no.outputs)):
                            templist.append([no.label, no.name, ""])
                templist.sort()
                templ = [[t[1], t[2]] for t in templist]
                tree.Sv3DProps.clear()
                for name, prop in templ:
                    tree.Sv3DProps.add()
                    tree.Sv3DProps[-1].node_name = name
                    tree.Sv3DProps[-1].prop_name = prop

        return {'FINISHED'}


sv_tools_classes = [
    SverchokUpdateCurrent,
    SverchokUpdateAll,
    SverchokBakeAll,
    SverchokCheckForUpgrades,
    SverchokUpdateAddon,
    SverchokPurgeCache,
    SverchokHome,
    Sv3dPropItem,
    SvSwitchToLayout,
    SvLayoutScanProperties,
    SvClearNodesLayouts
]


def register():
    bpy.types.Scene.sv_do_clear = bpy.props.BoolProperty(
        default=False, name='even used', description='remove even if \
        layout has one user (not fake user)')

    for class_name in sv_tools_classes:
        bpy.utils.register_class(class_name)

    bpy.types.SverchCustomTreeType.Sv3DProps = CollectionProperty(type=Sv3dPropItem)


def unregister():
    # cargo cult to unregister in reverse order? I don't think this is needed.
    # maybe it was handy at some point?
    for class_name in reversed(sv_tools_classes):
        bpy.utils.unregister_class(class_name)

if __name__ == '__main__':
    register()
