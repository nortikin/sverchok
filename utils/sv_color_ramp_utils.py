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

NODE_TYPE =  'ShaderNodeValToRGB'

def get_valid_node(group_name, node_name, bl_idname):

    node_groups = bpy.data.node_groups
    # make sure the node-group is present
    group = node_groups.get(group_name)
    if not group:
        group = node_groups.new(group_name, 'ShaderNodeTree')
        info_frame = group.nodes.new('NodeFrame')
        info_frame.width = 500
        info_frame.location.y = 100
        info_frame.label = "Used by the Sverchok add-on. Do not delete any node"

    group.use_fake_user = True

    # make sure the color_rampNode we want to use is present too
    node = group.nodes.get(node_name)
    if not node:
        node = group.nodes.new(bl_idname)
        node.name = node_name

    return node


def get_valid_evaluate_function(group_name, node_name):
    '''
    Takes a material-group name and a Node name it expects to find.
    The node will be of type ShaderNodeValToRGB and this function
    will force its existence, then return the evaluate function.
    '''

    node = get_valid_node(group_name, node_name, NODE_TYPE)

    color_ramp = node.color_ramp
    try: color_ramp.evaluate(0.0)
    except: color_ramp.initialize()

    evaluate = lambda val: color_ramp.evaluate(val)
    return evaluate

def get_color_ramp(group_name, node_name):
    '''
    loads json data in new color_ramp node
    '''
    node_groups = bpy.data.node_groups
    group = node_groups.get(group_name)
    node = group.nodes.get(node_name)
    color_ramp = node.color_ramp
    color_mode = color_ramp.color_mode
    interpolation = color_ramp.interpolation
    hue_interpolation = color_ramp.hue_interpolation
    out_list = []
    elements = node.color_ramp.elements
    out_list = [(p.position, p.color[:]) for p in elements]

    return dict(
        group_name=group_name,
        bl_idname=NODE_TYPE,
        data=out_list,
        color_mode=color_mode,
        interpolation=interpolation,
        hue_interpolation=hue_interpolation)


def set_color_ramp(data_dict, color_ramp_node_name):
    '''
    stores color_ramp data into json
    '''

    group_name = data_dict['group_name']
    bl_id = data_dict['bl_idname']

    node = get_valid_node(group_name, color_ramp_node_name, bl_id)

    # node.mapping.initialize()
    data = data_dict['data']
    node.color_ramp.color_mode = data_dict['color_mode']
    node.color_ramp.interpolation = data_dict['interpolation']
    node.color_ramp.hue_interpolation = data_dict['hue_interpolation']
    elements = node.color_ramp.elements
    extra = len(data) - len(elements)
    _ = [elements.new(0.5) for _ in range(extra)]
    for pidx, (position, color) in enumerate(data):
        elements[pidx].position = position
        elements[pidx].color = color

    elements.update()
