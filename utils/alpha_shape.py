# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict

from sverchok.utils.sv_mesh_utils import mask_vertices
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial import Delaunay

def alpha_shape(verts, alpha, fix_normals=True, volume_threshold = 1e-4):
    """
    Compute the alpha shape (concave hull) of a set of 3D points.
    Parameters:
        verts - np.array of shape (n, 3) points.
        alpha - alpha value.
    return
        outer surface edge indices and triangle indices
    """

    def calc_volume(tetra_verts):
        a = tetra_verts[:,0,:]
        b = tetra_verts[:,1,:]
        c = tetra_verts[:,2,:]
        d = tetra_verts[:,3,:]

        e1 = b - a
        e2 = c - a
        e3 = d - a

        e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
        e2 /= np.linalg.norm(e2, axis=1, keepdims=True)
        e3 /= np.linalg.norm(e3, axis=1, keepdims=True)

        volume = np.cross(e1, e2)
        volume = (volume * e3).sum(axis=1) / 6
        return abs(volume)

    alpha2 = alpha**2
    tetra = Delaunay(verts)
    # Find radius of the circumsphere.
    # By definition, radius of the sphere fitting inside the tetrahedral needs 
    # to be smaller than alpha value
    # http://mathworld.wolfram.com/Circumsphere.html
    tetra_verts = np.take(verts, tetra.simplices, axis=0) # (n_simplices, 4, 3)
    normsq = np.sum(tetra_verts**2, axis=2)[:, :, None]
    ones = np.ones((tetra_verts.shape[0], tetra_verts.shape[1], 1))
    a = np.linalg.det(np.concatenate((tetra_verts, ones), axis=2))
    Dx = np.linalg.det(np.concatenate((normsq, tetra_verts[:, :, [1, 2]], ones), axis=2))
    Dy = -np.linalg.det(np.concatenate((normsq, tetra_verts[:, :, [0, 2]], ones), axis=2))
    Dz = np.linalg.det(np.concatenate((normsq, tetra_verts[:, :, [0, 1]], ones), axis=2))
    c = np.linalg.det(np.concatenate((normsq, tetra_verts), axis=2))
    r2 = (Dx**2 + Dy**2 + Dz**2 - 4*a*c)/(4*np.abs(a)**2)

    small_radius = r2 < alpha2
    volumes = calc_volume(tetra_verts)
    non_planar = volumes >= volume_threshold
    good = np.logical_and(small_radius, non_planar)

    # Find tetrahedrals
    tetras = tetra.simplices[good, :]
    # triangles
    triangle_combinations = np.array([(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
    triangles = tetras[:, triangle_combinations].reshape(-1, 3)
    triangles = np.sort(triangles, axis=1)
    # Remove triangles that occurs twice, because they are within shapes
    triangles_dict = defaultdict(int)
    for tri in triangles:
        triangles_dict[tuple(tri)] += 1
    triangles = np.array([tri for tri in triangles_dict if triangles_dict[tri] ==1])
    #edges
    edges_comb = np.array([(0, 1), (0, 2), (1, 2)])
    edges = triangles[:, edges_comb].reshape(-1, 2)
    edges = np.sort(edges, axis=1)
    edges = np.unique(edges, axis=0)

    edges = edges.tolist()
    triangles = triangles.tolist()

    used_vert_idxs = set()
    for triangle in triangles:
        used_vert_idxs.update(set(triangle))
    verts_mask = [i in used_vert_idxs for i in range(len(verts))]

    verts, edges, faces = mask_vertices(verts, edges, triangles, verts_mask)
    if fix_normals:
        verts, edges, faces = recalc_normals(verts, edges, faces)

    return verts, edges, faces

