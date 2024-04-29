"""Point based clustering module"""

import ctypes

import numpy as np
import math
import pyvista as pv
from scipy import sparse
from cython.parallel import prange

from pyacvd import _clustering


def _clustering_weighted_points_double(v, f, additional_weights, return_weighted=True):
    """
    Returns point weight based on area weight and weighted points.
    Points are weighted by adjacent area faces.

    Parameters
    ----------
    v : np.ndarray, np.double
        Point array

    f : np.ndarray, int
        n x 4 face array.  First column is padding and is ignored.

    Returns
    -------
    pweight : np.ndarray, np.double
        Point weight array

    wvertex : np.ndarray, np.double
        Vertices mutlipled by their corresponding weights.
    """
    if f.shape[1] != 4:
        raise Exception('Must be an unclipped vtk face array')

    nfaces = f.shape[0]
    npoints = v.shape[0]
    pweight = np.zeros(npoints)
    farea = np.empty(nfaces)
    wvertex = np.empty((npoints, 3))

    #cdef double v0_0, v0_1, v0_2
    #cdef double v1_0, v1_1, v1_2
    #cdef double v2_0, v2_1, v2_2
    #cdef double e0_0, e0_1, e0_2
    #cdef double e1_0, e1_1, e1_2
    #cdef double c0, c1, c2
    #cdef double farea_l
    #cdef int i

    #cdef int point0, point1, point2

    for i in prange(nfaces, nogil=True):
        point0 = f[i, 1]
        point1 = f[i, 2]
        point2 = f[i, 3]

        v0_0 = v[point0, 0]
        v0_1 = v[point0, 1]
        v0_2 = v[point0, 2]

        v1_0 = v[point1, 0]
        v1_1 = v[point1, 1]
        v1_2 = v[point1, 2]

        v2_0 = v[point2, 0]
        v2_1 = v[point2, 1]
        v2_2 = v[point2, 2]

        # Edges
        e0_0 = v1_0 - v0_0
        e0_1 = v1_1 - v0_1
        e0_2 = v1_2 - v0_2

        e1_0 = v2_0 - v0_0
        e1_1 = v2_1 - v0_1
        e1_2 = v2_2 - v0_2

        c0 = e0_1*e1_2 - e0_2*e1_1
        c1 = e0_2*e1_0 - e0_0*e1_2
        c2 = e0_0*e1_1 - e0_1*e1_0

        # triangle area
        farea[i] = 0.5*math.sqrt(c0**2 + c1**2 + c2**2)  # подумать о numpy

    for i in range(nfaces):
        point0 = f[i, 1]
        point1 = f[i, 2]
        point2 = f[i, 3]
        farea_l = farea[i]

        # Store the area of the faces adjacent to each point
        pweight[point0] += farea_l
        pweight[point1] += farea_l
        pweight[point2] += farea_l

    # Compute weighted vertex
    #cdef double wgt
    if return_weighted:
        if additional_weights.shape[0] == npoints:
            for i in prange(npoints, nogil=True):
                wgt = additional_weights[i]*pweight[i]
                wvertex[i, 0] = wgt*v[i, 0]
                wvertex[i, 1] = wgt*v[i, 1]
                wvertex[i, 2] = wgt*v[i, 2]

        else:
            for i in prange(npoints, nogil=True):
                wgt = pweight[i]
                wvertex[i, 0] = wgt*v[i, 0]
                wvertex[i, 1] = wgt*v[i, 1]
                wvertex[i, 2] = wgt*v[i, 2]

        return np.asarray(pweight), np.asarray(wvertex)

    else:
        return np.asarray(pweight)


