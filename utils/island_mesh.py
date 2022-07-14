from collections import namedtuple
from itertools import accumulate
import random

import numpy as np
from sverchok.data_structure import fixed_iter


Attribute = namedtuple('Attribute', ['data', 'domain'])


class IslandMesh:
    """Standard Sverchok mesh data structure which also marks its separate parts
    useful to join a lot of small meshes, perform operation and separate them mack"""

    def __init__(self, obj_verts, obj_edges=None, obj_faces=None):
        """Join mesh objects and calculate island indexes for each domain"""
        self.verts = []
        self.edges = []
        self.faces = []
        self.vert_islands = np.zeros(sum(len(vs) for vs in obj_verts), dtype=int)
        self.edge_islands = np.zeros(sum(len(es) for es in obj_edges or []), dtype=int)
        self.face_islands = np.zeros(sum(len(fs) for fs in obj_faces or []), dtype=int)
        self._attributes: dict[str, Attribute] = dict()

        vert_num = list(accumulate(obj_verts, lambda t, el: t + len(el), initial=0))

        for verts in obj_verts:
            self.verts.extend(verts)
            self.vert_islands[len(self.verts):] += 1

        for v_num, edges in zip(vert_num, obj_edges) if obj_edges else []:
            self.edges.extend((e[0] + v_num, e[1] + v_num) for e in edges)
            self.edge_islands[len(self.edges):] += 1

        for v_num, faces in zip(vert_num, obj_faces) if obj_faces else []:
            self.faces.extend([i + v_num for i in f] for f in faces)
            self.face_islands[len(self.faces):] += 1

    def set_attribute(self, name, data, domain='FACE'):
        """Should be used right after initialization"""
        if not data:
            return
        sorted_islands = self._get_islands(domain)
        out = []
        indexes, sizes = np.unique(sorted_islands, return_counts=True)
        for i, s in zip(indexes, sizes):
            try:
                d = data[i]
            except IndexError:
                d = data[-1]

            if len(d) == s:
                out.extend(d)
            else:
                out.extend(list(fixed_iter(d, s)))
        self._attributes[name] = Attribute(out, domain)

    def get_attribute(self, name):
        return self._attributes[name].data

    def split_islands(self) -> tuple[list, list, list]:
        """Return separate meshes for each island"""
        indexes = np.unique(self.vert_islands)  # should be the same for all elem types

        new_v_indexes = []
        for isl_i in indexes:
            d = {new_: i for i, new_ in enumerate(np.where(self.vert_islands == isl_i)[0])}
            new_v_indexes.append(d)

        out_verts = []
        for new_indexes in new_v_indexes:
            out_verts.append([self.verts[i] for i in new_indexes.keys()])

        out_edges = []
        for isl_i, v_ind in zip(indexes, new_v_indexes):
            es = []
            for i in np.where(self.edge_islands == isl_i)[0]:
                edge = self.edges[i]
                es.append((v_ind[edge[0]], v_ind[edge[1]]))
            out_edges.append(es)

        out_faces = []
        for isl_i, v_ind in zip(indexes, new_v_indexes):
            fs = []
            for i in np.where(self.face_islands == isl_i)[0]:
                face = self.faces[i]
                fs.append([v_ind[i] for i in face])
            out_faces.append(fs)

        return out_verts, out_edges, out_faces

    def split_attribute(self, name) -> list:
        attr = self._attributes[name]
        islands = self._get_islands(attr.domain)
        indexes = np.unique(islands)
        out = []
        for isl_i in indexes:
            out.append([attr.data[i] for i in np.where(islands == isl_i)[0]])
        return out

    def shuffle_mesh(self, seed=0):
        """Change order of elements randomly"""
        random.seed(seed)

        verts_order = list(range(len(self.verts)))
        random.shuffle(verts_order)
        self.verts = [self.verts[i] for i in verts_order]
        self.vert_islands = self.vert_islands[verts_order]

        new_indexes = {new: i for i, new in enumerate(verts_order)}

        edges_order = list(range(len(self.edges)))
        random.shuffle(edges_order)
        self.edges = [(new_indexes[e[0]], new_indexes[e[1]]) for e in self.edges]
        self.edges = [self.edges[i] for i in edges_order]
        self.edge_islands = self.edge_islands[edges_order]

        faces_order = list(range(len(self.faces)))
        random.shuffle(faces_order)
        self.faces = [[new_indexes[i] for i in f] for f in self.faces]
        self.faces = [self.faces[i] for i in faces_order]
        self.face_islands = self.face_islands[faces_order]

        for name, (data, domain) in self._attributes.items():
            if domain == 'FACE':
                order = faces_order
            elif domain == 'POINT':
                order = verts_order
            elif domain == 'EDGE':
                order = edges_order
            else:
                raise TypeError(f"Unknown {domain=}")
            self._attributes[name] = Attribute([data[i] for i in order], domain)

    def _get_islands(self, domain='FACE'):
        if domain == 'FACE':
            return self.face_islands
        elif domain == 'POINT':
            return self.vert_islands
        elif domain == 'EDGE':
            return self.edge_islands
        else:
            raise TypeError(f"Unknown {domain=}")
