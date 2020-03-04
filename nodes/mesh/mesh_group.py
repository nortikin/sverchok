# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle, chain

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import repeat_last
from sverchok.core.mesh_structure import Mesh, MeshGroup, FacesGroup, EdgesGroup, VertsGroup, LoopsGroup
from sverchok.utils.mesh_structure.check_input import set_safe_attr


def generate_indexes(me: Mesh, indexes: list, input_type: str):
    if input_type == 'verts':
        edge_verts_in = np.isin(me.edges.ind, indexes)
        edge_mask = np.all(edge_verts_in, -1)
        loop_verts_in = np.isin(me.loops.ind, indexes)
        face_mask = np.logical_and.reduceat(loop_verts_in, me.faces.ind[:, 0])
        return indexes, np.arange(len(me.edges))[edge_mask].copy(), \
               np.arange(len(me.faces))[face_mask].copy(), np.arange(len(me.loops))[loop_verts_in].copy()
    elif input_type == 'edges':
        vert_indexes = np.unique(me.edges.ind[indexes])
        loop_verts_in = np.isin(me.loops.ind, vert_indexes)
        face_mask = np.logical_and.reduceat(loop_verts_in, me.faces.ind[:, 0])
        return vert_indexes, indexes, np.arange(len(me.faces))[face_mask].copy(),  \
               np.arange(len(me.loops))[loop_verts_in].copy()
    elif input_type == 'faces':
        face_mask = np.zeros(len(me.faces), np.bool)
        face_mask[indexes] = True
        loop_mask = np.repeat(face_mask, me.faces.ind[:, 1] - me.faces.ind[:, 0])
        vert_indexes = np.unique(me.loops.ind[loop_mask])
        edge_verts_in = np.isin(me.edges.ind, vert_indexes)
        edge_mask = np.all(edge_verts_in, -1)
        return vert_indexes, np.arange(len(me.edges))[edge_mask].copy(), indexes, \
               np.arange(len(me.loops))[loop_mask].copy()
    else:
        raise TypeError(f"Unsupported element={input_type}, verts or edges or faces are expected")


def get_next_name(current_name: str, groups: dict):
    if current_name not in groups:
        return current_name
    else:
        if '.' in current_name:
            base, index = current_name.rsplit('.', 1)
            try:
                index = int(index)
            except ValueError:
                return get_next_name(f"{current_name}.001", groups)
            ...
        else:
            return get_next_name(f"{current_name}.001", groups)


