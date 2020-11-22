# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from collections import defaultdict

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat, rotate_list, repeat_last_for_length, updateNode

import sverchok.utils.handling_nodes as hn


node = hn.WrapNode()

node.props.factor = hn.NodeProperties(bpy.props.FloatProperty(
        name="Factor", description="Split Factor",
        default=0.5, min=0.0, soft_min=0.0, max=1.0))
node.props.mirror = hn.NodeProperties(bpy.props.BoolProperty(
        name="Mirror", description="Mirror split",
        default=False, update=updateNode))

node.inputs.verts = hn.SocketProperties(
    name='Vertices', socket_type=hn.SockTypes.VERTICES,
    deep_copy=False, vectorize=False, mandatory=True)
node.inputs.edges = hn.SocketProperties(
    name='Edges', socket_type=hn.SockTypes.STRINGS,
    deep_copy=True, vectorize=False, mandatory=True)
node.inputs.faces = hn.SocketProperties(
    name='Faces', socket_type=hn.SockTypes.STRINGS,
    deep_copy=True, vectorize=False, mandatory=False, default=[[[]]])
node.inputs.mask = hn.SocketProperties(
    name='EdgeMask', socket_type=hn.SockTypes.STRINGS,
    deep_copy=False, vectorize=False, mandatory=False, default=[[True]])
node.inputs.factors = hn.SocketProperties(
    name='Factor', socket_type=hn.SockTypes.STRINGS, 
    prop=node.props.factor, deep_copy=False)

node.outputs.verts = hn.SocketProperties(name='Vertices', socket_type=hn.SockTypes.VERTICES)
node.outputs.edges = hn.SocketProperties(name='Edges', socket_type=hn.SockTypes.STRINGS)
node.outputs.faces = hn.SocketProperties(name='Faces', socket_type=hn.SockTypes.STRINGS)

@hn.initialize_node(node)
class SvSplitEdgesMk2Node(bpy.types.Node, SverchCustomTreeNode):
    ''' Split Edges '''
    bl_idname = 'SvSplitEdgesMk2Node'
    bl_label = 'Split Edges'
    sv_icon = 'SV_SPLIT_EDGES'
    # sv_icon = 'SV_EDGE_SPLIT'

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mirror')

    def process(self):

        new_faces = list(node.inputs.faces)
        faces_per_edge = defaultdict(list)
        for face_idx, face in enumerate(new_faces):
            for i,j in zip(face, rotate_list(face)):
                faces_per_edge[(i,j)].append((i, False, face_idx))
                faces_per_edge[(j,i)].append((j, True, face_idx))

        def insert_after(face, vert_idx, new_vert_idx):
            idx = face.index(vert_idx)
            face.insert(idx+1, new_vert_idx)

        def insert_before(face, vert_idx, new_vert_idx):
            idx = face.index(vert_idx)
            face.insert(idx, new_vert_idx)

        # sanitize the input
        input_f = list(map(lambda factor: min(1, max(0, factor)), node.inputs.factors))

        mask = repeat_last_for_length(node.inputs.mask, len(node.inputs.edges))
        params = match_long_repeat([node.inputs.edges, mask, input_f])

        offset = len(node.inputs.verts)
        new_verts = list(node.inputs.verts)
        new_edges = []
        i = 0
        for edge, ok, factor in zip(*params):
            if not ok:
                continue

            i0 = edge[0]
            i1 = edge[1]
            v0 = node.inputs.verts[i0]
            v1 = node.inputs.verts[i1]

            if node.props.mirror:
                factor = factor / 2

                vx = v0[0] * (1 - factor) + v1[0] * factor
                vy = v0[1] * (1 - factor) + v1[1] * factor
                vz = v0[2] * (1 - factor) + v1[2] * factor
                va = [vx, vy, vz]
                new_verts.append(va)

                vx = v0[0] * factor + v1[0] * (1 - factor)
                vy = v0[1] * factor + v1[1] * (1 - factor)
                vz = v0[2] * factor + v1[2] * (1 - factor)
                vb = [vx, vy, vz]
                new_verts.append(vb)

                new_edges.append([i0, offset + i])  # v0 - va
                new_edges.append([offset + i, offset + i + 1])  # va - vb
                new_edges.append([offset + i + 1, i1])  # vb - v1

                for vert_idx, before, face_idx in faces_per_edge[tuple(edge)]:
                    if before:
                        insert_before(new_faces[face_idx], vert_idx, offset+i)
                        insert_before(new_faces[face_idx], offset+i, offset+i+1)
                    else:
                        insert_after(new_faces[face_idx], vert_idx, offset+i)
                        insert_after(new_faces[face_idx], offset+i, offset+i+1)

                i = i + 2

            else:
                vx = v0[0] * (1 - factor) + v1[0] * factor
                vy = v0[1] * (1 - factor) + v1[1] * factor
                vz = v0[2] * (1 - factor) + v1[2] * factor
                va = [vx, vy, vz]
                new_verts.append(va)

                new_edges.append([i0, offset + i])  # v0 - va
                new_edges.append([offset + i, i1])  # va - v1

                for vert_idx, before, face_idx in faces_per_edge[tuple(edge)]:
                    if before:
                        insert_before(new_faces[face_idx], vert_idx, offset+i)
                    else:
                        insert_after(new_faces[face_idx], vert_idx, offset+i)

                i = i + 1

        node.outputs.verts = new_verts
        node.outputs.edges = new_edges
        node.outputs.faces = new_faces

