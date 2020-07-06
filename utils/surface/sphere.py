# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, cos, sin, atan, sqrt

from sverchok.utils.math import (
    from_spherical,
    FRENET, TRACK, TRACK_NORMAL
    )
from sverchok.utils.surface.core import SvSurface

class SvEquirectSphere(SvSurface):
    __description__ = "Equirectangular Sphere"

    def __init__(self, center, radius, theta1):
        self.center = center
        self.radius = radius
        self.theta1 = theta1
        self.u_bounds = (0, radius * 2*pi * cos(theta1))
        self.v_bounds = (-radius * theta1, radius * (pi - theta1))

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u / (rho * cos(self.theta1))
        theta = v / rho + self.theta1
        x, y, z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us / (rho * cos(self.theta1))
        thetas = vs / rho + self.theta1
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def gauss_curvature_array(self, us, vs):
        rho = self.radius
        c = 1.0 / (rho*rho)
        return np.full_like(us, c)

    def normal(self, u, v):
        rho = self.radius
        phi = u / (rho * np.cos(self.theta1))
        theta = v / rho + self.theta1
        x, y, z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us / (rho * cos(self.theta1))
        thetas = vs / rho + self.theta1
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvLambertSphere(SvSurface):
    __description__ = "Lambert Sphere"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.u_bounds = (0, 2*pi)
        self.v_bounds = (-1.0, 1.0)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u
        theta = np.arcsin(v)
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = np.arcsin(vs) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def gauss_curvature_array(self, us, vs):
        rho = self.radius
        c = 1.0 / (rho*rho)
        return np.full_like(us, c)

    def normal(self, u, v):
        rho = self.radius
        phi = u
        theta = np.arcsin(v) + pi/2
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = np.arcsin(vs) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvGallSphere(SvSurface):
    __description__ = "Gall Sphere"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.u_bounds = (0, radius * 2*pi / sqrt(2))
        self.v_bounds = (- radius * (1 + sqrt(2)/2), radius * (1 + sqrt(2)/2))

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u * sqrt(2) / rho
        theta = 2 * atan(v / (rho * (1 + sqrt(2)/2))) + pi/2
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z]) + self.center

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us * sqrt(2) / rho
        thetas = 2 * np.arctan(vs / (rho * (1 + sqrt(2)/2))) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def gauss_curvature_array(self, us, vs):
        rho = self.radius
        c = 1.0 / (rho*rho)
        return np.full_like(us, c)

    def normal(self, u, v):
        rho = self.radius
        phi = u * sqrt(2) / rho
        theta = 2 * atan(v / (rho * (1 + sqrt(2)/2))) + pi/2
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us * sqrt(2) / rho
        thetas = 2 * np.arctan(vs / (rho * (1 + sqrt(2)/2))) + pi/2
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

class SvDefaultSphere(SvSurface):
    __description__ = "Default Sphere"

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius
        self.u_bounds = (0, 2*pi)
        self.v_bounds = (0, pi)

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    def evaluate(self, u, v):
        rho = self.radius
        phi = u
        theta = v
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        point = np.array([x,y,z]) + self.center
        return point

    def evaluate_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = vs
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T + self.center

    def gauss_curvature_array(self, us, vs):
        rho = self.radius
        c = 1.0 / (rho*rho)
        return np.full_like(us, c)

    def normal(self, u, v):
        rho = self.radius
        phi = u
        theta = v
        x,y,z = from_spherical(rho, phi, theta, mode="radians")
        return np.array([x,y,z])

    def normal_array(self, us, vs):
        rho = self.radius
        phis = us
        thetas = vs
        xs = rho * np.sin(thetas) * np.cos(phis)
        ys = rho * np.sin(thetas) * np.sin(phis)
        zs = rho * np.cos(thetas)
        return np.stack((xs, ys, zs)).T

