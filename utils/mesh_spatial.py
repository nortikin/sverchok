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
from mathutils import Vector
from mathutils.geometry import intersect_point_line
try:
    from mathutils.geometry import delaunay_2d_cdt
except ImportError:
    pass
from mathutils.bvhtree import BVHTree
import bmesh

from sverchok.data_structure import rotate_list, numpy_full_list, repeat_last_for_length
from sverchok.utils.geom import linear_approximation,calc_bounds
from sverchok.utils.sv_mesh_utils import point_inside_mesh
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.surface.populate import _check_min_radius, _check_min_distance
from sverchok.utils.field.probe import field_random_probe
from sverchok.utils.surface.primitives import SvPlane
from sverchok.utils.surface.populate import populate_surface

def is_on_edge(pt, v1, v2, epsilon=1e-6):
    nearest, percentage = intersect_point_line(pt, v1, v2)
    distance = (Vector(pt) - nearest).length
    return (0.0 <= percentage <= 1.0) and (distance < epsilon)

def is_on_face_edge(pt, face_verts, epsilon=1e-6):
    for v1, v2 in zip(face_verts, rotate_list(face_verts)):
        if is_on_edge(pt, v1, v2, epsilon):
            return True
    return False

def single_face_delaunay(face_verts, add_verts, epsilon=1e-6, exclude_boundary=True):
    n = len(face_verts)
    face = list(range(n))
    edges = [(i,i+1) for i in range(n-1)] + [(n-1, 0)]
    plane = linear_approximation(face_verts).most_similar_plane()
    face_verts_2d = [plane.point_uv_projection(v) for v in face_verts]
    if exclude_boundary:
        add_verts = [v for v in add_verts if not is_on_face_edge(v, face_verts, epsilon)]
    add_verts_2d = [plane.point_uv_projection(v) for v in add_verts]
    TRIANGLES = 1
    res = delaunay_2d_cdt(face_verts_2d + add_verts_2d, edges, [face], TRIANGLES, epsilon)
    new_verts_2d = res[0]
    new_edges = res[1]
    new_faces = res[2]
    new_add_verts = [tuple(plane.evaluate(p[0], p[1], normalize=True)) for p in new_verts_2d[n:]]
    return face_verts + new_add_verts, new_edges, new_faces

def mesh_insert_verts(verts, faces, add_verts_by_face, epsilon=1e-6, exclude_boundary=True, recalc_normals=True, preserve_shape=False):
    if preserve_shape:
        bvh = BVHTree.FromPolygons(verts, faces)
    bm = bmesh_from_pydata(verts, [], [])
    for face_idx, face in enumerate(faces):
        n = len(face)
        add_verts = add_verts_by_face.get(face_idx)

        if not add_verts:
            bm_verts = [bm.verts[idx] for idx in face]
            bm.faces.new(bm_verts)
            bm.faces.index_update()
            continue

        done_verts = dict((i, bm.verts[face[i]]) for i in range(n))
        face_verts = [verts[i] for i in face]
        new_face_verts, edges, new_faces = single_face_delaunay(face_verts, add_verts, epsilon, exclude_boundary)
        if preserve_shape:
            new_face_verts = find_nearest_points(bvh, new_face_verts)
        for new_face in new_faces:
            bm_verts = []
            for i in new_face:
                bm_vert = done_verts.get(i)
                if not bm_vert:
                    bm_vert = bm.verts.new(new_face_verts[i])
                    bm.verts.index_update()
                    bm.verts.ensure_lookup_table()
                    done_verts[i] = bm_vert
                bm_verts.append(bm_vert)
                
            bm.faces.new(bm_verts)
            bm.faces.index_update()

    if recalc_normals:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    verts, edges, faces = pydata_from_bmesh(bm)
    bm.free()
    return verts, edges, faces

def find_nearest_points(bvh, verts):
    locs = []
    for vert in verts:
        loc, normal, idx, distance = bvh.find_nearest(vert)
        locs.append(tuple(loc))
    return locs

