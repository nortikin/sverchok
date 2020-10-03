# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
It is important to import this module like that: import meshes
And do this from meshes import PyMesh
It can bring unexpected errors
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Tuple, List, Callable, Union, Type, Iterable

import numpy as np

from mathutils import Matrix, Vector
from sverchok.utils.modules.matrix_utils import matrix_apply_np

PyVertex = Tuple[float, float, float]
PyEdge = Tuple[int, int]
PyPolygon = List[int]


def to_mesh(vertices, edges=None, polygons=None) -> Mesh:
    if isinstance(vertices, (list, tuple)):
        return PyMesh(vertices, edges, polygons)
    elif isinstance(vertices, np.ndarray):
        return NpMesh(vertices, edges, polygons)
    else:
        raise TypeError(f'Vertices type "{type(vertices).__name__}" is not in: list, tuple, np.ndarray')


class Mesh(ABC):

    @abstractmethod
    def add_mesh(self, mesh) -> Mesh: ...

    @abstractmethod
    def cast(self, mesh_type) -> Mesh: ...

    @abstractmethod
    def apply_matrix(self, matrix) -> Mesh: ...


def convert_mesh_type(method: Callable) -> Callable:
    @wraps(method)
    def wrap_method(base_mesh, mesh, *args, **kwargs):
        mesh = mesh.cast(type(base_mesh))
        return method(base_mesh, mesh, *args, **kwargs)
    return wrap_method


class PyMesh(Mesh):
    """Data structure of Python mesh and its basic operations"""
    def __init__(self, vertices: List[PyVertex], edges: List[PyEdge] = None, polygons: List[PyPolygon] = None):
        self.vertices = vertices
        self.edges = edges or []
        self.polygons = polygons or []

    @convert_mesh_type
    def add_mesh(self, mesh: PyMesh) -> PyMesh:
        """To join many meshes - reduce(lambda m1, m2: m1.add_mesh(m2), [mesh, mesh, mesh, mesh])"""
        self_vertices_number = len(self.vertices)
        self.vertices.extend(mesh.vertices)
        self.edges.extend([(edge[0] + self_vertices_number, edge[1] + self_vertices_number) for edge in mesh.edges])
        self.polygons.extend([[i + self_vertices_number for i in face] for face in mesh.polygons])
        return self

    def apply_matrix(self, matrix: Matrix) -> PyMesh:
        self.vertices = [tuple(matrix @ Vector(v)) for v in self.vertices]
        return self

    def cast(self, mesh_type: Type[Mesh]) -> Mesh:
        if mesh_type == PyMesh:
            return self
        elif mesh_type == NpMesh:
            return NpMesh(self.vertices, self.edges, self.polygons)
        else:
            raise TypeError(f'"{type(self).__name__}" type can not be converted to {mesh_type.__name__}')


class NpMesh(Mesh):
    def __init__(self, vertices: Iterable, edges: List[PyEdge] = None, polygons: List[PyPolygon] = None):
        self.vertices = np.asarray(vertices, dtype=np.float32)  # array is copied only if dtype does not match
        self.edges = edges or []
        self.polygons = polygons or []

    @convert_mesh_type
    def add_mesh(self, mesh: NpMesh) -> NpMesh:
        self_vertices_number = len(self.vertices)
        self.vertices = np.concatenate([self.vertices, mesh.vertices])
        self.edges.extend([(edge[0] + self_vertices_number, edge[1] + self_vertices_number) for edge in mesh.edges])
        self.polygons.extend([[i + self_vertices_number for i in face] for face in mesh.polygons])
        return self

    def apply_matrix(self, matrix) -> NpMesh:
        self.vertices = matrix_apply_np(self.vertices, matrix)
        return self

    def cast(self, mesh_type: Type[Mesh]) -> Mesh:
        if mesh_type == PyMesh:
            return PyMesh(self.vertices.tolist(), self.edges, self.polygons)
        elif mesh_type == NpMesh:
            return self
        else:
            raise TypeError(f'"{type(self).__name__}" type can not be converted to {mesh_type.__name__}')
