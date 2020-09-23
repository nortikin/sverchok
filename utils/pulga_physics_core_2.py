# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from mathutils.bvhtree import BVHTree
from sverchok.utils.modules.vector_math_utils import angle_between, unit_vector, np_dot
def cross_indices3(n):
    '''create crossed indices'''

    nu = np.sum(np.arange(n, dtype=np.int64))
    ind = np.zeros((nu, 2), dtype=np.int16)
    c = 0
    for i in range(n-1):
        l = n-i-1
        np_i = np.full(n-i-1, i, dtype=np.int32)
        np_j = np.arange(i+1, n, dtype=np.int32)
        np_a = np.stack((np_i, np_j), axis=-1)
        ind[c:c+l, :] = np_a
        c += l

    return ind


def numpy_match_long_repeat(p):
    '''match list length by repeating last one'''
    q = []
    maxl = 0
    for g in p:
        maxl = max(maxl, g.shape[0])
    for g in p:
        difl = maxl - g.shape[0]
        if difl > 0:
            rr = np.repeat(g[np.newaxis, -1], difl, axis=0)
            g = np.concatenate((g, rr))
        q.append(g)
    return q


def numpy_fit_long_repeat(p, maxl):
    '''match list length by repeating last one or removing end'''
    q = []
    for g in p:
        difl = maxl - g.shape[0]
        if difl > 0:
            rr = np.repeat(g[np.newaxis, -1], difl, axis=0)
            g = np.concatenate((g, rr))
        if difl < 0:
            g = g[:maxl]
        q.append(g)
    return q


def match_cylce(p, n):
    '''append cylcing till have n items'''
    difference = n - len(p)
    for i in range(difference):
        p.append(p[i % len(p)])


def expand_pols_numpy(p, len_max):
    '''to fit variable sided polygons in one array (cycling)'''
    np_match_cycle = np.vectorize(match_cylce)
    np_match_cycle(p, len_max)
    new_pols = np.zeros((len(p), len_max), dtype=np.int32)
    for i in range(len(p)):
        new_pols[i, :] = p[i]
    return new_pols


def calc_rest_length(np_verts, np_springs):
    '''calculate edges length'''
    pairs_springs = np_verts[np_springs, :]
    vect_rest = (pairs_springs[:, 0, :] - pairs_springs[:, 1, :])
    dist_rest = np.linalg.norm(vect_rest, axis=1)
    return dist_rest


def pols_normals(pol_v, mag):
    '''get actual polygons normal with controlled magnitude'''
    v1 = pol_v[:, 1, :] - pol_v[:, 0, :]
    v2 = pol_v[:, 2, :] - pol_v[:, 0, :]
    pols_normal = np.cross(v1, v2)
    pols_normal_d = np.linalg.norm(pols_normal, axis=1)
    return pols_normal / pols_normal_d[:, np.newaxis] * mag


def calc_area(pol_side_max, pol_v, pols_normal):
    '''calculate polygons area (equal sided polygons)'''
    prod = np.zeros((pol_side_max, len(pols_normal), 3), dtype=np.float32)
    for i in range(pol_side_max):
        prod[i, :, :] = np.cross(pol_v[:, i, :], pol_v[:, (i + 1) % pol_side_max, :])
    tot = np.sum(prod, axis=0)
    return abs(np.sum(tot * pols_normal, axis=1) / 2)


def calc_area_var_sides(pol_side_max, pols_sides, pol_v, pols_normal):
    '''calculate polygons area (variable sided polygons)'''
    prod = np.zeros((pol_side_max, len(pols_sides), 3), dtype=np.float32)
    for i in range(pol_side_max):
        mask = pols_sides > i
        prod[i, mask, :] = np.cross(pol_v[mask, i, :], pol_v[mask, (i + 1) % pol_side_max, :])

    tot = np.sum(prod, axis=0)
    return abs(np.sum(tot * pols_normal, axis=1) / 2)

def baricentric_mask(p_triang, edges, np_pol_v, coll_normals, ed_id, rad_axis):
    '''helper function to mask which points are inside the triangles'''
    edge = edges[:, ed_id, :]
    v0 = np_pol_v[:, ed_id, :]
    vp0 = p_triang - v0[:, np.newaxis, :]
    cross = np.cross(edge[:, np.newaxis, :], vp0)
    return np.sum(coll_normals * cross, axis=2) > -rad_axis

def collide_normals_get(collide_v1, collide_v2):
    '''get normalized normals'''
    collide_normals = np.cross(collide_v1, collide_v2)
    collide_normals_d = np.linalg.norm(collide_normals, axis=1)
    return collide_normals / collide_normals_d[:, np.newaxis]


def b_box_coll_filter(np_pol_v, verts, rad):
    '''filter intersections by checking bounding box overlap'''
    verts_x = verts[np.newaxis, :, :]
    rads_x = rad[np.newaxis, :, np.newaxis]
    keep = np.amin(np_pol_v, axis=1)[:, np.newaxis, :] < verts_x + rads_x
    keep2 = np.amax(np_pol_v, axis=1)[:, np.newaxis, :] > verts_x - rads_x
    keep3 = np.any(keep*keep2, axis=0)
    keep = np.any(keep*keep2, axis=1)
    verts_m = np.all(keep3, axis=1)
    pols_m = np.all(keep, axis=1)

    return pols_m, verts_m

def collision_dist(verts, collide_p_co, coll_norm):
    '''get collision distance and normal'''
    vector_coll = verts[np.newaxis, :, :] - collide_p_co[:, np.newaxis, :]
    coll_dist = np.sum(vector_coll * coll_norm, axis=2)
    return coll_dist


def pts_in_tris(p_triang, edges, pol_v, coll_normals, rad_axis, coll_mask):
    '''calculate if points are inside the triangles'''
    w = baricentric_mask(p_triang, edges, pol_v, coll_normals, 0, rad_axis)
    u = baricentric_mask(p_triang, edges, pol_v, coll_normals, 1, rad_axis)
    v = baricentric_mask(p_triang, edges, pol_v, coll_normals, 2, rad_axis)
    return w * u * v * coll_mask


def coll_displace(coll_normals, coll_inter, coll_sign, wuv, num_int):
    '''calculate resultant collision displacement'''
    rr = wuv[:, :, np.newaxis] * coll_normals * coll_inter[:, :, np.newaxis]*-coll_sign[:, :, np.newaxis]
    return np.sum(rr, axis=0) / num_int


def coll_vel(coll_normals, vels, wuv, num_int):
    '''calculate resultant collision speed'''
    new_vel_mag = np.sum(coll_normals * vels[np.newaxis, :, :], axis=-1)
    new_vel = new_vel_mag[:, :, np.newaxis] * coll_normals * wuv[:, :, np.newaxis]
    return np.sum(new_vel, axis=0)*-2 / num_int