def _clustering_weighted_points_float(v, f, additional_weights, return_weighted=True):
    """
    Returns point weight based on area weight and weighted points.
    Points are weighted by adjacent area faces.

    Parameters
    ----------
    v : np.ndarray, np.float
        Point array

    f : np.ndarray, int
        n x 4 face array.  First column is padding and is ignored.

    Returns
    -------
    pweight : np.ndarray, np.double
        Point weight array

    wvertex : np.ndarray, np.double
        Vertices mutlipled by their corresponding weights.
    """
    if f.shape[1] != 4:
        raise Exception('Must be an unclipped vtk face array')

    nfaces = f.shape[0]
    npoints = v.shape[0]
    pweight = np.zeros(npoints)
    farea = np.empty(nfaces)
    wvertex = np.empty((npoints, 3))

    #cdef double v0_0, v0_1, v0_2
    #cdef double v1_0, v1_1, v1_2
    #cdef double v2_0, v2_1, v2_2
    #cdef double e0_0, e0_1, e0_2
    #cdef double e1_0, e1_1, e1_2
    #cdef double c0, c1, c2
    #cdef double farea_l
    #cdef int i

    #cdef int point0, point1, point2

    for i in prange(nfaces, nogil=True):
        point0 = f[i, 1]
        point1 = f[i, 2]
        point2 = f[i, 3]

        v0_0 = v[point0, 0]
        v0_1 = v[point0, 1]
        v0_2 = v[point0, 2]

        v1_0 = v[point1, 0]
        v1_1 = v[point1, 1]
        v1_2 = v[point1, 2]

        v2_0 = v[point2, 0]
        v2_1 = v[point2, 1]
        v2_2 = v[point2, 2]

        # Edges
        e0_0 = v1_0 - v0_0
        e0_1 = v1_1 - v0_1
        e0_2 = v1_2 - v0_2

        e1_0 = v2_0 - v0_0
        e1_1 = v2_1 - v0_1
        e1_2 = v2_2 - v0_2

        c0 = e0_1*e1_2 - e0_2*e1_1
        c1 = e0_2*e1_0 - e0_0*e1_2
        c2 = e0_0*e1_1 - e0_1*e1_0

        # triangle area
        farea[i] = 0.5*math.sqrt(c0**2 + c1**2 + c2**2)  # Подумать о numpy

    for i in range(nfaces):
        point0 = f[i, 1]
        point1 = f[i, 2]
        point2 = f[i, 3]
        farea_l = farea[i]

        # Store the area of the faces adjacent to each point
        pweight[point0] += farea_l
        pweight[point1] += farea_l
        pweight[point2] += farea_l

    # Compute weighted vertex
    #cdef double wgt
    if return_weighted:
        if additional_weights.shape[0] == npoints:
            for i in prange(npoints, nogil=True):
                wgt = additional_weights[i]*pweight[i]
                wvertex[i, 0] = wgt*v[i, 0]
                wvertex[i, 1] = wgt*v[i, 1]
                wvertex[i, 2] = wgt*v[i, 2]

        else:
            for i in prange(npoints, nogil=True):
                wgt = pweight[i]
                wvertex[i, 0] = wgt*v[i, 0]
                wvertex[i, 1] = wgt*v[i, 1]
                wvertex[i, 2] = wgt*v[i, 2]

        return np.asarray(pweight), np.asarray(wvertex)

    else:
        return np.asarray(pweight)


def _clustering_max_con_face(npoints, f):
    """Get maximum number of connections given edges """

    nfaces = f.shape[0]
    #cdef int i
    mxval = 0
    ncon = np.zeros(npoints, ctypes.c_int)

    for i in range(nfaces):
        for j in range(1, 4):
            ncon[f[i, j]] += 1

    for i in range(npoints):
        if ncon[i] > mxval:
            mxval = ncon[i]

    return mxval

def _clustering_neighbors_from_faces(npoints, f):
    """
    Assemble neighbor array based on faces

    Parameters
    ----------
    points : int
        Number of points

    f : int [:, ::1]
        Face array.

    Returns
    -------
    neigh : int np.ndarray [:, ::1]
        Indices of each neighboring node for each node.

    nneigh : int np.ndarray [::1]
        Number of neighbors for each node.
    """

    # Find the maximum number of edges, with overflow buffer
    nconmax = _clustering_max_con_face(npoints, f) + 10
    # NON-CODE BREAKING BUG: under-estimates number of connections

    nfaces = f.shape[0]
    #cdef int i, j, k, pA, pB, pC
    neigharr = np.empty((npoints, nconmax), ctypes.c_int)
    neigharr[:] = -1
    ncon = np.empty(npoints, ctypes.c_int)
    ncon[:] = 0

    for i in range(nfaces):

        # for each edge
        for j in range(1, 4):

            # always the current point
            pA = f[i, j]

            # wrap around last edge
            if j < 4 - 1:
                pB = f[i, j + 1]
            else:
                pB = f[i, 1]

            for k in range(nconmax):
                if neigharr[pA, k] == pB:
                    break
                elif neigharr[pA, k] == -1:
                    neigharr[pA, k] = pB
                    ncon[pA] += 1

                    # Mirror node will have the same number of connections
                    neigharr[pB, ncon[pB]] = pA
                    ncon[pB] += 1
                    break

    py_neigharr = np.asarray(neigharr)
    py_ncon = np.asarray(ncon)
    py_neigharr = np.ascontiguousarray(py_neigharr[:, :py_ncon.max()])
    return py_neigharr, py_ncon

