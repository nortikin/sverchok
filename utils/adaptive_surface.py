# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import random
from math import ceil, isnan

from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface
from sverchok.utils.geom_2d.merge_mesh import crop_mesh_delaunay
from sverchok.utils.voronoi import computeDelaunayTriangulation, Site

def populate_surface_uv(surface, samples_u, samples_v, by_curvature=True, by_area=True, min_ppf=1, max_ppf=5, seed=1):
    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()
    us_range = np.linspace(u_min, u_max, num=samples_u)
    vs_range = np.linspace(v_min, v_max, num=samples_v)
    us, vs = np.meshgrid(us_range, vs_range, indexing='ij')
    us = us.flatten()
    vs = vs.flatten()

    if by_curvature:
        curvatures = abs(surface.gauss_curvature_array(us, vs)).clip(0, 100)
        curvatures = curvatures.reshape((samples_u, samples_v))

        curvatures_0 = curvatures[:-1, :-1]
        curvatures_du = curvatures[1:, :-1]
        curvatures_dv = curvatures[:-1, 1:]
        curvatures_du_dv = curvatures[1:, 1:]

        max_curvatures = np.max([curvatures_0, curvatures_du, curvatures_dv, curvatures_du_dv], axis=0)
        max_curvature = max_curvatures.max()
        min_curvature = max_curvatures.min()
        curvatures_range = max_curvature - min_curvature
        info("Curvature range: %s - %s", min_curvature, max_curvature)
        if curvatures_range == 0:
            max_curvatures = np.zeros((samples_u-1, samples_v-1))
        else:
            max_curvatures = (max_curvatures - min_curvature) / curvatures_range
    else:
        max_curvatures = np.zeros((samples_u-1, samples_v-1))
        curvatures_range = 0

    if by_area:
        surface_points = surface.evaluate_array(us, vs)
        surface_points = surface_points.reshape((samples_u, samples_v, 3))

        points_0 = surface_points[:-1, :-1,:]
        points_du = surface_points[1:, :-1,:]
        points_dv = surface_points[:-1, 1:,:]
        points_du_dv = surface_points[1:, 1:,:]

        areas_1 = np.linalg.norm(np.cross(points_du_dv - points_0, points_du - points_0), axis=2)/6.0
        areas_2 = np.linalg.norm(np.cross(points_dv - points_0, points_du_dv - points_0), axis=2)/6.0
        areas = areas_1 + areas_2
        h_u = us_range[1] - us_range[0]
        h_v = vs_range[1] - vs_range[0]
        areas = areas / (h_u * h_v)
        min_area = areas.min()
        max_area = areas.max()
        areas_range = max_area - min_area
        info("Areas range: %s - %s", min_area, max_area)
        if areas_range == 0:
            areas = np.zeros((samples_u-1, samples_v-1))
        else:
            areas = (areas - min_area) / areas_range
    else:
        areas = np.zeros((samples_u-1, samples_v-1))
        areas_range = 0

    factors = max_curvatures + areas
    factor_range = areas_range + curvatures_range
    if by_area and by_curvature:
        factors = factors / 2.0
        factor_range = factor_range / 2.0
    max_factor = factors.max()
    if max_factor != 0:
        factors = factors / max_factor
    #info("Factors: %s - %s (%s)", factors.min(), factors.max(), factor_range)
    #info("Areas: %s - %s", areas.min(), areas.max())
    #info("Curvatures: %s - %s", max_curvatures.min(), max_curvatures.max())

    ppf_range = max_ppf - min_ppf

    if not seed:
        seed = 12345
    random.seed(seed)
    new_u = []
    new_v = []
    for i in range(samples_u-1):
        u1 = us_range[i]
        u2 = us_range[i+1]
        for j in range(samples_v-1):
            v1 = vs_range[j]
            v2 = vs_range[j+1]
            factor = factors[i,j]
            if factor_range == 0 or isnan(factor):
                ppf = (min_ppf + max_ppf)/2
            else:
                ppf = min_ppf + ppf_range * factor
            #ppf = int(round(ppf))
            ppf = ceil(ppf)
#             if ppf > 1:
#                 info("I %s, J %s, factor %s, PPF %s", i, j, factor, ppf)
#                 info("U %s - %s, V %s - %s", u1, u2, v1, v2)
            for k in range(ppf):
                u = random.uniform(u1, u2)
                v = random.uniform(v1, v2)
                new_u.append(u)
                new_v.append(v)

    return us, vs, new_u, new_v

def adaptive_subdivide(surface, samples_u, samples_v, by_curvature=True, by_area=True, add_points=None, min_ppf=1, max_ppf=5, seed=1):
    us, vs, new_u, new_v = populate_surface_uv(surface, samples_u, samples_v, by_curvature, by_area, min_ppf, max_ppf, seed)
    us_list = list(us) + new_u
    vs_list = list(vs) + new_v
    if add_points and len(add_points[0]) > 0:
        us_list.extend([p[0] for p in add_points])
        vs_list.extend([p[1] for p in add_points])
    points_uv = [Site(u, v) for u, v in zip(us_list, vs_list)]
    faces = computeDelaunayTriangulation(points_uv)
    return np.array(us_list), np.array(vs_list), faces

