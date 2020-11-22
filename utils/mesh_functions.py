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

from itertools import cycle, count
from typing import Iterator, Tuple, List

from mathutils import Matrix, Vector

Vertex = Tuple[float, float, float]
Edge = Tuple[int, int]
Polygon = List[int]
Mesh = Tuple[List[Vertex], List[Edge], List[Polygon]]


def py_meshes(vertices: List[List[Vertex]],
              edges: List[List[Edge]] = None,
              polygons: List[List[Polygon]] = None) -> Iterator[Mesh]:
    yield from zip(vertices, edges or cycle([None]), polygons or cycle([None]))


def apply_matrices(meshes: Iterator[Mesh], matrices: Iterator[List[Matrix]]) -> Iterator[Mesh]:
    """It will generate new vertices with given matrix applied"""
    for (vertices, edges, polygons), _matrices in zip(meshes, matrices):
        # several matrices can be applied to a mesh
        # in this case each matrix will populate geometry inside object
        sub_vertices = []
        sub_edges = [edges] * len(_matrices) if edges else None
        sub_polygons = [polygons] * len(_matrices) if polygons else None
        for matrix in _matrices:
            sub_vertices.append([tuple(matrix @ Vector(v)) for v in vertices])

        yield from join_meshes(py_meshes(sub_vertices, sub_edges, sub_polygons))


def apply_matrix(meshes: Iterator[Mesh], matrices: Iterator[Matrix]) -> Iterator[Mesh]:
    """It will generate new vertices with given matrix applied"""
    for (vertices, edges, polygons), matrix in zip(meshes, matrices):
        # several matrices can be applied to a mesh
        # in this case each matrix will populate geometry inside object
        sub_vertices = [(matrix @ Vector(v)).to_tuple() for v in vertices]
        yield sub_vertices, edges, polygons


def join_meshes(meshes: Iterator[Mesh]) -> Iterator[Mesh]:
    joined_vertices = []
    joined_edges = []
    joined_polygons = []
    for vertices, edges, polygons in meshes:
        if edges:
            joined_edges.extend([(e[0] + len(joined_vertices), e[1] + len(joined_vertices)) for e in edges])
        if polygons:
            joined_polygons.extend([[i + len(joined_vertices) for i in p] for p in polygons])
        joined_vertices.extend(vertices)
    yield joined_vertices, joined_edges, joined_polygons


def to_elements(meshes: Iterator[Mesh]) -> Tuple[List[List[Vertex]],
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
