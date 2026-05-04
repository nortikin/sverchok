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

from sverchok.utils.sv_node_utils import framed_nodes_bounding_box as bounding_box
from sverchok.utils.sv_node_utils import are_nodes_in_same_frame


def streighten_macros(context, operator, term, nodes, links):
    '''Macros that places nodes to separate polyline curve,
       that preserve corners from smoothing'''

    selected_nodes = context.selected_nodes

    if not selected_nodes:
        operator.report({"ERROR_INVALID_INPUT"}, 'No selected nodes to straight')
        return

    tree = nodes[0].id_data

    framed = are_nodes_in_same_frame(selected_nodes)

    try:
        # get bounding box of all selected nodes
        _, maxx, _, maxy = bounding_box(selected_nodes)


        sorted_nodes = sorted(selected_nodes, key=lambda n: n.location.y, reverse=True)
        # Create SvCurveDiscontinuityNode, SvSplitCurveNode nodes
        join_nodes=[]
        for i, s in enumerate(sorted_nodes):
            join_nodes.append(nodes.new('SvCurveDiscontinuityNode'))
            join_nodes.append(nodes.new('SvSplitCurveNode'))
            join_nodes.append(nodes.new("SvCurveViewerDrawNode"))

            join_nodes[i*3].location =  maxx + (180) * 1, s.location[1]
            join_nodes[i*3+1].location =  maxx + (180) * 2, s.location[1]
            join_nodes[i*3+2].location =  maxx + (180) * 3, s.location[1]
            join_nodes[i*3+2].resolution = 2

        # link the nodes to nodes
        for i, node in enumerate(sorted_nodes):
            links.new(node.outputs[0], join_nodes[i*3].inputs[0])
            links.new(node.outputs[0], join_nodes[i*3+1].inputs[0])
            links.new(join_nodes[i*3].outputs[2], join_nodes[i*3+1].inputs[2])
            links.new(join_nodes[i*3+1].outputs[0], join_nodes[i*3+2].inputs[0])

        operator.report({'INFO'}, 'Curves straightened')
    except Exception as err:
        operator.report({'ERROR'}, f'Nodes not straightened, error:\n {err}')
