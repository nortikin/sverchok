# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from collections import ChainMap
from itertools import cycle, chain, count
from typing import List, Tuple, Union, Type, Dict, Iterable
from functools import singledispatch

import numpy as np
import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.mesh_structure import Mesh, Verts, Edges, Faces, Loops
from sverchok.utils.sv_bmesh_utils import empty_bmesh


def generate_mesh(objects: bpy.types.bpy_prop_collection, meshes: List[Mesh]) -> None:
    # faster (some tests show 3 times faster, some equal speed) but can crash Blender easily
    for bl_me, me in zip((prop.obj.data for prop in objects), meshes):
        if is_topology_changed(bl_me, me):
            me_edges = generate_unique_edges_from_faces(me.faces)
            me_faces = correct_faces(len(me.verts), me.faces)
            ensure_number_of_elements(bl_me, me, me_edges, me_faces)
            update_edges(bl_me, me_edges)
            update_loops(bl_me, me_faces, me_edges)
            update_faces(bl_me, me_faces)
        update_vertices(bl_me, me)
        bl_me.update()


def generate_mesh2(objects: bpy.types.bpy_prop_collection, meshes: List[Mesh]) -> None:
    for bl_me, me in zip((prop.obj.data for prop in objects), meshes):
        if is_topology_changed(bl_me, me):
            with empty_bmesh(False) as bm:
                me.to_bmesh(bm)
                bm.to_mesh(bl_me)
        else:
            update_vertices(bl_me, me)
        bl_me.update()


def is_topology_changed(bl_me: bpy.types.Mesh, me: Mesh) -> bool:
    return len(bl_me.vertices) != len(me.verts) or len(bl_me.polygons) != len(me.faces)


def ensure_number_of_elements(bl_me: bpy.types.Mesh, me: Mesh, me_edges: dict, me_faces: List[List[int]]) -> None:
    bl_me.clear_geometry()
    bl_me.vertices.add(len(me.verts))
    if me.verts and me_faces:
        bl_me.edges.add(len(me_edges))
        bl_me.loops.add(sum([len(f) for f in me_faces]))
        bl_me.polygons.add(len(me_faces))


def generate_unique_edges_from_faces(faces: List[List[int]]) -> dict:
    edge_index = dict()
    counter = count()
    for f in faces:
        for e in edge_list(f):
            if e not in edge_index:
                edge_index[e] = next(counter)
    return edge_index


def edge_list(face: List[int]) -> Tuple[int]:
    for i1, i2 in zip(face, face[1:] + face[:1]):
        yield tuple(sorted([i1, i2]))


def correct_faces(len_verts: int, faces: List[List[int]]) -> List[List[int]]:
    out_faces = []
    for f in faces:
        if any([i > len_verts for i in f]):
            continue
        else:
            out_faces.append(f)
    return out_faces


def update_vertices(bl_me: bpy.types.Mesh, me: Mesh) -> None:
    for bl_v, v in zip(bl_me.vertices, me.verts):
        bl_v.co = v


def update_edges(bl_me: bpy.types.Mesh, me_edges: dict) -> None:
    for bl_e, e in zip(bl_me.edges, me_edges):
        bl_e.vertices = e


def update_loops(bl_me: bpy.types.Mesh, me_faces: List[List[int]], me_edge_indexes: dict) -> None:
    if me_faces:
        vert_edge_indexes = []
        for f in me_faces:
            for vi, e in zip(f, edge_list(f)):
                vert_edge_indexes.append((vi, me_edge_indexes[e]))
        for l, (vi, ei) in zip(bl_me.loops, vert_edge_indexes):
            l.edge_index = ei
            l.vertex_index = vi


def update_faces(bl_me: bpy.types.Mesh, me_faces: List[List[int]]) -> None:
    if me_faces:
        next_loop_index = 0
        for bl_f, f in zip(bl_me.polygons, me_faces):
            bl_f.loop_start = next_loop_index
            bl_f.loop_total = len(f)
            next_loop_index += len(f)


