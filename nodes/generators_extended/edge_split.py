# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat

import sverchok.utils.handling_nodes as hn


node = hn.WrapNode()

node.props.factor = hn.NodeProperties(bpy.props.FloatProperty(
        name="Factor", description="Split Factor",
        default=0.5, min=0.0, soft_min=0.0, max=1.0))
node.props.mirror = hn.NodeProperties(bpy.props.BoolProperty(
        name="Mirror", description="Mirror split",
        default=False))

node.inputs.verts = hn.SocketProperties(
    name='Vertices', socket_type=hn.SockTypes.VERTICES,
    deep_copy=False, vectorize=False, mandatory=True)
node.inputs.edges = hn.SocketProperties(
    name='Edges', socket_type=hn.SockTypes.STRINGS,
    deep_copy=False, vectorize=False, mandatory=True)
node.inputs.factors = hn.SocketProperties(
    name='Factor', socket_type=hn.SockTypes.STRINGS, 
    prop=node.props.factor, deep_copy=False)

node.outputs.verts = hn.SocketProperties(name='Vertices', socket_type=hn.SockTypes.VERTICES)
node.outputs.edges = hn.SocketProperties(name='Edges', socket_type=hn.SockTypes.STRINGS)


@hn.initialize_node(node)
class SvSplitEdgesNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Split Edges '''
    bl_idname = 'SvSplitEdgesNode'
    bl_label = 'Split Edges'
    sv_icon = 'SV_SPLIT_EDGES'
    # sv_icon = 'SV_EDGE_SPLIT'

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mirror')

    def process(self):

        # sanitize the input
        input_f = list(map(lambda f: min(1, max(0, f)), node.inputs.factors))

        params = match_long_repeat([node.inputs.edges, input_f])

        offset = len(node.inputs.verts)
        new_verts = list(node.inputs.verts)
        new_edges = []
        i = 0
        for edge, f in zip(*params):
            i0 = edge[0]
            i1 = edge[1]
            v0 = node.inputs.verts[i0]
            v1 = node.inputs.verts[i1]

            if node.props.mirror:
                f = f / 2

                vx = v0[0] * (1 - f) + v1[0] * f
                vy = v0[1] * (1 - f) + v1[1] * f
                vz = v0[2] * (1 - f) + v1[2] * f
                va = [vx, vy, vz]
                new_verts.append(va)

                vx = v0[0] * f + v1[0] * (1 - f)
                vy = v0[1] * f + v1[1] * (1 - f)
                vz = v0[2] * f + v1[2] * (1 - f)
                vb = [vx, vy, vz]
                new_verts.append(vb)

                new_edges.append([i0, offset + i])  # v0 - va
                new_edges.append([offset + i, offset + i + 1])  # va - vb
                new_edges.append([offset + i + 1, i1])  # vb - v1
                i = i + 2

            else:
                vx = v0[0] * (1 - f) + v1[0] * f
                vy = v0[1] * (1 - f) + v1[1] * f
                vz = v0[2] * (1 - f) + v1[2] * f
                va = [vx, vy, vz]
                new_verts.append(va)

                new_edges.append([i0, offset + i])  # v0 - va
                new_edges.append([offset + i, i1])  # va - v1
                i = i + 1

        node.outputs.verts = new_verts
        node.outputs.edges = new_edges
