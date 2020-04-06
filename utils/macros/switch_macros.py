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


def switch_macros(context, operator, term, nodes, links):
    '''Macro that places a switch node and connects the selected nodes to it'''

    selected_nodes = context.selected_nodes

    _, maxx, _, maxy = nodes_bounding_box(selected_nodes)

    switch_node = nodes.new('SvInputSwitchNodeMOD')
    switch_node.location = maxx + 100, maxy

    # find out which sockets to connect
    socket_numbers = term.replace("switch", "")

    if len(socket_numbers) == 1:
        socket_indices = [0]
    else:
        socket_indices = [int(n) - 1 for n in socket_numbers]

    switch_node.num_sockets_per_set = len(socket_indices)
    sorted_nodes = sorted(selected_nodes, key=lambda n: n.location.y, reverse=True)

    # link the nodes to InputSwitch node
    get_indices_for_groupnum = switch_node.get_local_function("get_indices_for_groupnum")

    for i, node in enumerate(sorted_nodes):
        destination_indices = get_indices_for_groupnum(switch_node.node_state, i)
        for j, n in enumerate(socket_indices):
            remapped_index = destination_indices[j]
            links.new(node.outputs[n], switch_node.inputs[remapped_index])

    if all(node.outputs[0].bl_idname == "SvVerticesSocket" for node in sorted_nodes):
        viewer_node = nodes.new("SvVDExperimental")
        viewer_node.location = switch_node.location.x + switch_node.width + 100, maxy

        # link the input switch node to the ViewerDraw node
        for n, i in enumerate(socket_indices):
            links.new(switch_node.outputs[n], viewer_node.inputs[i])

        switch_node.process_node(context)
