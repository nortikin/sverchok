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
import json

def pack_monad(node, node_items, groups_dict, create_dict_of_tree):
    """
    we can not rely on .items() to be present for various reasons, so we must gather
    something to fill .params with - due to dynamic nature of node.
    """

    name = node.monad.name
    node_items['monad'] = name
    node_items['cls_dict'] = {}
    node_items['cls_dict']['cls_bl_idname'] = node.bl_idname

    for template in ['input_template', 'output_template']:
        node_items['cls_dict'][template] = getattr(node, template)

    if name not in groups_dict:
        group_ng = bpy.data.node_groups[name]
        group_dict = create_dict_of_tree(group_ng)
        group_dict['bl_idname'] = group_ng.bl_idname
        group_dict['cls_bl_idname'] = node.bl_idname
        group_json = json.dumps(group_dict)
        groups_dict[name] = group_json

    # [['Y', 'StringsSocket', {'prop_name': 'y'}], [....
    for idx, (socket_name, socket_type, prop_dict) in enumerate(node.input_template):
        socket = node.inputs[idx]
        if not socket.is_linked and prop_dict:

            prop_name = prop_dict['prop_name']
            v = getattr(node, prop_name)
            if not isinstance(v, (float, int, str)):
                v = v[:]

            node_items[prop_name] = v


def unpack_monad(nodes, node_ref):
    params = node_ref.get('params')
    if params:

        monad_name = params.get('monad')
        monad = bpy.data.node_groups[monad_name]
        cls_ref = monad.update_cls()
        node = nodes.new(cls_ref.bl_idname)

        cls_dict = params.get('cls_dict')
        node.input_template = cls_dict['input_template']
        node.output_template = cls_dict['output_template']

        # this should maybe be a function of the node, 
        # so we could call ` node.set_corresponding_renames '
        for idx, socket in enumerate(node.inputs):
            other_socket = monad.nodes['Group Inputs Exp'].outputs[idx]
            socket.name = other_socket.name
            if other_socket.prop_name:
                socket.prop_name = other_socket.prop_name

        for idx, socket in enumerate(node.outputs):
            other_socket = monad.nodes['Group Outputs Exp'].inputs[idx]
            socket.name = other_socket.name

        return node
    else:
        print('no parameters found! .json might be broken')                
