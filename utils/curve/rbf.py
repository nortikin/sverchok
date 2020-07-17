
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

    def tangent(self, t):
        point = self.rbf(t)
        point_h = self.rbf(t+self.tangent_delta)
        return (point_h - point) / self.tangent_delta
    
    def tangent_array(self, ts):
        points = self.rbf(ts)
        points_h = self.rbf(ts+self.tangent_delta)
        return (points_h - points) / self.tangent_delta

