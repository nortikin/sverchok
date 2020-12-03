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
from collections import defaultdict

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from sverchok.utils.sv_mesh_utils import mask_vertices, polygons_to_edges
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, bmesh_clip
from sverchok.utils.geom import calc_bounds, bounding_sphere
from sverchok.utils.math import project_to_sphere, weighted_center
from sverchok.dependencies import scipy, FreeCAD

if scipy is not None:
    from scipy.spatial import Voronoi, SphericalVoronoi

if FreeCAD is not None:
    from FreeCAD import Base
    import Part

def voronoi3d_layer(n_src_sites, all_sites, make_regions, do_clip, clipping, skip_added=True):
    diagram = Voronoi(all_sites)
    src_sites = all_sites[:n_src_sites]
    
    region_verts = dict()
    region_verts_map = dict()
    n_sites = n_src_sites if skip_added else len(all_sites)
    for site_idx in range(n_sites):
        region_idx = diagram.point_region[site_idx]
        region = diagram.regions[region_idx]
        vertices = [tuple(diagram.vertices[i,:]) for i in region]
        region_verts[site_idx] = vertices
        region_verts_map[site_idx] = {vert_idx: i for i, vert_idx in enumerate(region)}
    
    open_sites = set()
    region_faces = defaultdict(list)
    for ridge_idx, sites in enumerate(diagram.ridge_points):
        site_from, site_to = sites
        ridge = diagram.ridge_vertices[ridge_idx]
        if -1 in ridge:
            open_sites.add(site_from)
            open_sites.add(site_to)

        site_from_ok = not skip_added or site_from < n_src_sites
        site_to_ok = not skip_added or site_to < n_src_sites
        
        if make_regions:
            if site_from_ok:
                face_from = [region_verts_map[site_from][i] for i in ridge]
                region_faces[site_from].append(face_from)
           
            if site_to_ok:
                face_to = [region_verts_map[site_to][i] for i in ridge]
                region_faces[site_to].append(face_to)
        else:
            if site_from_ok and site_to_ok:
                face_from = [region_verts_map[site_from][i] for i in ridge]
                region_faces[site_from].append(face_from)
                face_to = [region_verts_map[site_to][i] for i in ridge]
                region_faces[site_to].append(face_to)
    
    verts = [region_verts[i] for i in range(n_sites) if i not in open_sites]
    faces = [region_faces[i] for i in range(n_sites) if i not in open_sites]

    empty_faces = [len(f) == 0 for f in faces]
    verts = [vs for vs, mask in zip(verts, empty_faces) if not mask]
    faces = [fs for fs, mask in zip(faces, empty_faces) if not mask]
    edges = polygons_to_edges(faces, True)

    if not make_regions:
        verts_n, edges_n, faces_n = [], [], []
        for verts_i, edges_i, faces_i in zip(verts, edges, faces):
            used_verts = set(sum(faces_i, []))
            mask = [i in used_verts for i in range(len(verts_i))]
            verts_i, edges_i, faces_i = mask_vertices(verts_i, edges_i, faces_i, mask)
            verts_n.append(verts_i)
            edges_n.append(edges_i)
            faces_n.append(faces_i)
        verts, edges, faces = verts_n, edges_n, faces_n

    if do_clip:
        verts_n, edges_n, faces_n = [], [], []
        bounds = calc_bounds(src_sites, clipping)
        for verts_i, edges_i, faces_i in zip(verts, edges, faces):
            bm = bmesh_from_pydata(verts_i, edges_i, faces_i)
            bmesh_clip(bm, bounds, fill=True)
            verts_i, edges_i, faces_i = pydata_from_bmesh(bm)
            bm.free()
            verts_n.append(verts_i)
            edges_n.append(edges_i)
            faces_n.append(faces_i)
        verts, edges, faces = verts_n, edges_n, faces_n

    return verts, edges, faces

def voronoi_on_surface(surface, uvpoints, thickness, do_clip, clipping, make_regions):
    u_min, u_max, v_min, v_max = surface.get_domain()
    u_mid = 0.5*(u_min + u_max)
    v_mid = 0.5*(v_min + v_max)

    us = np.array([p[0] for p in uvpoints])
    vs = np.array([p[1] for p in uvpoints])

    us_edge = np.empty(us.shape)
    us_edge[us > u_mid] = u_max
    us_edge[us <= u_mid] = u_min

    vs_edge = np.empty(vs.shape)
    vs_edge[vs > v_mid] = v_max
    vs_edge[vs <= v_mid] = v_min

    surface_points = surface.evaluate_array(us, vs)
    edge_points = surface.evaluate_array(us_edge, vs_edge)
    out_points = surface_points + 2*(edge_points - surface_points)

    normals = surface.normal_array(us, vs)
    k = 0.5*thickness
    plus_points = surface_points + k*normals
    minus_points = surface_points - k*normals
    all_points = surface_points.tolist() + out_points.tolist() + plus_points.tolist() + minus_points.tolist()

    return voronoi3d_layer(len(uvpoints), all_points,
            make_regions = make_regions,
            do_clip = do_clip,
            clipping = clipping)

