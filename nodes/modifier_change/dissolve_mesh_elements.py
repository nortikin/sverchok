# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handling_nodes import SocketProperties, SockTypes, NodeProperties, WrapNode, initialize_node


modes = [(n, n, '', ic, i) for i, (n, ic) in
         enumerate(zip(('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]

node = WrapNode()

node.props.mode = NodeProperties(bpy_props=bpy.props.EnumProperty(items=modes))
node.props.mask_mode = NodeProperties(bpy_props= bpy.props.EnumProperty(items=modes))
node.props.use_face_split = NodeProperties(bpy_props=bpy.props.BoolProperty())
node.props.use_boundary_tear = NodeProperties(bpy_props=bpy.props.BoolProperty())
node.props.use_verts = NodeProperties(bpy_props=bpy.props.BoolProperty())

node.inputs.verts = SocketProperties('Verts', SockTypes.VERTICES, deep_copy=False, vectorize=False, mandatory=True)
node.inputs.edges = SocketProperties('Edges', SockTypes.STRINGS, deep_copy=False, vectorize=False)
node.inputs.faces = SocketProperties('Faces', SockTypes.STRINGS, deep_copy=False, vectorize=False)
node.inputs.mask = SocketProperties('Mask', SockTypes.STRINGS, deep_copy=False,
                                    custom_draw='draw_mask_socket_modes', mandatory=True)
node.inputs.verts_data = SocketProperties('Verts data', SockTypes.STRINGS, deep_copy=False)
node.inputs.edges_data = SocketProperties('Edges data', SockTypes.STRINGS, deep_copy=False)
node.inputs.faces_data = SocketProperties('Faces data', SockTypes.STRINGS, deep_copy=False)

node.outputs.verts = SocketProperties('Verts', SockTypes.VERTICES)
node.outputs.edges = SocketProperties('Edges', SockTypes.STRINGS)
node.outputs.faces = SocketProperties('Faces', SockTypes.STRINGS)
node.outputs.mask = SocketProperties('Mask', SockTypes.STRINGS)
node.outputs.verts_data = SocketProperties('Verts data', SockTypes.STRINGS)
node.outputs.edges_data = SocketProperties('Edges data', SockTypes.STRINGS)
node.outputs.faces_data = SocketProperties('Faces_data', SockTypes.STRINGS)


@initialize_node(node)
class SvDissolveMeshElements(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: dissolve delete remove

    dissolve points edges or polygons of given mesh
    """
    bl_idname = 'SvDissolveMeshElements'
    bl_label = 'Dissolve mesh elements'
    sv_icon = 'SV_RANDOM_NUM_GEN'

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'use_face_split', toggle=1)
        layout.prop(self, 'use_boundary_tear', toggle=1)
        layout.prop(self, 'use_verts', toggle=1)

    def draw_mask_socket_modes(self, socket, context, layout):
        layout.label(text='Mask')
        layout.prop(self, 'mask_mode', expand=True, text='')

    def process(self):
        return 
        out = [node_process(inputs) for inputs in node_inputs.get_data(self)]
        node_outputs.set_data(self, out)


def register():
    bpy.utils.register_class(SvDissolveMeshElements)


def unregister():
    bpy.utils.unregister_class(SvDissolveMeshElements)
