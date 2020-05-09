"""
in   h_in s
out  field_out SF
"""

# This script shows an example of generating a custom Scalar Field object.
# This may be useful when the formula defining the field is too complex
# to be typed in the "Scalar Field Formula" node.

import math
import numpy as np

from sverchok.utils.field.scalar import SvScalarField

# You can implement some auxiliary funcitons
# to be used in your scalar field definition.
def erdos(z, n):
    return abs(z**n - 1)**2 - 1

def lemn3(x, y):
    return erdos(x + y*1j, 3)

# To make your own scalar field, you have to
# subclass a SvScalarField class.
#
# You have to define two methods in it: evaluate and evaluate_grid.
#
class MyField(SvScalarField):
    def __init__(self, h):
        # the field can have any parameters you want
        self.h = h
        
    def evaluate(self, x, y, z):
        # This method must calculate one real value for given x,y and z coordinates.
        # If you've already implemented evalaute_grid, you may simply write:
        #
        # def evaluate(self, x, y, z):
        #     return self.evaluate_grid(np.array([x]), np.array([y]), np.array([z]))[0]
        #
        # but employing all the numpy's vectorization magic for one single point
        # may have some performance overhead.
        w = x + y*1j
        h = self.h
        return lemn3(x,y)**2 + (16*abs(w)**4 + 1)*(z*z - h*h)
    
    def evaluate_grid(self, xs, ys, zs):
        # This method must calculate a numpy array of shape (n,)
        # given three numpy arrays xs, ys and zs of the same shape.
        # If you've already implemented evaluate() method, and do not
        # want to dig into numpy magic, or you do not care about
        # performance, or your algorithm is just impossible to vectorize,
        # you can write simply:
        #
        # def evaluate_grid(self, xs, ys, zs):
        #    return np.vectorize(self.evaluate, signature='(),(),()->()`)(xs, ys, zs)
        #
        ws = xs + ys*1j
        h = self.h
        return lemn3(xs,ys)**2 + (16*abs(ws)**4 + 1)*(zs*zs - h*h)

# And now you return an instance of your class for each set of the input parameters.

field_out = []
if h_in:
    for hs in h_in:
        for h in hs:
            field = MyField(h)
            field_out.append(field)