class SvAttractorsForce():
    def __init__(self, attractors, att_force, att_clamp, att_decay_power):

        # attractors, att_force, att_clamp, att_decay_power = local_params
        np_attrac = np.array(attractors)
        np_attrac_f = np.array(att_force)
        np_attrac_clamp = np.array(att_clamp)
        np_attrac_decay_pow = np.array(att_decay_power)
        params = numpy_match_long_repeat([np_attrac, np_attrac_f, np_attrac_clamp, np_attrac_decay_pow])
        self.points = params[0]
        self.magnitude = params[1]
        self.clamp = params[2]
        self.decay = params[3]



    def setup(self, ps):
        pass


    def add(self, ps):
        v_attract = ps.verts[np.newaxis, :, :] - self.points[:, np.newaxis, :]
        dist_attract = np.linalg.norm(v_attract, axis=2)
        mask = dist_attract > self.clamp[:, np.newaxis]
        mask_true = np.invert(mask)
        dist_attract2 = np.power(dist_attract, self.decay[:, np.newaxis])
        dist_attract_cor = np.clip(dist_attract2[mask_true], 1e-2, 1e4)

        v_attract *= self.magnitude[:, np.newaxis, np.newaxis]
        v_attract_normal = v_attract[mask_true] / dist_attract_cor[:, np.newaxis]

        v_attract[mask_true] = -v_attract_normal
        v_attract[mask, :] = 0

        r_attract = np.sum(v_attract, axis=0)
        ps.r += r_attract

class SvBoundingBoxForce():
    def __init__(self, b_box):

        np_bbox = np.array(b_box)
        bbox_max = np.amax(np_bbox, axis=0)
        bbox_min = np.amin(np_bbox, axis=0)
        self.bbox_min = bbox_min
        self.bbox_max = bbox_max
        print(bbox_min, bbox_max)


    def setup(self, ps):
        pass


    def add(self, ps):
        min_mask = ps.verts <= self.bbox_min + ps.rads[:, np.newaxis]
        max_mask = ps.verts >= self.bbox_max - ps.rads[:, np.newaxis]
        out_vals=np.any([min_mask, max_mask], axis=0)

        ps.vel[out_vals] = 0
        ps.r[out_vals] = 0

        ps.verts = np.clip(ps.verts, self.bbox_min + ps.rads[:, np.newaxis], self.bbox_max - ps.rads[:, np.newaxis])

def project_on_plane(vects, normal):
    distance = np.sum(vects * normal, axis=1)
    return vects - normal * distance[:,np.newaxis]

class SvBoundingSphereForce():
    def __init__(self, center, radius):


        self.center = center[0]
        self.radius = radius[0]



    def setup(self, ps):
        pass


    def add(self, ps):
        vs = ps.verts - self.center
        dist = np.linalg.norm(vs, axis=1)
        mask = dist + ps.rads > self.radius
        vs_normal = vs[mask]/dist[mask, np.newaxis]
        ps.verts[mask] = vs_normal*(self.radius - ps.rads[mask])[:,np.newaxis]

        ps.vel[mask] = project_on_plane(ps.vel[mask], vs_normal)
        ps.r[mask] = project_on_plane(ps.r[mask], vs_normal)

class SvBoundingSphereSurfaceForce():
    def __init__(self, center, radius):


        self.center = center[0]
        self.radius = radius[0]



    def setup(self, ps):
        pass


    def add(self, ps):
        vs = ps.verts - self.center
        dist = np.linalg.norm(vs, axis=1)
        mask = dist == 0
        vs[mask]=ps.verts[mask]+[[1,0,0]]
        dist[mask] =1
        vs_normal = vs/dist[:, np.newaxis]
        ps.verts = vs_normal * self.radius

        ps.vel = project_on_plane(ps.vel, vs_normal)
        ps.r = project_on_plane(ps.r, vs_normal)

class SvBoundingPlaneSurfaceForce():
    def __init__(self, center, normal):


        self.center = np.array(center[0])
        self.normal = np.array(normal[0])
        self.normal = self.normal/np.linalg.norm(self.normal)


    def setup(self, ps):
        pass


    def add(self, ps):

        vs = ps.verts - self.center
        distance = np.sum(vs * self.normal, axis=1)
        print(distance)
        ps.verts = ps.verts - self.normal[np.newaxis, :] * distance[:, np.newaxis]

        ps.vel = project_on_plane(ps.vel, self.normal)
        ps.r = project_on_plane(ps.r, self.normal)


class SvBoundingMeshSurfaceForce():
    def __init__(self, vertices, polygons, volume=False):


        self.bvh = BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0)

        if volume:
            self.add = self.add_volume
        else:
            self.add = self.add_surface

    def setup(self, ps):
        self.nearest = np.zeros(ps.verts.shape, dtype=np.float64)
        self.normals = np.zeros(ps.verts.shape, dtype=np.float64)

    def find2(self, verts):
        v_nearest = self.nearest
        v_normals = self.normals
        for v, near, norm in zip(verts, v_nearest, v_normals):
            nearest, normal, _, _ = self.bvh.find_nearest(v)

            near[0] = nearest[0]
            near[1] = nearest[1]
            near[2] = nearest[2]
            norm[0] = normal[0]
            norm[1] = normal[1]
            norm[2] = normal[2]

    def add_surface(self, ps):

        self.find2(ps.verts)
        ps.verts = self.nearest
        ps.vel = project_on_plane(ps.vel, self.normals)
        ps.r = project_on_plane(ps.r, self.normals)

    def add_volume(self, ps):
        self.find2(ps.verts)
        p2 = self.nearest - ps.verts
        outer_mask = np_dot(p2, self.normals) <= 0
        ps.verts[outer_mask] = self.nearest[outer_mask]

        ps.vel[outer_mask] = project_on_plane(ps.vel[outer_mask], self.normals[outer_mask])
        ps.r[outer_mask] = project_on_plane(ps.r[outer_mask], self.normals[outer_mask])
