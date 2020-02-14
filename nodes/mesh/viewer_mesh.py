# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle, chain, count
from typing import List, Tuple

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.mesh_structure import Mesh
from sverchok.utils.sv_bmesh_utils import empty_bmesh


def generate_mesh(objects: bpy.types.CollectionProperty, meshes: List[Mesh]) -> None:
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


def generate_mesh2(objects: bpy.types.CollectionProperty, meshes: List[Mesh]) -> None:
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


def ensure_object_list(objects: bpy.types.CollectionProperty, names: List[str]) -> None:
    correct_object_list_length(objects, len(names))
    ensure_links_to_objects(objects, names)
    fix_object_properties(objects, names)


def correct_object_list_length(objects: bpy.types.CollectionProperty, length: int) -> None:
    if len(objects) < length:
        for i in range(len(objects), length):
            objects.add()
    elif len(objects) > length:
        for i in range(len(objects) - 1, length - 1, -1):
            if objects[i].obj:
                me = objects[i].obj.data
                bpy.data.objects.remove(objects[i].obj)
                bpy.data.meshes.remove(me)
            objects.remove(i)


def ensure_links_to_objects(objects: bpy.types.CollectionProperty, names: List[str]) -> None:
    # objects can be deleted by users, so if property is exist it does not mean that it as an object
    for prop, name in zip(objects, names):
        if not prop.obj:
            me = bpy.data.meshes.new(name)
            prop.obj = bpy.data.objects.new(name=name, object_data=me)
            bpy.context.scene.collection.objects.link(prop.obj)


def fix_object_properties(objects: bpy.types.CollectionProperty, names: List[str]) -> None:
    for prop, name in zip(objects, names):
        name_parts = prop.obj.name.rsplit('.', 1) 
        if len(name_parts) > 2:
            raise NameError(f"SvMesh: using dots in names is forbidden, name={prop.obj.name}")
        elif name_parts[0] != name:
            prop.obj.name = name


class SvViewerMeshObjectList(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)


class SvViewerMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvViewerMesh'
    bl_label = 'Viewer Mesh'
    bl_icon = 'MOD_BOOLEAN'

    objects: bpy.props.CollectionProperty(type=SvViewerMeshObjectList)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Mesh')

    def update(self):
        with self.sv_throttle_tree_update():
            ensure_object_list(self.objects, [me.name for me in self.inputs['Mesh'].sv_get(deepcopy=False, default=[])])

    def process(self):
        if not self.inputs['Mesh'].is_linked:
            return

        with self.sv_throttle_tree_update():
            ensure_object_list(self.objects, [me.name for me in self.inputs['Mesh'].sv_get(deepcopy=False, default=[])])
            generate_mesh2(self.objects, self.inputs['Mesh'].sv_get(deepcopy=False, default=[]))


classes = [SvViewerMeshObjectList,
           SvViewerMesh]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes[::-1]]
