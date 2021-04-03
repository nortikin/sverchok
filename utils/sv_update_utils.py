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

import os
import urllib
import urllib.request
from zipfile import ZipFile

import bpy
import sverchok
from sverchok.utils import sv_requests as requests
from sverchok.utils.context_managers import sv_preferences, addon_preferences
# pylint: disable=w0141
ADDON_NAME = sverchok.__name__
COMMITS_LINK = 'https://api.github.com/repos/nortikin/sverchok/commits'

SHA_FILE = 'sv_shafile.sv'
SHA_DOWNLOADED = 'sv_sha_downloaded.sv'

ARCHIVE_LINK = 'https://github.com/nortikin/sverchok/archive/'
MASTER_BRANCH_NAME = 'master'

def sv_get_local_path():
    script_paths = os.path.normpath(os.path.dirname(__file__))
    addons_path = os.path.split(os.path.dirname(script_paths))[0]
    version_local = ".".join(map(str, sverchok.bl_info["version"]))
    return script_paths, addons_path, version_local

sv_script_paths, bl_addons_path, sv_version_local = sv_get_local_path()



def get_sha_filepath(filename=SHA_FILE, addon_name=ADDON_NAME):
    """ the act if calling this function should produce a file called
        ../datafiles/sverchok/sv_shafile.sv (or sv_sha_downloaded.sv)

    the location of datafiles is common for Blender apps and defined internally for each OS.
    returns: the path of this file

    """
    dirpath = os.path.join(bpy.utils.user_resource('DATAFILES', path=addon_name, create=True))
    fullpath = os.path.join(dirpath, filename)

    # create fullpath if it doesn't exist
    if not os.path.exists(fullpath):
        with open(fullpath, 'w') as _:
            pass

    return fullpath

def latest_github_sha(commits_link):
    """ get sha produced by latest commit on github

        sha = latest_github_sha()
        print(sha)

    """
    r = requests.get(commits_link)
    json_obj = r.json()
    return os.path.basename(json_obj[0]['commit']['url'])


def latest_local_sha(filename=SHA_FILE, addon_name=ADDON_NAME):
    """ get previously stored sha, if any. finding no local sha will return empty string

        reads from  ../datafiles/sverchok/sv_shafile.sv

    """
    filepath = get_sha_filepath(filename, addon_name=addon_name)
    with open(filepath) as p:
        return p.read()

def write_latest_sha_to_local(sha_value='', filename=SHA_FILE, addon_name=ADDON_NAME):
    """ write the content of sha_value to

        ../datafiles/sverchok/sv_shafile.sv

    """
    filepath = get_sha_filepath(filename, addon_name=addon_name)
    with open(filepath, 'w') as p:
        p.write(sha_value)


def make_version_sha(addon_name=ADDON_NAME):
    """ Generate a string to represent sverchok version including sha if found

        returns:   0.5.9.13 (a3bcd34)   (or something like that)
    """
    sha_postfix = ''
    sha = latest_local_sha(filename=SHA_DOWNLOADED, addon_name=addon_name)
    if sha:
        sha_postfix = " (" + sha[:7] + ")"

    return sv_version_local + sha_postfix

version_and_sha = make_version_sha()


class SverchokCheckForUpgradesSHA(bpy.types.Operator):
    """ Check if there new version on github (using sha) """
    bl_idname = "node.sverchok_check_for_upgrades_wsha"
    bl_label = "Sverchok check for new minor version"
    bl_options = {'REGISTER'}
    addon_name: bpy.props.StringProperty(default=ADDON_NAME)
    commits_link: bpy.props.StringProperty(default=COMMITS_LINK)

    def execute(self, context):
        report = self.report

        local_sha = latest_local_sha(addon_name=self.addon_name)
        latest_sha = latest_github_sha(self.commits_link)

        with addon_preferences(self.addon_name) as prefs:
            prefs.available_new_version = False
            if not local_sha:
                prefs.available_new_version = True
            else:
                if not local_sha == latest_sha:
                    prefs.available_new_version = True

            write_latest_sha_to_local(sha_value=latest_sha, addon_name=self.addon_name)
            downloaded_sha = latest_local_sha(filename=SHA_DOWNLOADED, addon_name=self.addon_name)
            if not downloaded_sha == latest_sha:
                prefs.available_new_version = True

            if prefs.available_new_version:
                report({'INFO'}, "New commits available, update at own risk ({0})".format(latest_sha[:7]))
            else:
                report({'INFO'}, "No new commits to download")

        return {'FINISHED'}