import Part
from  FreeCAD import Base
from sverchok.utils.surface.freecad import is_solid_face_surface
class SvBoundingSolidSurfaceForce():
    def __init__(self, solid, volume=False):

        if isinstance(solid, Part.Solid):
            self.shape = solid.OuterShell
        elif is_solid_face_surface(solid):
            self.shape= solid.face
        else:

            self.shape = solid

        if volume:
            self.add = self.add_volume
        else:
            self.add = self.add_surface
        def outside(v):
            return np.array(not self.shape.isInside(Base.Vector(v), 1e-6, False))
        self.outside = np.vectorize(outside, signature='(3)->()')
        def find(v):
            vertex = Part.Vertex(Base.Vector(v))

            dist = self.shape.distToShape(vertex)
            if str(dist[2][0][0]) == "b'Face'":
                normal = self.shape.Faces[dist[2][0][1]].normalAt(*dist[2][0][2])
            elif str(dist[2][0][0]) == "b'Edge'":
                edge = self.shape.Edges[dist[2][0][1]]
                vector = self.shape.Edges[dist[2][0][1]].valueAt(dist[2][0][2])
                face_list = self.shape.ancestorsOfType(edge,Part.Face)
                normal=[0,0,0]
                count=0
                for face in face_list:
                    for edge1 in face.Edges:

                        if edge1.isSame(edge):
                            param = face.Surface.parameter(vector)
                            normal_ed = face.normalAt(*param)
                            normal[0] += normal_ed[0]
                            normal[1] += normal_ed[1]
                            normal[2] += normal_ed[2]
                            count+=1
                            break
                if count > 0:
                    normal[0] /= count
                    normal[1] /= count
                    normal[2] /= count
                else:
                    normal = [0, 0, 1]
            else:
                vertex = self.shape.Vertexes[dist[2][0][1]]
                face_list = self.shape.ancestorsOfType(vertex, Part.Face)
                normal = [0, 0, 0]
                count = 0
                for face in face_list:
                    for vertex1 in face.Vertexes:

                        if vertex1.isSame(vertex):
                            param = face.Surface.parameter(vertex.Point)
                            normal_ed = face.normalAt(*param)
                            normal[0] += normal_ed[0]
                            normal[1] += normal_ed[1]
                            normal[2] += normal_ed[2]
                            count+=1
                            break
                if count > 0:
                    normal[0] /= count
                    normal[1] /= count
                    normal[2] /= count
                else:
                    normal = [0, 0, 1]
            return np.array([dist[1][0][0][:], normal[:]])


        self.find = np.vectorize(find, signature='(3)->(2,3)')
    def find_closest(self,v):
        vertex = Part.Vertex(Base.Vector(v))

        dist = self.shape.distToShape(vertex)
        if str(dist[2][0][0]) == "b'Face'":
            normal = self.shape.Faces[dist[2][0][1]].normalAt(*dist[2][0][2])
        elif str(dist[2][0][0]) == "b'Edge'":
            edge = self.shape.Edges[dist[2][0][1]]
            vector = self.shape.Edges[dist[2][0][1]].valueAt(dist[2][0][2])
            face_list = self.shape.ancestorsOfType(edge, Part.Face)
            normal = [0,0,0]
            count = 0
            for face in face_list:
                for edge1 in face.Edges:

                    if edge1.isSame(edge):
                        param = face.Surface.parameter(vector)
                        normal_ed = face.normalAt(*param)
                        normal[0] += normal_ed[0]
                        normal[1] += normal_ed[1]
                        normal[2] += normal_ed[2]
                        count+=1
                        break
            if count > 0:
                normal[0] /= count
                normal[1] /= count
                normal[2] /= count
            else:
                normal = [0, 0, 1]
        else:
            vertex = self.shape.Vertexes[dist[2][0][1]]
            face_list = self.shape.ancestorsOfType(vertex, Part.Face)
            normal = [0, 0, 0]
            count = 0
            for face in face_list:
                for vertex1 in face.Vertexes:

                    if vertex1.isSame(vertex):
                        param = face.Surface.parameter(vertex.Point)
                        normal_ed = face.normalAt(*param)
                        normal[0] += normal_ed[0]
                        normal[1] += normal_ed[1]
                        normal[2] += normal_ed[2]
                        count+=1
                        break
            if count > 0:
                normal[0] /= count
                normal[1] /= count
                normal[2] /= count
            else:
                normal = [0, 0, 1]
        return dist[1][0][0], normal
    def find2(self, verts):
        v_nearest = self.nearest
        v_normals = self.normals
        for v, near, norm in zip(verts, v_nearest, v_normals):
            nearest, normal = self.find_closest(v)
            near[0] = nearest[0]
            near[1] = nearest[1]
            near[2] = nearest[2]
            norm[0] = normal[0]
            norm[1] = normal[1]
            norm[2] = normal[2]
    def find_masked(self, verts, mask):
        v_nearest = self.nearest
        v_normals = self.normals
        for v, near, norm in zip(verts[mask], v_nearest[mask], v_normals[mask]):
            nearest, normal = self.find_closest(v)
            near[0] = nearest[0]
            near[1] = nearest[1]
            near[2] = nearest[2]
            norm[0] = normal[0]
            norm[1] = normal[1]
            norm[2] = normal[2]

    def is_outside(self, verts):

        return np.array([not self.shape.isInside(Base.Vector(v), 1e-6, False) for v in verts], dtype=np.bool_)
    def setup(self, ps):
        self.nearest = np.zeros(ps.verts.shape, dtype=np.float64)
        self.normals = np.zeros(ps.verts.shape, dtype=np.float64)


    def add_surface(self, ps):
        # find = self.find(ps.verts)
        # ps.verts = find[:,0,:]
        # ps.vel = project_on_plane(ps.vel, find[:,1,:])
        # ps.r = project_on_plane(ps.r, find[:,1,:])
        self.find2(ps.verts)
        ps.verts = self.nearest
        ps.vel = project_on_plane(ps.vel, self.normals)
        ps.r = project_on_plane(ps.r, self.normals)

    def add_volume(self, ps):
        outside = self.is_outside(ps.verts)
        find_masked(self, verts, outside)
        ps.verts[outside] =  self.nearest[outside]
        ps.vel[outside] = project_on_plane(ps.vel[outside], self.normals[outside])
        ps.r[outside] = project_on_plane(ps.r[outside], self.normals[outside])


class SvRandomForce():
    def __init__(self, random_force, random_variation, random_seed):

        # random_seed, random_force, random_variation = local_params
        np_random_force = np.array(random_force)

        np_random_variation = np.array(random_variation)
        random_force = np_random_force[:, np.newaxis]
        random_variation = np_random_variation[:, np.newaxis]
        random_variate = any(random_variation > 1e-6)
        self.seed = random_seed[0]
        self.random_force = random_force
        self.random_variate = random_variate
        self.random_variation = random_variation

    def setup(self, ps):
        np.random.seed(int(self.seed))
        self.random_v = self.random_force * np.random.random((ps.v_len, 3)) - self.random_force / 2


    def add(self, ps):

        if self.random_variate:
            random_var = 2 * self.random_force * np.random.random((ps.v_len, 3)) - self.random_force
            self.random_v = self.random_v * (1 - self.random_variation) + random_var * self.random_variation
        ps.r += self.random_v