BlenderDataBlocks = Union[bpy.types.Object, bpy.types.Mesh, bpy.types.Material]
BlenderDataBlockTypes = Union[Type[bpy.types.Object], Type[bpy.types.Mesh], Type[bpy.types.Material]]


def safe_del_object(obj: BlenderDataBlocks) -> None:
    @singledispatch
    def del_object(bl_obj) -> None:
        raise TypeError(f"Such type={type(bl_obj)} is not supported")

    @del_object.register
    def _(bl_obj: bpy.types.Object):
        bpy.data.objects.remove(bl_obj)

    @del_object.register
    def _(bl_obj: bpy.types.Mesh):
        bpy.data.meshes.remove(bl_obj)

    @del_object.register
    def _(bl_obj: bpy.types.Material):
        pass
        # if bl_obj.users == 1:
        #     bpy.data.materials.remove(bl_obj)

    try:
        del_object(obj)
    except ReferenceError:
        # looks like already was deleted
        pass


def pick_data_block_from_collection(collection: bpy.types.bpy_prop_collection, block_name: str, new: bool = True):
    block = None
    if not new:
        block = collection.get(block_name)
    if not block:
        block = collection.new(name=block_name)
    return block


def pick_object(obj_name: str, mesh: bpy.types.Mesh, new: bool = True):
    block = None
    if not new:
        block = bpy.data.objects.get(obj_name)
    if not block:
        block = bpy.data.objects.new(name=obj_name, object_data=mesh)
    return block


def ensure_object_list(objects: bpy.types.bpy_prop_collection, names: List[str]) -> None:
    # for animation mode could be implemented in faster way
    correct_collection_length(objects, len(names))
    ensure_links_to_objects(objects, names)
    check_data_name(objects, names)


def ensure_material_list(collection: bpy.types.bpy_prop_collection, names: List[List[str]]) -> Dict[str, int]:
    names = ChainMap(*[dict(zip(l, cycle([None]))) for l in names])
    correct_collection_length(collection, len(names))
    ensure_links_to_materials(collection, names)
    check_data_name(collection, names, False)
    return {prop.mat.name: i for prop, i in zip(collection, count())}


def correct_collection_length(collection: bpy.types.bpy_prop_collection, length: int) -> None:
    if len(collection) < length:
        for i in range(len(collection), length):
            collection.add()
    elif len(collection) > length:
        for i in range(len(collection) - 1, length - 1, -1):
            for key, value in collection[i].items():
                if key == 'name':
                    continue
                if value:
                    safe_del_object(value)
            collection.remove(i)


def ensure_links_to_objects(objects: bpy.types.bpy_prop_collection, names: List[str]) -> None:
    # objects can be deleted by users, so if property is exist it does not mean that it has an object
    for prop, name in zip(objects, names):
        if not prop.mesh:
            prop.mesh = pick_data_block_from_collection(bpy.data.meshes, name, True)
        if not prop.obj:
            prop.obj = pick_object(name, prop.mesh, True)
        try:
            bpy.context.scene.collection.objects.link(prop.obj)
        except RuntimeError:
            # then the object already added, it looks like more faster way to ensure object is in the scene
            pass


def ensure_links_to_materials(collection: bpy.types.bpy_prop_collection, names: Iterable[str]) -> None:
    for prop, name in zip(collection, names):
        if not prop.mat or prop.mat.name != name:
            prop.mat = pick_data_block_from_collection(bpy.data.materials, name, False)


def check_data_name(objects: bpy.types.bpy_prop_collection, names: Iterable[str], let_numbers: bool = True) -> None:
    for prop, name in zip(objects, names):
        for data in prop.values():
            real_name = data.name.rsplit('.', 1)[0] if let_numbers else data.name
            if real_name != name:
                data.name = name


