# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Union, Any, Dict, Type, NamedTuple
from enum import Enum

import numpy as np


class BlenderAttributes(Enum):
    vertex_colors = 1
    material_index = 2


class Elements(NamedTuple):
    object: Union['Mesh', 'MeshGroup']
    faces: Union['Faces', 'FacesGroup']
    edges: Union['Edges', 'EdgesGroup']
    vertices: Union['Verts', 'VertsGroup']
    loops: Union['Loops', 'LoopsGroup']

    def get_elements_above(self, element: Union['MeshElements', 'GroupElements'])\
            -> List[Union['MeshElements', 'GroupElements']]:
        return self[self.index(element):0:-1]


class ObjectAttrs(ABC):
    def __init__(self):
        super().__init__()
        self.vertex_colors: np.ndarray = np.array([], np.float32)
        self.material_index: int = 0

    @property
    @abstractmethod
    def faces(self) -> 'MeshElements': ...

    @property
    @abstractmethod
    def edges(self) -> 'MeshElements': ...

    @property
    @abstractmethod
    def verts(self) -> 'MeshElements': ...

    @property
    @abstractmethod
    def loops(self) -> 'MeshElements': ...

    def values_to_loops(self, value: Any) -> np.ndarray:
        return np.repeat(value[np.newaxis], len(self.loops), 0)

    def values_to_faces(self, value: Any) -> np.ndarray:
        return np.repeat(value, len(self.faces))

    def search_element_with_attr(self, start: str, name: str) -> 'MeshElements':
        search_order = ['loops', 'verts', 'edges', 'faces', 'mesh']
        elements = [self.loops, self.verts, self.edges, self.faces, self]
        for element in elements[search_order.index(start):]:
            attr_values = getattr(element, name, None)
            if attr_values is not None:
                if hasattr(attr_values, '__iter__'):
                    if len(attr_values):
                        return element
                else:
                    return element


class ElementUserAttributes:
    def __init__(self):
        super().__init__()
        self._user_attrs = dict()

    def get_attribute(self, name: str) -> Any:
        if name in self._user_attrs:
            values = getattr(self, name, None)
            if values:
                return values
        raise AttributeError(f"Attribute={name} does not found in element={self}")

    def set_attribute(self, name: str, value: Any, owner_id: int):
        self._user_attrs[name] = owner_id
        setattr(self, name, value)

    def has_attribute(self, name: str) -> bool:
        return name in self._user_attrs


class Mesh(ObjectAttrs, ElementUserAttributes):

    def __init__(self):
        super().__init__()
        self.name: str = 'Sv mesh'
        self.materials: List[str] = []

        self.groups: Dict[str, MeshGroup] = dict()

        self._verts = Verts(self)
        self._edges = Edges(self)
        self._faces = Faces(self)
        self._loops = Loops(self)

        self._elements = Elements(self, self._faces, self._edges, self._verts, self._loops)

    def set(self, verts: np.ndarray, edges: np.ndarray = None, faces: list = None):
        self._verts.co = np.asarray(verts, np.float32)
        if edges:
            self._edges.ind = np.asarray(edges, np.int32)
        if faces:
            self._faces.set(faces)
            self._loops.ind = np.array([i for f in faces for i in f], np.int32)

    def get(self) -> Tuple[np.ndarray, np.ndarray, list]:
        return self._verts.co, self._edges.ind, self._faces.get(self._loops.ind)

    def to_bmesh(self, bm) -> None:
        bm_verts = [bm.verts.new(v) for v in self._verts]
        _ = [bm.edges.new([bm_verts[i] for i in e]) for e in self._edges]
        _ = [bm.faces.new([bm_verts[i] for i in f]) for f in self._faces.get(self._loops.ind)]

    def set_element_attribute(self, element: 'MeshElements', name: str, value: Any): ...

    @property
    def verts(self):
        return self._verts

    @verts.setter
    def verts(self, verts: np.ndarray):
        self._verts.co = verts

    @property
    def edges(self):
        return self._edges

    @edges.setter
    def edges(self, edges):
        self._edges.ind = edges

    @property
    def faces(self):
        return self._faces

    @faces.setter
    def faces(self, faces):
        self._faces.set(faces)

    @property
    def loops(self):
        return self._loops

    def sv_deep_copy(self) -> 'Mesh': ...

    def __repr__(self):
        return f"<SvMesh: name='{self.name}', verts={len(self.verts.co)}, edges={len(self.edges.ind)}," \
               f" faces={len(self.faces.ind)}>"

    def _search_element_with_attr(self, from_element: 'MeshElements', name: str) -> 'MeshElements':
        for nex_element in self._elements.get_elements_above(from_element):
            if nex_element.has_attribute(name):
                return nex_element