def find_nearest_idxs(verts, faces, add_verts):
    bvh = BVHTree.FromPolygons(verts, faces)
    idxs = []
    for vert in add_verts:
        loc, normal, idx, distance = bvh.find_nearest(vert)
        idxs.append(idx)
    return idxs

def _verts_edges(verts, edges):
    if isinstance(verts, np.ndarray):
        np_verts = verts
    else:
        np_verts = np.array(verts)
    if isinstance(edges, np.ndarray):
        np_edges = edges
    else:
        np_edges = np.array(edges)
    return np_verts[np_edges]

BATCH_SIZE = 200
MAX_ITERATIONS = 1000

def populate_mesh_volume(verts, bvh, field, count,
                         min_r, radius_field, threshold,
                         field_min, field_max,
                         proportional_field = False,
                         random_radius=False,
                         seed=0):
    def check(vert):
        result = point_inside_mesh(bvh, vert)
        #print(f"{vert} => {result}")
        return result

    x_min, x_max, y_min, y_max, z_min, z_max = calc_bounds(verts)
    bbox = ((x_min, y_min, z_min), (x_max, y_max, z_max))
    
    return field_random_probe(field, bbox, count, threshold,
                proportional_field, field_min, field_max,
                min_r = min_r, min_r_field = radius_field,
                random_radius = random_radius,
                seed = seed, predicate=check)