def _clustering_subdivision(v, f):
    """Subdivide triangles

    Parameters
    ----------
    v : double np.ndarray
        Point array

    f : np.ndarray
        n x 4 face array.  First column is padding and is ignored.
    """
    nface = f.shape[0]
    nvert = v.shape[0]
    #cdef int i, j

    # Vertex and face arrays for maximum possible array sizes
    newv = np.empty((nvert + nface*3, 3))
    newf = np.empty((nface*4, 4), dtype=ctypes.c_int)

    # copy existing vertex array
    for i in range(nvert):
        for j in range(3):
            newv[i, j] = v[i, j]

    # split triangle into three new ones
    vc = nvert
    fc = 0
    #cdef int point0, point1, point2
    for i in range(nface):
        point0 = f[i, 1]
        point1 = f[i, 2]
        point2 = f[i, 3]

        # Face 0
        newf[fc, 0] = 3
        newf[fc, 1] = point0
        newf[fc, 2] = vc
        newf[fc, 3] = vc + 2
        fc += 1

        # Face 1
        newf[fc, 0] = 3
        newf[fc, 1] = point1
        newf[fc, 2] = vc + 1
        newf[fc, 3] = vc
        fc += 1

        # Face 2
        newf[fc, 0] = 3
        newf[fc, 1] = point2
        newf[fc, 2] = vc + 2
        newf[fc, 3] = vc + 1
        fc += 1

        # Face 3
        newf[fc, 0] = 3
        newf[fc, 1] = vc
        newf[fc, 2] = vc + 1
        newf[fc, 3] = vc + 2
        fc += 1

        # New Vertices
        newv[vc, 0] = (v[point0, 0] + v[point1, 0])*0.5
        newv[vc, 1] = (v[point0, 1] + v[point1, 1])*0.5
        newv[vc, 2] = (v[point0, 2] + v[point1, 2])*0.5
        vc += 1

        newv[vc, 0] = (v[point1, 0] + v[point2, 0])*0.5
        newv[vc, 1] = (v[point1, 1] + v[point2, 1])*0.5
        newv[vc, 2] = (v[point1, 2] + v[point2, 2])*0.5
        vc += 1

        newv[vc, 0] = (v[point0, 0] + v[point2, 0])*0.5
        newv[vc, 1] = (v[point0, 1] + v[point2, 1])*0.5
        newv[vc, 2] = (v[point0, 2] + v[point2, 2])*0.5
        vc += 1

    # Splice and return
    return np.asarray(newv), np.asarray(newf)


def cluster_centroid(cent, area, clusters):
    """Computes an area normalized centroid for each cluster"""

    # Check if null cluster exists
    null_clusters = np.any(clusters == -1)
    if null_clusters:
        clusters = clusters.copy()
        clusters[clusters == -1] = clusters.max() + 1

    wval = cent * area.reshape(-1, 1)
    cweight = np.bincount(clusters, weights=area)
    cweight[cweight == 0] = 1

    cval = (
        np.vstack(
            (
                np.bincount(clusters, weights=wval[:, 0]),
                np.bincount(clusters, weights=wval[:, 1]),
                np.bincount(clusters, weights=wval[:, 2]),
            )
        )
        / cweight
    )

    if null_clusters:
        cval[:, -1] = np.inf

    return cval.T


def create_mesh(mesh, area, clusters, cnorm, flipnorm=True):
    """Generates a new mesh given cluster data

    moveclus is a boolean flag to move cluster centers to the surface of their
    corresponding cluster

    """
    faces = mesh.faces.reshape(-1, 4)
    points = mesh.points
    if points.dtype != np.double:
        points = points.astype(np.double)

    # Compute centroids
    ccent = np.ascontiguousarray(cluster_centroid(points, area, clusters))

    # Create sparse matrix storing the number of adjacent clusters a point has
    rng = np.arange(faces.shape[0]).reshape((-1, 1))
    a = np.hstack((rng, rng, rng)).ravel()
    b = clusters[faces[:, 1:]].ravel()  # take?
    c = np.ones(len(a), dtype="bool")

    boolmatrix = sparse.csr_matrix((c, (a, b)), dtype="bool")

    # Find all points with three neighboring clusters.  Each of the three
    # cluster neighbors becomes a point on a triangle
    nadjclus = boolmatrix.sum(1)
    adj = np.array(nadjclus == 3).nonzero()[0]
    idx = boolmatrix[adj].nonzero()[1]

    # Append these points and faces
    points = ccent
    f = idx.reshape((-1, 3))

    # Remove duplicate faces
    f = f[unique_row_indices(np.sort(f, 1))]

    # Mean normals of clusters each face is build from
    if flipnorm:
        adjcnorm = cnorm[f].sum(1)
        adjcnorm /= np.linalg.norm(adjcnorm, axis=1).reshape(-1, 1)

        # and compare this with the normals of each face
        faces = np.empty((f.shape[0], 4), dtype=f.dtype)
        faces[:, 0] = 3
        faces[:, 1:] = f

        tmp_msh = pv.PolyData(points, faces.ravel())
        tmp_msh.compute_normals(point_normals=False, inplace=True, consistent_normals=False)
        newnorm = tmp_msh.cell_data["Normals"]

        # If the dot is negative, reverse the order of those faces
        agg = (adjcnorm * newnorm).sum(1)  # dot product
        mask = agg < 0.0
        f[mask] = f[mask, ::-1]

    # Create vtk surface
    triangles = np.empty((f.shape[0], 4), dtype=f.dtype)
    triangles[:, -3:] = f
    triangles[:, 0] = 3
    return pv.PolyData(points, triangles.ravel())


