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


def join_macros(context, operator, term, nodes, links):
    '''Macro that places a list join nodes and connects the selected nodes to them'''

    selected_nodes = context.selected_nodes

    if not selected_nodes:
        operator.report({"ERROR_INVALID_INPUT"}, 'No selected nodes to join')
        return  {'CANCELLED'}

    # get bounding box of all selected nodes
    _, maxx, _, maxy = nodes_bounding_box(selected_nodes)

    # find out which sockets to connect
    socket_numbers = term.replace("join", "")
    if len(socket_numbers) == 1: # one socket
        socket_indices = [int(socket_numbers) - 1]
    else: # multiple sockets
        socket_indices = [int(n) - 1 for n in socket_numbers]

    # Create List Join nodes
    join_nodes=[]
    for i, s in enumerate(socket_indices):
        join_nodes.append(nodes.new('ListJoinNode'))
        join_nodes[i].location = maxx + 100, maxy - (180+(22*(len(selected_nodes)))) * i

    sorted_nodes = sorted(selected_nodes, key=lambda n: n.location.y, reverse=True)

    # link the nodes to ListJoin nodes
    for i, node in enumerate(sorted_nodes):
        for j, n in enumerate(socket_indices):
            if len(node.outputs) > n:
                links.new(node.outputs[n], join_nodes[j].inputs[i])

    if all(node.outputs[0].bl_idname == "SvVerticesSocket" for node in sorted_nodes):
        viewer_node = nodes.new("SvVDExperimental")
        viewer_node.location = join_nodes[0].location.x + join_nodes[0].width + 100, maxy

        # link the output switch node to the SvVDExperimental node
        links.new(join_nodes[0].outputs[0], viewer_node.inputs[0])
        if len(socket_indices) > 1:
            links.new(join_nodes[1].outputs[0], viewer_node.inputs[socket_indices[1]])
        if len(socket_indices) > 2:
            links.new(join_nodes[2].outputs[0], viewer_node.inputs[socket_indices[2]])

    return True
