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

    # make sure the CurveNode we want to use is present too
    node = group.nodes.get(node_name)
    if not node:
        node = group.nodes.new(bl_idname)
        node.name = node_name

    return node


def get_valid_evaluate_function_legacy(group_name, node_name):
    '''
    Working with Blende Verion < 2.82
    Takes a material-group name and a Node name it expects to find.
    The node will be of type ShaderNodeRGBCurve and this function
    will force its existence, then return the evaluate function for the last
    component of RGBA - allowing us to use this as a float modifier.
    '''

    node = get_valid_node(group_name, node_name, 'ShaderNodeRGBCurve')

    curve = node.mapping.curves[3]
    try: curve.evaluate(0.0)
    except: node.mapping.initialize()

    return curve.evaluate

def get_valid_curve(group_name, node_name):
    '''
    Takes a material-group name and a Node name it expects to find.
    The node will be of type ShaderNodeRGBCurve and this function
    will force its existence, then return curve for the last
    component of RGBA - allowing us to use this as a float modifier.
    '''

    node = get_valid_node(group_name, node_name, 'ShaderNodeRGBCurve')

    curve = node.mapping.curves[3]
    return curve

def get_valid_evaluate_function(group_name, node_name):
    '''
    Takes a material-group name and a Node name it expects to find.
    The node will be of type ShaderNodeRGBCurve and this function
    will force its existence, then return the evaluate function for the last
    component of RGBA - allowing us to use this as a float modifier.
    '''

    node = get_valid_node(group_name, node_name, 'ShaderNodeRGBCurve')

    curve = node.mapping.curves[3]
    try:  node.mapping.evaluate(curve, 0.0)
    except: node.mapping.initialize()

    evaluate = lambda val: node.mapping.evaluate(curve, val)
    return evaluate

def get_rgb_curve(group_name, node_name):
    '''
    ShaderNodeRGBCurve support only
    '''
    node_groups = bpy.data.node_groups
    group = node_groups.get(group_name)
    node = group.nodes.get(node_name)
    # m = bpy.data.materials.get(material_name)
    # node = m.node_tree.nodes.get(node_name)

    out_list = []
    for curve in node.mapping.curves:
        points = curve.points
        out_list.append([(p.handle_type, p.location[:]) for p in points])

    x = 'ShaderNodeRGBCurve'
    return dict(group_name=group_name, bl_idname=x, data=out_list)


def set_rgb_curve(data_dict, node_id):
    '''
    ShaderNodeRGBCurve support only
    '''

    group_name = data_dict['group_name']
    bl_id = data_dict['bl_idname']

    node = get_valid_node(group_name, 'RGB Curves'+node_id, bl_id)

    node.mapping.initialize()
    data = data_dict['data']
    for idx, curve in enumerate(node.mapping.curves):

        # add extra points, if needed
        extra = len(data[idx]) - len(curve.points)
        _ = [curve.points.new(0.5, 0.5) for _ in range(extra)]

        # set points to correspond with stored collection
        for pidx, (handle_type, location) in enumerate(data[idx]):
            curve.points[pidx].handle_type = handle_type
            curve.points[pidx].location = location
    node.mapping.update()
