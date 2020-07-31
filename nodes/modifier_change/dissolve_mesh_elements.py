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
from sverchok.data_structure import updateNode
from sverchok.utils.handling_sockets import SocketProperties, NodeInputs


node_inputs = NodeInputs([
    SocketProperties('Verts', 'SvVerticesSocket', deep_copy=False, vectorize=False),
    SocketProperties('Edges', 'SvStringsSocket', deep_copy=False, vectorize=False),
    SocketProperties('Faces', 'SvStringsSocket', deep_copy=False, vectorize=False),
    SocketProperties('Mask', 'SvStringsSocket', deep_copy=False),
    SocketProperties('Verts data', 'SvStringsSocket', deep_copy=False),
    SocketProperties('Edges data', 'SvStringsSocket', deep_copy=False),
    SocketProperties('Faces data', 'SvStringsSocket', deep_copy=False)])

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

    proportional: bpy.props.BoolProperty(
        name="Proportional",
        description="If checked, then number of points at each face is proportional to the area of the face",
        default=True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        pass

    def sv_init(self, context):
        node_inputs.add_sockets(self)

        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Mask')
        self.outputs.new('SvStringsSocket', 'Verts data')
        self.outputs.new('SvStringsSocket', 'Edges data')
        self.outputs.new('SvStringsSocket', 'Face data')

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