def calc_bvh_normals(bvh, sites):
    normals = []
    for site in sites:
        loc, normal, index, distance = bvh.find_nearest(site)
        if loc is not None:
            normals.append(normal)
    return np.array(normals)

def calc_bvh_projections(bvh, sites):
    projections = []
    for site in sites:
        loc, normal, index, distance = bvh.find_nearest(site)
        if loc is not None:
            projections.append(loc)
    return np.array(projections)

def voronoi_on_mesh_impl(bvh, sites, thickness, clip_inner=True, clip_outer=True, do_clip=True, clipping=1.0, make_regions=True):
    npoints = len(sites)

    if clip_inner or clip_outer:
        normals = calc_bvh_normals(bvh, sites)
    k = 0.5*thickness
    sites = np.array(sites)
    all_points = sites.tolist()
    if clip_outer:
        plus_points = sites + k*normals
        all_points.extend(plus_points.tolist())
    if clip_inner:
        minus_points = sites - k*normals
        all_points.extend(minus_points.tolist())

    return voronoi3d_layer(npoints, all_points,
            make_regions = make_regions,
            do_clip = do_clip,
            clipping = clipping)

def voronoi_on_mesh(verts, faces, sites, thickness, clip_inner=True, clip_outer=True, do_clip=True, clipping=1.0, make_regions=True):
    bvh = BVHTree.FromPolygons(verts, faces)
    return voronoi_on_mesh_impl(bvh, sites, thickness,
            clip_inner = clip_inner, clip_outer = clip_outer,
            do_clip = do_clip, clipping = clipping,
            make_regions = make_regions)

def project_solid_normals(shell, pts, thickness, add_plus=True, add_minus=True, predicate_plus=None, predicate_minus=None):
    k = 0.5*thickness
    result = []
    for pt in pts:
        dist, vs, infos = shell.distToShape(Part.Vertex(Base.Vector(pt)))
        projection = vs[0][0]
        info = infos[0]
        if info[0] == b'Face':
            face_idx = info[1]
            u,v = info[2]
            normal = shell.Faces[face_idx].normalAt(u,v)
            plus_pt = projection + k*normal
            minus_pt = projection - k*normal
            if add_plus:
                if predicate_plus is None or predicate_plus(plus_pt):
                    result.append(tuple(plus_pt))
            if add_minus:
                if predicate_minus is None or predicate_minus(minus_pt):
                    result.append(tuple(minus_pt))
    return result

def voronoi_on_solid_surface(solid, sites, thickness,
        clip_inner=True, clip_outer=True,
        skip_added = True,
        do_clip=True, clipping=1.0,
        tolerance = 1e-4,
        make_regions=True): 

    npoints = len(sites)
    if solid.Shells:
        shell = solid.Shells[0]
    else:
        shell = Part.Shell(solid.Faces)

    def check(pt):
        return solid.isInside(pt, tolerance, False)

    all_points = sites
    if clip_inner or clip_outer:
        all_points.extend(project_solid_normals(shell, sites, thickness,
                add_plus=clip_outer, add_minus=clip_inner, predicate_minus=check))

    return voronoi3d_layer(npoints, all_points,
            make_regions = make_regions,
            skip_added = skip_added,
            do_clip = do_clip,
            clipping = clipping)

def lloyd_on_mesh(verts, faces, sites, thickness, n_iterations, weight_field=None):
    bvh = BVHTree.FromPolygons(verts, faces)

    def iteration(points):
        n = len(points)

        normals = calc_bvh_normals(bvh, points)
        k = 0.5*thickness
        points = np.array(points)
        plus_points = points + k*normals
        minus_points = points - k*normals
        all_points = points.tolist() + plus_points.tolist() + minus_points.tolist()

        diagram = Voronoi(all_points)
        centers = []
        for site_idx in range(n):
            region_idx = diagram.point_region[site_idx]
            region = diagram.regions[region_idx]
            region_verts = np.array([diagram.vertices[i] for i in region])
            center = weighted_center(region_verts, weight_field)
            centers.append(tuple(center))
        return centers

    points = calc_bvh_projections(bvh, sites)
    for i in range(n_iterations):
        points = iteration(points)
        points = calc_bvh_projections(bvh, points)

    return points.tolist()

