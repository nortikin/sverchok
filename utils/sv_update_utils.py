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

import requests
import os
import urllib
import urllib.request
from zipfile import ZipFile

import bpy
import sverchok

# pylint: disable=w0141

def sv_get_local_path():
    script_paths = os.path.normpath(os.path.dirname(__file__))
    addons_path = os.path.split(os.path.dirname(script_paths))[0]
    version_local = ".".join(map(str, sverchok.bl_info["version"]))
    return script_paths, addons_path, version_local

sv_script_paths, bl_addons_path, sv_version_local = sv_get_local_path()



def get_sha_filepath(filename='sv_shafile.sv'):
    """ the act if calling this function should produce a file called 
        ../datafiles/sverchok/sv_shafile.sv (or sv_sha_downloaded.sv)

    the location of datafiles is common for Blender apps and defined internally for each OS.
    returns: the path of this file

    """
    dirpath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    fullpath = os.path.join(dirpath, filename)
    
    # create fullpath if it doesn't exist
    if not os.path.exists(fullpath):
        with open(fullpath, 'w') as _:
            pass
    
    return fullpath

def latest_github_sha():
    """ get sha produced by latest commit on github

        sha = latest_github_sha()
        print(sha)

    """
    r = requests.get('https://api.github.com/repos/nortikin/sverchok/commits')
    json_obj = r.json()
    return os.path.basename(json_obj[0]['commit']['url'])


def latest_local_sha(filename='sv_shafile.sv'):
    """ get previously stored sha, if any. finding no local sha will return empty string

        reads from  ../datafiles/sverchok/sv_shafile.sv

    """
    filepath = get_sha_filepath(filename)
    with open(filepath) as p:
        return p.read()

def write_latest_sha_to_local(sha_value='', filename='sv_shafile.sv'):
    """ write the content of sha_value to 

        ../datafiles/sverchok/sv_shafile.sv

    """
    filepath = get_sha_filepath(filename)
    with open(filepath, 'w') as p:
        p.write(sha_value)


class SverchokCheckForUpgradesSHA(bpy.types.Operator):
    """ Check if there new version on github (using sha) """
    bl_idname = "node.sverchok_check_for_upgrades_wsha"
    bl_label = "Sverchok check for new minor version"
    bl_options = {'REGISTER'}
            

    def execute(self, context):
        report = self.report
        context.scene.sv_new_version = False
        
        local_sha = latest_local_sha()
        latest_sha = latest_github_sha()
        
        # this logic can be simplified.
        if not local_sha:
            context.scene.sv_new_version = True
        else:
            if not local_sha == latest_sha:
                context.scene.sv_new_version = True

        write_latest_sha_to_local(sha_value=latest_sha)
        downloaded_sha = latest_local_sha(filename='sv_sha_downloaded.sv')

        if not downloaded_sha == latest_sha:
            context.scene.sv_new_version = True

        if context.scene.sv_new_version:
            report({'INFO'}, "New commits available, update at own risk ({0})".format(latest_sha[:7]))
        else:
            report({'INFO'}, "No new commits to download")
        return {'FINISHED'}


class SverchokUpdateAddon(bpy.types.Operator):
    """ Update Sverchok addon. After completion press F8 to reload addons or restart Blender """
    bl_idname = "node.sverchok_update_addon"
    bl_label = "Sverchok update addon"
    bl_options = {'REGISTER'}

    def execute(self, context):

        os.curdir = sv_get_local_path()[1]  # addons path
        os.chdir(os.curdir)

        wm = bpy.data.window_managers[0]
        wm.progress_begin(0, 100)
        wm.progress_update(20)

        try:
            url = 'https://github.com/nortikin/sverchok/archive/master.zip'
            to_path = os.path.normpath(os.path.join(os.curdir, 'master.zip'))
            file = urllib.request.urlretrieve(url, to_path)
            wm.progress_update(50)
        except:
            self.report({'ERROR'}, "Cannot get archive from Internet")
            wm.progress_end()
            return {'CANCELLED'}
        
        try:
            err = 0
            ZipFile(file[0]).extractall(path=os.curdir, members=None, pwd=None)
            wm.progress_update(90)
            err = 1
            os.remove(file[0])
            err = 2
            bpy.context.scene.sv_new_version = False
            wm.progress_update(100)
            wm.progress_end()
            self.report({'INFO'}, "Unzipped, reload addons with F8 button, maybe restart Blender")
        except:
            self.report({'ERROR'}, "Cannot extract files errno {0}".format(str(err)))
            wm.progress_end()
            os.remove(file[0])
            return {'CANCELLED'}

        
        write_latest_sha_to_local(sha_value=latest_local_sha(), filename='sv_sha_downloaded.sv')
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SverchokCheckForUpgradesSHA)
    bpy.utils.register_class(SverchokUpdateAddon)

def unregister():
    bpy.utils.unregister_class(SverchokCheckForUpgradesSHA)
    bpy.utils.unregister_class(SverchokUpdateAddon)
