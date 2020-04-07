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

from sverchok.utils.sv_node_utils import nodes_bounding_box


def math_macros(context, operator, term, nodes, links):
    '''Macro that places a math node and connects the selected nodes to it'''

    selected_nodes = context.selected_nodes
    if not selected_nodes:
        operator.report({"ERROR_INVALID_INPUT"}, 'No selected nodes to use')
        return  False

    selected_nodes = selected_nodes[:2]
    if any(len(node.outputs) < 1 for node in selected_nodes):
        operator.report({"ERROR_INVALID_INPUT"}, 'No valid nodes to use')
        return  False

    # get bounding box of all selected nodes
    minx, maxx, miny, maxy = nodes_bounding_box(selected_nodes)
    # find out which sockets to connect
    operator = term.replace("math", "")
    sorted_nodes = sorted(selected_nodes, key=lambda n: n.location.y, reverse=True)

    is_vector = all(node.outputs[0].bl_idname == "SvVerticesSocket" for node in sorted_nodes)

    if operator == 'MUL':
        if is_vector:
            math_node = nodes.new('SvVectorMathNodeMK3')
            math_node.current_op = 'CROSS'
        else:

            if (sorted_nodes[0].outputs[0].bl_idname == "SvVerticesSocket"):
                math_node = nodes.new('SvVectorMathNodeMK3')
                math_node.current_op = 'SCALAR'

            elif len(sorted_nodes) > 1 and (sorted_nodes[1].outputs[0].bl_idname == "SvVerticesSocket"):
                math_node = nodes.new('SvVectorMathNodeMK3')
                math_node.current_op = 'SCALAR'
                sorted_nodes = [sorted_nodes[1], sorted_nodes[0]]

            else:
                math_node = nodes.new('SvScalarMathNodeMK4')
                math_node.current_op = operator
    else:
        if is_vector:
            math_node = nodes.new('SvVectorMathNodeMK3')
            math_node.current_op = operator
        else:
            math_node = nodes.new('SvScalarMathNodeMK4')
            math_node.current_op = operator

    math_node.location = maxx + 100, maxy
    # link the nodes to Math node
    for i, node in enumerate(sorted_nodes):
        links.new(node.outputs[0], math_node.inputs[i])

    if is_vector:
        viewer_node = nodes.new("SvVDExperimental")
        viewer_node.location = math_node.location.x + math_node.width + 100, maxy

        # link the output math node to the ViewerDraw node
        links.new(math_node.outputs[0], viewer_node.inputs[0])

    return True