def unique_row_indices(a):
    """Indices of unique rows"""
    b = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
    _, idx = np.unique(b, return_index=True)
    return idx

def weighted_points(mesh, return_weighted=True, additional_weights=None):
    """Returns point weight based on area weight and weighted points.

    Points are weighted by adjacent area faces.

    Parameters
    ----------
    mesh : pv.PolyData
        All triangular surface mesh.

    return_weighted : bool, optional
        Returns vertices mutlipled by point weights.

    Returns
    -------
    pweight : np.ndarray, np.double
        Point weight array

    wvertex : np.ndarray, np.double
        Vertices mutlipled by their corresponding weights.  Returned only
        when return_weighted is True.

    """
    faces = mesh.faces.reshape(-1, 4)
    if faces.dtype != np.int32:
        faces = faces.astype(np.int32)
    points = mesh.points

    if additional_weights is not None:
        weights = additional_weights
        return_weighted = True
        if not weights.flags["C_CONTIGUOUS"]:
            weights = np.ascontiguousarray(weights, dtype=ctypes.c_double)
        elif weights.dtype != ctypes.c_double:
            weights = weights.astype(ctypes.c_double)

        if (weights < 0).any():
            raise Exception("Negative weights not allowed.")

    else:
        weights = np.array([])

    if points.dtype == np.float64:
        weighted_point_func = _clustering_weighted_points_double
    else:
        weighted_point_func = _clustering_weighted_points_float

    return weighted_point_func(points, faces, weights, return_weighted)

def neighbors_from_mesh(mesh):
    """Assemble neighbor array.  Assumes all-triangular mesh.

    Parameters
    ----------
    mesh : pyvista.PolyData
        Mesh to assemble neighbors from.

    Returns
    -------
    neigh : int np.ndarray [:, ::1]
        Indices of each neighboring node for each node.

    nneigh : int np.ndarray [::1]
        Number of neighbors for each node.
    """
    npoints = mesh.number_of_points
    faces = mesh.faces.reshape(-1, 4)
    if faces.dtype != np.int32:
        faces = faces.astype(np.int32)

    return _clustering_neighbors_from_faces(npoints, faces)

def _subdivide(mesh, nsub):
    """Perform a linear subdivision of a mesh"""
    new_faces = mesh.faces.reshape(-1, 4)
    if new_faces.dtype != np.int32:
        new_faces = new_faces.astype(np.int32)

    new_points = mesh.points
    if new_points.dtype != np.double:
        new_points = new_points.astype(np.double)

    for _ in range(nsub):
        new_points, new_faces = _clustering_subdivision(new_points, new_faces)

    sub_mesh = pv.PolyData(new_points, new_faces)
    sub_mesh.clean(inplace=True)
    return sub_mesh