def get_archive_path(addon_name):
    with addon_preferences(addon_name) as prefs:
        return prefs.dload_archive_path, prefs.dload_archive_name


class SverchokUpdateAddon(bpy.types.Operator):
    """ Update Sverchok addon. After completion press F8 to reload addons or restart Blender """
    bl_idname = "node.sverchok_update_addon"
    bl_label = "Sverchok update addon"
    bl_options = {'REGISTER'}
    addon_name: bpy.props.StringProperty(default=ADDON_NAME)
    master_branch_name: bpy.props.StringProperty(default=MASTER_BRANCH_NAME)
    archive_link: bpy.props.StringProperty(default=ARCHIVE_LINK)

    def execute(self, context):

        os.curdir = bl_addons_path
        os.chdir(os.curdir)

        # wm = bpy.context.window_manager  should be this i think....
        wm = bpy.data.window_managers[0]
        wm.progress_begin(0, 100)
        wm.progress_update(20)

        dload_archive_path, dload_archive_name = get_archive_path(self.addon_name)

        try:
            branch_name = dload_archive_name or self.master_branch_name
            branch_origin = dload_archive_path or self.archive_link
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
            with addon_preferences(self.addon_name) as prefs:
                prefs.available_new_version = False
            wm.progress_update(100)
            wm.progress_end()
            self.report({'INFO'}, "Unzipped, reload addons with F8 button, maybe restart Blender")
        except:
            self.report({'ERROR'}, "Cannot extract files errno {0}".format(str(err)))
            wm.progress_end()
            os.remove(file[0])
            return {'CANCELLED'}

        # write to both sv_sha_download and sv_shafile.sv
        lastest_local_sha = latest_local_sha(addon_name=self.addon_name)
        write_latest_sha_to_local(sha_value=lastest_local_sha, filename=SHA_DOWNLOADED, addon_name=self.addon_name)
        write_latest_sha_to_local(sha_value=lastest_local_sha, addon_name=self.addon_name)
        return {'FINISHED'}


class SvPrintCommits(bpy.types.Operator):
    """ show latest commits in info panel, and terminal """
    bl_idname = "node.sv_show_latest_commits"
    bl_label = "Show latest commits"
    commits_link: bpy.props.StringProperty(default=COMMITS_LINK)
    num_commits: bpy.props.IntProperty(default=30)

    def execute(self, context):
        r = requests.get(self.commits_link)
        json_obj = r.json()

        rewrite_date = lambda date: f'{date[:10]}' #  @ {date[11:16]}'

        # table boilerplate for github markdown
        print("author | commit details\n--- | ---")

        # intro message for Info printing
        messages = [f"The {self.num_commits} most recent commits to Sverchok (master)"]

        for i in range(self.num_commits):
            commit = json_obj[i]['commit']
            sha = os.path.basename(commit['url'])[:7]

            author = commit['author']['name']
            date = commit['author']['date'] #  format : '2021-04-03T10:44:59Z'
            comments = commit['message'].split('\n')
            comment = comments[0] + '...' if len(comments) else ''

            message = f'{author} | {comment} {sha} on {rewrite_date(date)}'
            print(message)
            messages.append(message)

        multiline_string_of_messages = "\n".join(messages)
        self.report({'INFO'}, multiline_string_of_messages)

        return {'FINISHED'}




def register():
    bpy.utils.register_class(SverchokCheckForUpgradesSHA)
    bpy.utils.register_class(SverchokUpdateAddon)
    bpy.utils.register_class(SvPrintCommits)

def unregister():
    bpy.utils.unregister_class(SverchokCheckForUpgradesSHA)
    bpy.utils.unregister_class(SverchokUpdateAddon)
    bpy.utils.unregister_class(SvPrintCommits)