def lloyd_in_solid(solid, sites, n_iterations, tolerance=1e-4, weight_field=None):
    shell = solid.Shells[0]

    def invert(pt):
        src = Base.Vector(pt)
        dist, vs, infos = shell.distToShape(Part.Vertex(src))
        projection = vs[0][0]
        dst = src + 2*(projection - src)
        return (dst.x, dst.y, dst.z)
        
    def iteration(pts):
        n = len(pts)
        all_pts = pts
        for pt in pts:
            if solid.isInside(Base.Vector(pt), tolerance, False):
                all_pts.append(invert(pt))

        diagram = Voronoi(all_pts)
        centers = []
        for site_idx in range(n):
            region_idx = diagram.point_region[site_idx]
            region = diagram.regions[region_idx]
            region_verts = np.array([diagram.vertices[i] for i in region])
            center = weighted_center(region_verts, weight_field)
            centers.append(tuple(center))
        return centers

    def restrict(points):
        result = []
        for point in points:
            v = Base.Vector(point)
            if solid.isInside(v, tolerance, True):
                result.append(point)
            else:
                dist, vs, infos = solid.distToShape(Part.Vertex(v))
                v = vs[0][0]
                result.append((v.x, v.y, v.z))
        return result

    points = restrict(sites)
    for i in range(n_iterations):
        points = iteration(points)
        points = restrict(points)
    return points

def lloyd_on_solid_surface(solid, sites, thickness, n_iterations, tolerance=1e-4, weight_field=None):
    if solid.Shells:
        shell = solid.Shells[0]
    else:
        shell = Part.Shell(solid.Faces)
    
    def iteration(pts):
        all_pts = pts + project_solid_normals(shell, pts, thickness)
        diagram = Voronoi(all_pts)
        centers = []
        for site_idx in range(len(pts)):
            region_idx = diagram.point_region[site_idx]
            region = diagram.regions[region_idx]
            region_verts = np.array([diagram.vertices[i] for i in region])
            center = weighted_center(region_verts, weight_field)
            centers.append(tuple(center))
        return centers

    def restrict(points):
        result = []
        for point in points:
            v = Base.Vector(point)
            if any(face.isInside(v, tolerance, True) for face in shell.Faces):
                result.append(point)
            else:
                dist, vs, infos = shell.distToShape(Part.Vertex(v))
                v = vs[0][0]
                result.append((v.x, v.y, v.z))
        return result

    points = restrict(sites)
    for i in range(n_iterations):
        points = iteration(points)
        points = restrict(points)
    return points

def lloyd_on_fc_face(fc_face, sites, thickness, n_iterations, weight_field = None):

    def iteration(pts):
        n = len(pts)
        all_pts = pts + project_solid_normals(fc_face, pts, thickness)
        diagram = Voronoi(all_pts)
        centers = []
        for site_idx in range(n):
            region_idx = diagram.point_region[site_idx]
            region = diagram.regions[region_idx]
            region_verts = np.array([diagram.vertices[i] for i in region])
            center = weighted_center(region_verts, weight_field)
            centers.append(tuple(center))
        return centers
    
    def project(point):
        dist, vs, infos = fc_face.distToShape(Part.Vertex(Base.Vector(point)))
        pt = vs[0][0]
        info = infos[0]
        if info[0] == b'Face':
            uv = info[2]
        elif info[0] == b'Edge':
            edge_idx = info[1]
            edge = fc_face.Edges[edge_idx]
            curve, m, M = fc_face.curveOnSurface(edge)
            curve_param = info[2]
            uvpt = curve.value(curve_param)
            uv = uvpt.x, uvpt.y
        else:
            uv = None
        projection = (pt.x, pt.y, pt.z)
        return uv, projection

    def restrict(points):
        projections = [project(point) for point in points]
        uvpoints = [(uv[0], uv[1], 0) for uv,_ in projections if uv is not None]
        points = [r[1] for r in projections]
        return uvpoints, points

    uvpoints, points = restrict(sites)
    for i in range(n_iterations):
        points = iteration(points)
        uvpoints, points = restrict(points)

    return uvpoints, points

