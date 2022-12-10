# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

def curve_to_meshdata(curve, resolution):
    t_min, t_max = curve.get_u_bounds()
    ts = np.linspace(t_min, t_max, num=resolution)
    points = curve.evaluate_array(ts).tolist()
    edges = [(i,i+1) for i in range(resolution-1)]
    return points, edges

def bake_curve(curve, resolution, object_name):
    points, edges = curve_to_meshdata(curve, resolution)
    me = bpy.data.meshes.new(object_name)
    me.from_pydata(points, edges, [])
    ob = bpy.data.objects.new(object_name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

class CurveData(object):
    def __init__(self, node, curve, resolution):
        self.node = node
        self.curve = curve
        self.resolution = resolution

        if node.draw_line or node.draw_verts or node.draw_comb:
            t_min, t_max = curve.get_u_bounds()
            ts = np.linspace(t_min, t_max, num=resolution)
            n = len(ts)
            self.points = curve.evaluate_array(ts).tolist()

        if node.draw_line:
            self.edges = [(i,i+1) for i in range(n-1)]

        if (node.draw_control_polygon or node.draw_control_points) and hasattr(curve, 'get_control_points'):
            self.control_points = curve.get_control_points().tolist()
        else:
            self.control_points = None

        if node.draw_control_polygon:
            n = len(self.control_points)
            self.control_polygon_edges = [(i,i+1) for i in range(n-1)]

        if node.draw_nodes and hasattr(curve, 'calc_greville_points'):
            self.node_points = curve.calc_greville_points().tolist()
        else:
            self.node_points = None

        if node.draw_comb:
            n = len(self.points)
            normals = curve.main_normal_array(ts, normalize=True)
            curvatures = curve.curvature_array(ts)[np.newaxis].T
            comb_normals = node.comb_scale * curvatures * normals
            comb_points = self.points - comb_normals
            self.comb_points = np.concatenate((self.points, comb_points)).tolist()
            comb_normal_edges = [(i, i+n) for i in range(n-1)]
            comb_tangent_edges = [(i, i+1) for i in range(n, 2*n-1)]
            self.comb_edges = comb_normal_edges + comb_tangent_edges
        else:
            self.comb_points = None
            self.comb_edges = None

    def bake(self, object_name):
        me = bpy.data.meshes.new(object_name)
        me.from_pydata(self.points, self.edges, [])
        ob = bpy.data.objects.new(object_name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob

