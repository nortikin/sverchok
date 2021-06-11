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

import re
import bpy
import ast


UNPARSABLE = None, None, None, None

sock_dict = {
    'v': 'SvVerticesSocket',
    's': 'SvStringsSocket',
    'm': 'SvMatrixSocket',
    'o': 'SvObjectSocket',
    'C': 'SvCurveSocket',
    'S': 'SvSurfaceSocket',
    'So': 'SvSolidSocket',
    'SF': 'SvScalarFieldSocket',
    'VF': 'SvVectorFieldSocket',
    'FP': 'SvFilePathSocket',
}


def set_autocolor(node, use_me, color_me):
    node.use_custom_color = use_me
    node.color = color_me


def processed(str_in):
    _, b = str_in.split('=')
    return ast.literal_eval(b)


def parse_socket_line(line):
    lsp = line.strip().split()
    if not len(lsp) in {3, 5}:
        print(line, 'is malformed')
        return UNPARSABLE
    else:
        socket_type = sock_dict.get(lsp[2])
        socket_name = lsp[1]
        if not socket_type:
            return UNPARSABLE
        elif len(lsp) == 3:
            return socket_type, socket_name, None, None
        else:
            default = processed(lsp[3])
            nested = processed(lsp[4])
            return socket_type, socket_name, default, nested

def parse_required_socket_line(node, line)
    ... # node.info()


def extract_directive_as_multiline_string(lines):
    pattern = """
    \"{3}(.*?)\"{3}   # double quote enclosure
    |                 # or
    \'{3}(.*?)\'{3}   # single quote enclosure
    """

    try:
        p = re.compile(pattern, re.MULTILINE|re.DOTALL|re.VERBOSE)
        g = p.search(lines.strip())

        matches = g.groups()
        for idx, m in enumerate(matches):
            if m:
                return m
    except Exception as err:
        print("SNLITE ERROR:", err)
        return 

    return

def print_node_script(node):
    err_message = 'failed to find a directive in this script: SNLITE Error 1 (see docs for more info)'
    print(node.script_name, err_message)
    print("start --->")
    print(node.script_str)
    print("<--- end")


def parse_sockets(node):

    if hasattr(node, 'inject_params'):
        node.inject_params = False

    snlite_info = {
        'inputs': [], 'outputs': [],
        'snlite_ui': [], 'includes': {},
        'custom_enum': [], 'custom_enum_2': [],
        'callbacks': {}, 'inputs_required': [],
    }

    directive = extract_directive_as_multiline_string(node.script_str)
    if not directive:
        print_node_script(node)
        return snlite_info

    for line in directive.split('\n'):
        L = line.strip()

        if L.startswith('in ') or L.startswith('out '):
            socket_dir = L.split(' ')[0] + 'puts'
            snlite_info[socket_dir].append(parse_socket_line(node, L))

        if L.startswith('>in '):
            # one or more inputs can be required before processing/showing errors
            snlite_info['inputs'].append(parse_required_socket_line(L))

        elif L.startswith('inject'):
            if hasattr(node, 'inject_params'):
                node.inject_params = True

        elif L.startswith('enum ='):
            snlite_info['custom_enum'] = L[6:].strip().split(' ')

        elif L.startswith('enum2 ='):
            snlite_info['custom_enum_2'] = L[7:].strip().split(' ')

        elif L.startswith('include <') and L.endswith('>'):
            filename = L[9:-1]
            file = bpy.data.texts.get(filename)
            if file:
                snlite_info['includes'][filename] = file.as_string()

        elif L in {'fh', 'filehandler'}:
            snlite_info['display_file_handler'] = True

    return snlite_info


def are_matched(sock_, socket_description):
    return (sock_.bl_idname, sock_.name) == socket_description[:2]