class SvCollisionForce():
    def __init__(self, magnitude, use_kdtree=False):

        self.magnitude = np.array(magnitude)
        self.uniform_magnitude = len(magnitude) < 2
        self.needs = ['dif_v', 'dist', 'dist_cor', 'collide', 'normal_v']
        self.use_kdtree = use_kdtree
        if self.use_kdtree:
            self.needs = ['kd_tree', 'max_radius']
            self.add = self.add_kdt
        else:
            self.needs = ['indexes', 'sum_rad', 'dif_v', 'dist', 'dist_cor', 'collide', 'normal_v']
            self.add = self.add_brute_force


    def setup(self, ps):
        ps.aware = True
        for need in self.needs:
            ps.relations.needed[need] = True
        if self.uniform_magnitude:
            self.f_magnitude = self.magnitude
        else:
            self.f_magnitude = numpy_fit_long_repeat([self.magnitude], ps.v_len)

    def add_brute_force(self, ps):
        ps.relations.result[:] = 0
        id0 = ps.relations.index_inter[:, 0]
        id1 = ps.relations.index_inter[:, 1]

        le = ps.relations.dist[ps.relations.mask, np.newaxis] - ps.relations.sum_rad[ps.relations.mask, np.newaxis]
        no = ps.relations.normal_v[ps.relations.mask]
        sf = self.f_magnitude[:, np.newaxis]
        len0, len1 = [sf, sf] if self.uniform_magnitude else [sf[id1], sf[id0]]

        np.add.at(ps.r, id0, -no * le * len0)
        np.add.at(ps.r, id1, no * le * len1)

    def add_kdt(self, ps):
        indexes = ps.relations.kd_tree.query_pairs(r=ps.relations.max_radius*2, output_type='ndarray')

        if len(indexes) > 0:

            id0 = indexes[:, 0]
            id1 = indexes[:, 1]
            dif_v = ps.verts[indexes[:, 0], :] - ps.verts[indexes[:, 1], :]

            sum_rad = ps.rads[indexes[:, 0]] + ps.rads[indexes[:, 1]]

            dist = np.linalg.norm(dif_v, axis=1)
            dist_cor = np.clip(dist, 1e-6, 1e4)

            normal_v = dif_v / dist_cor[:, np.newaxis]



            le = (dist - sum_rad)[:, np.newaxis]

            variable_coll = len(self.f_magnitude) > 1
            sf = self.f_magnitude[:, np.newaxis]
            len0, len1 = [sf[id1], sf[id0]] if variable_coll else [sf, sf]


            np.add.at(ps.r, id0, -normal_v * le * len0)
            np.add.at(ps.r, id1, normal_v * le * len1)


class SvAttractionForce():
    def __init__(self, magnitude, decay, max_distance, use_kdtree=False):

        self.magnitude = np.array(magnitude)
        self.uniform_magnitude = len(magnitude) < 2
        print(self.magnitude, self.uniform_magnitude)
        self.decay = np.array(decay)
        self.use_kdtree = use_kdtree
        self.max_distance = max_distance[0]
        if self.use_kdtree:
            self.needs = ['kd_tree']
            self.add = self.add_kdt
        else:
            self.needs = ['indexes', 'sum_rad', 'mass_product', 'dif_v', 'dist', 'dist_cor', 'attract', 'normal_v']
            self.add = self.add_brute_force

    def setup(self, ps):
        ps.aware = True
        for need in self.needs:
            ps.relations.needed[need] = True
        if self.uniform_magnitude:
            self.f_magnitude = self.magnitude
        else:
            self.f_magnitude = numpy_fit_long_repeat([self.magnitude], ps.v_len)

    def add_brute_force(self, ps):
        rel = ps.relations
        mask = np.all(( rel.dist < self.max_distance, ps.relations.attract_mask), axis=0)
        index_non_inter = ps.relations.indexes[mask]
        id0 = index_non_inter[:, 0]
        id1 = index_non_inter[:, 1]
        dist2 = np.power(rel.dist[mask], self.decay)[:, np.newaxis]
        no = ps.relations.normal_v[mask]
        direction = no / dist2 * rel.mass_product[mask, np.newaxis]

        att = self.f_magnitude
        len0, len1 = [att, att] if self.uniform_magnitude else [att[id1], att[id0]]

        np.add.at(ps.r, id0, -direction * len0)
        np.add.at(ps.r, id1, direction * len1)

    def add_kdt(self, ps):
        rel = ps.relations
        indexes = ps.relations.kd_tree.query_pairs(r=self.max_distance, output_type='ndarray')
        if len(indexes)>0:

            dif_v = ps.verts[indexes[:, 0], :] - ps.verts[indexes[:, 1], :]
            mass_product = ps.mass[indexes[:, 0]] * ps.mass[indexes[:, 1]]

            dist = np.linalg.norm(dif_v, axis=1)
            dist_cor = np.clip(dist, 1e-6, 1e4)
            id0 = indexes[:, 0]
            id1 = indexes[:, 1]
            dist2 = np.power(dist, self.decay)[:, np.newaxis]
            dist_cor = np.clip(dist, 1e-6, 1e4)
            normal_v = dif_v / dist_cor[:, np.newaxis]

            direction = normal_v / dist2 * mass_product[:, np.newaxis]

            att = self.f_magnitude
            len0, len1 = [att, att] if self.uniform_magnitude else [att[id1], att[id0]]
            np.add.at(ps.r, id0, -direction * len0)
            np.add.at(ps.r, id1, direction * len1)


class SvAlignForce():
    def __init__(self, magnitude, radius):

        self.magnitude = np.array(magnitude)
        self.uniform_magnitude = len(magnitude) < 2

        self.f_magnitude = self.magnitude
        self.radius = np.array(radius)

        self.needs = ['dif_v', 'dist', 'dist_cor']


    def setup(self, ps):

        ps.aware = True
        for need in self.needs:
            ps.relations.needed[need] = True
        if self.uniform_magnitude:
            self.f_magnitude = self.magnitude
        else:
            self.f_magnitude = numpy_fit_long_repeat([self.magnitude], ps.v_len)

    def add(self, ps):
        rel = ps.relations
        mask = ps.relations.dist_cor < self.radius
        id0 = ps.relations.indexes[mask, 0]
        id1 = ps.relations.indexes[mask, 1]
        ps.relations.result[:] = 0
        if self.uniform_magnitude:
            constant = (self.f_magnitude / (ps.relations.dist_cor[mask] * ps.v_len))[:, np.newaxis]

            ps.relations.result[id0, id1, :] = ps.vel[id1, :] * constant
            ps.relations.result[id1, id0, :] = ps.vel[id0, :] * constant
            ps.r += np.sum(ps.relations.result, axis=1)
        else:
            constant0 = (self.f_magnitude[id0] / (ps.relations.dist_cor[mask] * ps.v_len))[:, np.newaxis]
            constant1 = (self.f_magnitude[id1] / (ps.relations.dist_cor[mask] * ps.v_len))[:, np.newaxis]

            ps.relations.result[id0, id1, :] = ps.vel[id1, :] * constant0
            ps.relations.result[id1, id0, :] = ps.vel[id0, :] * constant1
            ps.r += np.sum(ps.relations.result, axis=1)