class Iterable(ABC):

    def __bool__(self) -> bool:
        return bool(len(self._main_attr))

    def __len__(self) -> int:
        return len(self._main_attr)

    def __iter__(self) -> 'Iterable':
        return iter(self._main_attr)

    def __getitem__(self, item):
        return self._main_attr[item]

    @property
    @abstractmethod
    def _main_attr(self): ...


class Verts(Iterable, ElementUserAttributes):
    def __init__(self, mesh: Mesh):
        super().__init__()
        self.mesh: Mesh = mesh
        self.co: np.ndarray = []

    @property
    def _main_attr(self):
        return self.co

    def values_to_loops(self, values: list) -> list:
        last_ind = len(values) - 1
        loop_inds = self.mesh.loops.ind
        loop_inds[loop_inds > last_ind] = last_ind
        return values[loop_inds]


class Edges(Iterable, ElementUserAttributes):
    def __init__(self, mesh: Mesh):
        super().__init__()
        self.mesh: Mesh = mesh
        self.ind: np.ndarray = np.array([], np.int32)

    @property
    def _main_attr(self):
        return self.ind

    def values_to_verts(self, values: list) -> np.ndarray:
        verts_values = np.zeros((len(self.mesh.verts), len(values[0])))
        values = ensure_array_length(values, len(self))
        np.add.at(verts_values, self.ind, values[:, np.newaxis])
        _, vert_number = np.unique(self.ind, return_counts=True)
        verts_values /= vert_number[:, np.newaxis]
        return verts_values

    def values_to_loops(self, values: list) -> np.ndarray:
        return self.mesh.verts.values_to_loops(self.values_to_verts(values))


class Faces(Iterable, ElementUserAttributes):
    def __init__(self, mesh: Mesh):
        super().__init__()
        self.loop_starts = np.array([], np.int32)
        self.loop_totals = np.array([], np.int32)

    def get(self, loops_ind: np.ndarray) -> list:
        return np.split(loops_ind, self.loop_starts[1:])

    def set(self, faces: list):
        self.loop_totals = np.fromiter(map(len, faces), np.int32)
        self.loop_starts = np.add.accumulate(np.concatenate(([0], self.loop_totals[:-1])))

    def values_to_loops(self, values: list) -> np.ndarray:
        values = ensure_array_length(values, len(self))
        return np.repeat(values, self.loop_totals, 0)

    def values_to_faces(self, values: list) -> np.ndarray:
        return ensure_array_length(values, len(self))

    @property
    def _main_attr(self):
        return self.loop_starts


class Loops(Iterable, ElementUserAttributes):
    def __init__(self, mesh: Mesh):
        super().__init__()
        self.mesh: Mesh = mesh
        self.uv: np.ndarray = np.array([], np.float32)

        self.ind: np.ndarray = np.array([], np.int32)

    def values_to_loops(self, values: list) -> np.ndarray:
        return ensure_array_length(values, len(self))

    @property
    def _main_attr(self):
        return self.ind


class MeshGroup(ObjectAttrs):
    def __init__(self, mesh):
        super().__init__()
        self.name: str = "MG.001"
        self.mesh: Mesh = mesh

        self._verts: VertsGroup = VertsGroup(self)
        self._edges: EdgesGroup = EdgesGroup(self)
        self._faces: FacesGroup = FacesGroup(self)
        self._loops: LoopsGroup = LoopsGroup(self)

    @property
    def verts(self):
        return self._verts

    @property
    def edges(self):
        return self._edges

    @property
    def faces(self):
        return self._faces

    @property
    def loops(self):
        return self._loops


