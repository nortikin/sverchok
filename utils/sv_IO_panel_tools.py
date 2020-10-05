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
from time import gmtime, strftime
import zipfile
import json
import urllib

from sverchok.utils.logging import debug, info, warning, error, exception
from sverchok.utils.sv_requests import urlopen

# pylint: disable=w0621


def get_file_obj_from_zip(fullpath):
    '''
    fullpath must point to a zip file.
    usage:
        nodes_json = get_file_obj_from_zip(fullpath)
        print(nodes_json['export_version'])
    '''
    with zipfile.ZipFile(fullpath, "r") as jfile:
        exported_name = ""
        for name in jfile.namelist():
            if name.endswith('.json'):
                exported_name = name
                break

        if not exported_name:
            error('zip contains no files ending with .json')
            return

        debug(exported_name + ' <')
        fp = jfile.open(exported_name, 'r')
        m = fp.read().decode()
        return json.loads(m)


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


def propose_archive_filepath(blendpath, extension='zip'):
    """ disect existing filepath, add timestamp """
    blendname = os.path.basename(blendpath)
    blenddir = os.path.dirname(blendpath)
    blendbasename = blendname.split('.')[0]
    raw_time_stamp = strftime("%Y_%m_%d_%H_%M", gmtime())
    archivename = blendbasename + '_' + raw_time_stamp + '.' + extension

    return os.path.join(blenddir, archivename), blendname