def populate_mesh_surface(bm, weights, field,
                          total_count, min_r, min_r_field,
                          threshold, field_min, field_max,
                          proportional_field=False,
                          proportional_faces=True,
                          random_radius=False,
                          seed=0, predicate=None):

    def get_weights():
        nonlocal weights
        if proportional_faces:
            areas = [face.calc_area() for face in bm.faces]
        else:
            areas = [1.0 for face in bm.faces]
        if weights is None:
            weights = areas
        else:
            weights = repeat_last_for_length(weights, len(bm.faces))
            weights = [w*a for w, a in zip(weights, areas)]

        return weights

    all_idxs = np.arange(len(bm.faces))
    start_verts = np.array([f.verts[0].co for f in bm.faces])
    edges_1 = np.array([f.verts[1].co - f.verts[0].co for f in bm.faces])
    edges_2 = np.array([f.verts[2].co - f.verts[0].co for f in bm.faces])
    weights = get_weights()

    def generate_batch(batch_size):
        ps = np.array(weights) / np.sum(weights)
        chosen_faces = np.random.choice(all_idxs,
                                         batch_size,
                                         replace=True,
                                         p = ps)
        faces_with_points, points_per_face = np.unique(chosen_faces, return_counts=True)
        uvs = np.random.uniform(0.0, 1.0, size=(batch_size,2))
        us = uvs[:,0]
        vs = uvs[:,1]
        edges_u = np.repeat(edges_1[faces_with_points], points_per_face, axis=0)
        edges_v = np.repeat(edges_2[faces_with_points], points_per_face, axis=0)
        start = np.repeat(start_verts[faces_with_points], points_per_face, axis=0)
        chosen_indices = np.repeat(all_idxs[faces_with_points], points_per_face, axis=0)
        random_points = start + edges_u * us[np.newaxis].T + edges_v * vs[np.newaxis].T
        good_uv_idxs = (us + vs) <= 1
        return random_points[good_uv_idxs], chosen_indices[good_uv_idxs]

    if seed == 0:
        seed = 12345
    if seed is not None:
        np.random.seed(seed)

    done = 0
    iterations = 0
    generated_pts = []
    generated_idxs = []
    generated_radiuses = []

    if field is None and min_r == 0 and min_r_field is None and predicate is None:
        batch_size = total_count
    else:
        batch_size = BATCH_SIZE

    while done < total_count:
        iterations += 1
        if iterations > MAX_ITERATIONS:
            sv_logger.error("Maximum number of iterations (%s) reached, stop.", MAX_ITERATIONS)
            break
        left = total_count - done
        size = min(batch_size, left)
        batch_pts, batch_idxs = generate_batch(size)
        size = len(batch_pts)

        if field is not None:
            values = field.evaluate_grid(batch_pts[:,0], batch_pts[:,1], batch_pts[:,2])
            threshold_idxs = values >= threshold
            if not proportional_field:
                good_idxs = threshold_idxs
            else:
                probes = np.random.uniform(field_min, field_max, size=size)
                probe_idxs = probes <= values
                good_idxs = np.logical_and(threshold_idxs, probe_idxs)
            candidates = batch_pts[good_idxs]
            candidate_idxs = batch_idxs[good_idxs]
        else:
            candidates = batch_pts
            candidate_idxs = batch_idxs

        good_radiuses = []
        if len(candidates) > 0:
            if min_r == 0 and min_r_field is None:
                good_pts = candidates
                good_idxs = candidate_idxs
                good_radiuses = np.zeros((len(good_pts),))
            elif min_r_field is not None:
                min_rs = min_r_field.evaluate_grid(candidates[:,0], candidates[:,1], candidates[:,2])
                if random_radius:
                    min_rs = np.random.uniform(
                                np.zeros((len(candidates),)),
                                min_rs
                            )
                good_pts = []
                good_idxs = []
                for candidate_idx, candidate, min_r in zip(candidate_idxs, candidates, min_rs):
                    radius_ok = _check_min_radius(candidate,
                                                  generated_pts + good_pts,
                                                  generated_radiuses + good_radiuses,
                                                  min_r)
                    if radius_ok:
                        good_pts.append(candidate)
                        good_idxs.append(candidate_idx)
                        good_radiuses.append(min_r)
            else: # min_r != 0:
                good_pts = []
                good_idxs = []
                for candidate_idx, candidate in zip(candidate_idxs, candidates):
                    distance_ok = _check_min_distance(candidate,
                                                      generated_pts + good_pts,
                                                      min_r)
                    if distance_ok:
                        good_pts.append(candidate)
                        good_idxs.append(candidate_idx)
                        good_radiuses.append(0)
            if predicate is not None:
                res = [(i, pt, radius) for i, pt, radius in zip(good_idxs, good_pts, good_radiuses) if predicate(pt)]
                good_idxs = [r[0] for r in res]
                good_pts = [r[1] for r in res]
                good_radiuses = [r[2] for r in res]

            generated_pts.extend(np.array(good_pts).tolist())
            generated_idxs.extend(good_idxs)
            generated_radiuses.extend(good_radiuses)
            done += len(good_pts)

    return generated_idxs, generated_pts, generated_radiuses

