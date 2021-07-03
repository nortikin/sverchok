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

from sverchok.data_structure import get_data_nesting_level, is_ultimately
from sverchok.utils.field.vector import SvVectorField, SvMatrixVectorField, SvConstantVectorField
from sverchok.utils.field.scalar import SvScalarField, SvConstantScalarField
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.solid_conversion import to_solid_recursive

from mathutils import Matrix, Quaternion
from numpy import ndarray

SOCKET_TYPES = {
    'v': 'SvVerticesSocket',
    's': 'SvStringsSocket',
    'm': 'SvMatrixSocket',
    'q': 'SvQuaternionSocket',
    'c': 'SvColorSocket',
    'vf': "SvVectorFieldSocket",
    'sf': 'SvScalarFieldSocket'
    }

def test_socket_type(self, other, A, B):
    """ A is origin type, B is destination type """
    return other.bl_idname == SOCKET_TYPES[A] and self.bl_idname == SOCKET_TYPES[B]

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


def is_matrix(mat):  # doesn't work with Mathutils.Matrix ?
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
    if isinstance(data, (list, tuple)):
        return [matrices_to_vfield(item) for item in data]

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

def vectors_to_matrices(socket, source_data):
    # this means we're going to get a flat list of the incoming
    # locations and convert those into matrices proper.
    out = get_matrices_from_locs(source_data)
    socket.num_matrices = len(out)
    return out

def matrices_to_vectors(socket, source_data):
    return get_locs_from_matrices(source_data)

def quaternions_to_matrices(socket, source_data):
    out = get_matrices_from_quaternions(source_data)
    socket.num_matrices = len(out)
    return out

def matrices_to_quaternions(socket, source_data):
    return get_quaternions_from_matrices(source_data)

def string_to_vector(socket, source_data):
    # it can be so that socket is string but data their are already vectors, performance-wise we check only first item
    if isinstance(source_data[0][0], (float, int)):
        return [[(v, v, v) for v in obj] for obj in source_data]
    return source_data


def string_to_color(socket, source_data):
    # it can be so that socket is string but data their are already colors, performance-wise we check only first item
    if isinstance(source_data[0][0], (float, int)):
        return [[(v, v, v, 1) for v in obj] for obj in source_data]
    if len(source_data[0][0]) == 3:
        return vector_to_color(socket, source_data)
    return source_data

def vector_to_color(socket, source_data):

    return [[(v[0], v[1], v[2], 1) for v in obj] for obj in source_data]

class ImplicitConversionProhibited(Exception):
    def __init__(self, socket, msg=None):
        super().__init__()
        self.socket = socket
        self.node = socket.node
        self.from_socket_type = socket.other.bl_idname
        self.to_socket_type = socket.bl_idname
        if msg is None:
            self.message = "Implicit conversion from socket type {} to socket type {} is not supported for socket {} of node {}. Please use explicit conversion nodes.".format(self.from_socket_type, self.to_socket_type, socket.name, socket.node.name)
        else:
            self.message = msg

    def __str__(self):
        return self.message


class NoImplicitConversionPolicy():
    """
    Base (empty) implicit conversion policy.
    This prohibits any implicit conversions.
    """
    @classmethod
    def convert(cls, socket, other, source_data):
        raise ImplicitConversionProhibited(socket)


class LenientImplicitConversionPolicy():
    """
    Lenient implicit conversion policy.
    Does not actually convert anything, but passes any
    type of data as-is.
    To be used for sockets that do not care about the
    nature of data they process (such as most List processing
    nodes).
    """
    @classmethod
    def convert(cls, socket, other, source_data):
        return source_data


class DefaultImplicitConversionPolicy(NoImplicitConversionPolicy):
    """
    Default implicit conversion policy.
    """
    tests = [
        ['v', 'm', vectors_to_matrices],
        ['m', 'v', matrices_to_vectors],
        ['q', 'm', quaternions_to_matrices],
        ['m', 'q', matrices_to_quaternions],
        ['s', 'v', string_to_vector],
        ['s', 'c', string_to_color],
        ['v', 'c', vector_to_color]]

    @classmethod
    def convert(cls, socket, other, source_data):

        for t in cls.tests:
            if test_socket_type(socket, other, t[0], t[1]):
                return t[2](socket, source_data)
        if socket.bl_idname in cls.get_lenient_socket_types():
            return source_data
        if cls.data_type_check(socket, other, source_data):
            return source_data

        return super().convert(socket, other, source_data)

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
    def data_type_check(cls, socket, other, source_data):
        checking_sockets = cls.get_data_type_checking_socket_types()
        expected_type = checking_sockets.get(socket.bl_idname)
        if expected_type is None:
            return False
        if not other.bl_idname in cls.get_arbitrary_type_socket_types():
            return False
        return is_ultimately(source_data, expected_type)


class FieldImplicitConversionPolicy(DefaultImplicitConversionPolicy):
    @classmethod
    def convert(cls, socket, other, source_data):
        # let policy to decide if deep copy of data is needed
        if test_socket_type(socket, other, 'm', 'vf'):
            return matrices_to_vfield(source_data)
        if test_socket_type(socket, other, 'v', 'vf'):
            return vertices_to_vfield(source_data)
        if test_socket_type(socket, other, 's', 'sf'):
            level = get_data_nesting_level(source_data)
            if level > 2:
                raise TypeError("Too high data nesting level for Number -> Scalar Field conversion: %s" % level)
            return numbers_to_sfield(source_data)

        return super().convert(socket, other, source_data)


class SolidImplicitConversionPolicy(NoImplicitConversionPolicy):
    @classmethod
    def convert(cls, socket, other, source_data):
        try:
            return to_solid_recursive(source_data)
        except TypeError as e:
            raise ImplicitConversionProhibited(socket, msg=f"Cannot perform implicit socket conversion for socket {socket.name}: {e}")


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