class SvFitForce():
    def __init__(self, magnitude, min_radius, max_radius, mode):

        self.magnitude = np.array(magnitude)
        self.uniform_magnitude = len(magnitude) < 2
        self.min_radius = np.array(min_radius)
        self.max_radius = np.array(max_radius)
        if mode == 'Absolute':
            self.absolute= True
        else:
            self.absolute= False
            if mode == 'Percent':
                self.magnitude /= 100

        self.size_changer = True
        self.needs = ['dif_v', 'dist', 'collide']

    def setup(self, ps):
        ps.aware = True
        self.all_range = np.arange(ps.v_len, dtype=np.int16)

        for need in self.needs:
            ps.relations.needed[need] = True
        if self.uniform_magnitude:
            self.f_magnitude = self.magnitude
        else:
            self.f_magnitude = numpy_fit_long_repeat([self.magnitude], ps.v_len)

    def add(self, ps):
        rel = ps.relations
        touch = np.unique(rel.index_inter)
        free = np.setdiff1d(self.all_range, touch)
        v_grow = len(self.f_magnitude) > 1
        grow_un, grow_tou = [self.f_magnitude[free], self.f_magnitude[touch]] if v_grow else [self.f_magnitude, self.f_magnitude]
        if self.absolute:
            ps.rads[free] += grow_un
            ps.rads[touch] -= grow_tou
        else:
            ps.rads[free] += grow_un * ps.rads[free]
            ps.rads[touch] -= grow_tou * ps.rads[touch]
        ps.rads = np.clip(ps.rads, self.min_radius, self.max_radius)

class SvDragForce():

    def __init__(self, drag_force, exponent):
        print()
        self.magnitude = np.array(drag_force)
        self.surf = 0
        self.exponent = exponent
        self.add_func = self.add_size_change


    def setup(self, ps):
        size_change = ps.size_change
        if len(self.magnitude)<2:
            self.ap_magnitude = self.magnitude
        else:
            self.ap_magnitude = numpy_fit_long_repeat([self.magnitude], ps.v_len)[0]
        if len(self.exponent)<2:
            self.ap_exponent = self.exponent
        else:
            self.ap_exponent = numpy_fit_long_repeat([self.exponent], ps.v_len)[0]

        self.surf = np.power(ps.rads, 2)
        if not size_change:
            self.constant = (self.ap_magnitude * self.surf)[:, np.newaxis]

            self.add_func = self.add_constant_size
        else:
            self.add_func = self.add_size_change
            self.ap_magnitude = self.magnitude[:, np.newaxis]

    def add_size_change(self, ps):
        vel_mag = np.linalg.norm(ps.vel, axis=1)
        vel_mag_zero = vel_mag == 0
        vel_mag[vel_mag_zero] = 1
        vel_mag2 = np.power(vel_mag, self.ap_exponent)
        vel_norm = ps.vel/vel_mag[:, np.newaxis]
        self.surf = np.power(ps.rads, 2)
        drag = -vel_norm * self.ap_magnitude * vel_mag2[:, np.newaxis] * self.surf[:, np.newaxis]

        ps.r += drag

    def add_constant_size(self, ps):

        vel_mag = np.linalg.norm(ps.vel, axis=1)
        vel_mag_zero = vel_mag == 0
        vel_mag[vel_mag_zero] = 1

        vel_mag2 = np.power(vel_mag, self.ap_exponent)
        vel_norm = ps.vel/vel_mag[:, np.newaxis]

        drag = -vel_norm * vel_mag2[:, np.newaxis] *  self.constant

        ps.r += drag

    def add(self, ps):
        self.add_func(ps)

class SvWorldForce():
    def __init__(self, force, strength, mass_proportional):

        self.strength, self.force = numpy_match_long_repeat([np.array(strength), np.array(force)])

        self.force *= self.strength[:, np.newaxis]
        self.func = self.apply_mass_proportional
        self.mass_proportional = mass_proportional

    def setup(self, ps):
        size_change = ps.size_change
        if len(self.force) > 1:
            self.force2 = numpy_fit_long_repeat([self.force], ps.v_len)[0]
        if size_change and self.mass_proportional:
            self.func = self.apply_mass_proportional

        elif self.mass_proportional:

            self.force2 = self.force * ps.mass[:, np.newaxis]
            self.func = self.apply_dependant
        else:

            self.force2 = self.force
            self.func = self.apply_dependant

    def apply_mass_proportional(self, ps):
        '''apply constant forces'''

        ps.r += self.force2 * ps.mass[:, np.newaxis]

    def apply_dependant(self, ps):
        '''apply constant forces'''

        ps.r += self.force2

    def add(self, ps):
        self.func(ps)

class SvFieldForce():
    def __init__(self, field, strength, mass_proportional):

        self.field = field
        self.func = self.apply_mass_proportional
        self.mass_proportional = mass_proportional
        self.strength = np.array(strength)
        if self.mass_proportional:
            self.add_func = self.apply_dependant
        else:
            self.add_func = self.apply_mass_proportional


    def setup(self, ps):
        pass


    def apply_mass_proportional(self, ps):
        '''apply constant forces'''
        if not np.any(self.strength != 0):
            return
        xs = ps.verts[:, 0]
        ys = ps.verts[:, 1]
        zs = ps.verts[:, 2]
        rx, ry, rz = self.field.evaluate_grid(xs, ys, zs)
        ps.r[:, 0] += rx * ps.mass * self.strength
        ps.r[:, 1] += ry * ps.mass * self.strength
        ps.r[:, 2] += rz * ps.mass * self.strength

    def apply_dependant(self, ps):
        '''apply constant forces'''
        if not np.any(self.strength != 0):
            return
        xs = ps.verts[:, 0]
        ys = ps.verts[:, 1]
        zs = ps.verts[:, 2]
        rx, ry, rz = self.field.evaluate_grid(xs, ys, zs)
        ps.r[:, 0] += rx * self.strength
        ps.r[:, 1] += ry * self.strength
        ps.r[:, 2] += rz * self.strength

    def add(self, ps):
        self.add_func(ps)


def pin_type_get(pin_type):
    print(pin_type, isinstance(pin_type[0], str))
    if isinstance(pin_type[0], str):
        axis = []
        for ch in pin_type[0]:
            if ch == "X":
                axis.append(0)
            elif ch == "Y":
                axis.append(1)
            else:
                axis.append(2)
        return np.array(axis)
    else:
        pin_types =[[0,1,2], [0,1], [0,2], [1,2],[0],[1],[2]]
        return np.array(pin_types[pin_type[0]])

