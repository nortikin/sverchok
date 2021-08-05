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
import os
import urllib
import urllib.request
from zipfile import ZipFile
import addon_utils


import bpy
import sverchok
from sverchok.utils import sv_requests as requests



EXTRA_ADDONS = {
'Sverchok Extra': {
    'name': 'sverchok_extra',
    'description': 'Experimental Nodes on Surfaces, Curves, Solids and Data managment',
    'archive_link':'https://github.com/portnov/sverchok-extra/archive/',
    'branch': 'master',
    'self_instalable': True
    },
'Sverchok Open3d': {
    'name': 'sverchok_open3d',
    'description': 'Point Cloud and Triangle Mesh nodes',
    'archive_link':'https://github.com/vicdoval/sverchok-open3d/archive/',
    'branch': 'master',
    'self_instalable': True
    }
}

ARCHIVE_LINK = 'https://github.com/nortikin/sverchok/archive/'
MASTER_BRANCH_NAME = 'master'

def sv_get_local_path():
    script_paths = os.path.normpath(os.path.dirname(__file__))
    addons_path = os.path.split(os.path.dirname(script_paths))[0]

    return addons_path

bl_addons_path = sv_get_local_path()
import importlib


def get_addons_folder():
    addons ={}
    for p in bpy.utils.script_paths():
        p2 = os.path.join(p, 'addons')
        if os.path.exists(p2):
            addons.update({name: os.path.join(p2, name) for name in os.listdir(p2) if os.path.isdir(os.path.join(p2, name))})
    return addons


ADDON_LIST = get_addons_folder()

def draw_extra_addons(layout):
    for pretty_name in EXTRA_ADDONS:
        addon = EXTRA_ADDONS[pretty_name]

        b = layout.box()
        b.label(text=pretty_name)
        if addon['name'] in ADDON_LIST:
            addon_name = addon['name']
        elif addon['name'].replace('_', '-') in ADDON_LIST:
            addon_name = addon['name'].replace('_', '-')
        elif addon['name']+'-'+ addon['branch'] in ADDON_LIST:
            addon_name = addon['name']+'-'+ addon['branch']
        elif addon['name'].replace('_', '-')+'-'+ addon['branch'] in ADDON_LIST:
            addon_name = addon['name'].replace('_', '-')+'-'+ addon['branch']
        else:
            addon_name = False
        # print(addon_name)  # this prints constantly False if extra-addons isn't installed
        if addon_name:
            loaded_default, loaded_state = addon_utils.check(addon_name)
            if loaded_state:
                op = b.operator('preferences.addon_disable')
                op.module = addon_name
                try:
                    module = importlib.import_module(addon['name'])
                    if hasattr(module, 'settings'):
                        if hasattr(module.settings, 'draw_in_sv_prefs'):
                            module.settings.draw_in_sv_prefs(b)
                        if hasattr(module.settings, 'update_addon_ui'):
                            row = b.row()
                            module.settings.update_addon_ui(row)
                except ModuleNotFoundError:
                    addon_name = False
            else:
                op = b.operator('preferences.addon_enable')
                op.module = addon_name
        if not addon_name:
            b.label(text=addon['description'])
            op = b.operator('node.sverchok_download_addon', text=f'Download {pretty_name}')
            op.master_branch_name = addon['branch']
            op.archive_link = addon['archive_link']

class SverchokDownloadExtraAddon(bpy.types.Operator):
    """ Download Sverchok Extra Addon. After completion press F8 to reload addons or restart Blender """
    bl_idname = "node.sverchok_download_addon"
    bl_label = "Sverchok update addon"
    bl_options = {'REGISTER'}

    master_branch_name: bpy.props.StringProperty(default=MASTER_BRANCH_NAME)
    archive_link: bpy.props.StringProperty(default=ARCHIVE_LINK)

    def execute(self, context):
        global ADDON_LIST
        os.curdir = bl_addons_path
        os.chdir(os.curdir)

        # wm = bpy.context.window_manager  should be this i think....
        wm = bpy.data.window_managers[0]
        wm.progress_begin(0, 100)
        wm.progress_update(20)

        # dload_archive_path, dload_archive_name = get_archive_path(self.addon_name)

        try:
            branch_name = self.master_branch_name
            branch_origin = self.archive_link
            zipname = '{0}.zip'.format(branch_name)
            url = branch_origin + zipname

            to_path = os.path.normpath(os.path.join(os.curdir, zipname))

            print('> obtaining: [{0}]\n> sending to path: [{1}]'.format(url, to_path))
            # return {'CANCELLED'}

            file = requests.urlretrieve(url, to_path)
            wm.progress_update(50)
        except Exception as err:
            self.report({'ERROR'}, "Cannot get archive from Internet")
            print(err)
            wm.progress_end()
            return {'CANCELLED'}

        try:
            err = 0
            ZipFile(file[0]).extractall(path=os.curdir, members=None, pwd=None)
            wm.progress_update(90)
            err = 1
            os.remove(file[0])
            err = 2
            wm.progress_update(100)
            wm.progress_end()
            bpy.ops.preferences.addon_refresh()
            ADDON_LIST = get_addons_folder()
            self.report({'INFO'}, "Unzipped, reload addons with F8 button, maybe restart Blender")
        except:
            self.report({'ERROR'}, "Cannot extract files errno {0}".format(str(err)))
            wm.progress_end()
            os.remove(file[0])
            return {'CANCELLED'}

        return {'FINISHED'}



def register():

    bpy.utils.register_class(SverchokDownloadExtraAddon)


def unregister():

    bpy.utils.unregister_class(SverchokDownloadExtraAddon)
