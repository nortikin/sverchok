# -*- coding: utf-8 -*-
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
from sverchok.ui.nodeview_rclick_menu import get_output_sockets_map
from sverchok.utils.sv_node_utils import frame_adjust

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}

def similar_sockets(node_out, node_in, term):
    socket_out, socket_in = -1, -1

    for i, s in enumerate(node_out.outputs):
        if s.hide_safe:
            continue
        if term in s.name.casefold().replace(' ', ''):
            socket_out = i
            break
    for i, s in enumerate(node_in.inputs):
        if s.hide_safe:
            continue
        if term in s.name.casefold().replace(' ', ''):
            socket_in = i
            break
    return socket_out, socket_in

def verts_edges_faces_connector(operator, context):
    space = context.space_data
    node_tree = space.node_tree

    links = node_tree.links
    selected_nodes = context.selected_nodes

    if not selected_nodes:
        operator.report({"ERROR_INVALID_INPUT"}, 'No selected nodes to join')
        return  {'CANCELLED'}

    previous_state = node_tree.sv_process
    node_tree.sv_process = False
    # find out which sockets to connect
    sorted_nodes = sorted(selected_nodes, key=lambda n: n.location.x, reverse=False)

    for node_out, node_in in zip(sorted_nodes[:-1], sorted_nodes[1:]):
        socket_out, socket_in = similar_sockets(node_out, node_in, 've')
        if socket_out != -1 and socket_in != -1:
            links.new(node_out.outputs[socket_out], node_in.inputs[socket_in])

        socket_out, socket_in = similar_sockets(node_out, node_in, 'edg')
        if socket_out != -1 and socket_in != -1:
            links.new(node_out.outputs[socket_out], node_in.inputs[socket_in])

        socket_out, socket_in = similar_sockets(node_out, node_in, 'pol')
        if socket_out != -1 and socket_in != -1:
            links.new(node_out.outputs[socket_out], node_in.inputs[socket_in])
        else:
            socket_out2, socket_in2 = similar_sockets(node_out, node_in, 'face')

            if max(socket_out, socket_out2) != -1 and max(socket_in, socket_in2) != -1:
                faces_out = socket_out2 if socket_out == -1 else socket_out
                faces_in = socket_in2 if socket_in == -1 else socket_in
                links.new(node_out.outputs[faces_out], node_in.inputs[faces_in])

        socket_out, socket_in = similar_sockets(node_out, node_in, 'facedata')
        if socket_out != -1 and socket_in != -1:
            links.new(node_out.outputs[socket_out], node_in.inputs[socket_in])

        node_tree.sv_process = previous_state
        node_tree.update()


class SvNodeConnectorOperator(bpy.types.Operator):
    """Vectors Edges Faces Node Connector"""
    bl_idname = "node.sv_node_connector"
    bl_label = "Sverchok Node Connector"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):

        space = context.space_data
        tree_type = space.tree_type
        return space.type == 'NODE_EDITOR' and tree_type in sv_tree_types

    def execute(self, context):
        verts_edges_faces_connector(self, context)
        return {'FINISHED'}



def register():
    bpy.utils.register_class(SvNodeConnectorOperator)


def unregister():
    bpy.utils.unregister_class(SvNodeConnectorOperator)