class SvPinForce():
    def __init__(self, indices, pin_type, pins_goal_pos, use_pins_goal):

        self.pins = np.array(indices)
        self.unpinned = []
        self.use_pins_goal = use_pins_goal
        self.pins_goal_pos = np.array(pins_goal_pos)
        self.pin_force = True
        self.pin_type = pin_type_get(pin_type)

    def setup(self, ps):
        if self.pins.dtype == np.int32:
            if len(self.pins) == len(ps.verts):
                self.pins = self.pins == 1
                self.unpinned = np.invert(self.pins)
            else:
                self.unpinned = np.ones(len(ps.verts), dtype=np.bool_)
                self.unpinned[self.pins] = False
        for axis in self.pin_type:
            ps.vel[self.pins, axis] = 0

    def add(self, ps):
        if self.use_pins_goal:
            ps.verts[self.pins, :] = self.pins_goal_pos
        ps.params["Pins Reactions"] = -ps.r[self.pins]
        for axis in self.pin_type:
            ps.params["Pins Reactions"][:, axis] = 0
            ps.vel[self.pins, axis] = 0
            ps.r[self.pins, axis] = 0
        # ps.vel[self.pins, :] = 0
        ps.params['unpinned'][self.pins] = False

class SvSpringsForce():
    def __init__(self, springs, spring_k, fixed_len, clamp, use_fix_len ):
        self.springs = np.array(springs)
        self.spring_k = np.array(spring_k)
        self.use_fix_len = use_fix_len
        self.fixed_len = fixed_len
        self.dist_rest = fixed_len
        self.clamp = np.array(clamp)
        self.use_clamp = np.any(self.clamp > 0)

    def setup(self, ps):
        if self.use_fix_len or self.fixed_len[0] > 0:
            self.dist_rest = self.fixed_len
        else:
            self.dist_rest = calc_rest_length(ps.verts, self.springs)
            self.clamp_distance = self.dist_rest * self.clamp

    def add(self, ps):


        pairs = ps.verts[self.springs, :]
        dif_v = pairs[:, 0, :] - pairs[:, 1, :]
        dist = np.linalg.norm(dif_v, axis=1)
        if self.use_clamp:
            dif_l = np.clip(dist - self.dist_rest, -self.clamp_distance, self.clamp_distance)
        else:
            dif_l = dist - self.dist_rest
        dist[dist == 0] = 1
        normal_v = dif_v / dist[:, np.newaxis]
        x = dif_l[:, np.newaxis]
        k = self.spring_k[:, np.newaxis]

        np.add.at(ps.r, self.springs[:, 0], -normal_v * x * k)
        np.add.at(ps.r, self.springs[:, 1], normal_v * x * k)


class SvEdgesAngleForce():
    def __init__(self, springs, spring_k, fixed_angle, use_fix_angle):
        self.springs = np.array(springs)
        self.spring_k = np.array(spring_k)
        self.use_fix_angle = use_fix_angle
        self.fixed_angle = fixed_angle
        self.rest_ang = fixed_angle

    def setup(self, ps):
        rel=[[] for i in range(ps.v_len)]
        for (e0, e1) in self.springs:
            rel[e0].append(e1)
            rel[e1].append(e0)
        target_v = []
        rest_ang = []
        rel_idx = []

        if self.use_fix_angle or self.fixed_angle[0] > 0:
            self.rest_ang = self.fixed_angle
            for v,r, idx in zip(ps.verts, rel, range(ps.v_len)):
                if len(r) == 2:
                    target_v.append(idx)
                    rel_idx.append(r)
                elif len(r)>2:
                    for idx0, idx1 in zip(r,r[1:]+[r[0]]):
                        target_v.append(idx)
                        rel_idx.append([idx0, idx1])

            self.target_v = np.array(target_v)
            self.rest_ang = self.fixed_angle
            self.rel_idx = np.array(rel_idx)
        else:

            for v,r, idx in zip(ps.verts, rel, range(ps.v_len)):
                if len(r) == 2:
                    vec = ps.verts[r[0]] - v
                    vec2 = ps.verts[r[1]] - v
                    rest_ang.append(angle_between([vec], [vec2])[0])
                    target_v.append(idx)
                    rel_idx.append(r)
                elif len(r)>2:
                    for idx0, idx1 in zip(r,r[1:]+[r[0]]):
                        vec = ps.verts[idx0] - v
                        vec2 = ps.verts[idx1] - v
                        rest_ang.append(angle_between([vec], [vec2])[0])
                        target_v.append(idx)
                        rel_idx.append([idx0, idx1])
            self.target_v = np.array(target_v)
            self.rest_ang = np.array(rest_ang)
            self.rel_idx = np.array(rel_idx)


    def add(self, ps):


        vs = ps.verts[self.target_v, :]
        v1_u = unit_vector(ps.verts[self.rel_idx[:,0]] - vs)
        v2_u = unit_vector(ps.verts[self.rel_idx[:,1]] - vs)
        act_ang = np.arccos(np.clip(np_dot(v1_u, v2_u), -1.0, 1.0))


        average_vector = (v1_u + v2_u)/2
        f = average_vector * ((self.rest_ang - act_ang)*self.spring_k)[:, np.newaxis]
        ps.r[self.target_v] += f
        np.add.at(ps.r, self.target_v, f)



class SvTimedForce():
    def __init__(self, force, start, end):

        self.force = force
        self.start = start
        self.end = end
        if hasattr(force,'size_changer'):
            self.size_changer = True
        if hasattr(force,'pin_force'):
            self.pin_force = True
            self.use_pins_goal = force.use_pins_goal

    def setup(self, ps):
        self.force.setup(ps)


    def add(self, ps):
        iteration = ps.iteration
        if self.end > iteration >= self.start:

            self.force.add(ps)

