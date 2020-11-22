# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


"""
Some benchmark

m = Matrix.Identity(4)
v = Vector((1,0,0))
timeit('(m @ v)[:]', 'from __main__ import m, v')  <--- 0.2413583000000017
timeit('tuple(m @ v)', 'from __main__ import m, v')  <--- 0.5317709999999352
"""

from functools import wraps
from itertools import cycle, count, tee
from typing import Iterator, Tuple, List, Union

import numpy as np

from mathutils import Matrix, Vector
from sverchok.utils.modules.matrix_utils import matrix_apply_np

Vertex = Tuple[float, float, float]
Edge = Tuple[int, int]
Polygon = List[int]
PyMesh = Tuple[List[Vertex], List[Edge], List[Polygon]]

NpVertexes = np.ndarray
NpMesh = Tuple[NpVertexes, List[Edge], List[Polygon]]

Mesh = Union[PyMesh, NpMesh]


def meshes_py(vertices: List[List[Vertex]],
              edges: List[List[Edge]] = None,
              polygons: List[List[Polygon]] = None) -> Iterator[PyMesh]:
    yield from zip(vertices, edges or cycle([None]), polygons or cycle([None]))


def meshes_np(vertices: List[NpVertexes],
              edges: List[List[Edge]] = None,
              polygons: List[List[Polygon]] = None) -> Iterator[NpMesh]:
    vertices = np.asarray(vertices, dtype=np.float32)
    yield from zip(vertices, edges or cycle([None]), polygons or cycle([None]))


def pass_mesh_type(gen_func):
    @wraps(gen_func)
    def wrapper(meshes: Iterator[Mesh], *args, **kwargs):
        meshes, _meshes = tee(meshes)
        vertices, edges, polygons = next(_meshes)
        mesh_type = 'NP' if isinstance(vertices, np.ndarray) else 'PY'
        return gen_func(meshes, *args, _mesh_type=mesh_type, **kwargs)
    return wrapper


@pass_mesh_type
def apply_matrix(meshes: Iterator[Mesh], matrices: Iterator[Matrix], *, _mesh_type) -> Iterator[Mesh]:
    """It will generate new vertices with given matrix applied"""
    implementation = matrix_apply_np if _mesh_type == 'NP' else apply_matrix_to_vertices_py
    for (vertices, edges, polygons), matrix in zip(meshes, matrices):
        # several matrices can be applied to a mesh
        # in this case each matrix will populate geometry inside object
        sub_vertices = implementation(vertices, matrix)
        yield sub_vertices, edges, polygons


@pass_mesh_type
def apply_matrices(meshes: Iterator[Mesh], matrices: Iterator[List[Matrix]], *, _mesh_type) -> Iterator[Mesh]:
    """It will generate new vertices with given matrix applied"""
    implementation = matrix_apply_np if _mesh_type == 'NP' else apply_matrix_to_vertices_py
    for (vertices, edges, polygons), _matrices in zip(meshes, matrices):
        # several matrices can be applied to a mesh
        # in this case each matrix will populate geometry inside object
        sub_vertices = []
        sub_edges = [edges] * len(_matrices) if edges else None
        sub_polygons = [polygons] * len(_matrices) if polygons else None
        for matrix in _matrices:
            sub_vertices.append(implementation(vertices, matrix))

        yield from join_meshes(meshes_py(sub_vertices, sub_edges, sub_polygons))


@pass_mesh_type
def join_meshes(meshes: Iterator[PyMesh], *, _mesh_type) -> Iterator[PyMesh]:
    _vertices = []
    # joined_vertices = []
    joined_edges = []
    joined_polygons = []
    vertexes_number = 0
    for vertices, edges, polygons in meshes:
        if edges:
            joined_edges.extend([(e[0] + vertexes_number, e[1] + vertexes_number) for e in edges])
        if polygons:
            joined_polygons.extend([[i + vertexes_number for i in p] for p in polygons])
        vertexes_number += len(vertices)
        # joined_vertices.extend(vertices)
        _vertices.append(vertices)
    implementation = np.concatenate if _mesh_type == 'NP' else lambda vs: [v for _vs in vs for v in _vs]
    joined_vertices = implementation(_vertices)
    yield joined_vertices, joined_edges, joined_polygons


def to_elements(meshes: Iterator[PyMesh]) -> Tuple[List[List[Vertex]],
                                                   List[List[Edge]],
                                                   List[List[Polygon]]]:
    vertices, edges, polygons = zip(*meshes)
    edges = edges if edges[0] else []
    polygons = polygons if polygons[0] else []
    return vertices, edges, polygons


def repeat_meshes(meshes: Iterator[Mesh], number: int = -1) -> Iterator[Mesh]:
    counter = count()
    last = None
    while next(counter) != number:
        try:
            last = next(meshes)
        except StopIteration:
            pass
        yield last


def apply_matrix_to_vertices_py(vertices: List[Vertex], matrix: Matrix) -> List[Vertex]:
    return [(matrix @ Vector(v)).to_tuple() for v in vertices]
