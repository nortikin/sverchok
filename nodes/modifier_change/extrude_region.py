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


from typing import Generator, Set

import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
import bmesh.ops
from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


def is_matrix(lst):
    return len(lst) == 4 and len(lst[0]) == 4

def get_faces_center(faces):
    result = Vector((0,0,0))
    for face in faces:
        result += Vector(face.calc_center_median())
    result = (1.0/float(len(faces))) * result
    return result

def get_avg_normal(faces):
    result = Vector((0,0,0))
    for face in faces:
        result += Vector(face.normal)
    result = (1.0/float(len(faces))) * result
    return result

MASK = 0
OUT = 1
IN = 2
MASK_MEANING = {MASK: 'mask', OUT: 'out', IN: 'in'}
LAYER_INDEX_NAME = 'initial_index'
LAYER_MASK_NAME = 'mask'


def vert_neighbours_walk(vert):
    for edge in vert.link_edges:
        v = edge.other_vert(vert)
        if ensure_next_element(vert, v):
            yield v


def edge_neighbours_walk(edge):
    for vert in edge.verts:
        for e in vert.link_edges:
            if ensure_next_element(edge, e):
                yield e


def face_neighbours_walk(face):
    for edge in face.edges:
        for f in edge.link_faces:
            if ensure_next_element(face, f):
                yield f


def ensure_next_element(start_elem, next_elem):
    if start_elem == next_elem:
        return False
    else:
        return True


class UniqueStack:
    # any element can get in the stack only once
    def __init__(self, element=None):
        self._added = set(list(element)) if element else set()
        self._stack = list(element) if element else []

    def try_add(self, element):
        if element not in self._added:
            self._stack.append(element)
            self._added.add(element)

    def pop(self):
        return self._stack.pop()

    def __bool__(self):
        return bool(self._stack)


def mesh_walk(elements, neighbours_walk):
    stack = UniqueStack()
    for element in elements:
        stack.try_add(element)

        while stack:
            next_element = stack.pop()
            yield next_element

            for el in neighbours_walk(next_element):
                stack.try_add(el)


def loop_neighbour_walk(start_loop) -> Generator[bmesh.types.BMLoop, None, None]:
    """
       +    6+
    +++++++++++++
      7+3   2+
       +0   1+5
    +++++++++++++
       +4    +
    0, 1, 2, ... - loops
    0 - start loop
    it returns 4, 5, 6, 7 loops in such particular order
    if loop have several radial faces it will return their loops first
    """
    def radial_neighbour_faces(loop) -> Generator[bmesh.types.BMLoop, None, None]:
        next_loop = loop.link_loop_radial_next
        while loop != next_loop:
            yield next_loop
            next_loop = next_loop.link_loop_radial_next

    def face_loops_from_loop(loop) -> Generator[bmesh.types.BMLoop, None, None]:
        yield loop
        next_loop = loop.link_loop_next
        while loop != next_loop:
            yield next_loop
            next_loop = next_loop.link_loop_next

    for l in face_loops_from_loop(start_loop):
        yield from radial_neighbour_faces(l)


def mesh_walk_from_loop(start_loop: bmesh.types.BMLoop) -> Generator[bmesh.types.BMFace, None, None]:
    # Such walk can't walk over all mesh if mesh include disjoint mesh islands
    # In this case islands should be detected and walk separately
    used_faces = set()
    stack = UniqueStack([start_loop])
    while stack:
        next_loop = stack.pop()
        if next_loop.face not in used_faces:
            yield next_loop.face
            used_faces.add(next_loop.face)

        for l in loop_neighbour_walk(next_loop):
            stack.try_add(l)