class SvObstaclesForce():
    def __init__(self, obstacles, obstacles_pols, obstacles_bounce):

        np_collide_v = np.array(obstacles)
        np_collide_pol = np.array(obstacles_pols, dtype=np.int16)
        np_pol_v = np_collide_v[np_collide_pol]
        collide_v1 = np_pol_v[:, 1, :] - np_pol_v[:, 0, :]
        collide_v2 = np_pol_v[:, 2, :] - np_pol_v[:, 0, :]
        edges = np.zeros(np_pol_v.shape, dtype=np.float32)
        edges[:, 0, :] = collide_v1
        edges[:, 1, :] = np_pol_v[:, 2, :] - np_pol_v[:, 1, :]
        edges[:, 2, :] = np_pol_v[:, 0, :] - np_pol_v[:, 2, :]

        coll_norm = collide_normals_get(collide_v1, collide_v2)
        coll_p_co = np_pol_v[:, 0, :]
        bounce = np.array(obstacles_bounce)

        self.coll_p_co = coll_p_co
        self.collide_normals = coll_norm
        self.pol_v = np_pol_v
        self.bounce = bounce
        self.edges = edges
            # limits_composite[0].append(local_func)
            # limits_composite[1].append(collide_params)

    def setup(self, ps):
        pass


    def add(self, ps):

        collide_p_co = self.coll_p_co
        collide_normals = self.collide_normals
        pol_v = self.pol_v
        bounce = self.bounce
        edges = self.edges

        pols_m, verts_m = b_box_coll_filter(pol_v, ps.verts, ps.rads)

        verts = ps.verts[verts_m]
        rads = ps.rads[verts_m]
        vels = ps.vel[verts_m]
        index = ps.index[verts_m]

        coll_norm = collide_normals[pols_m, np.newaxis, :]
        coll_dist = collision_dist(verts, collide_p_co[pols_m], coll_norm)
        coll_inter = np.absolute(coll_dist) - rads[np.newaxis, :]
        coll_mask = coll_inter < 0
        if not np.any(coll_mask):
            return

        coll_sign = 2*(coll_dist > 0) - 1
        mask_none = np.any(coll_mask, axis=0)

        p_triang = verts[mask_none] + coll_dist[:, mask_none, np.newaxis] * coll_norm
        rad_axis = rads[np.newaxis, mask_none]
        index = index[mask_none]
        coll_mask = coll_mask[:, mask_none]
        coll_inter = coll_inter[:, mask_none]
        coll_sign = coll_sign[:, mask_none]
        vels = vels[mask_none]

        wuv = pts_in_tris(p_triang, edges[pols_m], pol_v[pols_m], coll_norm, rad_axis, coll_mask)
        num_int = np.maximum(np.sum(wuv, axis=0), 1)[:, np.newaxis]

        displace = np.zeros((ps.v_len, 3), dtype=np.float32)
        velocity = np.zeros((ps.v_len, 3), dtype=np.float32)
        displace[index, :] = coll_displace(coll_norm, coll_inter, coll_sign, wuv, num_int)
        velocity[index, :] = coll_vel(coll_norm, vels, wuv, num_int)
        ps.verts += displace
        ps.vel += velocity * bounce


class SvInflateForce():
    def __init__(self, pols, inflate):

        np_pols = np.array(pols)
        p_len = len(pols)
        if np_pols.dtype == np.object:
            np_len = np.vectorize(len)
            pols_sides = np_len(np_pols)
            pol_side_max = np.amax(pols_sides)
            np_pols = expand_pols_numpy(np_pols, pol_side_max)
            p_regular = False
        else:
            p_regular = True
            pols_sides = np.array(p_len)
            pol_side_max = len(pols[0])

        # inflate_params = [ps,
        self.pols = np_pols
        self.pols_side_max = pol_side_max
        self.pols_sides = pols_sides
        self.inflate = inflate
        self.p_regular = p_regular


    def setup(self, ps):
        pass


    def add(self, ps):

        np_pols = self.pols
        pol_side_max = self.pols_side_max
        pols_sides = self.pols_sides
        inflate = self.inflate
        p_regular = self.p_regular

        pol_v = ps.verts[np_pols, :]
        pols_normal = pols_normals(pol_v, inflate)
        result = np.zeros((ps.v_len, 3), dtype=np.float64)

        if p_regular:
            p_area = calc_area(pol_side_max, pol_v, pols_normal)[:, np.newaxis]
            for i in range(pol_side_max):
                np.add.at(result, np_pols[:, i], pols_normal * p_area)

        else:
            p_area = calc_area_var_sides(pol_side_max, pols_sides, pol_v, pols_normal)[:, np.newaxis]
            for i in range(pol_side_max):
                mask = pols_sides > i
                np.add.at(result, np_pols[mask, i], pols_normal[mask] * p_area[mask])

        ps.r += result


def limit_speed(np_vel, max_vel):
    ''''constrain speed magniture'''
    vel_mag = np.linalg.norm(np_vel, axis=1)
    vel_exceded = vel_mag > max_vel
    np_vel[vel_exceded] = np_vel[vel_exceded] / vel_mag[vel_exceded, np.newaxis] * max_vel

