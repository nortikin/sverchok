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

xyz_axes = [
        ('X', "X", "X axis", 0),
        ('Y', "Y", "Y axis", 1),
        ('Z', "Z", "Z axis", 2)
    ]

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
        ("gauss", "Gauss - Exp(-R^2/2)", "", 5),
        ("rotation", "Rotation 1/R^(3/2)", "", 6)
    ]

proportional_falloff_types = [
        ('smooth', "(P) Smooth", "Smooth falloff", 0),
        ('sphere', '(P) Sphere', "Spherical falloff", 1),
        ('root', '(P) Root', "Root falloff", 2),
        ('invsquare', '(P) Inverse square', "Root falloff", 3),
        ('sharp', "(P) Sharp", "Sharp falloff", 4),
        ('linear', "(P) Linear", "Linear falloff", 5),
        ('const', "(P) Constant", "Constant falloff", 6)
    ]

all_falloff_types = falloff_types + [(id, title, desc, i + len(falloff_types)) for id, title, desc, i in proportional_falloff_types]

# Vector rotation calculation algorithms
NONE = 'NONE'
ZERO = 'ZERO'
FRENET = 'FRENET'
HOUSEHOLDER = 'householder'
TRACK = 'track'
DIFF = 'diff'
TRACK_NORMAL = 'track_normal'
NORMAL_DIR = 'normal_direction'

rbf_functions = [
    ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
    ('inverse', "Inverse", "Inverse", 1),
    ('gaussian', "Gaussian", "Gaussian", 2),
    ('cubic', "Cubic", "Cubic", 3),
    ('quintic', "Quintic", "Qunitic", 4),
    ('thin_plate', "Thin Plate", "Thin Plate", 5)
]

supported_metrics = [
        ('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
        ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
        ('POINTS', 'Points', "Points based", 2),
        ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3),
        ('CENTRIPETAL', "Centripetal", "Centripetal distance - square root of Euclidian distance", 4)
    ]

xyz_metrics = [
        ('X', "X Axis", "Distance along X axis", 5),
        ('Y', "Y Axis", "Distance along Y axis", 6),
        ('Z', "Z Axis", "Distance along Z axis", 7)
    ]

def smooth(x):
    return 3*x*x - 2*x*x*x

def sharp(x):
    return x * (2 - x)

def root(x):
    return 1.0 - math.sqrt(1.0 - x)

def root_np(x):
    return 1.0 - np.sqrt(1.0 - x)

def linear(x):
    return x

def const(x):
    return 0.0

def sphere(x):
    return 1.0 - math.sqrt(1.0 - x*x)

def sphere_np(x):
    return 1.0 - np.sqrt(1.0 - x*x)

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

def inverse_exp_np(c, x):
    return np.exp(-c*x)

def rotation_fallof_np(c, x):
    return np.power(x, -3/2)

def gauss_np(c, x):
    return np.exp(-c*x*x/2.0)

def falloff(type, radius, rho):
    if rho <= 0:
        return 1.0
    if rho > radius:
        return 0.0
    func = globals()[type]
    return 1.0 - func(rho / radius)

def wrap_falloff(func):
    def falloff(c, xs):
        result = np.empty_like(xs)
        negative = (xs <= 0)
        result[negative] = 1.0
        outer = (xs > c)
        result[outer] = 0.0
        good = np.logical_not(negative) & np.logical_not(outer)
        result[good] = 1.0 - func(xs[good] / c)
        return result
    return falloff

def falloff_array(falloff_type, amplitude, coefficient, clamp=False):
    types = {
            'inverse': inverse,
            'inverse_square': inverse_square,
            'inverse_cubic': inverse_cubic,
            'inverse_exp': inverse_exp_np,
            'gauss': gauss_np,
            'rotation': rotation_fallof_np,
            'smooth': wrap_falloff(smooth),
            'sphere': wrap_falloff(sphere_np),
            'root': wrap_falloff(root_np),
            'invsquare': wrap_falloff(invsquare),
            'sharp': wrap_falloff(sharp),
            'linear': wrap_falloff(linear),
            'const': wrap_falloff(const)
        }
    falloff_func = types[falloff_type]

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

def from_cylindrical_np(rho, phi, z, mode='degrees'):
    if mode == "degrees":
        phi = np.radians(phi)
    x = rho*np.cos(phi)
    y = rho*np.sin(phi)
    return x, y, z

