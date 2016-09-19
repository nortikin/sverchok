from itertools import chain, islice, accumulate

import numpy as np
from mathutils.geometry import normal

class Mesh:
    @classmethod
    def from_mesh(cls, mesh):
        return cls(SvVertices.from_mesh(mesh), SvPolygon.from_mesh(mesh))

    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces

    def calc_normals(self):
        """
        Face normals
        """
        normals = np.empty((len(self.faces), 3))
        for idx, face in enumerate(self.faces):
            normals[idx] = normal(self.vertices[face])
        self.faces.normals = normals


class SvVertices:
    @classmethod
    def from_mesh(cls, mesh):
        vertices = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", vertices)
        vertices.shape = (len(mesh.vertices), 3)
        return cls(vertices)

    def __getitem__(self, key):
        return self.vertices[key]

    def __init__(self, vertices):
        self.vertices = vertices

class SvPolygon:
    @classmethod
    def from_pydata(cls, faces):

        loop_info = np.zeros((len(faces), 2),dtype=np.uint32)
        loop_info[:, 0] = tuple(map(len, faces))
        loop_info[1:,1] = loop_info[:-1,0].cumsum()
        vertex_indices = np.fromiter(chain.from_iterable(faces),
                                     dtype=np.uint32,
                                     count=self.loop_info[:,0].sum())
        return cls(loop_info, vertex_indices)

    def __init__(self, loop_info=None, vertex_indices=None):
       self.loop_info = loop_info
       self.vertex_indices = vertex_indices

    @classmethod
    def from_mesh(cls, mesh):
        loop = np.zeros((len(mesh.polygons), 2), dtype=np.uint32)
        mesh.polygons.foreach_get("loop_total", loop[:,0])
        mesh.polygons.foreach_get("loop_start", loop[:,1])
        vertex_indices = np.empty(len(mesh.loops), dtype=np.uint32)
        mesh.loops.foreach_get("vertex_index", vertex_indices)
        return cls(loop, vertex_indices)


    def __getitem__(self, key):
        loop_start = self.loop_info[key, 1]
        loop_stop = loop_start + self.loop_info[key, 0]
        return self.vertex_indices[loop_start: loop_stop]

    def __len__(self):
        return self.loop_info.shape[0]

    def as_pydata(self):
        return [tuple(face) for face in self]

    def join(self, poly):
        offset = len(poly.vertex_indices)
        face_count = len(self)
        self.loop_info = np.concatenate((self.loop_info, poly.loop_info))
        self.vertex_indices = np.concatenate((self.vertex_indices, poly.vertex_indices + offset))
        self.loop_info[face_count:,1] += offset
