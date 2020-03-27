# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from typing import NamedTuple, Any, List, Tuple
import random
from itertools import chain, repeat

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon, area_tri

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SocketProperties(NamedTuple):
    name: str
    socket_type: str
    prop_name: str = ''
    deep_copy: bool = True
    vectorize: bool = True
    default: Any = object()


class InputData(NamedTuple):
    index: int
    verts: list
    faces: list
    face_weight: list
    number: list
    seed: list


INPUT_CONFIG = [
    SocketProperties('Verts', 'SvVerticesSocket', deep_copy=False, vectorize=False),
    SocketProperties('Faces', 'SvStringsSocket', deep_copy=False, vectorize=False),
    SocketProperties('Face weight', 'SvStringsSocket', deep_copy=False, default=[[]]),
    SocketProperties('Number', 'SvStringsSocket', prop_name='points_number', deep_copy=False),
    SocketProperties('Seed', 'SvStringsSocket', prop_name='seed', deep_copy=False)]


class NodeProperties(NamedTuple):
    proportional: bool


def node_process(inputs: InputData, properties: NodeProperties):
    me = TriangulatedMesh([Vector(co) for co in inputs.verts], inputs.faces)
    if properties.proportional:
        me.use_even_points_distribution()
    if inputs.face_weight:
        me.set_custom_face_weights(inputs.face_weight)
    return me.generate_random_points(inputs.number[0], inputs.seed[0])  # todo [0] <-- ?!


class TriangulatedMesh:
    def __init__(self, verts: List[Vector], faces: List[List[int]]):
        self._verts = verts
        self._faces = faces
        self._face_weights = None

        self._tri_faces = []
        self._tri_face_areas = []
        self._old_face_indexes_per_tri = []

        self._triangulate()

    def use_even_points_distribution(self, even=True):
        self._face_weights = self.tri_face_areas if even else None

    def set_custom_face_weights(self, custom_weights):
        weights_per_tri = self._face_attrs_to_tri_face_attrs(custom_weights)
        if self._face_weights:
            self._face_weights *= weights_per_tri  # can be troubles if set custom weights several times
        else:
            self._face_weights = weights_per_tri

    def generate_random_points(self, random_points_total: int, seed: int) -> Tuple[list, list]:
        random.seed(seed)
        points_total_per_face = self._distribute_points(random_points_total)
        random_points = []
        old_face_indexes_per_point = []
        for tri_face, face_index, points_total in zip(self._tri_faces,
                                                      self._old_face_indexes_per_tri,
                                                      points_total_per_face):
            tri_random_points = self._get_random_vectors_on_tri(*[self._verts[i] for i in tri_face], points_total)
            random_points.extend(tri_random_points)
            old_face_indexes_per_point.extend([face_index for _ in range(len(tri_random_points))])
        return random_points, old_face_indexes_per_point

    @property
    def tri_face_areas(self):
        if not self._tri_face_areas:
            self._tri_face_areas = [area_tri(*[self._verts[i] for i in f]) for f in self._tri_faces]
        return self._tri_face_areas

    def _distribute_points(self, random_points_total: int) -> List[int]:
        # generate list of numbers which mean how many points should be created on face
        points_total_per_face = [0 for _ in range(len(self._tri_faces))]
        chosen_faces = random.choices(range(len(self._tri_faces)), self._face_weights, k=random_points_total)
        for i in chosen_faces:
            points_total_per_face[i] += 1
        return points_total_per_face

    def _triangulate(self):
        # generate list of triangle faces and list of indexes which points to initial faces for each new triangle
        for i, f in enumerate(self._faces):
            face_verts = [[self._verts[i] for i in f]]
            # [[v1,v2,v3,v4]] - face_verts
            for tri_face in tessellate_polygon(face_verts):
                self._tri_faces.append([f[itf] for itf in tri_face])
                self._old_face_indexes_per_tri.append(i)

    @staticmethod
    def _get_random_vectors_on_tri(v1, v2, v3, number):
        # returns random vertices for given triangle
        out = []
        for _ in range(number):
            u1 = random.random()
            u2 = random.random()
            u1 = u1 if u1 + u2 <= 1 else 1 - u1
            u2 = u2 if u1 + u2 <= 1 else 1 - u2
            side1 = v2 - v1
            side2 = v3 - v1
            out.append(v1 + side1 * u1 + side2 * u2)
        return out

    def _face_attrs_to_tri_face_attrs(self, values):
        return [values[i] if i <= len(values) - 1 else values[len(values) - 1] for i in self._old_face_indexes_per_tri]


class SvRandomPointsOnMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: random points vertices

    distribute points on given mesh
    points are created evenly according area faces
    based on Blender function - tessellate_polygon
    """
    bl_idname = 'SvRandomPointsOnMesh'
    bl_label = 'Random points on mesh'
    sv_icon = 'SV_RANDOM_NUM_GEN'

    points_number: bpy.props.IntProperty(name='Number', default=10, description="Number of random points",
                                         update=updateNode)
    seed: bpy.props.IntProperty(name='Seed', update=updateNode)

    proportional: bpy.props.BoolProperty(
            name="Proportional",
            description="If checked, then number of points at each face is proportional to the area of the face",
            default=True,
            update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "proportional", toggle=True)

    def sv_init(self, context):
        [self.inputs.new(p.name, p.socket_type) for p in INPUT_CONFIG]
        [setattr(s, 'prop_name', p.prop_name) for s, p in zip(self.inputs, INPUT_CONFIG)]

        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Face index')

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
    bpy.utils.register_class(SvRandomPointsOnMesh)


def unregister():
    bpy.utils.unregister_class(SvRandomPointsOnMesh)
