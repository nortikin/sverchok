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

import math
from math import sin, cos, radians, sqrt

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

def falloff(type, radius, rho):
    if rho <= 0:
        return 1.0
    if rho > radius:
        return 0.0
    func = globals()[type]
    return 1.0 - func(rho / radius)

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

