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

from sverchok.utils.sv_mesh_utils import mask_vertices, polygons_to_edges
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, bmesh_clip
from sverchok.utils.geom import calc_bounds
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial import Voronoi

def voronoi_on_surface(surface, uvpoints, thickness, do_clip, clipping, make_regions):
    npoints = len(uvpoints)
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
    diagram = Voronoi(all_points)
    
    region_verts = dict()
    region_verts_map = dict()
    for site_idx in range(npoints):
        region_idx = diagram.point_region[site_idx]
        region = diagram.regions[region_idx]
        vertices = [tuple(diagram.vertices[i,:]) for i in region]
        region_verts[site_idx] = vertices
        region_verts_map[site_idx] = {vert_idx: i for i, vert_idx in enumerate(region)}
    
    open_sites = set()
    region_faces = defaultdict(list)
    for ridge_idx, sites in enumerate(diagram.ridge_points):
        site_from, site_to = sites
#             if site_from < 0 or site_to < 0:
#                 print(ridge_idx, site_from, site_to)
        ridge = diagram.ridge_vertices[ridge_idx]
        if -1 in ridge:
            open_sites.add(site_from)
            open_sites.add(site_to)
        
        if make_regions:
            if site_from < npoints:
                face_from = [region_verts_map[site_from][i] for i in ridge]
                region_faces[site_from].append(face_from)
           
            if site_to < npoints:
                face_to = [region_verts_map[site_to][i] for i in ridge]
                region_faces[site_to].append(face_to)
        else:
            if site_from < npoints and site_to < npoints:
                face_from = [region_verts_map[site_from][i] for i in ridge]
                region_faces[site_from].append(face_from)
                face_to = [region_verts_map[site_to][i] for i in ridge]
                region_faces[site_to].append(face_to)
    
    verts = [region_verts[i] for i in range(npoints) if i not in open_sites]
    faces = [region_faces[i] for i in range(npoints) if i not in open_sites]

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
        bounds = calc_bounds(surface_points.tolist(), clipping)
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

