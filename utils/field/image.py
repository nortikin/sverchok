# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from mathutils import Color

from sverchok.utils.modules.color_utils import color_channels

from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.field.vector import SvVectorField

def get_scalar(channel, x):
    return color_channels[channel][1](x)

def get_vector(space, x):
    if space == 'RGB':
        return np.array(x[:3])
    elif space == 'HSV':
        return np.array(Color(x[:3]).hsv)

def load_image(image_name):
    image = bpy.data.images[image_name]
    width, height = image.size
    pixels = np.array(image.pixels).reshape((height, width, 4))
    return pixels

class SvImageScalarField(SvScalarField):
    def __init__(self, pixels, channel, plane='XY', fallback=0.0):
        self.plane = plane
        self.channel = channel
        self.fallback = fallback
        self.pixels = pixels
        self.width, self.height, _ = pixels.shape

    def evaluate(self, x, y, z):
        if self.plane == 'XY':
            u,v = x,y
        elif self.plane == 'YZ':
            u,v = y,z
        else: # XZ
            u,v = x,z
        return self._evaluate(u, v)
    
    def _evaluate(self, u, v):
        if u < 0 or u >= self.height or v < 0 or v >= self.width:
            return self.fallback
        u, v = int(u), int(v)
        color = self.pixels[v][u]
        return get_scalar(self.channel, color)

    def evaluate_grid(self, xs, ys, zs):
        if self.plane == 'XY':
            us, vs = xs, ys
        elif self.plane == 'YZ':
            us, vs = ys, zs
        else: # XZ
            us, vs = xs, zs
        return np.vectorize(self._evaluate)(us, vs)

class SvImageVectorField(SvVectorField):
    def __init__(self, pixels, space, plane='XY', fallback=None):
        if fallback is None:
            fallback = np.array([0, 0, 0])
        self.fallback = fallback
        self.plane = plane
        self.space = space
        self.pixels = pixels
        self.width, self.height, _ = pixels.shape

    def evaluate(self, x, y, z):
        if self.plane == 'XY':
            u,v = x,y
        elif self.plane == 'YZ':
            u,v = y,z
        else: # XZ
            u,v = x,z
        return self._evaluate(u, v)
    
    def _evaluate(self, u, v):
        if u < 0 or u >= self.height or v < 0 or v >= self.width:
            return self.fallback
        u, v = int(u), int(v)
        color = self.pixels[v][u]
        return get_vector(self.space, color)

    def evaluate_grid(self, xs, ys, zs):
        if self.plane == 'XY':
            us, vs = xs, ys
        elif self.plane == 'YZ':
            us, vs = ys, zs
        else: # XZ
            us, vs = xs, zs
        vectors = np.vectorize(self._evaluate, signature='(),()->(3)')(us, vs).T
        return vectors[0], vectors[1], vectors[2]