def lloyd_on_sphere(center, radius, sites, n_iterations, weight_field=None):
    def iteration(pts):
        diagram = SphericalVoronoi(pts, radius=radius, center=np.array(center))
        diagram.sort_vertices_of_regions()
        centers = []
        for region in diagram.regions:
            verts = np.array([diagram.vertices[i] for i in region])
            new_vert = weighted_center(verts, weight_field)
            centers.append(tuple(new_vert))
        return centers

    def restrict(points):
        projections = [project_to_sphere(center, radius, pt) for pt in points]
        return projections

    points = restrict(sites)
    for i in range(n_iterations):
        points = iteration(points)
        points = restrict(points)

    return points

class Bounds(object):
    @staticmethod
    def new(kind, points, clipping):
        if kind == 'BOX':
            return BoxBounds(points, clipping)
        elif kind == 'SPHERE':
            return SphereBounds(points, clipping)
        else:
            raise Exception("Unsupported bounds type")

    def contains(self, point):
        raise Exception("not implemented")

    def invert(self, point):
        raise Exception("not implemented")

    def restrict(self, point):
        raise Exception("not implemented")

    def make_mesh(self, diagram):
        raise Exception("not implemented")

class BoxBounds(Bounds):
    def __init__(self, points, clipping):
        points = np.array(points)
        xs = points[:,0]
        ys = points[:,1]
        zs = points[:,2]

        self.min_x = xs.min() - clipping
        self.max_x = xs.max() + clipping
        self.min_y = ys.min() - clipping
        self.max_y = ys.max() + clipping
        self.min_z = zs.min() - clipping
        self.max_z = zs.max() + clipping

    def contains(self, point):
        x, y, z = tuple(point)
        return (self.min_x <= x <= self.max_x) and (self.min_y <= y <= self.max_y) and (self.min_z <= z <= self.max_z)

    def restrict(self, point):
        #if self.contains(point):
        #    return point
        
        mid_x = 0.5 * (self.min_x + self.max_x)
        mid_y = 0.5 * (self.min_y + self.max_y)
        mid_z = 0.5 * (self.min_z + self.max_z)

        x, y, z = point

        if self.min_x <= x <= self.max_x:
            x1 = x
        else:
            if x > mid_x:
                x1 = self.max_x
            else:
                x1 = self.min_x

        if self.min_y <= y <= self.max_y:
            y1 = y
        else:
            if y > mid_y:
                y1 = self.max_y
            else:
                y1 = self.min_y

        if self.min_z <= z <= self.max_z:
            z1 = z
        else:
            if z > mid_z:
                z1 = self.max_z
            else:
                z1 = self.min_z

        return np.array([x1, y1, z1])

    def invert(self, point):
        point = np.array(point)
        projection = self.restrict(point)
        result = projection + 2 * (projection - point)
        #print(f"I: {point} => {projection} => {result}")
        return result

class SphereBounds(Bounds):
    def __init__(self, points, clipping):
        self.center, self.radius = bounding_sphere(points)
        self.center = np.array(self.center)
        self.radius += clipping

    def contains(self, point):
        point = np.array(point)
        dv = point - self.center
        return np.linalg.norm(dv) <= self.radius

    def restrict(self, point):
        #if self.contains(point):
        #    return point
        point = np.array(point)
        dv = point - self.center
        dv1 = self.radius * dv / np.linalg.norm(dv)
        projection = self.center + dv1
        return projection

    def invert(self, point):
        point = np.array(point)
        projection = self.restrict(point)
        return point + 2*(projection - point)

def lloyd3d_bounded(bounds, sites, n_iterations, weight_field=None):
    def invert(points):
        result = []
        for pt in points:
            if bounds.contains(pt):
                r = bounds.invert(pt)
                result.append(tuple(r))
        return result

    def restrict(points):
        result = [tuple(point if bounds.contains(point) else bounds.restrict(point)) for point in points]
        return result

    def iteration(pts):
        n = len(pts)
        all_pts = pts + invert(pts)
        diagram = Voronoi(all_pts)
        vertices = restrict(diagram.vertices)
        centers = []
        for site_idx in range(n):
            region_idx = diagram.point_region[site_idx]
            region = diagram.regions[region_idx]

            if -1 in region:
                site = pts[site_idx]
                centers.append(site)
                continue

            region_verts = np.array([vertices[i] for i in region])
            center = weighted_center(region_verts, weight_field)
            centers.append(tuple(center))
        return centers

    points = restrict(sites)
    for i in range(n_iterations):
        points = iteration(points)
        points = restrict(points)
    return points