from sverchok.dependencies import scipy
class PulgaSystem():
    '''Store states'''
    verts, rads, vel, density = [[], [], [], []]
    v_len = []
    params = {}
    def __init__(self, init_params):
        self.main_setup(init_params)
        self.mass = self.density * np.power(self.rads, 3)
        self.random_v = []
        self.r = np.zeros((self.v_len, 3), dtype=np.float64)
        self.index = np.arange(self.v_len)
        self.size_change = False
        self.aware = False
        self.iteration = 0
        self.aware = False
        self.pinned = False
        self.goal_pins = True
        self.relations = lambda: None
        self.relations.needed = {}
        for force in self.forces:
            if hasattr(force, 'pin_force'):
                self.pinned = True
                self.params['unpinned'] = np.ones(self.v_len, dtype=np.bool_)
                if force.use_pins_goal:
                    self.goal_pins = True
                    break


        for force in self.forces:
            if hasattr(force, 'size_changer'):
                self.size_change = True


    def relations_setup(self):
        if 'indexes' in self.relations.needed:
            self.relations.indexes = cross_indices3(self.v_len)
        if 'cross_matrix' in self.relations.needed:
            self.relations.result = np.zeros((self.v_len, self.v_len, 3), dtype=np.float64)
        if not self.size_change:
            if 'sum_rad' in self.relations.needed:
                self.relations.sum_rad = self.rads[self.relations.indexes[:, 0]] + self.rads[self.relations.indexes[:, 1]]
            if 'mass_product' in self.relations.needed:
                self.relations.mass_product = self.mass[self.relations.indexes[:, 0]] * self.mass[self.relations.indexes[:, 1]]

    def relations_update(self):
        if 'kd_tree' in self.relations.needed:
            self.relations.kd_tree = scipy.spatial.cKDTree(self.verts)
        if self.size_change:
            if 'sum_rad' in self.relations.needed:
                self.relations.sum_rad = self.rads[self.relations.indexes[:, 0]] + self.rads[self.relations.indexes[:, 1]]
            if 'mass_product' in self.relations.needed:
                self.relations.mass_product = self.mass[self.relations.indexes[:, 0]] * self.mass[self.relations.indexes[:, 1]]

        if 'max_radius' in self.relations.needed:
            self.relations.max_radius = np.amax(self.rads)
        if 'dif_v' in self.relations.needed:
            self.relations.dif_v = self.verts[self.relations.indexes[:, 0], :] - self.verts[self.relations.indexes[:, 1], :]
        if 'dist' in self.relations.needed:
            self.relations.dist = np.linalg.norm(self.relations.dif_v, axis=1)
        if 'collide' in self.relations.needed or 'attract' in self.relations.needed:
            self.relations.mask = self.relations.sum_rad > self.relations.dist
            self.relations.index_inter = self.relations.indexes[self.relations.mask]
        if 'collide' in self.relations.needed:
            self.relations.some_collisions = len(self.relations.index_inter) > 0
        if 'attract' in self.relations.needed:
            self.relations.attract_mask = np.invert(self.relations.mask)
            self.relations.index_non_inter = self.relations.indexes[self.relations.attract_mask]
            self.relations.some_attractions = (len(self.relations.index_inter) < len(self.relations.index_inter))

        if 'dist_cor' in self.relations.needed or 'normal_v' in self.relations.needed:
            self.relations.dist_cor = np.clip(self.relations.dist, 1e-6, 1e4)

        if 'normal_v' in self.relations.needed:
            self.relations.normal_v = self.relations.dif_v / self.relations.dist_cor[:, np.newaxis]
        if 'cross_matrix' in self.relations.needed:
            self.relations.result[:] = 0

    def main_setup(self, local_params):
        '''prepare main data'''
        p = self.params
        initial_pos, _, rads_in, initial_vel, max_vel, density, forces = local_params
        self.forces = forces
        self.verts = np.array(initial_pos)
        self.rads = np.array(rads_in, dtype=np.float64)
        self.vel = np.array(initial_vel, dtype=np.float64)
        self.v_len = len(self.verts)
        p['max_vel'] = np.array(max_vel)
        self.rads, self.vel = numpy_fit_long_repeat([self.rads, self.vel], self.v_len)

        if len(p['max_vel']) > 1:
            p['max_vel'] = numpy_fit_long_repeat([p['max_vel']], self.v_len)[0]

        self.density = np.array(density)
        if len(density) > 1:
            self.density = numpy_fit_long_repeat([self.density], self.v_len)[0]
        # p["Pins Reactions"] = []
        p["Pins Reactions"] = np.array([[]])

    def hard_update(self, cache):
        '''replace verts, rads and vel (in NumPy)'''

        size_change = self.size_change
        verts, rads, vel, react = cache
        if len(verts) == self.v_len:

            if self.pinned and self.goal_pins:
                unpinned = self.params['unpinned']
                self.verts[unpinned] = verts[unpinned]
            else:
                self.verts = verts
            self.vel = vel
            if size_change:
                self.rads = rads
                self.mass = self.density * np.power(self.rads, 3)

    def hard_update_list(self, cache):
        '''replace verts, rads and velocity'''
        size_change = self.size_change
        verts, rads, vel, react = cache
        if type(verts) == list:
            if len(verts) == self.v_len:
                if self.pinned and self.goal_pins:
                    unpinned = self.params['unpinned']
                    self.verts[unpinned] = np.array(verts)[unpinned]
                else:
                    self.verts = np.array(verts)
                if size_change:
                    self.rads = np.array(rads)
                    self.mass = self.density * np.power(self.rads, 3)
                self.vel = np.array(vel)
        else:
            self.hard_update(cache)

    def apply_forces(self):
        '''resultant --> acceleration --> speed --> position'''
        acc = self.r / self.mass[:, np.newaxis]
        self.vel += acc

        if np.any(self.params['max_vel']) > 0:
            limit_speed(self.vel, self.params['max_vel'])

        self.verts += self.vel
        self.r[:] = 0

    def pins_init(self, dicti, forces_composite):
        local_func, local_gates, local_params = dicti
        pins, pins_goal_pos = local_params
        use_pins, use_pins_goal = local_gates

        if not use_pins:
            self.params["Pins Reactions"] = np.array([[]])
            return

        self.params['Pins'] = np.array(pins)

        if self.params['Pins'].dtype == np.int32:
            if len(self.params['Pins']) == len(self.verts):
                self.params['Pins'] = self.params['Pins'] == 1
                self.params['unpinned'] = np.invert(self.params['Pins'])
            else:
                self.params['unpinned'] = np.ones(len(self.verts), dtype=np.bool)
                self.params['unpinned'][self.params['Pins']] = False

        self.vel[self.params['Pins'], :] = 0

        if use_pins_goal:
            self.verts[self.params['Pins'], :] = np.array(pins_goal_pos)
        forces_composite[0].append(local_func)
        forces_composite[1].append(self)
        return


    def apply_pins(self):
        '''cancel forces on pins'''
        self.params["Pins Reactions"] = -self.r[self.params["Pins"]]
        self.r[self.params["Pins"], :] = 0

    def setup_forces(self):
        for force in self.forces:
            if hasattr(force, 'size_changer'):
                self.size_change = True
                break

        for force in self.forces:
            force.setup(self)
        if self.aware:
            self.relations_setup()

    def iterate(self):
        if self.aware:
            self.relations_update()
        if self.pinned:
            self.params['unpinned'][:] = True
        for force in self.forces:

            force.add(self)
        self.iteration += 1
        self.apply_forces()


def local_dict(dictionaries, name):
    '''get all related to the name'''
    return [dictionaries[0][name], dictionaries[1][name], dictionaries[2][name]]


def pulga_system_init(parameters, gates, out_lists, cache):
    '''the main function of the engine'''

    ps = PulgaSystem(parameters)

    iterations = parameters[1]
    iterations_max = max(iterations)
    iterations_rec = [i-1 for i in iterations]
    out_params = [iterations_rec, ps, gates["output"], out_lists]
    ps.setup_forces()

    if gates["accumulate"] and len(cache) > 0:
        ps.hard_update_list(cache)

    iterate(iterations_max, out_params)

    return ps.verts, ps.rads, ps.vel, ps.params["Pins Reactions"]


def iterate(iterations_max, out_params):
    ''' execute repeatedly the defined force map'''
    ps = out_params[1]

    for it in range(iterations_max):
        ps.iterate()
        # for i in range(num_forces):
        #     force_map[i](force_parameters[i])
        output_data(it, out_params)


def output_data(it, params):
    '''if is pertinent output the data'''
    iterations_rec, ps, gate, out_lists = params
    record_iteration = it in iterations_rec
    if record_iteration:
        data_out = prepare_output_data(ps, gate)
        record_data(data_out, out_lists)


def prepare_output_data(ps, gate):
    '''prepare data to output'''
    use_numpy_out = gate

    if use_numpy_out:
        return [ps.verts, ps.rads, ps.vel, ps.params["Pins Reactions"]]
    else:
        return [ps.verts.tolist(), ps.rads.tolist(), ps.vel.tolist(), ps.params["Pins Reactions"].tolist()]


def record_data(data_out, out_lists):
    '''save data to main list'''
    verts_out, rads_out, velocity_out, reactions_out = out_lists
    new_verts, new_rad, new_vel, new_react = data_out
    verts_out.append(new_verts)
    rads_out.append(new_rad)
    velocity_out.append(new_vel)
    reactions_out.append(new_react)