class Clustering:
    """Uniform point clustering based on ACVD.

    Parameters
    ----------
    mesh : pyvista.PolyData
        Mesh to cluster.

    Examples
    --------
    Perform a uniform recluster of the stanford bunny.

    >>> from pyvista import examples
    >>> import pyacvd
    >>> mesh = examples.download_bunny()
    >>> clus = pyacvd.Clustering()
    >>> clus.cluster()
    >>> remeshed = clus.create_mesh()

    """

    def __init__(self, mesh):
        """Check inputs and initializes neighbors"""
        # mesh must be triangular
        if not mesh.is_all_triangles:
            mesh = mesh.triangulate()

        self.mesh = mesh.copy()
        self.clusters = None
        self.nclus = None
        self.remesh = None
        self._area = None
        self._wcent = None
        self._neigh = None
        self._nneigh = None
        self._edges = None
        self._update_data(None)

    def _update_data(self, weights=None):
        # Compute point weights and weighted points
        self._area, self._wcent = weighted_points(self.mesh, additional_weights=weights)

        # neighbors and edges
        self._neigh, self._nneigh = neighbors_from_mesh(self.mesh)
        self._edges = _clustering.edge_id(self._neigh, self._nneigh)

    def _clustering_init_clusters(self, clusters, neighbors,
                            nneigh, area, nclus, items):
        """ Initialize clusters"""

        # cdef double tarea, new_area, carea
        # cdef int item
        # cdef int i, j, k, checkitem, c, c_prev
        # cdef double ctarea
        lstind = 0
        npoints = area.shape[0]
        #cdef int i_items_new, i_items_old

        # Total mesh size
        area_remain = 0
        for i in range(npoints):
            area_remain += area[i]

        # Assign clsuters
        ctarea = area_remain/nclus
        for i in range(nclus):
            # Get target area and reset current area
            tarea = area_remain - ctarea*(nclus - i - 1)
            carea = 0.0

            # Get starting index (the first free face in list)
            i_items_new = 0
            for j in range(lstind, npoints):
                if clusters[j] == -1:
                    carea += area[j]
                    items[i_items_new, 0] = j
                    clusters[j] = i
                    lstind = j
                    break

            if j == npoints:
                break

            # While there are new items to be added
            c = 1
            while c:

                # reset items
                c_prev = c
                c = 0
                # switch indices
                if i_items_new == 0:
                    i_items_old = 0
                    i_items_new = 1
                else:
                    i_items_old = 1
                    i_items_new = 0


                # progressively add neighbors
                for j in range(c_prev):
                    checkitem = items[i_items_old, j]
                    for k in range(nneigh[checkitem]):
                        item = neighbors[checkitem, k]

                        # check if the face is free
                        if clusters[item] == -1:
                            # if allowable, add to cluster
                            if area[item] + carea < tarea:
                                carea += area[item]
                                clusters[item] = i
                                items[i_items_new, c] = item
                                c += 1

            area_remain -= carea

    def _clustering_grow_null(self, edges, clusters):
        """ Grow clusters to include null faces """
        #cdef int i
        #cdef int face_a, face_b, clusA, clusB, nchange

        nchange = 1
        while nchange > 0:
            nchange = 0
            # Determine edges that share two clusters
            for i in range(edges.shape[0]):
                # Get the two clusters sharing an edge
                face_a = edges[i, 0]
                face_b = edges[i, 1]
                clusA = clusters[face_a]
                clusB = clusters[face_b]

                # Check and immedtialy flip a cluster edge if one is part
                # of the null cluster
                if clusA == -1 and clusB != -1:
                    clusters[face_a] = clusB
                    nchange += 1
                elif clusB == -1 and clusA != -1:
                    clusters[face_b] = clusA
                    nchange += 1


    def _clustering_minimize_energy(self, edges, clusters, area, sgamma, cent, srho,
                        cluscount, maxiter, energy, mod1, mod2):
        """ Minimize cluster energy"""
        #cdef int face_a, face_b, clusA, clusB
        #cdef double areaface_a, centA0, centA1, centA2
        #cdef double areaface_b, centB0, centB1, centB2
        #cdef double eA, eB, eorig, eAwB, eBnB, eAnA, eBwA
        nchange = 1
        niter = 0
        nclus = mod1.shape[0]
        nedge = edges.shape[0]
        #cdef int i

        #cdef int [1] nchange_arr

        # start all as modified
        for i in range(nclus):
            mod2[i] = 1

        tlast = 0
        while nchange > 0 and niter < maxiter:

            # Reset modification arrays
            for i in range(nclus):
                mod1[i] = mod2[i]
                mod2[i] = 0

            nchange = 0
            for i in range(nedge):
                # Get the two clusters sharing an edge
                face_a = edges[i, 0]
                face_b = edges[i, 1]
                clusA = clusters[face_a]
                clusB = clusters[face_b]

                # If edge shares two different clusters and at least one
                # has been modified since last iteration
                if clusA != clusB and (mod1[clusA] == 1 or mod1[clusB] == 1):
                    # Verify that face can be removed from cluster
                    if cluscount[clusA] > 1 and cluscount[clusB] > 1:

                        areaface_a = area[face_a]
                        centA0 = cent[face_a, 0]
                        centA1 = cent[face_a, 1]
                        centA2 = cent[face_a, 2]

                        areaface_b = area[face_b]
                        centB0 = cent[face_b, 0]
                        centB1 = cent[face_b, 1]
                        centB2 = cent[face_b, 2]

                        # Current energy
                        eorig =  energy[clusA] + energy[clusB]

                        # Energy with both items assigned to cluster A
                        eAwB = ((sgamma[clusA, 0] + centB0)**2 + \
                                (sgamma[clusA, 1] + centB1)**2 + \
                                (sgamma[clusA, 2] + centB2)**2)/(srho[clusA] + areaface_b)

                        eBnB = ((sgamma[clusB, 0] - centB0)**2 + \
                                (sgamma[clusB, 1] - centB1)**2 + \
                                (sgamma[clusB, 2] - centB2)**2)/(srho[clusB] - areaface_b)

                        eA = eAwB + eBnB

                        # Energy with both items assigned to clusterB
                        eAnA = ((sgamma[clusA, 0] - centA0)**2 + \
                                (sgamma[clusA, 1] - centA1)**2 + \
                                (sgamma[clusA, 2] - centA2)**2)/(srho[clusA] - areaface_a)

                        eBwA = ((sgamma[clusB, 0] + centA0)**2 + \
                                (sgamma[clusB, 1] + centA1)**2 + \
                                (sgamma[clusB, 2] + centA2)**2)/(srho[clusB] + areaface_a)

                        eB = eAnA + eBwA

                        # select the largest case (most negative)
                        if eA > eorig and eA > eB:
                            mod2[clusA] = 1
                            mod2[clusB] = 1

                            nchange += 1
                            # reassign
                            clusters[face_b] = clusA
                            cluscount[clusB] -= 1
                            cluscount[clusA] += 1

                            # Update cluster A mass and centroid
                            srho[clusA] += areaface_b
                            sgamma[clusA, 0] += centB0
                            sgamma[clusA, 1] += centB1
                            sgamma[clusA, 2] += centB2

                            srho[clusB] -= areaface_b
                            sgamma[clusB, 0] -= centB0
                            sgamma[clusB, 1] -= centB1
                            sgamma[clusB, 2] -= centB2

                            # Update cluster energy
                            energy[clusA] = eAwB
                            energy[clusB] = eBnB

                        # if the energy contribution of both to B is less than the original and to cluster A
                        elif eB > eorig and eB > eA:

                            # Show clusters as modifies
                            mod2[clusA] = 1
                            mod2[clusB] = 1
                            nchange += 1

                            # reassign
                            clusters[face_a] = clusB
                            cluscount[clusA] -= 1
                            cluscount[clusB] += 1

                            # Add item A to cluster A
                            srho[clusB] += areaface_a
                            sgamma[clusB, 0] += centA0
                            sgamma[clusB, 1] += centA1
                            sgamma[clusB, 2] += centA2

                            # Remove item A from cluster A
                            srho[clusA] -= areaface_a
                            sgamma[clusA, 0] -= centA0
                            sgamma[clusA, 1] -= centA1
                            sgamma[clusA, 2] -= centA2

                            # Update cluster energy
                            energy[clusA] = eAnA
                            energy[clusB] = eBwA

                    elif cluscount[clusA] > 1:

                        areaface_a = area[face_a]
                        centA0 = cent[face_a, 0]
                        centA1 = cent[face_a, 1]
                        centA2 = cent[face_a, 2]

                        # Current energy
                        eorig =  energy[clusA] + energy[clusB]

                        # Energy with both items assigned to clusterB
                        eAnA = ((sgamma[clusA, 0] - centA0)**2 + \
                                (sgamma[clusA, 1] - centA1)**2 + \
                                (sgamma[clusA, 2] - centA2)**2)/(srho[clusA] - areaface_a)

                        eBwA = ((sgamma[clusB, 0] + centA0)**2 + \
                                (sgamma[clusB, 1] + centA1)**2 + \
                                (sgamma[clusB, 2] + centA2)**2)/(srho[clusB] + areaface_a)

                        eB = eAnA + eBwA

                        # Compare energy contributions
                        if eB > eorig:

                            # Flag clusters as modified
                            mod2[clusA] = 1
                            mod2[clusB] = 1
                            nchange += 1

                            # reassign
                            clusters[face_a] = clusB
                            cluscount[clusA] -= 1
                            cluscount[clusB] += 1

                            # Add item A to cluster A
                            srho[clusB] += areaface_a
                            sgamma[clusB, 0] += centA0
                            sgamma[clusB, 1] += centA1
                            sgamma[clusB, 2] += centA2

                            # Remove item A from cluster A
                            srho[clusA] -= areaface_a
                            sgamma[clusA, 0] -= centA0
                            sgamma[clusA, 1] -= centA1
                            sgamma[clusA, 2] -= centA2

                            # Update cluster energy
                            energy[clusA] = eAnA
                            energy[clusB] = eBwA


                    elif cluscount[clusB] > 1:

                        areaface_b = area[face_b]
                        centB0 = cent[face_b, 0]
                        centB1 = cent[face_b, 1]
                        centB2 = cent[face_b, 2]

                        # Current energy
                        eorig =  energy[clusA] + energy[clusB]

                        # Energy with both items assigned to cluster A
                        eAwB = ((sgamma[clusA, 0] + centB0)**2 + \
                                (sgamma[clusA, 1] + centB1)**2 + \
                                (sgamma[clusA, 2] + centB2)**2)/(srho[clusA] + areaface_b)

                        eBnB = ((sgamma[clusB, 0] - centB0)**2 + \
                                (sgamma[clusB, 1] - centB1)**2 + \
                                (sgamma[clusB, 2] - centB2)**2)/(srho[clusB] - areaface_b)

                        eA = eAwB + eBnB

                        # If moving face B reduces cluster energy
                        if eA > eorig:

                            mod2[clusA] = 1
                            mod2[clusB] = 1

                            nchange+=1
                            # reassign
                            clusters[face_b] = clusA
                            cluscount[clusB] -= 1
                            cluscount[clusA] += 1

                            # Update cluster A mass and centroid
                            srho[clusA] += areaface_b
                            sgamma[clusA, 0] += centB0
                            sgamma[clusA, 1] += centB1
                            sgamma[clusA, 2] += centB2

                            srho[clusB] -= areaface_b
                            sgamma[clusB, 0] -= centB0
                            sgamma[clusB, 1] -= centB1
                            sgamma[clusB, 2] -= centB2

                            # Update cluster energy
                            energy[clusA] = eAwB
                            energy[clusB] = eBnB

            niter += 1


    def _clustering_null_disconnected(self, nclus, nneigh, neigh, clusters):
        """ Removes isolated clusters """
        npoints = nneigh.shape[0]
        ccheck = np.zeros(nclus, ctypes.c_uint8)
        visited = np.zeros(npoints, ctypes.c_uint8)
        visited_cluster = np.zeros(nclus, ctypes.c_uint8)
        front = np.empty((2, npoints), np.int32)
        nclus_checked = 0
        lst_check = 0
        #cdef int ind, index, ifound, cur_clus, c, i_front_old, i_front_new, j
        #cdef int c_prev
        i = 0

        while nclus_checked < nclus:

            # seedpoint is first point available that has not been checked
            for i in range(lst_check, npoints):
                # if point and cluster have not been visited
                if not visited[i] and not visited_cluster[clusters[i]]:
                    ifound = i
                    lst_check = i
                    nclus_checked += 1
                    break

            # restart if reached the end of points
            if i == npoints - 1:
                break

            # store cluster data and check that this has been visited
            cur_clus = clusters[ifound]
            visited[ifound] = 1
            visited_cluster[cur_clus] = 1

            # perform front expansion
            i_front_new = 0
            front[i_front_new, 0] = ifound
            c = 1 # dummy init to start while loop
            while c > 0:

                # reset front
                c_prev = c
                c = 0
                # switch indices
                if i_front_new == 0:
                    i_front_old = 0
                    i_front_new = 1
                else:
                    i_front_old = 1
                    i_front_new = 0

                for j in range(c_prev):
                    ind = front[i_front_old, j]
                    for i in range(nneigh[ind]):
                        index = neigh[ind, i]
                        if clusters[index] == cur_clus and not visited[index]:
                            front[i_front_new, c] = index
                            c += 1
                            visited[index] = 1


        # Finally, null any points that have not been visited
        ndisc = 0
        for i in range(npoints):
            if not visited[i]:
                clusters[i] = -1
                ndisc += 1

        return ndisc

    def _clustering_renumber_clusters(self, clusters, npoints, nclus):
        """ renumbers clusters ensuring consecutive indexing """
        assigned = np.zeros(nclus, ctypes.c_uint8)
        ref_arr = np.empty(nclus, ctypes.c_int)
        #cdef int cnum
        c = 0
        for i in range(npoints):
            cnum = clusters[i]
            if assigned[cnum] == 0:
                assigned[cnum] = 1
                ref_arr[cnum] = c
                c += 1
            clusters[i] = ref_arr[cnum]

        return c


    def _clustering_cluster(self, neighbors, nneigh,
                nclus, area, cent, edges, maxiter,
                debug=False, iso_try=10):
        """ Python interface function for cluster optimization """
        #cdef int i

        # Initialize clusters
        npoints = nneigh.shape[0]
        clusters = np.empty(npoints, ctypes.c_int)
        clusters [:] = -1

        items = np.empty((2, npoints), ctypes.c_int)
        self._clustering_init_clusters(clusters, neighbors, nneigh, area, nclus, items)

        # Eliminat null clusters by growing existing null clusters
        self._clustering_grow_null(edges, clusters)

        # Assign any remaining clusters to 0 (just in case null clusters fails)
        for i in range(npoints):
            if clusters[i] == -1:
                clusters[i] = 0

        # Arrays for cluster centers, masses, and energies
        sgamma = np.zeros((nclus, 3))
        srho = np.zeros(nclus)
        energy = np.empty(nclus)

        # Compute initial masses of clusters
        for i in range(npoints):
            srho[clusters[i]] += area[i]
            sgamma[clusters[i], 0] += cent[i, 0]
            sgamma[clusters[i], 1] += cent[i, 1]
            sgamma[clusters[i], 2] += cent[i, 2]

        for i in range(nclus):
            energy[i] = (sgamma[i, 0]**2 + \
                        sgamma[i, 1]**2 + \
                        sgamma[i, 2]**2)/srho[i]

        # Count number of clusters
        cluscount = np.bincount(clusters).astype(ctypes.c_int)

        # Initialize modified array
        mod1 = np.empty(nclus, ctypes.c_uint8)
        mod2 = np.empty(nclus, ctypes.c_uint8)

        # Optimize clusters
        self._clustering_minimize_energy(edges, clusters, area, sgamma, cent, srho, cluscount,
                        maxiter, energy, mod1, mod2)
        # Identify isolated clusters here
        ndisc = self._clustering_null_disconnected(nclus, nneigh, neighbors, clusters)
        niter = 0
        while ndisc and niter < iso_try:
            self._clustering_grow_null(edges, clusters)
            # Re optimize clusters
            self._clustering_minimize_energy(edges, clusters, area, sgamma, cent, srho, cluscount,
                        maxiter, energy, mod1, mod2)
            # Check again for disconnected clusters
            for i in range(npoints):
                if clusters[i] == -1:
                    clusters[i] = 0
            ndisc = self._clustering_null_disconnected(nclus, nneigh, neighbors, clusters)
            niter += 1

            if ndisc:
                self._clustering_grow_null(edges, clusters)

                # Check again for disconnected clusters
                for i in range(npoints):
                    if clusters[i] == -1:
                        clusters[i] = 0

        # renumber clusters 0 to n
        nclus = self._clustering_renumber_clusters(clusters, npoints, nclus)
        return np.asarray(clusters), ndisc > 0, nclus

    def cluster(self, nclus, maxiter=100, debug=False, iso_try=10):
        """Cluster points"""
        self.clusters, _, self.nclus = self._clustering_cluster(
            self._neigh,
            self._nneigh,
            nclus,
            self._area,
            self._wcent,
            self._edges,
            maxiter,
            debug,
            iso_try,
        )

        return self.clusters

    def subdivide(self, nsub):
        """Perform a linear subdivision of the mesh.

        Parameters
        ----------
        nsub : int
            Number of subdivisions
        """
        self.mesh.copy_from(_subdivide(self.mesh, nsub))
        self._update_data()

    def plot(self, random_color=True, **kwargs):
        """Plot clusters if available.

        Parameters
        ----------
        random_color : bool, optional
            Plots clusters with a random color rather than a color
            based on the order of creation.

        **kwargs : keyword arguments, optional
            See help(pyvista.plot)

        Returns
        -------
        cpos : list
            Camera position.  See help(pyvista.plot)
        """
        if not hasattr(self, "clusters"):
            return self.mesh.plot(**kwargs)

        # Setup color
        if random_color:
            rand_color = np.random.random(self.nclus)
        else:
            rand_color = np.linspace(0, 1, self.nclus)
        colors = rand_color[self.clusters]

        # Set color range depending if null clusters exist
        if np.any(colors == -1):
            colors[colors == -1] = -0.25
            rng = [-0.25, 1]
        else:
            rng = [0, 1]

        return self.mesh.plot(scalars=colors, rng=rng, **kwargs)

    def create_mesh(self, flipnorm=True):
        """Generates mesh from clusters"""
        if flipnorm:
            cnorm = self.cluster_norm
        else:
            cnorm = None

        # Generate mesh
        self.remesh = create_mesh(self.mesh, self._area, self.clusters, cnorm, flipnorm)
        return self.remesh

    @property
    def cluster_norm(self):
        """Return cluster norms"""
        if not hasattr(self, "clusters"):
            raise Exception("No clusters available")

        # Normals of original mesh
        self.mesh.compute_normals(cell_normals=False, inplace=True)
        norm = self.mesh.point_data["Normals"]

        # Compute normalized mean cluster normals
        cnorm = np.empty((self.nclus, 3))
        cnorm[:, 0] = np.bincount(self.clusters, weights=norm[:, 0] * self._area)
        cnorm[:, 1] = np.bincount(self.clusters, weights=norm[:, 1] * self._area)
        cnorm[:, 2] = np.bincount(self.clusters, weights=norm[:, 2] * self._area)
        weights = ((cnorm * cnorm).sum(1) ** 0.5).reshape((-1, 1))
        weights[weights == 0] = 1
        cnorm /= weights
        return cnorm

    @property
    def cluster_centroid(self):
        """Computes an area normalized value for each cluster"""
        wval = self.mesh.points * self._area.reshape(-1, 1)
        cval = np.vstack(
            (
                np.bincount(self.clusters, weights=wval[:, 0]),
                np.bincount(self.clusters, weights=wval[:, 1]),
                np.bincount(self.clusters, weights=wval[:, 2]),
            )
        )
        weights = np.bincount(self.clusters, weights=self._area)
        weights[weights == 0] = 1
        cval /= weights
        return cval.T