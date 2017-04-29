# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from sverchok.data_structure import get_other_socket


## conversion tests, to be used in sv_get! 

def cross_test_socket(self, A, B):
    """ A is origin type, B is destination type """
    other = get_other_socket(self)
    get_type = {'v': 'VerticesSocket', 'm': 'MatrixSocket'}
    return other.bl_idname == get_type[A] and self.bl_idname == get_type[B]

def is_vector_to_matrix(self):
    return cross_test_socket(self, 'v', 'm')

def is_matrix_to_vector(self):
    return cross_test_socket(self, 'm', 'v')

# ---

def get_matrices_from_locs(data):
    location_matrices = []
    collect_matrix = location_matrices.append

    def get_all(data):
        for item in data:
            if isinstance(item, (tuple, list)) and len(item) == 3 and isinstance(item[0], (float, int)):
                # generate location matrix from location
                x, y, z = item
                collect_matrix([(1., .0, .0, x), (.0, 1., .0, y), (.0, .0, 1., z), (.0, .0, .0, 1.)])
            else:
                get_all(item)

    get_all(data)
    return location_matrices


def is_matrix(mat):
    ''' expensive function call? '''
    if not isinstance(mat, (tuple, list)) or not len(mat) == 4:
        return

    for i in range(4):
        if isinstance(mat[i], (tuple, list)):
            if not (len(mat[i]) == 4 and all([isinstance(j, (float, int)) for j in mat[i]])):
                return
        else:
            return
    return True


def get_locs_from_matrices(data):
    locations = []
    collect_vector = locations.append

    def get_all(data):

        for sublist in data:
            if is_matrix(sublist):
                collect_vector((sublist[0][3], sublist[1][3], sublist[2][3]))
            else:
                get_all(sublist)

    get_all(data)
    return locations