def from_spherical(rho, phi, theta, mode="degrees"):
    if mode == "degrees":
        phi = radians(phi)
        theta = radians(theta)
    x = rho * sin(theta) * cos(phi)
    y = rho * sin(theta) * sin(phi)
    z = rho * cos(theta)
    return x, y, z

def from_spherical_np(rho, phi, theta, mode="degrees"):
    if mode == "degrees":
        phi = np.radians(phi)
        theta = np.radians(theta)
    x = rho * np.sin(theta) * np.cos(phi)
    y = rho * np.sin(theta) * np.sin(phi)
    z = rho * np.cos(theta)
    return x, y, z

def to_cylindrical(v, mode="degrees"):
    x,y,z = v
    rho = sqrt(x*x + y*y)
    phi = atan2(y,x)
    if mode == "degrees":
        phi = degrees(phi)
    return rho, phi, z

def to_cylindrical_np(v, mode="degrees"):
    x,y,z = v
    rho = np.sqrt(x*x + y*y)
    phi = np.arctan2(y,x)
    if mode == "degrees":
        phi = np.degrees(phi)
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

def to_spherical_np(v, mode="degrees"):
    x,y,z = v
    rho = np.sqrt(x*x + y*y + z*z)
    bad = (rho == 0)
    good = np.logical_not(bad)

    theta = np.empty_like(x)
    theta[good] = np.arccos(z[good]/rho[good])
    theta[bad] = 0.0

    phi = np.empty_like(x)
    phi[good] = np.arctan2(y[good], x[good])
    phi[bad] = 0.0

    if mode == "degrees":
        phi = np.degrees(phi)
        theta = np.degrees(theta)
    return rho, phi, theta

def project_to_sphere(center, radius, v):
    x,y,z = v
    x0,y0,z0 = center
    dv = x-x0, y-y0, z-z0
    rho, phi, theta = to_spherical(dv, "radians")
    x,y,z = from_spherical(radius, phi, theta, "radians")
    result = x+x0, y+y0, z+z0
    return result

def binomial(n,k):
    if not 0<=k<=n:
        return 0
    b = 1
    for t in range(min(k,n-k)):
        b *= n
        b //= t+1
        n -= 1
    return b

def np_mixed_product(a, b, c):
    return np.dot(a, np.cross(b, c))

def np_signed_angle(a, b, normal):
    cross = np.cross(a, b)
    scalar = np.dot(cross, normal)
    sign = 1 if scalar >= 0 else -1
    sin_alpha = np.linalg.norm(cross) / (np.linalg.norm(a) * np.linalg.norm(b))
    alpha = asin(sin_alpha)
    return sign * alpha

def np_vectors_angle(v1, v2):
    v1 /= np.linalg.norm(v1)
    v2 /= np.linalg.norm(v2)
    dot = np.dot(v1, v2)
    return np.arccos(dot)

def np_dot(u, v, axis=1):
    'conveniece function to calculate dot vector between vector arrays'
    return np.sum(u * v, axis=axis)

def np_normalized_vectors(vecs):
    '''Returns new array with normalized vectors'''
    result = np.zeros(vecs.shape)
    norms = np.linalg.norm(vecs, axis=1)
    nonzero = (norms > 0)
    result[nonzero] = vecs[nonzero] / norms[nonzero][:,np.newaxis]
    return result

def np_normalize_vectors(vecs):
    '''Does normalization in-place'''
    norms = np.linalg.norm(vecs, axis=1)
    nonzero = (norms > 0)
    vecs[nonzero] = vecs[nonzero] / norms[nonzero][:,np.newaxis]

def weighted_center(verts, field=None):
    if field is None:
        return np.mean(verts, axis=0)
    else:
        xs = verts[:,0]
        ys = verts[:,1]
        zs = verts[:,2]
        weights = field.evaluate_grid(xs, ys, zs)
        wpoints = weights[:,np.newaxis] * verts
        result = wpoints.sum(axis=0) / weights.sum()
        return result

def gcd(a, b):

    """Calculate the Greatest Common Divisor of a and b.

    Unless b==0, the result will have the same sign as b (so that when
    b is divided by it, the result comes out positive).
    Taken from fractions.py to override depreciation
    """

    if type(a) is int is type(b):
        if (b or a) < 0:
            return -math.gcd(a, b)
        return math.gcd(a, b)
    return _gcd(a, b)

def _gcd(a, b):
    # Supports non-integers for backward compatibility.
    while b:
        a, b = b, a%b
    return a
