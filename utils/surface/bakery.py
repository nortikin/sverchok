# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

from sverchok.utils.modules.polygon_utils import pols_normals
from sverchok.utils.modules.vertex_utils import np_vertex_normals
from sverchok.utils.math import np_dot
from sverchok.utils.curve.algorithms import SvIsoUvCurve
from sverchok.utils.curve.bakery import CurveData

def make_quad_edges(n_u, n_v):
    edges = []
    for row in range(n_v):
        e_row = [(i + n_u * row, (i+1) + n_u * row) for i in range(n_u-1)]
        edges.extend(e_row)
        if row < n_v - 1:
            e_col = [(i + n_u * row, i + n_u * (row+1)) for i in range(n_u)]
            edges.extend(e_col)
    return edges

def make_quad_faces(samples_u, samples_v):
    faces = []
    for row in range(samples_v - 1):
        for col in range(samples_u - 1):
            i = row * samples_u + col
            face = (i, i+samples_u, i+samples_u+1, i+1)
            faces.append(face)
    return faces

def surface_to_meshdata(surface, resolution_u, resolution_v):
    u_min, u_max = surface.get_u_bounds()
    v_min, v_max = surface.get_v_bounds()
    us = np.linspace(u_min, u_max, num=resolution_u)
    vs = np.linspace(v_min, v_max, num=resolution_v)
    us, vs = np.meshgrid(us, vs)
    us = us.flatten()
    vs = vs.flatten()
    points = surface.evaluate_array(us, vs).tolist()
    edges = make_quad_edges(resolution_u, resolution_v)
    faces = make_quad_faces(resolution_u, resolution_v)
    return points, edges, faces

def bake_surface(surface, resolution_u, resolution_v, object_name):
    verts, edges, faces = surface_to_meshdata(surface, resolution_u, resolution_v)
    me = bpy.data.meshes.new(object_name)
    me.from_pydata(points, edges, faces)
    ob = bpy.data.objects.new(object_name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def make_tris(n_u, n_v):
    def calc_idx(row_idx, column_idx):
        return n_u * row_idx + column_idx

    tris = []
    for row_idx in range(n_v-1):
        for column_idx in range(n_u-1):
            pt1 = calc_idx(row_idx, column_idx)
            pt2 = calc_idx(row_idx, column_idx+1)
            pt3 = calc_idx(row_idx+1, column_idx+1)
            pt4 = calc_idx(row_idx+1, column_idx)
            #tri1 = [pt1, pt2, pt3]
            #tri2 = [pt1, pt3, pt4]
            tri1 = [pt1, pt3, pt2]
            tri2 = [pt1, pt4, pt3]
            tris.append(tri1)
            tris.append(tri2)
    return tris

def vert_light_factor(vecs, polygons, light):
    return (np_dot(np_vertex_normals(vecs, polygons, output_numpy=True), light)*0.5+0.5).tolist()

def calc_surface_data(light_vector, surface_color, n_u, n_v, points):
    #points = points.reshape((n_u*n_v, 3))
    tris = make_tris(n_u, n_v)
    n_tris = len(tris)
    light_factor = vert_light_factor(points, tris, light_vector)
    colors = []
    col = surface_color
    for l_factor in light_factor:
        colors.append([col[0]*l_factor, col[1]*l_factor, col[2]*l_factor, col[3]])
    return tris, colors

class SurfaceData(object):
    class IsoCurveConfig(object):
        def __init__(self):
            self.draw_line = True
            self.draw_verts = False
            self.draw_control_polygon = False
            self.draw_control_points = False
            self.draw_nodes = False
            self.draw_comb = False
            self.draw_curvature = False

    def __init__(self, node, surface, resolution_u, resolution_v):
        self.node = node
        self.surface = surface
        self.resolution_u = resolution_u
        self.resolution_v = resolution_v

        u_min, u_max = surface.get_u_bounds()
        v_min, v_max = surface.get_v_bounds()
        us = np.linspace(u_min, u_max, num=resolution_u)
        vs = np.linspace(v_min, v_max, num=resolution_v)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()
        self.points = surface.evaluate_array(us, vs)#.tolist()
        self.points_list = self.points.reshape((resolution_u*resolution_v, 3)).tolist()

        if hasattr(surface, 'get_control_points'):
            self.cpts = surface.get_control_points()
            n_v, n_u, _ = self.cpts.shape
            self.cpts_list = self.cpts.reshape((n_u*n_v, 3)).tolist()
            self.control_net = make_quad_edges(n_u, n_v)
        else:
            self.cpts_list = None

        if hasattr(surface, 'calc_greville_us'):
            nodes_u = surface.calc_greville_us()
            nodes_v = surface.calc_greville_vs()
            node_u_isolines = [SvIsoUvCurve(surface, 'U', u) for u in nodes_u]
            node_v_isolines = [SvIsoUvCurve(surface, 'V', v) for v in nodes_v]
            cfg = SurfaceData.IsoCurveConfig()
            self.node_u_isoline_data = [CurveData(cfg, isoline, resolution_v) for isoline in node_u_isolines]
            self.node_v_isoline_data = [CurveData(cfg, isoline, resolution_u) for isoline in node_v_isolines]
        else:
            self.node_u_isoline_data = node_v_isoline_data = None

        self.edges = make_quad_edges(resolution_u, resolution_v)
        self.tris, self.tri_colors = calc_surface_data(node.light_vector, node.surface_color, resolution_u, resolution_v, self.points)
    
    def bake(self, object_name):
        me = bpy.data.meshes.new(object_name)
        faces = make_quad_faces(self.resolution_u, self.resolution_v)
        me.from_pydata(self.points_list, self.edges, faces)
        is_smooth = np.ones(len(faces), dtype=bool)
        me.polygons.foreach_set('use_smooth', is_smooth)
        ob = bpy.data.objects.new(object_name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob

