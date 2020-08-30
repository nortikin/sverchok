# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.nurbs import SvNurbsSurface

from sverchok.dependencies import FreeCAD
if FreeCAD is not None:
    from FreeCAD import Base
    import Part

class SvSolidFaceSurface(SvSurface):
    __description__ = "Solid Face"
    def __init__(self, solid_face):
        self.face = solid_face
        self.surface = solid_face.Surface
        self.u_bounds = solid_face.ParameterRange[:2]
        self.v_bounds = solid_face.ParameterRange[2:]
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
        return np.array(self.surface.value(u, v))

    def evaluate_array(self, us, vs):
        v_out = []
        for u, v in zip(us, vs):
            v_out.append(self.surface.value(u, v))
        return np.array(v_out)

    def gauss_curvature_array(self, us, vs):
        v_out = []
        for u, v in zip(us, vs):
            v_out.append(self.surface.curvature(u, v, "Gauss"))
        return np.array(v_out)
    def mean_curvature_array(self, us, vs):
        v_out = []
        for u,v in zip(us, vs):
            v_out.append(self.surface.curvature(u, v, "Mean"))
        return np.array(v_out)

    def normal(self, u, v):
        return np.array(self.surface.normal(u, v))

    def normal_array(self, us, vs):
        v_out = []
        for u,v in zip(us, vs):
            v_out.append(self.surface.normal(u, v))
        return np.array(v_out)

class SvFreeCadNurbsSurface(SvNurbsSurface):
    def __init__(self, surface):
        self.surface = surface

    @classmethod
    def build(cls, implementation, degree_u, degree_v, knotvector_u, knotvector_v, control_points, weights=None, normalize_knots=False):
        m,n,_ = control_points.shape
        if weights is None:
            weights = np.ones((m,n))
        if normalize_knots:
            knotvector_u = sv_knotvector.normalize(knotvector_u)
            knotvector_v = sv_knotvector.normalize(knotvector_v)

        pts = [[Base.Vector(*t) for t in row] for row in control_points]

        ms_u = sv_knotvector.to_multiplicity(knotvector_u)
        knots_u = [p[0] for p in ms_u]
        mults_u = [p[1] for p in ms_u]
        ms_v = sv_knotvector.to_multiplicity(knotvector_v)
        knots_v = [p[0] for p in ms_v]
        mults_v = [p[1] for p in ms_v]

        surface = Part.BSplineSurface()
        surface.buildFromPolesMultsKnots(pts,
                    mults_u, mults_v,
                    knots_u, knots_v,
                    False, False,
                    degree_u, degree_v,
                    weights.tolist())
        return SvFreeCadNurbsSurface(surface)
    
    @classmethod
    def get_nurbs_implementation(cls):
        return SvNurbsMaths.FREECAD

    def get_degree_u(self):
        return self.surface.UDegree

    def get_degree_v(self):
        return self.surface.VDegree

    def get_knotvector_u(self):
        return np.array(self.surface.UKnotSequence)

    def get_knotvector_v(self):
        return np.array(self.surface.VKnotSequence)

    def get_control_points(self):
        poles = self.surface.getPoles()
        points = [[[pt.x, pt.y, pt.z] for pt in row] for row in poles]
        return np.array(points)

    def get_weights(self):
        weights = self.surface.getWeights()
        return np.array(weights)

    def get_u_min(self):
        return self.surface.UKnotSequence[0]

    def get_u_max(self):
        return self.surface.UKnotSequence[-1]

    def get_v_min(self):
        return self.surface.VKnotSequence[0]

    def get_v_max(self):
        return self.surface.VKnotSequence[-1]

    def _convert(self, p):
        return [p.x, p.y, p.z]

    def evaluate(self, u, v):
        pt = self.surface.value(u, v)
        return np.array(self._convert(pt))

    def evaluate_array(self, us, vs):
        return np.vectorize(self.evaluate, signature='(),()->(3)')(us, vs)

    def normal(self, u, v):
        v = self.surface.normal(u, v)
        return np.array(self._convert(v))

    def normal_array(self, us, vs):
        return np.vectorize(self.normal, signature='(),()->(3)')(us, vs)

