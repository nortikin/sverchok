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
import bpy
import json
from time import gmtime, strftime
from urllib.request import urlopen


def main_upload_function(gist_filename, gist_description, gist_body, show_browser=False):

    gist_post_data = {
        'description': gist_description, 
        'public': True,
        'files': {
            gist_filename: {
                'content': gist_body
            }
        }
    }

    json_post_data = json.dumps(gist_post_data).encode('utf-8')

    def get_gist_url(found_json):
        wfile = json.JSONDecoder()
        wjson = wfile.decode(found_json)
        gist_url = 'https://gist.github.com/' + wjson['id']

        if show_browser:
            import webbrowser
            print(gist_url)
            webbrowser.open(gist_url)

        return gist_url

    def upload_gist():
        print('sending')
        url = 'https://api.github.com/gists'
        json_to_parse = urlopen(url, data=json_post_data)
        
        print('received response from server')
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


def load_json_from_gist(gist_id, operator=None):
    """
    Load JSON data from Gist by gist ID.

    gist_id: gist ID. Passing full URL is also supported.
    operator: optional instance of bpy.types.Operator. Used for errors reporting.

    Returns JSON dictionary.
    """

    def read_n_decode(url):
        try:
            content_at_url = urlopen(url)
            found_json = content_at_url.read().decode()
            return found_json
        except urllib.error.HTTPError as err:
            if err.code == 404:
                message = 'url: ' + str(url) + ' doesn\'t appear to be a valid url, copy it again from your source'
                error(message)
                if operator:
                    operator.report({'ERROR'}, message)
            else:
                message = 'url error:' + str(err.code)
                error(message)
                if operator:
                    operator.report({'ERROR'}, message)
        except Exception as err:
            exception(err)
            if operator:
                operator.report({'ERROR'}, 'unspecified error, check your internet connection')

        return

    # if it still has the full gist path, trim down to ID
    if '/' in gist_id:
        gist_id = gist_id.split('/')[-1]

    gist_id = str(gist_id)
    url = 'https://api.github.com/gists/' + gist_id
    found_json = read_n_decode(url)
    if not found_json:
        return

    wfile = json.JSONDecoder()
    wjson = wfile.decode(found_json)

    # 'files' may contain several names, we pick the first (index=0)
    file_name = list(wjson['files'].keys())[0]
    nodes_str = wjson['files'][file_name]['content']
    return json.loads(nodes_str)