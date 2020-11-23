# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
The module provide basic operations with meshes
Also support several mesh types
All mesh types share the same API so user should not know which type of mesh is used

It is important to import this module like that: import meshes
And don't do this: from meshes import PyMesh
It can bring unexpected errors
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Collection
from functools import wraps
from itertools import chain
from typing import Tuple, List, Callable, Union, Type, Iterable, Dict

import numpy as np

from mathutils import Matrix, Vector

from sverchok.data_structure import fixed_iter
from sverchok.utils.modules.matrix_utils import matrix_apply_np


PyVertex = Tuple[float, float, float]
PyEdge = Tuple[int, int]
PyPolygon = List[int]


def to_mesh(vertices, edges=None, polygons=None) -> Union[PyMesh, NpMesh]:
    """Convert mesh elements into a mesh with type dependent on type of given elements"""
    if isinstance(vertices, (list, tuple)):
        return PyMesh(vertices, edges, polygons)
    elif isinstance(vertices, np.ndarray):
        return NpMesh(vertices, edges, polygons)
    else:
        raise TypeError(f'Vertices type "{type(vertices).__name__}" is not in: list, tuple, np.ndarray')


def join(meshes: List[Mesh], return_type: Type[Mesh] = None) -> Mesh:
    """efficiently join data of given meshes into one"""
    if return_type is None:
        return_type = type(meshes[0])

    out_mesh = return_type([], [], [])
    added_vertices = 0
    for mesh in meshes:
        elements = [(out_mesh.vertices, mesh.vertices), (out_mesh.edges, mesh.edges),
                    (out_mesh.polygons, mesh.polygons)]
        for out_elem, elem in elements:
            for attr in out_elem.attributes | elem.attributes:
                out_data = out_elem.get_attribute(attr)
                data = elem.get_attribute(attr)
                if out_data is None:
                    out_data = [data[0]] * len(out_elem)
                else:
                    out_data = fix_len(out_data, len(out_elem))
                out_data.extend(data or [])
                out_elem[attr] = out_data

        out_mesh.vertices.data.extend(mesh.vertices.data)
        out_mesh.edges.data.extend([i + added_vertices for i in e] for e in mesh.edges)
        out_mesh.polygons.data.extend([i + added_vertices for i in p] for p in mesh.polygons)
        added_vertices += len(mesh.vertices)

    return out_mesh


class Mesh(ABC):

    @property
    def vertices(self) -> MeshElements:
        return self._vertices

    @property
    def edges(self) -> MeshElements:
        return self._edges

    @property
    def polygons(self) -> MeshElements:
        return self._polygons

    @abstractmethod
    def add_mesh(self, mesh) -> Mesh: ...

    @abstractmethod
    def cast(self, mesh_type) -> Mesh: ...

    @abstractmethod
    def apply_matrix(self, matrix) -> Mesh: ...

    def __repr__(self):
        return f'<MESH vertices={len(self.vertices)} [{", ".join(self.vertices.attributes)}], ' \
               f'edges={len(self.edges)} [{", ".join(self.edges.attributes)}], ' \
               f'polygons={len(self.polygons)} [{", ".join(self.polygons.attributes)}]>'


def convert_mesh_type(method: Callable) -> Callable:
    """
    Decorator for methods with mesh as first argument
    it will convert this attribute into the same type as type of the class of the method
    mesh class should have `cast` method which will be called to convert mesh
    """
    @wraps(method)
    def wrap_method(base_mesh, mesh, *args, **kwargs):
        mesh = mesh.cast(type(base_mesh))
        return method(base_mesh, mesh, *args, **kwargs)
    return wrap_method


class PyMesh(Mesh):
    """
    Data structure of Python mesh and its basic operations
    Its methods always generates new lists so there is no need in list.copy()
    """
    def __init__(self, vertices: List[PyVertex], edges: List[PyEdge] = None, polygons: List[PyPolygon] = None):
        # Example usage: PyMesh(vertices, edges, faces).polygons['materials'] = [0, 1, 1, ...]
        self._vertices = MeshElements(vertices)
        self._edges = MeshElements(edges or [])
        self._polygons = MeshElements(polygons or [])

    @convert_mesh_type
    def add_mesh(self, mesh: PyMesh) -> PyMesh:
        """To join many meshes - reduce(lambda m1, m2: m1.add_mesh(m2), [mesh, mesh, mesh, mesh])"""
        self_vertices_number = len(self.vertices)
        self.vertices.join_data(mesh.vertices)
        mesh.edges.data = [(edge[0] + self_vertices_number, edge[1] + self_vertices_number) for edge in mesh.edges]
        self.edges.join_data(mesh.edges)
        mesh.polygons.data = [[i + self_vertices_number for i in face] for face in mesh.polygons]
        self.polygons.join_data(mesh.polygons)

        return self

    def apply_matrix(self, matrix: Matrix) -> PyMesh:
        """It will generate new vertices with given matrix applied"""
        self.vertices.data = [(matrix @ Vector(v)).to_tuple() for v in self.vertices]
        return self

    def cast(self, mesh_type: Type[Mesh]) -> Mesh:
        """Convert itself into other mesh types"""
        if mesh_type == PyMesh:
            return self
        elif mesh_type == NpMesh:
            cast_mesh = NpMesh(self.vertices.data, self.edges.data, self.polygons.data)
            cast_mesh.vertices.copy_attributes(self.vertices)
            cast_mesh.edges.copy_attributes(self.edges)
            cast_mesh.polygons.copy_attributes(self.polygons)
            return cast_mesh
        else:
            raise TypeError(f'"{type(self).__name__}" type can not be converted to {mesh_type.__name__}')