def convert_bmesh_to_sv_mesh(bm, extruded_faces: Set[bmesh.types.BMFace],
                             extruded_verts: set, mask_content: set, face_data=None):
    """
    ++++++++++++++++++
    +   ++  1   ++   +
    +   + +    + +   +
    +   +  ++++  +   +
    + 0 +1 +2 +1 + 0 +
    +   +  ++++  +   +
    +   + +    + +   +
    +   ++  1   ++   +
    ++++++++++++++++++
    0 - masked faces
    1 - side faces
    2 - extruded face

    mask_content can include 0, 1, 2
    """
    mask_layer = bm.faces.layers.int.get(LAYER_MASK_NAME)
    index_layer = bm.faces.layers.int.get(LAYER_INDEX_NAME)

    def classify_faces():
        for face in bm.faces:
            if face in extruded_faces:
                face[mask_layer] = 2
            elif any(v in extruded_verts for v in face.verts):
                face[mask_layer] = 1
            else:
                face[mask_layer] = 0

    classify_faces()

    def is_masked_face(face):
        return face[mask_layer] == 0

    def is_side_face(face):
        return face[mask_layer] == 1

    def is_extruded_face(face):
        return face[mask_layer] == 2

    def start_walk_loop() -> bmesh.types.BMLoop:
        # The idea is start from firs of extruded face
        # Even the order of edges is undefined
        for face in extruded_faces:
            if face.tag:
                for loop in face.loops:
                    if loop.tag:
                        return loop
        raise LookupError(f"No one extruded face was tagged as first face"
                          f" or first face does not have tagged first loop")

    def sv_mesh_from_bm_faces(bm_faces):
        def element_indexer():
            indexes = dict()
            element = None
            stop_iteration = False
            while True:
                try:
                    element = yield list(indexes.keys()) if stop_iteration else\
                                    indexes[element] if element is not None else None
                    if element not in indexes:
                        indexes[element] = len(indexes)
                    stop_iteration = False
                except StopIteration:
                    stop_iteration = True

        vert_indexes = element_indexer()
        vert_indexes.send(None)

        sv_faces = [[vert_indexes.send(v) for v in f.verts] for f in bm_faces]
        sv_edges = [[vert_indexes.send(v) for v in e.verts] for e in bm.edges]
        sv_verts = [v.co[:] for v in vert_indexes.throw(StopIteration)]
        return sv_verts, sv_edges, sv_faces

    def rebuild_face_data(bm_faces):
        return [face_data[min(f[index_layer], len(face_data))] for f in bm_faces]

    def build_mask(bm_faces):
        return [f[mask_layer] in mask_content for f in bm_faces]

    if not extruded_faces:
        new_vertices, new_edges, new_faces, *new_face_data = pydata_from_bmesh(bm, face_data)
        face_mask = build_mask(bm.faces)
    else:
        new_face_order = [face for face in mesh_walk_from_loop(start_walk_loop())]
        new_vertices, new_edges, new_faces = sv_mesh_from_bm_faces(new_face_order)
        new_face_data = rebuild_face_data(new_face_order) if face_data else []
        face_mask = build_mask(new_face_order)
    return new_vertices, new_edges, new_faces, new_face_data, face_mask


class SvExtrudeRegionNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Extrude region of faces '''
    bl_idname = 'SvExtrudeRegionNode'
    bl_label = 'Extrude Region'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTRUDE_REGION'

    keep_original: BoolProperty(
        name="Keep original", description="Keep original geometry",
        default=False, update=updateNode)

    transform_modes = [
            ("Matrix", "By matrix", "Transform vertices by specified matrix", 0),
            ("Normal", "Along normal", "Extrude vertices along normal", 1)
        ]

    @throttled
    def update_mode(self, context):
        self.inputs['Matrices'].hide_safe = (self.transform_mode != "Matrix")
        self.inputs['Height'].hide_safe = (self.transform_mode != "Normal")
        self.inputs['Scale'].hide_safe = (self.transform_mode != "Normal")

        if self.transform_mode == "Normal":
            self.multiple = True

    transform_mode: EnumProperty(
        name="Transformation mode", description="How vertices transformation is specified",
        default="Matrix", items=transform_modes, update=update_mode)

    height_: FloatProperty(
        name="Height", description="Extrusion amount", default=0.0, update=updateNode)

    scale_: FloatProperty(
        name="Scale", description="Extruded faces scale", default=1.0, min=0.0, update=updateNode)

    multiple: BoolProperty(
        name="Multiple extrude", description="Extrude the same region several times", default=False, update=updateNode)

    mask_type_items = [
            ('mask', "Mask", "Faces that were masked out"),
            ('out',  "Out", "Outer faces of the extrusion"),
            ('in',   "In",  "Inner faces of the extrusion"),
        ]

    mask_out_type : EnumProperty(
            name = "Mask Output",
            items=mask_type_items,
            update=updateNode,
            options={'ENUM_FLAG'},
            default={'out'},
            description="Switch between untouched, inner and outer faces generated by insertion")

    properties_to_skip_iojson = ['mask_out_type']

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvStringsSocket', 'Mask')
        self.inputs.new('SvMatrixSocket', 'Matrices')
        self.inputs.new('SvStringsSocket', "Height").prop_name = "height_"
        self.inputs.new('SvStringsSocket', "Scale").prop_name = "scale_"
        self.inputs.new('SvStringsSocket', "FaceData")

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')
        self.outputs.new('SvVerticesSocket', 'NewVertices')
        self.outputs.new('SvStringsSocket', 'NewEdges')
        self.outputs.new('SvStringsSocket', 'NewFaces')
        self.outputs.new('SvStringsSocket', 'Mask').custom_draw = 'draw_mask_socket'
        self.outputs.new('SvStringsSocket', 'FaceData')

        self.update_mode(context)

    def draw_mask_socket(self, socket, context, layout):
        layout.prop(self, 'mask_out_type', expand=True)
        layout.label(text=socket.name)

    def draw_buttons(self, context, layout):
        layout.prop(self, "transform_mode")
        if self.transform_mode == "Matrix":
            layout.prop(self, "multiple", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "keep_original", toggle=True)

    def process(self):
        # inputs
        if not self.inputs['Vertices'].is_linked:
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        masks_s = self.inputs['Mask'].sv_get(default=[[1]])
        if self.transform_mode == "Matrix":
            matrices_s = [self.inputs['Matrices'].sv_get(Matrix())]
            heights_s = [0.0]
            scales_s = [1.0]
        else:
            matrices_s = [[]]
            heights_s = self.inputs['Height'].sv_get()
            scales_s  = self.inputs['Scale'].sv_get()
        if 'FaceData' in self.inputs:
            face_data_s = self.inputs['FaceData'].sv_get(default=[[]])
        else:
            face_data_s = [[]]

        result_vertices = []
        result_edges = []
        result_faces = []
        result_ext_vertices = []
        result_ext_edges = []
        result_ext_faces = []
        result_face_data = []
        result_mask = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, matrices_s, heights_s, scales_s, face_data_s])

        for vertices, edges, faces, masks, matrix_per_iteration, height_per_iteration, scale_per_iteration, face_data in zip(*meshes):
            if self.transform_mode == "Matrix":
                if not matrix_per_iteration:
                    matrix_per_iteration = [Matrix()]

            if self.multiple:
                if self.transform_mode == "Matrix":
                    n_iterations = len(matrix_per_iteration)
                else:
                    n_iterations = max(len(height_per_iteration), len(scale_per_iteration))
                    fullList(height_per_iteration, n_iterations)
                    fullList(scale_per_iteration, n_iterations)
            else:
                n_iterations = 1
                matrix_per_iteration = [matrix_per_iteration]

            fullList(masks,  len(faces))
            if face_data:
                fullList(face_data, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True, markup_face_data=True)
            mask_layer = bm.faces.layers.int.new('mask')
            bm.faces.ensure_lookup_table()
            #fill_faces_layer(bm, masks, 'mask', int, MASK, invert_mask=True)

            b_faces = []
            b_edges = set()
            b_verts = set()
            for mask, face in zip(masks, bm.faces):
                if mask:
                    b_faces.append(face)
                    for edge in face.edges:
                        b_edges.add(edge)
                    for vert in face.verts:
                        b_verts.add(vert)

            b_faces[0].tag = True  # This is flag of first extruded face for reordering algorithm
            b_faces[0].loops[0].tag = True  # This is flag walk direction
            extrude_geom = b_faces+list(b_edges)+list(b_verts)

            extruded_verts_last = []
            extruded_bm_verts_all = set()
            extruded_edges_last = []
            extruded_faces_last = []
            extruded_bm_faces_last = []

            matrix_spaces = [Matrix()]

            for idx in range(n_iterations):

                for item in extrude_geom:
                    if isinstance(item, bmesh.types.BMFace):
                        item[mask_layer] = OUT

                new_geom = bmesh.ops.extrude_face_region(bm,
                                geom=extrude_geom,
                                edges_exclude=set(),
                                use_keep_orig=self.keep_original)['geom']

                extruded_verts = [v for v in new_geom if isinstance(v, bmesh.types.BMVert)]
                extruded_faces = [f for f in new_geom if isinstance(f, bmesh.types.BMFace)]

                if self.transform_mode == "Matrix":
                    matrices = matrix_per_iteration[idx]
                    if isinstance(matrices, Matrix):
                        matrices = [matrices]
                    fullList(matrix_spaces, len(extruded_verts))
                    for vertex_idx, (vertex, matrix) in enumerate(zip(*match_long_repeat([extruded_verts, matrices]))):
                        bmesh.ops.transform(bm, verts=[vertex], matrix=matrix, space=matrix_spaces[vertex_idx])
                        matrix_spaces[vertex_idx] = matrix.inverted() @ matrix_spaces[vertex_idx]
                else:
                    height = height_per_iteration[idx]
                    scale = scale_per_iteration[idx]

                    normal = get_avg_normal(extruded_faces)
                    dr = normal * height
                    center = get_faces_center(extruded_faces)
                    translation = Matrix.Translation(center)
                    rotation = normal.rotation_difference((0,0,1)).to_matrix().to_4x4()
                    m = translation @ rotation
                    bmesh.ops.scale(bm, vec=(scale, scale, scale), space=m.inverted(), verts=extruded_verts)
                    bmesh.ops.translate(bm, verts=extruded_verts, vec=dr)

                extruded_bm_verts_all.update(extruded_verts)
                extruded_verts_last = [tuple(v.co) for v in extruded_verts]

                extruded_edges = [e for e in new_geom if isinstance(e, bmesh.types.BMEdge)]
                extruded_edges_last = [tuple(v.index for v in edge.verts) for edge in extruded_edges]

                extruded_bm_faces_last = extruded_faces
                extruded_faces_last = [[v.index for v in face.verts] for face in extruded_faces]

                extrude_geom = new_geom

            mask_content = {i for i, mask_type in enumerate(['mask', 'out', 'in']) if mask_type in self.mask_out_type}
            new_vertices, new_edges, new_faces, new_face_data, face_mask = convert_bmesh_to_sv_mesh(
                bm, set(extruded_bm_faces_last), extruded_bm_verts_all, mask_content, face_data or None)

            bm.free()

            result_mask.append(face_mask)
            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_ext_vertices.append(extruded_verts_last)
            result_ext_edges.append(extruded_edges_last)
            result_ext_faces.append(extruded_faces_last)
            result_face_data.append(new_face_data)

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Polygons'].sv_set(result_faces)
        self.outputs['NewVertices'].sv_set(result_ext_vertices)
        self.outputs['NewEdges'].sv_set(result_ext_edges)
        self.outputs['NewFaces'].sv_set(result_ext_faces)
        if 'Mask' in self.outputs:
            self.outputs['Mask'].sv_set(result_mask)
        if 'FaceData' in self.outputs:
            self.outputs['FaceData'].sv_set(result_face_data)

    def storage_get_data(self, storage):
        storage['mask_out_type'] = list(self.mask_out_type)

    def storage_set_data(self, storage):
        self.mask_out_type = set(storage.get('mask_out_type', []))

def register():
    bpy.utils.register_class(SvExtrudeRegionNode)


def unregister():
    bpy.utils.unregister_class(SvExtrudeRegionNode)
