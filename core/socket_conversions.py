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

from sverchok.core.sv_custom_exceptions import ImplicitConversionProhibited
from sverchok.data_structure import get_data_nesting_level, is_ultimately, NUMERIC_DATA_TYPES
from sverchok.utils.field.vector import SvVectorField, SvMatrixVectorField, SvConstantVectorField
from sverchok.utils.field.scalar import SvScalarField, SvConstantScalarField
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.solid_conversion import to_solid_recursive

from mathutils import Matrix, Quaternion
import numpy as np
from numpy import ndarray


def matrices_to_vfield(data):
    if isinstance(data, Matrix):
        data = deepcopy(data)
        return SvMatrixVectorField(data)
    if isinstance(data, (list, tuple)):
        return [matrices_to_vfield(item) for item in data]

    raise TypeError("Unexpected data type from Matrix socket: %s" % type(data))


def vertices_to_vfield(data):
    if isinstance(data, (tuple, list)) and len(data) == 3 and isinstance(data[0], NUMERIC_DATA_TYPES):
        data = deepcopy(data)
        return SvConstantVectorField(data)
    elif isinstance(data, (list, tuple)):
        return [vertices_to_vfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from Vertex socket: %s" % type(data))


def numbers_to_sfield(data):
    if isinstance(data, NUMERIC_DATA_TYPES):
        return SvConstantScalarField(data)
    elif isinstance(data, (list, tuple)):
        return [numbers_to_sfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from String socket: %s" % type(data))


def vectors_to_matrices(source_data):
    """This means we're going to get a flat list of the incoming
    locations and convert those into matrices proper."""
    location_matrices = []
    collect_matrix = location_matrices.append

    def get_all(data):
        for item in data:
            if isinstance(item, (tuple, list, ndarray)) and len(item) == 3 and isinstance(item[0], NUMERIC_DATA_TYPES):
                # generate location matrix from location
                x, y, z = item
                collect_matrix(Matrix([(1., .0, .0, x), (.0, 1., .0, y), (.0, .0, 1., z), (.0, .0, .0, 1.)]))
            else:
                get_all(item)

    get_all(source_data)
    return location_matrices


def matrices_to_vectors(source_data):
    locations = []
    collect_vector = locations.append

    def get_all(data):
        for sublist in data:
            collect_vector(sublist.to_translation()[:])

    get_all(source_data)
    return [locations]


def quaternions_to_matrices(source_data):
    matrices = []
    collect_matrix = matrices.append

    def get_all(data):
        for item in data:
            if isinstance(item, (tuple, list)) and len(item) == 4 and isinstance(item[0], NUMERIC_DATA_TYPES):
                mat = Quaternion(item).to_matrix().to_4x4()
                collect_matrix(mat)
            else:
                get_all(item)

    get_all(source_data)
    return matrices


def matrices_to_quaternions(source_data):
    quaternions = []
    collect_quaternion = quaternions.append

    def get_all(data):
        for mat in data:
            q = tuple(mat.to_quaternion())
            collect_quaternion(q)

    get_all(source_data)
    return [quaternions]


def string_to_vector(source_data):
    # it can be so that socket is string but data their are already vectors, performance-wise we check only first item
    if isinstance(source_data[0][0], NUMERIC_DATA_TYPES):
        return [[(v, v, v) for v in obj] for obj in source_data]
    return source_data


def string_to_color(source_data):
    # it can be so that socket is string but data their are already colors, performance-wise we check only first item
    if isinstance(source_data[0][0], NUMERIC_DATA_TYPES):
        return [[(v, v, v, 1) for v in obj] for obj in source_data]
    if len(source_data[0][0]) == 3:
        return vector_to_color(source_data)
    return source_data


def vector_to_color(source_data):
    if source_data and isinstance(source_data[0], np.ndarray):
        out = []
        for obj in source_data:
            out.append(np.concatenate((obj, np.ones((len(obj), 1))), axis=1))
        return out
    else:
        return [[(v[0], v[1], v[2], 1) for v in obj] for obj in source_data]


class NoImplicitConversionPolicy:
    """
    Base (empty) implicit conversion policy.
    This prohibits any implicit conversions.
    """
    @classmethod
    def convert(cls, socket, other, source_data):
        raise ImplicitConversionProhibited(socket)


class LenientImplicitConversionPolicy:
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
    default_conversions = {
        ('SvVerticesSocket', 'SvMatrixSocket'): vectors_to_matrices,
        ('SvVerticesSocket', 'SvColorSocket'): vector_to_color,
        ('SvMatrixSocket', 'SvVerticesSocket'): matrices_to_vectors,
        ('SvMatrixSocket', 'SvQuaternionSocket'): matrices_to_quaternions,
        ('SvQuaternionSocket', 'SvMatrixSocket'): quaternions_to_matrices,
        ('SvStringsSocket', 'SvVerticesSocket'): string_to_vector,
        ('SvStringsSocket', 'SvColorSocket'): string_to_color,
    }

    # socket types that are allowed to consume arbitrary data type.
    lenient_socket_types = {
        'SvStringsSocket',
        'SvObjectSocket',
        'SvColorSocket',
        'SvVerticesSocket',
    }

    @classmethod
    def convert(cls, to_sock, from_sock, source_data):

        # apply default conversion
        convert_pattern = (from_sock.bl_idname, to_sock.bl_idname)
        if conversion := cls.default_conversions.get(convert_pattern):
            return conversion(source_data)

        # conversion is not needed
        elif to_sock.bl_idname in cls.lenient_socket_types \
                or cls.is_expected_type_from_string_socket(to_sock, from_sock, source_data):
            return source_data

        # raise exception
        super().convert(to_sock, from_sock, source_data)

    expected_data_types = {
        'SvScalarFieldSocket': SvScalarField,
        'SvVectorFieldSocket': SvVectorField,
        'SvSurfaceSocket': SvSurface,
        'SvCurveSocket': SvCurve,
    }

    @classmethod
    def is_expected_type_from_string_socket(cls, to_sock, from_sock, source_data):
        if from_sock.bl_idname != 'SvStringsSocket':
            return False
        if expected_type := cls.expected_data_types.get(to_sock.bl_idname):
            return is_ultimately(source_data, expected_type)


def check_nesting_level(func):
    def the_check(source_data):
        level = get_data_nesting_level(source_data)
        if level > 2:
            raise TypeError("Too high data nesting level for Number -> Scalar Field conversion: %s" % level)
        return func(source_data)
    return the_check


class FieldImplicitConversionPolicy(DefaultImplicitConversionPolicy):

    default_conversions = {
        ('SvMatrixSocket', 'SvVectorFieldSocket'): matrices_to_vfield,
        ('SvVerticesSocket', 'SvVectorFieldSocket'): vertices_to_vfield,
        ('SvStringsSocket', 'SvScalarFieldSocket'): check_nesting_level(numbers_to_sfield),
    }

    @classmethod
    def convert(cls, to_sock, from_sock, source_data):
        # let policy to decide if deep copy of data is needed
        types_pattern = (from_sock.bl_idname, to_sock.bl_idname)
        if conversion := cls.default_conversions.get(types_pattern):
            return conversion(source_data)
        return super().convert(to_sock, from_sock, source_data)


class SolidImplicitConversionPolicy(NoImplicitConversionPolicy):
    @classmethod
    def convert(cls, socket, other, source_data):
        try:
            return to_solid_recursive(source_data)
        except TypeError as e:
            raise ImplicitConversionProhibited(
                socket, msg=f"Cannot perform implicit socket conversion for"
                            f" socket {socket.name}: {e}")


conversions = {
    'DefaultImplicitConversionPolicy': DefaultImplicitConversionPolicy,
    'FieldImplicitConversionPolicy': FieldImplicitConversionPolicy,
    'LenientImplicitConversionPolicy': LenientImplicitConversionPolicy,
    'SolidImplicitConversionPolicy': SolidImplicitConversionPolicy,
}


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
