# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
import bmesh

from sverchok.data_structure import updateNode
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handling_nodes import SocketProperties, SockTypes, NodeProperties, WrapNode, initialize_node
from sverchok.utils.sv_bmesh_utils import empty_bmesh, add_mesh_to_bmesh, mesh_indexes_from_bmesh

modes = [(n, n, '', ic, i) for i, (n, ic) in
         enumerate(zip(('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]

node = WrapNode()

node.props.mask_mode = NodeProperties(bpy_props=bpy.props.EnumProperty(items=modes, update=updateNode))
node.props.use_face_split: bool = NodeProperties(bpy_props=bpy.props.BoolProperty(update=updateNode))
node.props.use_boundary_tear: bool = NodeProperties(bpy_props=bpy.props.BoolProperty(update=updateNode))
node.props.use_verts: bool = NodeProperties(bpy_props=bpy.props.BoolProperty(update=updateNode))

node.inputs.verts = SocketProperties('Verts', SockTypes.VERTICES, deep_copy=False, vectorize=False, mandatory=True)
node.inputs.edges = SocketProperties('Edges', SockTypes.STRINGS, deep_copy=False, vectorize=False)
node.inputs.faces = SocketProperties('Faces', SockTypes.STRINGS, deep_copy=False, vectorize=False)
node.inputs.mask = SocketProperties('Mask', SockTypes.STRINGS, deep_copy=False,
                                    custom_draw='draw_mask_socket_modes', mandatory=True)

node.outputs.verts = SocketProperties('Verts', SockTypes.VERTICES)
node.outputs.edges = SocketProperties('Edges', SockTypes.STRINGS)
node.outputs.faces = SocketProperties('Faces', SockTypes.STRINGS)
node.outputs.verts_ind = SocketProperties('Verts ind', SockTypes.STRINGS)
node.outputs.edges_ind = SocketProperties('Edges ind', SockTypes.STRINGS)
node.outputs.faces_ind = SocketProperties('Face ind', SockTypes.STRINGS)
node.outputs.loop_ind = SocketProperties('Loop ind', SockTypes.STRINGS)


@initialize_node(node)
class SvDissolveMeshElements(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: dissolve delete remove

    dissolve points edges or polygons of given mesh
    """
    bl_idname = 'SvDissolveMeshElements'
    bl_label = 'Dissolve mesh elements'
    bl_icon = 'EXPERIMENTAL'

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'use_face_split', toggle=1)
        layout.prop(self, 'use_boundary_tear', toggle=1)
        layout.prop(self, 'use_verts', toggle=1)

    def draw_mask_socket_modes(self, socket, context, layout):
        layout.label(text='Mask')
        layout.prop(self, 'mask_mode', expand=True, text='')

    def process(self):
        with empty_bmesh() as bm:
            add_mesh_to_bmesh(bm, node.inputs.verts, node.inputs.edges, node.inputs.faces, 'sv_index')
            if node.props.mask_mode == 'Verts':
                bmesh.ops.dissolve_verts(bm,
                                         verts=[v for v, m in zip(bm.verts, node.inputs.mask) if m],
                                         use_face_split=node.props.use_face_split,
                                         use_boundary_tear=node.props.use_boundary_tear)
            elif node.props.mask_mode == 'Edges':
                bmesh.ops.dissolve_edges(bm,
                                         edges=[e for e, m in zip(bm.edges, node.inputs.mask) if m],
                                         use_verts=node.props.use_verts,
                                         use_face_split=node.props.use_face_split)
            elif node.props.mask_mode == 'Faces':
                bmesh.ops.dissolve_faces(bm,
                                         faces=[f for f, m in zip(bm.faces, node.inputs.mask) if m],
                                         use_verts=node.props.use_verts)
            v, e, f, vi, ei, fi, li = mesh_indexes_from_bmesh(bm, 'sv_index')
            node.outputs.verts, node.outputs.edges, node.outputs.faces = v, e, f
            node.outputs.verts_ind, node.outputs.edges_ind, node.outputs.faces_ind = vi, ei, fi
            node.outputs.loop_ind = li