def apply_materials_to_mesh(objects: bpy.types.bpy_prop_collection,
                            materials: bpy.types.bpy_prop_collection,
                            meshes: List[Mesh],
                            mat_name_obj_ind: Dict[str, int]) -> None:
    for prop, me in zip(objects, meshes):
        prop.mesh.materials.clear()
        for mat_name in me.materials:
            mat = materials[mat_name_obj_ind[mat_name]].mat
            prop.mesh.materials.append(mat)


def set_vertex_color(objects: bpy.types.bpy_prop_collection, meshes: List[Mesh]):
    for bm_me, me in zip((prop.mesh for prop in objects), meshes):
        loop_colors = get_loop_colors(me)
        if np.any(loop_colors):
            col_layer = pick_data_block_from_collection(bm_me.vertex_colors, 'SvCol', False)
            col_layer.data.foreach_set('color', loop_colors)


def get_loop_colors(me: Mesh) -> np.ndarray:
    @singledispatch
    def loop_colors(elem, _, __):
        raise TypeError(f"Such type={type(elem)} of mesh elements does not supported")

    @loop_colors.register
    def _(loops: Loops, np_colors: np.ndarray, _):
        for i, col in zip(range(len(np_colors)), chain.from_iterable(loops.vertex_colors)):
            np_colors[i] = col
        return np_colors

    @loop_colors.register
    def _(verts: Verts, np_colors: np.ndarray, mesh: Mesh):
        for i, col in zip(range(len(np_colors)), chain.from_iterable([verts.vertex_colors[i] for i in mesh.loops])):
            np_colors[i] = col
        return np_colors

    @loop_colors.register
    def _(mesh: Mesh, np_colors: np.ndarray, _):
        for i, col in zip(range(len(np_colors)), cycle(mesh.vertex_colors)):
            np_colors[i] = col
        return np_colors

    @loop_colors.register
    def _(faces: Faces, np_colors: np.ndarray, mesh: Mesh):
        for i, col in zip(range(len(np_colors)), chain.from_iterable([faces.vertex_colors[i] for i, f in enumerate(faces) for fi in f])):
            np_colors[i] = col
        return np_colors

    elements = None
    if me.loops.vertex_colors:
        elements = me.loops
    elif me.verts.vertex_colors:
        elements = me.verts
    elif me.faces.vertex_colors:
        elements = me.faces
    elif me.vertex_colors:
        elements = me

    if elements:
        colors = np.zeros((len(me.loops) * 4), dtype=float)
        return loop_colors(elements, colors, me)
    else:
        return []


class SvViewerMeshObjectList(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    mesh: bpy.props.PointerProperty(type=bpy.types.Mesh)


class SvViewerMeshMaterials(bpy.types.PropertyGroup):
    mat: bpy.props.PointerProperty(type=bpy.types.Material)


class SvViewerMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvViewerMesh'
    bl_label = 'Viewer Mesh'
    bl_icon = 'MOD_BOOLEAN'

    objects: bpy.props.CollectionProperty(type=SvViewerMeshObjectList)
    materials: bpy.props.CollectionProperty(type=SvViewerMeshMaterials)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Mesh')

    def update(self):
        with self.sv_throttle_tree_update():
            ensure_object_list(self.objects, [me.name for me in self.inputs['Mesh'].sv_get(deepcopy=False, default=[])])

    def process(self):
        if not self.inputs['Mesh'].is_linked:
            return

        with self.sv_throttle_tree_update():
            meshes = self.inputs['Mesh'].sv_get(deepcopy=False, default=[])
            ensure_object_list(self.objects, [me.name for me in meshes])
            material_obj_ind = ensure_material_list(self.materials, [me.materials for me in meshes])
            generate_mesh2(self.objects, meshes)
            apply_materials_to_mesh(self.objects, self.materials, meshes, material_obj_ind)
            set_vertex_color(self.objects, meshes)


classes = [SvViewerMeshObjectList,
           SvViewerMeshMaterials,
           SvViewerMesh]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes[::-1]]
