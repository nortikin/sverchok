# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.math import (
            from_cylindrical, from_spherical,
            from_cylindrical_np, to_cylindrical_np,
            from_spherical_np, to_spherical_np)
from sverchok.utils.field.vector import SvVectorField

class SvVectorFieldBinOp(SvVectorField):
    def __init__(self, field1, field2, function):
        self.function = function
        self.field1 = field1
        self.field2 = field2
        self.__description__ = f"<BinOp ({field1}, {field2})>"

    def evaluate(self, x, y, z):
        return self.function(self.field1.evaluate(x, y, z), self.field2.evaluate(x, y, z))

    def evaluate_grid(self, xs, ys, zs):
        def func(xs, ys, zs):
            vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
            vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
            R = self.function(np.array([vx1, vy1, vz1]), np.array([vx2, vy2, vz2]))
            return R[0], R[1], R[2]
        return np.vectorize(func, signature="(m),(m),(m)->(m),(m),(m)")(xs, ys, zs)

class SvAverageVectorField(SvVectorField):

    def __init__(self, fields):
        self.fields = fields
        self.__description__ = "Average"

    def evaluate(self, x, y, z):
        vectors = np.array([field.evaluate(x, y, z) for field in self.fields])
        return np.mean(vectors, axis=0)

    def evaluate_grid(self, xs, ys, zs):
        def func(xs, ys, zs):
            data = []
            for field in self.fields:
                vx, vy, vz = field.evaluate_grid(xs, ys, zs)
                vectors = np.stack((vx, vy, vz)).T
                data.append(vectors)
            data = np.array(data)
            mean = np.mean(data, axis=0).T
            return mean[0], mean[1], mean[2]
        return np.vectorize(func, signature="(m),(m),(m)->(m),(m),(m)")(xs, ys, zs)

class SvVectorFieldCrossProduct(SvVectorField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "{} x {}".format(field1, field2)

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x, y, z)
        v2 = self.field2.evaluate(x, y, z)
        return np.cross(v1, v2)

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T
        R = np.cross(vectors1, vectors2).T
        return R[0], R[1], R[2]

class SvVectorFieldMultipliedByScalar(SvVectorField):
    def __init__(self, vector_field, scalar_field):
        self.vector_field = vector_field
        self.scalar_field = scalar_field
        self.__description__ = "{} * {}".format(scalar_field, vector_field)

    def evaluate(self, x, y, z):
        scalar = self.scalar_field.evaluate(x, y, z)
        vector = self.vector_field.evaluate(x, y, z)
        return scalar * vector

    def evaluate_grid(self, xs, ys, zs):
        def product(xs, ys, zs):
            scalars = self.scalar_field.evaluate_grid(xs, ys, zs)
            vx, vy, vz = self.vector_field.evaluate_grid(xs, ys, zs)
            vectors = np.stack((vx, vy, vz))
            R = (scalars * vectors)
            return R[0], R[1], R[2]
        return np.vectorize(product, signature="(m),(m),(m)->(m),(m),(m)")(xs, ys, zs)

class SvVectorFieldsLerp(SvVectorField):

    def __init__(self, vfield1, vfield2, scalar_field):
        self.vfield1 = vfield1
        self.vfield2 = vfield2
        self.scalar_field = scalar_field
        self.__description__ = "Lerp"

    def evaluate(self, x, y, z):
        scalar = self.scalar_field.evaluate(x, y, z)
        vector1 = self.vfield1.evaluate(x, y, z)
        vector2 = self.vfield2.evaluate(x, y, z)
        return (1 - scalar) * vector1 + scalar * vector2

    def evaluate_grid(self, xs, ys, zs):
        scalars = self.scalar_field.evaluate_grid(xs, ys, zs)
        vx1, vy1, vz1 = self.vfield1.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1))
        vx2, vy2, vz2 = self.vfield2.evaluate_grid(xs, ys, zs)
        vectors2 = np.stack((vx2, vy2, vz2))
        R = (1 - scalars) * vectors1 + scalars * vectors2
        return R[0], R[1], R[2]

class SvComposedVectorField(SvVectorField):
    def __init__(self, coords, sfield1, sfield2, sfield3):
        self.coords = coords
        self.sfield1 = sfield1
        self.sfield2 = sfield2
        self.sfield3 = sfield3
        self.__description__ = "{}({}, {}, {})".format(coords, sfield1, sfield2, sfield3)

    def evaluate(self, x, y, z):
        v1 = self.sfield1.evaluate(x, y, z)
        v2 = self.sfield2.evaluate(x, y, z)
        v3 = self.sfield3.evaluate(x, y, z)
        if self.coords == 'XYZ':
            return np.array((v1, v2, v3))
        elif self.coords == 'CYL':
            return np.array(from_cylindrical(v1, v2, v3, mode='radians'))
        else: # SPH:
            return np.array(from_spherical(v1, v2, v3, mode='radians'))

    def evaluate_grid(self, xs, ys, zs):
        v1s = self.sfield1.evaluate_grid(xs, ys, zs)
        v2s = self.sfield2.evaluate_grid(xs, ys, zs)
        v3s = self.sfield3.evaluate_grid(xs, ys, zs)
        if self.coords == 'XYZ':
            return v1s, v2s, v3s
        elif self.coords == 'CYL':
            vectors = np.stack((v1s, v2s, v3s)).T
            vectors = np.apply_along_axis(lambda v: np.array(from_cylindrical(*tuple(v), mode='radians')), 1, vectors).T
            return vectors[0], vectors[1], vectors[2]
        else: # SPH:
            vectors = np.stack((v1s, v2s, v3s)).T
            vectors = np.apply_along_axis(lambda v: np.array(from_spherical(*tuple(v), mode='radians')), 1, vectors).T
            return vectors[0], vectors[1], vectors[2]

