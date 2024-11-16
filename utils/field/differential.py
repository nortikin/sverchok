# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvVectorField

class SvScalarFieldGradient(SvVectorField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Grad({})".format(field)

    def evaluate(self, x, y, z):
        return self.field.gradient([x, y, z], step=self.step)

    def evaluate_grid(self, xs, ys, zs):
        return self.field.gradient_grid(xs, ys, zs, step=self.step)

class SvVectorFieldRotor(SvVectorField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Rot({})".format(field)

    def evaluate(self, x, y, z):
        step = self.step
        _, y_dx_plus, z_dx_plus = self.field.evaluate(x+step,y,z)
        _, y_dx_minus, z_dx_minus = self.field.evaluate(x-step,y,z)
        x_dy_plus, _, z_dy_plus = self.field.evaluate(x, y+step, z)
        x_dy_minus, _, z_dy_minus = self.field.evaluate(x, y-step, z)
        x_dz_plus, y_dz_plus, _ = self.field.evaluate(x, y, z+step)
        x_dz_minus, y_dz_minus, _ = self.field.evaluate(x, y, z-step)

        dy_dx = (y_dx_plus - y_dx_minus) / (2*step)
        dz_dx = (z_dx_plus - z_dx_minus) / (2*step)
        dx_dy = (x_dy_plus - x_dy_minus) / (2*step)
        dz_dy = (z_dy_plus - z_dy_minus) / (2*step)
        dx_dz = (x_dz_plus - x_dz_minus) / (2*step)
        dy_dz = (y_dz_plus - y_dz_minus) / (2*step)

        rx = dz_dy - dy_dz
        ry = - (dz_dx - dx_dz)
        rz = dy_dx - dx_dy

        return np.array([rx, ry, rz])

    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        _, y_dx_plus, z_dx_plus = self.field.evaluate_grid(xs+step,ys,zs)
        _, y_dx_minus, z_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        x_dy_plus, _, z_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        x_dy_minus, _, z_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        x_dz_plus, y_dz_plus, _ = self.field.evaluate_grid(xs, ys, zs+step)
        x_dz_minus, y_dz_minus, _ = self.field.evaluate_grid(xs, ys, zs-step)

        dy_dx = (y_dx_plus - y_dx_minus) / (2*step)
        dz_dx = (z_dx_plus - z_dx_minus) / (2*step)
        dx_dy = (x_dy_plus - x_dy_minus) / (2*step)
        dz_dy = (z_dy_plus - z_dy_minus) / (2*step)
        dx_dz = (x_dz_plus - x_dz_minus) / (2*step)
        dy_dz = (y_dz_plus - y_dz_minus) / (2*step)

        rx = dz_dy - dy_dz
        ry = - (dz_dx - dx_dz)
        rz = dy_dx - dx_dy
        R = np.stack((rx, ry, rz))
        return R[0], R[1], R[2]

class SvVectorFieldDivergence(SvScalarField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Div({})".format(field)

    def evaluate(self, x, y, z):
        step = self.step
        xs_dx_plus, _, _ = self.field.evaluate(x+step,y,z)
        xs_dx_minus, _, _ = self.field.evaluate(x-step,y,z)
        _, ys_dy_plus, _ = self.field.evaluate(x, y+step, z)
        _, ys_dy_minus, _ = self.field.evaluate(x, y-step, z)
        _, _, zs_dz_plus = self.field.evaluate(x, y, z+step)
        _, _, zs_dz_minus = self.field.evaluate(x, y, z-step)

        dx_dx = (xs_dx_plus - xs_dx_minus) / (2*step)
        dy_dy = (ys_dy_plus - ys_dy_minus) / (2*step)
        dz_dz = (zs_dz_plus - zs_dz_minus) / (2*step)

        return dx_dx + dy_dy + dz_dz
    
    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        xs_dx_plus, _, _ = self.field.evaluate_grid(xs+step, ys,zs)
        xs_dx_minus, _, _ = self.field.evaluate_grid(xs-step,ys,zs)
        _, ys_dy_plus, _ = self.field.evaluate_grid(xs, ys+step, zs)
        _, ys_dy_minus, _ = self.field.evaluate_grid(xs, ys-step, zs)
        _, _, zs_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        _, _, zs_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)

        dx_dx = (xs_dx_plus - xs_dx_minus) / (2*step)
        dy_dy = (ys_dy_plus - ys_dy_minus) / (2*step)
        dz_dz = (zs_dz_plus - zs_dz_minus) / (2*step)

        return dx_dx + dy_dy + dz_dz

class SvScalarFieldLaplacian(SvScalarField):
    def __init__(self, field, step):
        self.field = field
        self.step = step
        self.__description__ = "Laplace({})".format(field)

    def evaluate(self, x, y, z):
        step = self.step
        v_dx_plus = self.field.evaluate(x+step,y,z)
        v_dx_minus = self.field.evaluate(x-step,y,z)
        v_dy_plus = self.field.evaluate(x, y+step, z)
        v_dy_minus = self.field.evaluate(x, y-step, z)
        v_dz_plus = self.field.evaluate(x, y, z+step)
        v_dz_minus = self.field.evaluate(x, y, z-step)
        v0 = self.field.evaluate(x, y, z)

        sides = v_dx_plus + v_dx_minus + v_dy_plus + v_dy_minus + v_dz_plus + v_dz_minus
        result = (sides - 6*v0) / (8 * step * step * step)
        return result

    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        v_dx_plus = self.field.evaluate_grid(xs+step, ys,zs)
        v_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        v_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        v_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        v_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        v_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)
        v0 = self.field.evaluate_grid(xs, ys, zs)

        sides = v_dx_plus + v_dx_minus + v_dy_plus + v_dy_minus + v_dz_plus + v_dz_minus
        result = (sides - 6*v0) / (8 * step * step * step)
        return result

