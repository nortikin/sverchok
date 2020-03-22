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

import numpy as np
import math
from math import sin, cos, radians, degrees, sqrt, asin, acos, atan2

coordinate_modes = [
    ('XYZ', "Carthesian", "Carthesian coordinates - x, y, z", 0),
    ('CYL', "Cylindrical", "Cylindrical coordinates - rho, phi, z", 1),
    ('SPH', "Spherical", "Spherical coordinates - rho, phi, theta", 2)
]

falloff_types = [
        ('NONE', "None - R", "Output distance", 0),
        ("inverse", "Inverse - 1/R", "", 1),
        ("inverse_square", "Inverse square - 1/R^2", "Similar to gravitation or electromagnetizm", 2),
        ("inverse_cubic", "Inverse cubic - 1/R^3", "", 3),
        ("inverse_exp", "Inverse exponent - Exp(-R)", "", 4),
        ("gauss", "Gauss - Exp(-R^2/2)", "", 5)
    ]

def smooth(x):
    return 3*x*x - 2*x*x*x

def sharp(x):
    return x * (2 - x)

def root(x):
    return 1.0 - math.sqrt(1.0 - x)

def linear(x):
    return x

def const(x):
    return 0.0

def sphere(x):
    return 1.0 - math.sqrt(1.0 - x*x)

def invsquare(x):
    return x*x

def inverse(c, x):
    return 1.0/x

def inverse_square(c, x):
    return 1.0/(x*x)

def inverse_cubic(c, x):
    return 1.0/(x*x*x)

def inverse_exp(c, x):
    return math.exp(-c*x)

def gauss(c, x):
    return math.exp(-c*x*x/2.0)

def falloff(type, radius, rho):
    if rho <= 0:
        return 1.0
    if rho > radius:
        return 0.0
    func = globals()[type]
    return 1.0 - func(rho / radius)

def falloff_array(falloff_type, amplitude, coefficient, clamp=False):
    falloff_func = globals()[falloff_type]

    def function(rho_array):
        zero_idxs = (rho_array == 0)
        nonzero = (rho_array != 0)
        result = np.empty_like(rho_array)
        result[zero_idxs] = amplitude
        result[nonzero] = amplitude * falloff_func(coefficient, rho_array[nonzero])
        negative = result <= 0
        result[negative] = 0.0

        if clamp:
            high = result >= rho_array
            result[high] = rho_array[high]
        return result
    return function

# Standard functions which for some reasons are not in the math module
def sign(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    else:
        return 0

def from_cylindrical(rho, phi, z, mode="degrees"):
    if mode == "degrees":
        phi = radians(phi)
    x = rho*cos(phi)
    y = rho*sin(phi)
    return x, y, z

def from_spherical(rho, phi, theta, mode="degrees"):
    if mode == "degrees":
        phi = radians(phi)
        theta = radians(theta)
    x = rho * sin(theta) * cos(phi)
    y = rho * sin(theta) * sin(phi)
    z = rho * cos(theta)
    return x, y, z

def to_cylindrical(v, mode="degrees"):
    x,y,z = v
    rho = sqrt(x*x + y*y)
    phi = atan2(y,x)
    if mode == "degrees":
        phi = degrees(phi)
    return rho, phi, z

def to_spherical(v, mode="degrees"):
    x,y,z = v
    rho = sqrt(x*x + y*y + z*z)
    if rho == 0.0:
        return 0.0, 0.0, 0.0
    theta = acos(z/rho)
    phi = atan2(y,x)
    if mode == "degrees":
        phi = degrees(phi)
        theta = degrees(theta)
    return rho, phi, theta

