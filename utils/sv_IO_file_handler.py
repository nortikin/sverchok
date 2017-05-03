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

import json
import os
import re
import zipfile
import traceback


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
            print('zip contains no files ending with .json')
            return

        print(exported_name, '<')
        fp = jfile.open(exported_name, 'r')
        m = fp.read().decode()
        return json.loads(m)


def write_json(layout_dict, destination_path):
    m = json.dumps(layout_dict, sort_keys=True, indent=2)
    # optional post processing step
    post_processing = False
    if post_processing:
        flatten = lambda match: r' {}'.format(match.group(1), m)
        m = re.sub(r'\s\s+(\d+)', flatten, m)

    with open(destination_path, 'w') as node_tree:
        node_tree.writelines(m)
