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
import json
import base64
from time import gmtime, strftime
from urllib.request import Request
import webbrowser

import bpy
from sverchok.utils.logging import info, debug, error
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.sv_requests import urlopen

API_URL = 'https://api.github.com/gists'
TOKEN_HELP_URL = "https://github.com/nortikin/sverchok/wiki/Set-up-GitHub-account-for-exporting-node-trees-from-Sverchok"

def show_token_help():
    webbrowser.open(TOKEN_HELP_URL)

def main_upload_function(gist_filename, gist_description, gist_body, show_browser=False):

    gist_post_data = {
        'description': gist_description, 
        'public': True,
        'files': {gist_filename: {'content': gist_body}}
    }

    json_post_data = json.dumps(gist_post_data).encode('utf-8')

    def get_gist_url(found_json):
        wfile = json.JSONDecoder()
        wjson = wfile.decode(found_json)
        gist_url = wjson['html_url']

        if show_browser:
            import webbrowser
            print(gist_url)
            webbrowser.open(gist_url)

        return gist_url

    def upload_gist():

        with sv_preferences() as prefs:
            token = prefs.github_token
            if not token:
                info("GitHub API access token is not specified")
                show_token_help()
                return

            info("Uploading: %s", gist_filename)
            headers = {"Authorization": "token " + token}
        
            req = Request(API_URL, data=json_post_data, headers=headers)
            json_to_parse = urlopen(req, data=json_post_data)
            
            info('Received response from server')
            found_json = json_to_parse.read().decode()
            return get_gist_url(found_json)

    return upload_gist()



def write_or_append_datafiles(gist_url, layout_name):
    """
    usage:
               write_or_append_datafiles("some_long_url", "some_name")

    the first time this function is called 
    - it will generate a file at YYYY_MM_gist_uploads.csv with column headings: 
    - gist_url, layout_name, time_stamp, sha
    - then fill out the first line
    any following time this function is called it will append the next line.

    if the YYYY_MM changes, you get a new empty file ..and the same thing will happen.

    """

    filename = strftime("%Y_%m", gmtime()) + "_gist_uploads.csv"

    dirpath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    fullpath = os.path.join(dirpath, filename)
    
    # create fullpath if it doesn't exist
    if not os.path.exists(fullpath):
        with open(fullpath, 'w') as ofile:
            ofile.write('gist_url, layout_name, time_stamp, sha\n')
    
    with open(fullpath, 'a') as ofile:
        raw_time_stamp = strftime("%Y_%m_%d_%H_%M", gmtime())
        ofile.write(gist_url + ', ' + layout_name + ', ' + raw_time_stamp + ', no_sha\n')