class SvMeshGroup(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    """
    bl_idname = 'SvMeshGroup'
    bl_label = 'Mesh Group'
    bl_icon = 'MOD_BOOLEAN'

    group_name = bpy.props.StringProperty(default="Mesh group")
    element = bpy.props.EnumProperty(items=[(i, i, '') for i in ['verts', 'edges', 'faces']])
    attr_element = bpy.props.EnumProperty(items=[(i, i, '') for i in ['object', 'faces', 'edges', 'verts', 'loops']])

    def draw_buttons(self, context, layout):
        layout.prop(self, 'group_name', text='')

    def draw_index_socket(self, socket, context, layout):
        layout.label(text='Indexes')
        layout.prop(self, 'element', text='')

    def draw_attr_socket(self, socket, context, layout):
        layout.label(text='Attributes')
        layout.prop(self, 'attr_element', text='')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Mesh')
        self.inputs.new('SvStringsSocket', 'Indexes').custom_draw = 'draw_index_socket'
        self.inputs.new('SvDictionarySocket', 'Attributes').custom_draw = 'draw_attr_socket'
        self.outputs.new('SvStringsSocket', 'Mesh')

    def process(self):
        if not self.inputs['Mesh'].is_linked and not self.inputs['Indexes'].is_linked:
            return

        indexes, attrs = [repeat_last(s.sv_get(deepcopy=False, default=[None])) for s in self.inputs[1:]]
        me: Mesh
        attrs: dict
        for me, inds, attrs in zip(self.inputs['Mesh'].sv_get(), indexes, attrs):
            mg = MeshGroup(me)
            group_elements = {'object': mg, 'faces': mg.faces, 'edges': mg.edges, 'verts': mg.verts, 'loops': mg.loops}
            mg.name = self.name
            mg.verts.links, mg.edges.links, mg.faces.links, mg.loops.links = generate_indexes(me, inds, self.element)
            if attrs:
                for atr_name, val in attrs.items():
                    set_safe_attr(group_elements[self.attr_element], atr_name, val)
            me.groups[self.name] = mg
        self.outputs['Mesh'].sv_set(self.inputs['Mesh'].sv_get())


def register():
    bpy.utils.register_class(SvMeshGroup)


def unregister():
    bpy.utils.unregister_class(SvMeshGroup)


if __name__ == "__main__":
    """
    3    4    5
    ┌────┬────┐
    │    │    │
    └────┴────┘
    0    1    2
    """
    verts = [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 0], [1, 1, 0], [2, 1, 0]]
    edges = [[0, 1], [1, 2], [3, 4], [4, 5], [0, 1], [1, 4], [2, 5]]
    faces = [[0, 1, 4, 3], [1, 2, 5, 4]]

    mesh = Mesh()
    mesh.verts = np.array(verts, np.float32)
    mesh.edges = np.array(edges, np.int32)
    mesh.faces = faces

    vert_indexes = [1, 2, 4, 5]
    edge_indexes = [1, 3, 5, 6]
    face_indexes = [1]
    loop_indexes = [1, 2, 4, 5, 6, 7]
    assert [vert_indexes, edge_indexes, face_indexes, loop_indexes] == [a.tolist() for a in generate_indexes(mesh, vert_indexes, 'verts')]
    assert [vert_indexes, edge_indexes, face_indexes, loop_indexes] == [a.tolist() for a in generate_indexes(mesh, edge_indexes, 'edges')]
    assert [vert_indexes, edge_indexes, face_indexes, [4, 5, 6, 7]] == [a.tolist() for a in generate_indexes(mesh, face_indexes, 'faces')]

    # ++++++++++++++++++++++++++++
    # Speed test of face handling
    # Selection faces from selected vertex
    from timeit import timeit
    import numpy as np

    faces_2d = np.arange(1000000).reshape(-1, 4)
    selected_verts = np.arange(500000, 600000)

    py_faces = faces_2d.tolist()
    py_selected_verts = selected_verts.tolist()

    def python_impl(faces, selected):
        selected = set(selected)
        return [True if all([i in selected for i in f]) else False for f in faces]

    def use_isin_2d_faces(faces, selected):
        return np.isin(faces, selected, True).all(axis=1)

    def use_sets_2d_faces(faces, selected):
        selected = set(selected)
        face_selected = np.empty(len(faces))
        for i, f in enumerate(faces):
            face_selected[i] = True if all([i in selected for i in f]) else False
        return face_selected

    face_loops = np.ravel(faces_2d)
    face_slices = np.column_stack((np.arange(0, 1000000, 4), np.arange(4, 1000001, 4)))
    face_slices2 = np.arange(0, 1000000, 4)

    def flat_faces(loops, selected, slices):
        selected_loops = np.isin(loops, selected, True)
        selected_slices = np.empty(len(slices))
        for i, sl in enumerate(slices):
            val = selected_loops[range(*sl)].all(axis=0)
            selected_slices[i] = val
        return selected_slices

    def use_reduceat_flat_faces(loops, selected, slices):  # <- winner
        selected_loops = np.isin(loops, selected, True)
        return np.logical_and.reduceat(selected_loops, slices)

    assert (np.array(python_impl(py_faces, py_selected_verts)) == use_isin_2d_faces(faces_2d, selected_verts)).all()
    assert (np.array(python_impl(py_faces, py_selected_verts)) == use_reduceat_flat_faces(face_loops, selected_verts, face_slices2)).all()

    print("Test Python - ", timeit("python_impl(py_faces, py_selected_verts)", "from __main__ import python_impl, py_faces, py_selected_verts", number=1))
    print("Test 1 - ", timeit("use_isin_2d_faces(faces_2d, selected_verts)", "from __main__ import use_isin_2d_faces, faces_2d, selected_verts", number=1))
    print("Test 2 - ", timeit("use_sets_2d_faces(faces_2d, selected_verts)", "from __main__ import use_sets_2d_faces, faces_2d, selected_verts", number=1))
    print("Test 3 - ", timeit("flat_faces(face_loops, selected_verts, face_slices)", "from __main__ import flat_faces, face_loops, selected_verts, face_slices", number=1))
    print("Test 4 - ", timeit("use_reduceat_flat_faces(face_loops, selected_verts, face_slices2)", "from __main__ import use_reduceat_flat_faces, face_loops, selected_verts, face_slices2", number=1))

    # Selection vertex from selected faces
    from itertools import count

    selected_faces = np.arange(75000, 100000)
    face_starts = np.arange(0, 1000000, 4)
    face_totals = np.repeat(4, 250000)
    py_selected_faces = selected_faces.tolist()
    ind_iter = count()
    py_faces = [[next(ind_iter) for _ in range(4)] for _ in range(250000)]

    def py_select_verts():
        return list(set([i for ind in py_selected_faces for i in py_faces[ind]]))

    def np_select_verts():
        face_mask = np.isin(np.arange(250000), selected_faces, True)
        loop_mask = np.repeat(face_mask, face_totals)
        return np.unique(face_loops[loop_mask])

    def np_select_verts2():
        face_mask = np.zeros(len(face_starts), np.bool)
        face_mask[selected_faces] = True
        loop_mask = np.repeat(face_mask, face_totals)
        return np.unique(face_loops[loop_mask])

    assert np.array_equal(py_select_verts(), np_select_verts())
    assert np.array_equal(py_select_verts(), np_select_verts2())

    print("Test Python - ", timeit("py_select_verts()", "from __main__ import py_select_verts", number=1))
    print("Test Numpy - ", timeit("np_select_verts()", "from __main__ import np_select_verts", number=1))
    print("Test Numpy2 - ", timeit("np_select_verts2()", "from __main__ import np_select_verts2", number=1))
