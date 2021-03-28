# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from typing import NamedTuple, Any, List, Tuple
import random
from itertools import chain, repeat
import numpy as np

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon, area_tri

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, throttle_and_update_node
from sverchok.utils.bvh_tree import bvh_tree_from_polygons
from sverchok.utils.geom import calc_bounds
from sverchok.utils.sv_mesh_utils import point_inside_mesh

def np_calc_tris_areas(v_pols):
    perp = np.cross(v_pols[:, 1]- v_pols[:, 0], v_pols[:, 2]- v_pols[:, 0])/2
    return np.linalg.norm(perp, axis=1)/2

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
    mode: str
    all_triangles: bool
    implementation: str
    safe_check: bool
    out_np: tuple

MAX_ITERATIONS = 1000

def populate_mesh(verts, faces, count, seed, all_triangles, safe_check):

    bvh = bvh_tree_from_polygons(verts, faces, all_triangles=all_triangles, epsilon=0.0, safe_check=safe_check)
    np.random.seed(seed)
    x_min, x_max, y_min, y_max, z_min, z_max = calc_bounds(verts)
    low = np.array([x_min, y_min, z_min])
    high = np.array([x_max, y_max, z_max])
    result = []
    done = 0
    iterations = 0
    while True:
        if iterations > MAX_ITERATIONS:
            raise Exception("Iterations limit is reached")
        max_pts = max(count, count-done)
        points = np.random.uniform(low, high, size=(max_pts, 3)).tolist()
        points = [p for p in points if point_inside_mesh(bvh, p)]
        n = len(points)
        result.extend(points)
        done += n
        iterations += 1
        if done >= count:
            break
    return result, []

def node_process(inputs: InputData, properties: NodeProperties):
    if properties.mode == 'SURFACE':
        me = TriangulatedMesh(inputs.verts, inputs.faces, properties.all_triangles, properties.implementation)

        if properties.proportional:
            me.use_even_points_distribution()
        if inputs.face_weight:
            me.set_custom_face_weights(inputs.face_weight)
        if properties.implementation == 'NUMPY':
            return me.generate_random_points_np(inputs.number[0], inputs.seed[0], properties.out_np)
        return me.generate_random_points(inputs.number[0], inputs.seed[0])
    else:
        return populate_mesh(inputs.verts, inputs.faces, inputs.number[0], inputs.seed[0], properties.all_triangles, properties.safe_check)

class TriangulatedMesh:
    def __init__(self, verts: List[List[float]], faces: List[List[int]], all_triangles: bool, implementation: str):
        if implementation == 'NUMPY':
            self._verts = verts
        else:
            self._verts = [Vector(v) for v in verts]

        self._faces = faces
        self._face_weights = []
        self._tri_face_areas = []
        if all_triangles:
            self._tri_faces = faces
            self._old_face_indexes_per_tri = list(range(len(faces)))
        else:
            self._tri_faces = []
            self._old_face_indexes_per_tri = []
            self._triangulate()

    def use_even_points_distribution(self, even=True):
        self._face_weights = self.tri_face_areas if even else None

    def set_custom_face_weights(self, custom_weights):
        weights_per_tri = self._face_attrs_to_tri_face_attrs(custom_weights)
        if self._face_weights:
            self._face_weights = [f*w for f, w in zip(self._face_weights, weights_per_tri)]
        else:
            self._face_weights = weights_per_tri

    def generate_random_points_np(self,
                                  random_points_total: int,
                                  seed: int,
                                  out_np: Tuple[bool, bool]) -> Tuple[list, list]:

        np.random.seed(seed)
        faces_with_points, points_total_per_face = self._distribute_points_np(random_points_total)
        random_points = []
        old_face_indexes_per_point = []
        u1 = np.random.uniform(low=0, high=1, size=random_points_total)
        u2 = np.random.uniform(low=0, high=1, size=random_points_total)
        mask = (u1 + u2) > 1
        u1[mask] = 1 - u1[mask]
        mask = (u1+u2) > 1
        u2[mask] = 1 - u2[mask]

        if isinstance(self._tri_faces, np.ndarray):
            np_faces = self._tri_faces[faces_with_points]
        else:
            np_faces = np.array(self._tri_faces)[faces_with_points]
        if isinstance(self._verts, np.ndarray):
            v_pols = np.repeat(self._verts[np_faces], points_total_per_face, axis=0)
        else:
            v_pols = np.repeat(np.array(self._verts)[np_faces], points_total_per_face, axis=0)

        side1 = v_pols[:, 1, :] - v_pols[:, 0, :]
        side2 = v_pols[:, 2, :] - v_pols[:, 0, :]

        random_points = v_pols[:, 0, :] + side1 * u1[:, np.newaxis] + side2 * u2[:, np.newaxis]

        old_face_indexes_per_point = np.repeat(np.array(self._old_face_indexes_per_tri)[faces_with_points], points_total_per_face, axis=0)

        return (random_points if out_np[0] else random_points.tolist(),
                old_face_indexes_per_point if out_np[1] else old_face_indexes_per_point.tolist())

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
        return [v[:] for v in random_points], old_face_indexes_per_point

    @property
    def tri_face_areas(self):
        if not self._tri_face_areas:
            if isinstance(self._verts, np.ndarray):
                self._tri_face_areas = np_calc_tris_areas(self._verts[np.array(self._tri_faces)])
            else:
                self._tri_face_areas = [area_tri(*[self._verts[i] for i in f]) for f in self._tri_faces]

        return self._tri_face_areas

    def _distribute_points(self, random_points_total: int) -> List[int]:
        # generate list of numbers which mean how many points should be created on face
        points_total_per_face = [0 for _ in range(len(self._tri_faces))]
        chosen_faces = random.choices(range(len(self._tri_faces)), self._face_weights, k=random_points_total)
        for i in chosen_faces:
            points_total_per_face[i] += 1
        return points_total_per_face

    def _distribute_points_np(self, random_points_total: int) -> List[int]:
        # generate list of numbers which mean how many points should be created on face

        if len(self._face_weights) != 0:
            weights = np.array(self._face_weights, dtype='float')
            weights /= np.sum(weights)
        else:
            weights = None
        chosen_faces = np.random.choice(
            np.arange(len(self._tri_faces)),
            random_points_total,
            replace=True,
            p=weights)

        return np.unique(chosen_faces, return_counts=True)

    def _triangulate(self):
        # generate list of triangle faces and list of indexes which points to initial faces for each new triangle
        verts = self._verts
        tri_faces_add = self._tri_faces.append
        old_face_index_add = self._old_face_indexes_per_tri.append
        for i, f in enumerate(self._faces):
            if len(f) == 3:
                tri_faces_add(f)
                old_face_index_add(i)
            else:
                face_verts = [[verts[i] for i in f]]
                # [[v1,v2,v3,v4]] - face_verts
                for tri_face in tessellate_polygon(face_verts):
                    tri_faces_add([f[itf] for itf in tri_face])
                    old_face_index_add(i)

    @staticmethod
    def _get_random_vectors_on_tri(v1, v2, v3, number):
        # returns random vertices for given triangle
        out = []
        side1 = v2 - v1
        side2 = v3 - v1
        for _ in range(number):
            u1 = random.random()
            u2 = random.random()
            u1 = u1 if u1 + u2 <= 1 else 1 - u1
            u2 = u2 if u1 + u2 <= 1 else 1 - u2

            out.append(v1 + side1 * u1 + side2 * u2)
        return out

    def _face_attrs_to_tri_face_attrs(self, values):
        return [values[i] if i <= len(values) - 1 else values[len(values) - 1] for i in self._old_face_indexes_per_tri]


class SvRandomPointsOnMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: random points vertices
    Tooltip: distribute points on given mesh
    """
    bl_idname = 'SvRandomPointsOnMesh'
    bl_label = 'Random points on mesh'
    sv_icon = 'SV_RANDOM_NUM_GEN'

    points_number: bpy.props.IntProperty(
        name='Number',
        default=10,
        description="Number of random points",
        update=updateNode)

    seed: bpy.props.IntProperty(
        name='Seed',
        update=updateNode)

    proportional: bpy.props.BoolProperty(
        name="Proportional",
        description="If checked, then number of points at each face is proportional to the area of the face",
        default=True,
        update=updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        self.outputs['Face index'].hide_safe = self.mode != 'SURFACE'

    modes = [('SURFACE', "Surface", "Surface", 0),
             ('VOLUME', "Volume", "Volume", 1)
            ]

    mode: bpy.props.EnumProperty(
        name="Mode",
        items=modes,
        default='SURFACE',
        update=update_sockets)

    all_triangles: bpy.props.BoolProperty(
        name="All Triangles",
        description="Enable if the input mesh is made only of triangles (makes node faster)",
        default=False,
        update=updateNode)

    safe_check: bpy.props.BoolProperty(
        name='Safe Check',
        description='When disabled polygon indices referring to unexisting points will crash Blender but makes node faster',
        default=True)

    implementations = [
        ('NUMPY', "NumPy", "Faster", 0),
        ('MATHUTILS', "MathUtils", "Old implementation", 1)
        ]
    implementation: bpy.props.EnumProperty(
        name="Implementation",
        items=implementations,
        default='NUMPY',
        update=updateNode)

    out_np: bpy.props.BoolVectorProperty(
        name="Ouput Numpy",
        description="Output NumPy arrays",
        default=(False, False),
        size=2, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')
        if self.mode == 'SURFACE':
            layout.prop(self, "proportional")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "mode", text='')
        if self.mode == 'SURFACE':
            layout.prop(self, "proportional")
            layout.prop(self, "all_triangles")
            layout.prop(self, "implementation")
            if self.implementation == 'NUMPY':
                b = layout.box()
                b.label(text='Output Numpy')
                r = b.row()
                r.prop(self, "out_np", index=0, text='Verts', toggle=True)
                r.prop(self, "out_np", index=1, text='Face index', toggle=True)
        else:
            layout.prop(self, "all_triangles")
            layout.prop(self, "safe_check")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "mode")
        if self.mode == 'SURFACE':
            layout.prop(self, "proportional")
            layout.prop(self, "all_triangles")
            layout.prop_menu_enum(self, "implementation")
            if self.implementation == 'NUMPY':
                layout.label(text='Output Numpy')
                layout.prop(self, "out_np", index=0, text='Verts')
                layout.prop(self, "out_np", index=1, text='Face index')


    def sv_init(self, context):
        [self.inputs.new(p.socket_type, p.name) for p in INPUT_CONFIG]
        [setattr(s, 'prop_name', p.prop_name) for s, p in zip(self.inputs, INPUT_CONFIG)]

        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Face index')

    def process(self):
        if not all([self.inputs['Verts'].is_linked, self.inputs['Faces'].is_linked]):
            return

        props = NodeProperties(self.proportional,
                               self.mode,
                               self.all_triangles,
                               self.implementation,
                               self.safe_check,
                               self.out_np)
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
