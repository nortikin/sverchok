
import numpy as np

from sverchok.utils.curve import SvCurve

##################
#                #
#  Curves        #
#                #
##################

class SvRbfCurve(SvCurve):
    """
    RBF-based interpolation curve
    """
    def __init__(self, rbf, u_bounds):
        self.rbf = rbf
        self.u_bounds = u_bounds
        self.tangent_delta = 0.0001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        v = self.rbf(t)
        return v

    def evaluate_array(self, ts):
        vs = self.rbf(ts)
        return vs

    def tangent(self, t, tangent_delta=None):
        h = self.get_tangent_delta(tangent_delta)
        point = self.rbf(t)
        point_h = self.rbf(t+h)
        return (point_h - point) / h
    
    def tangent_array(self, ts, tangent_delta=None):
        h = self.get_tangent_delta(tangent_delta)
        points = self.rbf(ts)
        points_h = self.rbf(ts+h)
        return (points_h - points) / h

