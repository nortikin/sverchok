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
from copy import deepcopy
from enum import Enum

from sverchok.data_structure import get_other_socket, get_data_nesting_level
from sverchok.utils.field.vector import SvVectorField, SvMatrixVectorField, SvConstantVectorField
from sverchok.utils.field.scalar import SvScalarField, SvConstantScalarField
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.solid_conversion import to_solid_recursive

from mathutils import Matrix, Quaternion
from numpy import ndarray

# conversion tests, to be used in sv_get!

def cross_test_socket(self, A, B):
    """ A is origin type, B is destination type """
    other = get_other_socket(self)
    get_type = {'v': 'SvVerticesSocket', 'm': 'SvMatrixSocket', 'q': "SvQuaternionSocket"}
    return other.bl_idname == get_type[A] and self.bl_idname == get_type[B]


def is_vector_to_matrix(self):
    return cross_test_socket(self, 'v', 'm')


def is_matrix_to_vector(self):
    return cross_test_socket(self, 'm', 'v')


def is_matrix_to_quaternion(self):
    return cross_test_socket(self, 'm', 'q')


def is_quaternion_to_matrix(self):
    return cross_test_socket(self, 'q', 'm')

def is_matrix_to_vfield(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvMatrixSocket' and socket.bl_idname == 'SvVectorFieldSocket'

def is_vertex_to_vfield(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvVerticesSocket' and socket.bl_idname == 'SvVectorFieldSocket'

def is_string_to_sfield(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvStringsSocket' and socket.bl_idname == 'SvScalarFieldSocket'

def is_ultimately(data, data_type):
    if isinstance(data, (list, tuple)):
        return is_ultimately(data[0], data_type)
    return isinstance(data, data_type)


def is_string_to_vector(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvStringsSocket' and socket.bl_idname == 'SvVerticesSocket'

# ---


def get_matrices_from_locs(data):
    location_matrices = []
    collect_matrix = location_matrices.append

    def get_all(data):
        for item in data:
            if isinstance(item, (tuple, list, ndarray)) and len(item) == 3 and isinstance(item[0], (float, int)):
                # generate location matrix from location
                x, y, z = item
                collect_matrix(Matrix([(1., .0, .0, x), (.0, 1., .0, y), (.0, .0, 1., z), (.0, .0, .0, 1.)]))
            else:
                get_all(item)

    get_all(data)
    return location_matrices


def get_matrices_from_quaternions(data):
    matrices = []
    collect_matrix = matrices.append

    def get_all(data):
        for item in data:
            if isinstance(item, (tuple, list)) and len(item) == 4 and isinstance(item[0], (float, int)):
                mat = Quaternion(item).to_matrix().to_4x4()
                collect_matrix(mat)
            else:
                get_all(item)

    get_all(data)
    return matrices


def get_quaternions_from_matrices(data):
    quaternions = []
    collect_quaternion = quaternions.append

    def get_all(data):
        for mat in data:
            q = tuple(mat.to_quaternion())
            collect_quaternion(q)

    get_all(data)
    return [quaternions]


def is_matrix(mat):  # doesnt work with Mathutils.Matrix ?
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
            collect_vector(sublist.to_translation()[:])

    get_all(data)
    return [locations]

def matrices_to_vfield(data):
    if isinstance(data, Matrix):
        data = deepcopy(data)
        return SvMatrixVectorField(data)
    elif isinstance(data, (list, tuple)):
        return [matrices_to_vfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from Matrix socket: %s" % type(data))

def vertices_to_vfield(data):
    if isinstance(data, (tuple, list)) and len(data) == 3 and isinstance(data[0], (float, int)):
        data = deepcopy(data)
        return SvConstantVectorField(data)
    elif isinstance(data, (list, tuple)):
        return [vertices_to_vfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from Vertex socket: %s" % type(data))

def numbers_to_sfield(data):
    if isinstance(data, (int, float)):
        return SvConstantScalarField(data)
    elif isinstance(data, (list, tuple)):
        return [numbers_to_sfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from String socket: %s" % type(data))

class ImplicitConversionProhibited(Exception):
    def __init__(self, socket, msg=None):
        super().__init__()
        self.socket = socket
        self.node = socket.node
        self.from_socket_type = socket.other.bl_idname
        self.to_socket_type = socket.bl_idname
        self.message = "Implicit conversion from socket type {} to socket type {} is not supported for socket {} of node {}. Please use explicit conversion nodes.".format(self.from_socket_type, self.to_socket_type, socket.name, socket.node.name)
        if msg is not None:
            self.message += "\nReason: " + msg

    def __str__(self):
        return self.message

class NoImplicitConversionPolicy(object):
    """
    Base (empty) implicit conversion policy.
    This prohibits any implicit conversions.
    """
    @classmethod
    def convert(cls, socket, source_data):
        raise ImplicitConversionProhibited(socket)

class LenientImplicitConversionPolicy(object):
    """
    Lenient implicit conversion policy.
    Does not actually convert anything, but passes any
    type of data as-is.
    To be used for sockets that do not care about the
    nature of data they process (such as most List processing
    nodes).
    """
    @classmethod
    def convert(cls, socket, source_data):
        return source_data

class DefaultImplicitConversionPolicy(NoImplicitConversionPolicy):
    """
    Default implicit conversion policy.
    """
    @classmethod
    def convert(cls, socket, source_data):
        # let policy to decide if deep copy of data is needed
        if is_vector_to_matrix(socket):
            return cls.vectors_to_matrices(socket, source_data)
        elif is_matrix_to_vector(socket):
            return cls.matrices_to_vectors(socket, source_data)
        elif is_quaternion_to_matrix(socket):
            return cls.quaternions_to_matrices(socket, source_data)
        elif is_matrix_to_quaternion(socket):
            return cls.matrices_to_quaternions(socket, source_data)
        elif is_string_to_vector(socket):
            return cls.string_to_vector(socket, source_data)
        elif socket.bl_idname in cls.get_lenient_socket_types():
            return source_data
        elif cls.data_type_check(socket, source_data):
            return source_data
        else:
            super().convert(socket, source_data)

    @classmethod
    def get_lenient_socket_types(cls):
        """
        Return collection of bl_idnames of socket classes
        that are allowed to consume arbitrary data type.
        """
        return ['SvStringsSocket', 'SvObjectSocket', 'SvColorSocket', 'SvVerticesSocket']

    @classmethod
    def get_data_type_checking_socket_types(cls):
        return {'SvScalarFieldSocket': SvScalarField,
                'SvVectorFieldSocket': SvVectorField,
                'SvSurfaceSocket': SvSurface,
                'SvCurveSocket': SvCurve}

    @classmethod
    def get_arbitrary_type_socket_types(cls):
        return ['SvStringsSocket']

    @classmethod
    def data_type_check(cls, socket, source_data):
        checking_sockets = cls.get_data_type_checking_socket_types()
        expected_type = checking_sockets.get(socket.bl_idname)
        if expected_type is None:
            return False
        if not get_other_socket(socket).bl_idname in cls.get_arbitrary_type_socket_types():
            return False
        return is_ultimately(source_data, expected_type)

    @classmethod
    def vectors_to_matrices(cls, socket, source_data):
        # this means we're going to get a flat list of the incoming
        # locations and convert those into matrices proper.
        out = get_matrices_from_locs(source_data)
        socket.num_matrices = len(out)
        return out

    @classmethod
    def matrices_to_vectors(cls, socket, source_data):
        return get_locs_from_matrices(source_data)

    @classmethod
    def quaternions_to_matrices(cls, socket, source_data):
        out = get_matrices_from_quaternions(source_data)
        socket.num_matrices = len(out)
        return out

    @classmethod
    def matrices_to_quaternions(cls, socket, source_data):
        return get_quaternions_from_matrices(source_data)

    @classmethod
    def string_to_vector(cls, socket, source_data):
        # it can be so that socket is string but data their are already vectors
        return [[(v, v, v) if isinstance(v, (float, int)) else v for v in obj] for obj in source_data]


class FieldImplicitConversionPolicy(DefaultImplicitConversionPolicy):
    @classmethod
    def convert(cls, socket, source_data):
        # let policy to decide if deep copy of data is needed
        if is_matrix_to_vfield(socket):
            return matrices_to_vfield(source_data) 
        elif is_vertex_to_vfield(socket):
            return vertices_to_vfield(source_data)
        elif is_string_to_sfield(socket):
            level = get_data_nesting_level(source_data)
            if level > 2:
                raise TypeError("Too high data nesting level for Number -> Scalar Field conversion: %s" % level)
            return numbers_to_sfield(source_data)
        else:
            super().convert(socket, source_data)

class SolidImplicitConversionPolicy(NoImplicitConversionPolicy):
    @classmethod
    def convert(cls, socket, source_data):
        try:
            return to_solid_recursive(source_data)
        except TypeError as e:
            raise ImplicitConversionProhibited(socket, msg=str(e))

class ConversionPolicies(Enum):
    """It should keeps all policy classes"""
    DEFAULT = DefaultImplicitConversionPolicy
    FIELD = FieldImplicitConversionPolicy
    LENIENT = LenientImplicitConversionPolicy
    SOLID = SolidImplicitConversionPolicy

    @property
    def conversion(self):
        return self.value

    @property
    def conversion_name(self):
        return self.value.__name__

    @classmethod
    def get_conversion(cls, conversion_name: str):
        for enum in cls:
            if conversion_name == enum.conversion_name:
                return enum.conversion
        raise LookupError(f"Conversion policy with name={conversion_name} was not found,"
                          f"Available names: {[e.conversion_name for e in cls]}")