def populate_mesh_edges(verts, edges, weights,
                       field, total_count, threshold,
                       field_min=None, field_max=None,
                       min_r=0, min_r_field = None,
                       random_radius = False,
                       avoid_spheres = None,
                       proportional_field=False,
                       proportional_edges=True,
                       seed=0, predicate=None):


    def get_weights(edges_dir, weights):
        if proportional_edges:
            lengths = np.linalg.norm(edges_dir, axis=1)
        else:
            lengths = np.full((len(edges_dir),), 1.0)

        if weights is not None and len(weights) > 0:
            weights = numpy_full_list(weights, len(edges_dir)) * lengths
        else:
            weights = lengths

        return weights

    if seed == 0:
        seed = 12345
    if seed is not None:
        np.random.seed(seed)

    v_edges = _verts_edges(verts, edges)
    edges_dir = v_edges[:, 1] - v_edges[:, 0]
    weights = get_weights(edges_dir, weights)
    indices = np.arange(len(edges))

    if avoid_spheres is not None:
        old_points = [s[0] for s in avoid_spheres]
        old_radiuses = [s[1] for s in avoid_spheres]
    else:
        old_points = []
        old_radiuses = []

    def generate_batch(batch_size):
        ps = np.array(weights) / np.sum(weights)
        chosen_edges = np.random.choice(indices,
                                        batch_size,
                                        replace=True,
                                        p=ps)

        edges_with_points, points_total_per_edge = np.unique(chosen_edges, return_counts=True)
        t_s = np.random.uniform(low=0, high=1, size=batch_size)
        direc = np.repeat(edges_dir[edges_with_points], points_total_per_edge, axis=0)
        orig = np.repeat(v_edges[edges_with_points, 0], points_total_per_edge, axis=0)

        chosen_indices = np.repeat(indices[edges_with_points], points_total_per_edge, axis=0)
        random_points = orig + direc * t_s[np.newaxis].T

        return random_points, chosen_indices

    done = 0
    iterations = 0
    generated_pts = []
    generated_idxs = []
    generated_radiuses = []

    if field is None and avoid_spheres is None and min_r == 0 and min_r_field is None and predicate is None:
        batch_size = total_count
    else:
        batch_size = BATCH_SIZE
    while done < total_count:
        if iterations > MAX_ITERATIONS:
            sv_logger.error("Maximum number of iterations (%s) reached, generated only (%s) points of (%s), stop.", MAX_ITERATIONS, done, total_count)
            break
        iterations += 1
        left = total_count - done
        size = min(batch_size, left)
        batch_pts, batch_idxs = generate_batch(size)

        if field is not None:
            values = field.evaluate_grid(batch_pts[:,0], batch_pts[:,1], batch_pts[:,2])

            threshold_idxs = values >= threshold
            if not proportional_field:
                good_idxs = threshold_idxs
            else:
                probes = np.random.uniform(field_min, field_max, size=size)
                probe_idxs = probes <= values
                good_idxs = np.logical_and(threshold_idxs, probe_idxs)
            candidates = batch_pts[good_idxs]
            candidate_idxs = batch_idxs[good_idxs]
        else:
            candidates = batch_pts
            candidate_idxs = batch_idxs

        good_radiuses = []
        if len(candidates) > 0:
            if min_r == 0 and min_r_field is None:
                good_pts = candidates
                good_idxs = candidate_idxs
                good_radiuses = np.zeros((len(good_pts),))
            elif min_r_field is not None:
                min_rs = min_r_field.evaluate_grid(candidates[:,0], candidates[:,1], candidates[:,2])
                if random_radius:
                    min_rs = np.random.uniform(
                                np.zeros((len(candidates),)),
                                min_rs
                            )
                good_pts = []
                good_idxs = []
                for candidate_idx, candidate, min_r in zip(candidate_idxs, candidates, min_rs):
                    radius_ok = _check_min_radius(candidate,
                                                  old_points + generated_pts + good_pts,
                                                  old_radiuses + generated_radiuses + good_radiuses,
                                                  min_r)
                    if radius_ok:
                        good_pts.append(candidate)
                        good_idxs.append(candidate_idx)
                        good_radiuses.append(min_r)
            else: # min_r != 0:
                good_pts = []
                good_idxs = []
                for candidate_idx, candidate in zip(candidate_idxs, candidates):
                    distance_ok = _check_min_distance(candidate,
                                                      old_points + generated_pts + good_pts,
                                                      min_r)
                    if distance_ok:
                        good_pts.append(candidate)
                        good_idxs.append(candidate_idx)
                        good_radiuses.append(0)
            if predicate is not None:
                res = [(i, pt, radius) for i, pt, radius in zip(good_idxs, good_pts, good_radiuses) if predicate(pt)]
                good_idxs = [r[0] for r in res]
                good_pts = [r[1] for r in res]
                good_radiuses = [r[2] for r in res]

            generated_pts.extend(np.array(good_pts).tolist())
            generated_idxs.extend(good_idxs)
            generated_radiuses.extend(good_radiuses)
            done += len(good_pts)

    return generated_idxs, generated_pts, generated_radiuses

