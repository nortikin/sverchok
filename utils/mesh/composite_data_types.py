#composite_data_types.py

# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import functools
import operator
import numpy as np
from collections import defaultdict
from dataclasses import dataclass

"""        
mpl = PolyList(m)
prin(mpl.sparse_matrix)
flatlist, starts_ends = mpl.loops
prin(starts_ends)    

for idx_range in np.nditer(starts_ends.T, flags=['external_loop'], order='F'):
    prin(flatlist[idx_range[0]:idx_range[1]])


def my_function(row):
    row_without_nans = row[~np.isnan(row)]
    return sum(row_without_nans)

k = np.apply_along_axis(my_function, axis=1, arr=mpl.sparse_matrix)


"""

@dataclass
class PolyList(list):
    array: list

    def get_max_dims(self):
        """ return num rows and length of longest row """
        return len(self.array), max(map(len, self.array))

    @property
    def loops(self):
        flat = np.array(functools.reduce(operator.iconcat, self.array, []))
        
        start_indices, end_indices = [], []
        add_start, add_end = start_indices.append, end_indices.append
        
        sum_state = 0
        for row in self.array:
            add_start(sum_state)
            sum_state = sum_state + len(row)
            add_end(sum_state)

        return flat, np.vstack((start_indices, end_indices)).T
    
    @property
    def sparse_matrix(self):
        f = self.get_max_dims()
        M = np.full(f, np.nan)

        for idx, x in enumerate(M):
            rsize = len(m[idx])
            M[idx][:rsize] = m[idx]
        return M
 

class CompositeList():
    """
    - map the incoming polygon list to a collection of tris, quads and ngons
    - make a remap lookup, which allows the user to treat the content of this class as a continguous array
    - provide a generic set of functions which return normals (face, edge and vertex on demand), and tesselations
    """
    def __init__(self, plist):
        self.num_polygons = len(plist)
        self.remap = defaultdict(tuple)
        self.tris = []
        self.quads = []
        self.ngons = []
        self.add_tri = self.tris.append
        self.add_quad = self.quads.append
        self.add_ngon = self.ngons.append
        index_polygons(self, plist)
        
        # create numpy representations
        self.np_tris = np.array(self.tris, dtype="i32")
        self.np_quads = np.array(self.quads, dtype="i32")
        self.np_ngons = PolyList(self.ngons)

    def index_polygons(self, plist):
        for idx, p in enumerate(plist):
            length = len(p)
            if length == 3:
                self.remap[idx] = (0, len(self.tris))
                self.add_tri(p)
            elif length == 4:
                self.remap[idx] = (1, len(self.quads))
                self.add_quad(p)
            else:
                self.remap[idx] = (2, len(self.ngons))
                self.add_ngon(p)

        # polylist will need to be widend if a new ngon exceeds largest existing ngon


    def extend(self, items):
        ...
    def append(self, item):
        ...

    def lookup(self, idx):
        if idx < self.num_polygons:
            index_type, index_list = self.remap.get(idx)
            return [self.tris, self.quads, self.ngons][index_type][index_list]
        else:
            raise IndexError





