from itertools import chain, islice, accumulate

import numpy as np






class SvPolygon:
    def __init__(self, faces=None, loop_info=None, vertex_indices=None):
        if faces:
            self.loop_info = np.zeros((len(faces), 2),dtype=np.uint32)
            self.loop_info[:, 0] = tuple(map(len, faces))
            self.loop_info[1:,1] = self.loop_info[:-1,0].cumsum()
            self.vertex_indices = np.fromiter(chain.from_iterable(faces),
                                              dtype=np.uint32,
                                              count=self.loop_info[:,0].sum())
       else:
           self.loop_info = loop_info
           self.vertex_indices = vertex_indices

    @classmethod
    def from_mesh(cls, mesh):
        

        sv_poly = cls()


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
