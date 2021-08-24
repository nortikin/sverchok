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


def parse_socket_line(node, line):
    lsp = line.strip().split()
    if not len(lsp) in {3, 5}:
        self.info(f"{line} -> is malformed")
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

def parse_required_socket_line(node, line):
    # receives a line like
    # required input sockets do not accept defaults or nested info, what would be the point?
    # >in socketname sockettype
    lsp = line.strip().split()
    if len(lsp) == 3:
        socket_type = sock_dict.get(lsp[2])
        socket_name = lsp[1]
        if not socket_type:
            return UNPARSABLE
        return socket_type, socket_name, None, None

    self.info(f"{line} -> is malformed")
    return UNPARSABLE


def parse_extended_socket_line(node, line):
    """
    returns socket_info: 
        socket_type, socket_name, default, nested  (display name)
    """
    socket_info = [None, None, None, None, None]

    pattern = """
    \+in\s+              # valid for inputs
    (\w+)\s+             # list name to use
    (\w+)\s+             # socket type
    d=(.+)\s+            # default value
    n=(\d)               # nested value
    (.+name="(.+)")?     # optional socket label
    """

    try:
        p = re.compile(pattern, re.VERBOSE)
        g = p.search(line.strip())

        matches = g.groups()
        for idx, m in enumerate(matches):
            if m:
                if idx == 0:
                    # the socket name used by user passing info to lists.
                    socket_info[1] = m
                elif idx == 1:
                    # remap to the bl_idname of a sockettype
                    socket_info[0] = sock_dict.get(m.strip())
                elif idx in (2, 3): 
                    # defaults or nested, are still a string at this point
                    socket_info[idx] = ast.literal_eval(m)
                elif idx == 4:
                    # if 4 is a match, then 5 contains the desired label
                    socket_info[idx] = matches[5]
                    break

        # print(f"socket_info:{socket_info}")
        return socket_info

    except Exception as err:
        print("SNLITE ERROR:", err)



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
            input_info = parse_required_socket_line(node, L)
            snlite_info['inputs'].append(input_info)
            snlite_info['inputs_required'].append(input_info[1])

        if L.startswith('+in '):
            # this is extended :regex: parsing of socket info line.
            input_info = parse_extended_socket_line(node, L)
            snlite_info['inputs'].append(input_info)

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