class VertsGroup(Iterable, ElementUserAttributes):
    def __init__(self, group):
        super().__init__()
        self.group: MeshGroup = group
        self._links: np.ndarray = np.array([], np.int32)
        self.link_sorter = np.array([], np.int32)

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, indexes):
        self._links = indexes
        self.link_sorter = np.argsort(indexes)

    @property
    def _main_attr(self):
        return self.links

    def values_to_loops(self, values: list) -> np.ndarray:
        values_to_loops_mask = self.link_sorter[np.searchsorted(self.links, self.group.loops.ind, sorter=self.link_sorter)]
        np.clip(values_to_loops_mask, None, len(values) - 1, out=values_to_loops_mask)
        return values[values_to_loops_mask]


class EdgesGroup(Iterable, ElementUserAttributes):
    def __init__(self, group):
        super().__init__()
        self.group: MeshGroup = group
        self.links: np.ndarray = np.array([], np.int32)
        # self.link_sorter = np.array([], np.int32)

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, indexes):
        self._links = indexes
        # self.link_sorter = np.argsort(indexes)

    @property
    def ind(self):
        return self.group.mesh.edges.ind[self.links]

    @property
    def _main_attr(self):
        return self.links

    def values_to_loops(self, values: list) -> np.ndarray:
        edge_sorter = np.argsort(np.ravel(self.ind))
        loop_mask = edge_sorter[np.searchsorted(np.ravel(self.ind), self.group.loops.ind, sorter=edge_sorter)]
        loop_mask[np.asarray(loop_mask % 2, np.bool)] -= 1
        loop_mask //= 2
        np.clip(loop_mask, None, len(values) - 1, out=loop_mask)
        return values[loop_mask]

    def values_to_verts(self, values: list) -> np.ndarray:
        raise NotImplementedError


class FacesGroup(Iterable, ElementUserAttributes):
    def __init__(self, group):
        super().__init__()
        self.group: MeshGroup = group

        self.links: np.ndarray = np.array([], np.int32)
        self.link_sorter = np.array([], np.int32)

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, indexes):
        self._links = indexes
        self.link_sorter = np.argsort(indexes)

    @property
    def ind(self):
        return self.group.mesh.faces.ind[self.links]

    @property
    def _main_attr(self):
        return self.links

    def values_to_loops(self, values: list) -> np.ndarray:
        loop_mask = np.arange(len(self))
        loop_mask = np.repeat(loop_mask, self.ind[:, 1] - self.ind[:, 0])
        np.clip(loop_mask, None, len(values) - 1, out=loop_mask)
        return values[loop_mask]

    def values_to_faces(self, values: list) -> np.ndarray:
        return ensure_array_length(values, len(self))


class LoopsGroup(Iterable, ElementUserAttributes):
    def __init__(self, group):
        super().__init__()
        self.group: MeshGroup = group
        self.links: np.ndarray = np.array([], np.int32)

    @property
    def links(self):
        return self._links

    @property
    def ind(self):
        return self.group.mesh.loops[self.links]

    @links.setter
    def links(self, values):
        # should be with a same order as face.links
        self._links = values

    @property
    def _main_attr(self):
        return self.links

    def values_to_loops(self, values: list) -> np.ndarray:
        loop_mask = np.clip(self.links, None, len(values) - 1)
        return values[loop_mask]


MeshElements = Union[Mesh, Faces, Edges, Verts, Loops]
GroupElements = Union[MeshGroup, FacesGroup, EdgesGroup, VertsGroup, LoopsGroup]


def ensure_array_length(array: np.ndarray, length: int) -> np.ndarray:
    if len(array) == length:
        return array
    elif len(array) > length:
        return array[:length]
    else:
        tail = np.repeat(array[-1][np.newaxis], length - len(array), 0)
        return np.concatenate((array, tail))


if __name__ == '__main__':
    me = Mesh()
    me.verts = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]

    assert bool(me.verts)
    assert len(me.verts) == 4
    assert iter(me.verts)
    assert me.verts[0] == (0, 0, 0)

    me.faces = [[0, 1, 3], [1, 2, 3]]

    assert bool(me.faces)
    assert len(me.faces) == 2
    assert iter(me.faces)
    assert not bool(me.edges)
    assert bool(me.loops)
    assert len(me.loops) == 6
    assert me.faces[1] == [1, 2, 3]
