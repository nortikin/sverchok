# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from typing import NamedTuple, Any, List, Tuple
from itertools import chain, repeat

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handling_nodes import SocketProperties, NodeInputs, NodeProperties, NodeOutputs


node_props = NodeProperties()
node_props.mode = bpy.props.EnumProperty(items=[(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))])
node_props.mask_mode = bpy.props.EnumProperty(items=[(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))])
node_props.use_face_split = bpy.props.BoolProperty()
node_props.use_boundary_tear = bpy.props.BoolProperty()
node_props.use_verts = bpy.props.BoolProperty()


node_inputs = NodeInputs()
node_inputs.verts = SocketProperties('Verts', 'SvVerticesSocket', deep_copy=False, vectorize=False)
node_inputs.edges = SocketProperties('Edges', 'SvStringsSocket', deep_copy=False, vectorize=False)
node_inputs.faces = SocketProperties('Faces', 'SvStringsSocket', deep_copy=False, vectorize=False)
node_inputs.mask = SocketProperties('Mask', 'SvStringsSocket', deep_copy=False, prop_name='mask_mode',
                                    custom_draw='draw_mask_socket_modes')
node_inputs.verts_data = SocketProperties('Verts data', 'SvStringsSocket', deep_copy=False)
node_inputs.edges_data = SocketProperties('Edges data', 'SvStringsSocket', deep_copy=False)
node_inputs.faces_data = SocketProperties('Faces data', 'SvStringsSocket', deep_copy=False)


node_outputs = NodeOutputs()
node_outputs.verts = SocketProperties('Verts', 'SvVerticesSocket')
node_outputs.edges = SocketProperties('Edges', 'SvStringsSocket')
node_outputs.faces = SocketProperties('Faces', 'SvStringsSocket')
node_outputs.mask = SocketProperties('Mask', 'SvStringsSocket')
node_outputs.verts_data = SocketProperties('Verts data', 'SvStringsSocket')
node_outputs.edges_data = SocketProperties('Edges data', 'SvStringsSocket')
node_outputs.faces_data = SocketProperties('Faces_data', 'SvStringsSocket')

# def node_process(inputs: InputData, properties: NodeProperties):
#     me = TriangulatedMesh([Vector(co) for co in inputs.verts], inputs.faces)
#     if properties.proportional:
#         me.use_even_points_distribution()
#     if inputs.face_weight:
#         me.set_custom_face_weights(inputs.face_weight)
#     return me.generate_random_points(inputs.number[0], inputs.seed[0])  # todo [0] <-- ?!


class SvDissolveMeshElements(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: dissolve delete remove

    dissolve points edges or polygons of given mesh
    """
    bl_idname = 'SvDissolveMeshElements'
    bl_label = 'Dissolve mesh elements'
    sv_icon = 'SV_RANDOM_NUM_GEN'

    _: bool  # for crating annotation dict
    node_props.add_properties(vars()['__annotations__'])

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'use_face_split', toggle=1)
        layout.prop(self, 'use_boundary_tear', toggle=1)
        layout.prop(self, 'use_verts', toggle=1)

    def draw_mask_socket_modes(self, socket, context, layout):
        layout.label(text='Mask')
        layout.prop(self, 'mask_mode', expand=True, text='')

    def sv_init(self, context):
        node_inputs.add_sockets(self)
        node_outputs.add_sockets(self)

    def process(self):
        if not all([self.inputs['Verts'].is_linked, self.inputs['Faces'].is_linked]):
            return

        props = NodeProperties(self.proportional)
        out = [node_process(inputs, props) for inputs in self.get_input_data_iterator(INPUT_CONFIG)]
        [s.sv_set(data) for s, data in zip(self.outputs, zip(*out))]

    def get_input_data_iterator(self, input_config: List[SocketProperties]):
        length_max = max([len(s.sv_get(default=p.default, deepcopy=False)) for s, p in zip(self.inputs, input_config)])
        socket_iterators = []
        for socket, props in zip(self.inputs, input_config):
            socket_data = socket.sv_get(deepcopy=props.deep_copy, default=props.default)
            if props.vectorize:
                socket_iterators.append(chain(socket_data, repeat(socket_data[-1])))
            else:
                socket_iterators.append(socket_data)
        return [InputData(*data) for data in zip(range(length_max), *socket_iterators)]


def register():
    bpy.utils.register_class(SvDissolveMeshElements)


def unregister():
    bpy.utils.unregister_class(SvDissolveMeshElements)
