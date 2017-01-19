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
import json

import bpy
import sverchok

def get_sha_filepath():
    """ the act if calling this function should produce a file called 
        ../datafiles/sverchok/sv_shafile.sv

    the location of datafiles is common for Blender apps and defined internally for each OS.
    returns: the path of this file

    """
    dirpath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    sv_sha_filename = 'sv_shafile.sv'
    fullpath = os.path.join(dirpath, sv_sha_filename)
    
    # create fullpath if it doesn't exist
    if not os.path.exists(fullpath):
        with open(fullpath, 'w') as j:
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


def latest_local_sha():
    """ get previously stored sha, if any. finding no local sha will return empty string

        reads from  ../datafiles/sverchok/sv_shafile.sv

    """
    filepath = get_sha_filepath()
    with open(filepath) as p:
        return p.read()

def write_latest_sha_to_local(sha_value):
    """ write the content of sha_value to 

        ../datafiles/sverchok/sv_shafile.sv

    """
    filepath = get_sha_filepath()
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

        write_latest_sha_to_local(latest_sha)

        if context.scene.sv_new_version:
            report({'INFO'}, "New commits available, update at own risk")
        else:
            report({'INFO'}, "No new commits to download")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SverchokCheckForUpgradesSHA)


def unregister():
    bpy.utils.unregister_class(SverchokCheckForUpgradesSHA)