class NpMesh(Mesh):
    """
    Numpy mesh data structure
    For keeping balance between simplicity and efficiency only vertices has numpy format
    """
    def __init__(self, vertices: Iterable, edges: List[PyEdge] = None, polygons: List[PyPolygon] = None):
        # array is copied only if dtype does not match
        self._vertices = MeshElements(np.asarray(vertices, dtype=np.float32))
        self._edges = MeshElements(edges or [])
        self._polygons = MeshElements(polygons or [])

    @convert_mesh_type
    def add_mesh(self, mesh: NpMesh) -> NpMesh:
        """To join many meshes - reduce(lambda m1, m2: m1.add_mesh(m2), [mesh, mesh, mesh, mesh])"""
        self_vertices_number = len(self.vertices)
        self.vertices.join_data(mesh.vertices)
        mesh.edges.data = [(edge[0] + self_vertices_number, edge[1] + self_vertices_number) for edge in mesh.edges]
        self.edges.join_data(mesh.edges)
        mesh.polygons.data = [[i + self_vertices_number for i in face] for face in mesh.polygons]
        self.polygons.join_data(mesh.polygons)
        return self

    def apply_matrix(self, matrix) -> NpMesh:
        """It will generate new vertices with given matrix applied"""
        self.vertices.data = matrix_apply_np(self.vertices.data, matrix)
        return self

    def cast(self, mesh_type: Type[Mesh]) -> Mesh:
        """Convert itself into other mesh types"""
        if mesh_type == PyMesh:
            cast_mesh = PyMesh(self.vertices.data.tolist(), self.edges.data, self.polygons.data)
            cast_mesh.vertices.copy_attributes(self.vertices)
            cast_mesh.edges.copy_attributes(self.edges)
            cast_mesh.polygons.copy_attributes(self.polygons)
            return cast_mesh
        elif mesh_type == NpMesh:
            return self
        else:
            raise TypeError(f'"{type(self).__name__}" type can not be converted to {mesh_type.__name__}')


class MeshElements(Collection):
    """
    Class for data of mesh elements such as vertices, edges, polygons
    Main reason of this class is to keep elements attributes

    It supports:
    iteration over elements - [vertex for vertex in mesh.vertices]
    check if list of elements is not empty - if mesh.vertices: "There are some vertices in mesh"
    gen number of elements - polygon_number = len(mesh.polygons)
    set attributes to elements - mesh.polygons['material'] = material_indexes
    get attributes of elements - vertex_colors = mesh.vertices['vertex color']
    """
    def __init__(self, data: Union[list, np.ndarray]):
        """Data should be vertices, edges or faces"""
        self.data = data

        # given data can has its attributes
        # data can has different length then actual number of elements (vertices, edges, polygons)
        self._attrs: Dict[str, list] = dict()

    def join_data(self, other: MeshElements):
        """
        Merging two elements data into first
        Also attributes are merged
        """
        if self._attrs or other._attrs:
            for key in self._attrs.keys() | other._attrs.keys():
                self._attrs[key] = list(chain(fixed_iter(self._attrs.get(key), len(self.data)),
                                              fixed_iter(other._attrs.get(key), len(other.data))))
        if isinstance(self.data, list):
            self.data = self.data + other.data
        elif isinstance(self.data, np.ndarray):
            self.data = np.concatenate([self.data, other.data])
        else:
            raise TypeError(f'Type "{type(self.data).__name__}" of "data" attribute does not supported')

    def copy_attributes(self, other: MeshElements):
        """Copy attributes from given other mesh elements"""
        self._attrs.update(other._attrs)

    def get_attribute(self, attr: str, default=None) -> list:
        """Get elements attribute, using instead of polygons['attr']"""
        return self._attrs.get(attr, default)

    @property
    def attributes(self):
        return self._attrs.keys()

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, item):
        return item in self.data

    def __bool__(self):
        return bool(self.data)

    def __getitem__(self, item):
        return self._attrs[item]

    def __setitem__(self, key, value):
        self._attrs[key] = value

    def __delitem__(self, key):
        del self._attrs[key]


def fix_len(lst: list, length: int) -> list:
    """
    timeit('fix_len(l, 99999)', 'from __main__ import fix_len; l = list(range(100000))', number=1)
    0.0011104999998678977
    timeit('fix_len(l, 100000)', 'from __main__ import fix_len; l = list(range(100000))', number=1)
    4.699999863078119e-06
    timeit('fix_len(l, 100001)', 'from __main__ import fix_len; l = list(range(100000))', number=1)
    5.7999995988211595e-06
    """
    if len(lst) == length:
        return lst
    elif len(lst) > length:
        return lst[:length]
    else:
        lst.extend([lst[-1]] * (length - len(lst)))
        return lst