class SvSelectVectorField(SvVectorField):
    def __init__(self, fields, mode):
        self.fields = fields
        self.mode = mode
        self.__description__ = "{}({})".format(mode, fields)

    def evaluate(self, x, y, z):
        vectors = [field.evaluate(x, y, z) for field in self.fields]
        vectors = np.array(vectors)
        norms = np.linalg.norm(vectors, axis=1)
        if self.mode == 'MIN':
            selected = np.argmin(norms)
        else: # MAX
            selected = np.argmax(norms)
        return vectors[selected]

    def evaluate_grid(self, xs, ys, zs):
        n = len(xs)
        vectors = [field.evaluate_grid(xs, ys, zs) for field in self.fields]
        vectors = np.stack(vectors)
        vectors = np.transpose(vectors, axes=(2,0,1))
        norms = np.linalg.norm(vectors, axis=2)
        if self.mode == 'MIN':
            selected = np.argmin(norms, axis=1)
        else: # MAX
            selected = np.argmax(norms, axis=1)
        all_points = list(range(n))
        vectors = vectors[all_points, selected, :]
        return vectors.T

class SvVectorFieldCartesianFilter(SvVectorField):
    def __init__(self, field, use_x=True, use_y=True, use_z=True):
        self.field = field
        self.use_x = use_x
        self.use_y = use_y
        self.use_z = use_z
        desc = ""
        if use_x:
            desc = desc + 'X'
        if use_y:
            desc = desc + 'Y'
        if use_z:
            desc = desc + 'Z'
        self.__description__ = f"Filter[{desc}]({field})"

    def evaluate_grid(self, xs, ys, zs):
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        if not self.use_x:
            vxs[:] = 0
        if not self.use_y:
            vys[:] = 0
        if not self.use_z:
            vzs[:] = 0
        return vxs, vys, vzs

class SvVectorFieldCylindricalFilter(SvVectorField):
    def __init__(self, field, use_rho=True, use_phi=True, use_z=True):
        self.field = field
        self.use_rho = use_rho
        self.use_phi = use_phi
        self.use_z = use_z

    def evaluate_grid(self, xs, ys, zs):
        pts = np.stack((xs,ys,zs)).T
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vectors = np.stack((vxs,vys,vzs)).T
        s_rho, s_phi, s_z = to_cylindrical_np(pts.T, mode='radians')
        v_rho, v_phi, v_z = to_cylindrical_np((pts + vectors).T, mode='radians')
        if not self.use_rho:
            v_rho = s_rho
        if not self.use_phi:
            v_phi = s_phi
        if not self.use_z:
            v_z = s_z
        v_x, v_y, v_z = from_cylindrical_np(v_rho, v_phi, v_z, mode='radians')
        return (v_x - xs), (v_y - ys), (v_z - zs)

class SvVectorFieldSphericalFilter(SvVectorField):
    def __init__(self, field, use_rho=True, use_phi=True, use_theta=True):
        self.field = field
        self.use_rho = use_rho
        self.use_phi = use_phi
        self.use_theta = use_theta

    def evaluate_grid(self, xs, ys, zs):
        pts = np.stack((xs,ys,zs)).T
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vectors = np.stack((vxs,vys,vzs)).T
        s_rho, s_phi, s_theta = to_spherical_np(pts.T, mode='radians')
        v_rho, v_phi, v_theta = to_spherical_np((pts + vectors).T, mode='radians')
        if not self.use_rho:
            v_rho = s_rho
        if not self.use_phi:
            v_phi = s_phi
        if not self.use_theta:
            v_theta = s_theta
        v_x, v_y, v_z = from_spherical_np(v_rho, v_phi, v_theta, mode='radians')
        return (v_x - xs), (v_y - ys), (v_z - zs)

class SvVectorFieldTangent(SvVectorField):

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "Tangent"

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x,y,z)
        projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
        return projection

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T

        def project(v1, v2):
            projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
            vx, vy, vz = projection
            return vx, vy, vz

        return np.vectorize(project, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvVectorFieldCotangent(SvVectorField):

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "Cotangent"

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x,y,z)
        projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
        return v1 - projection

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.stack((vx1, vy1, vz1)).T
        vectors2 = np.stack((vx2, vy2, vz2)).T

        def project(v1, v2):
            projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
            coprojection = v1 - projection
            vx, vy, vz = coprojection
            return vx, vy, vz

        return np.vectorize(project, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvVectorFieldComposition(SvVectorField):

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
        self.__description__ = "Composition"

    def evaluate(self, x, y, z):
        x1, y1, z1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x1,y1,z1)
        return v2

    def evaluate_grid(self, xs, ys, zs):
        r = self.field1.evaluate_grid(xs, ys, zs)
        vx1, vy1, vz1 = r
        return self.field2.evaluate_grid(vx1, vy1, vz1)

class SvPreserveCoordinateField(SvVectorField):
    def __init__(self, field, axis):
        self.field = field
        self.axis = axis

    def evaluate(self, x, y, z):
        xyz = self.field.evaluate(x, y, z)
        xyz = np.array(xyz)
        xyz[self.axis] = [x, y, z][self.axis]
        return xyz

    def evaluate_grid(self, xs, ys, zs):
        r = self.field.evaluate_grid(xs, ys, zs)
        r = np.array(r)
        r[self.axis] = [xs, ys, zs][self.axis]
        return r

