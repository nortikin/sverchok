# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

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


def self_react(params):
    '''behaviors between particles: collide, attract and fit'''
    ps, collision, sum_rad, gates, att_params, fit_params = params
    use_collide, use_attract, use_grow = gates
    indexes = ps.params['indexes']
    if use_grow:
        sum_rad = ps.rads[indexes[:, 0]] + ps.rads[indexes[:, 1]]
        if use_attract:
            att_params[2] = ps.mass[indexes[:, 0]] * ps.mass[indexes[:, 1]]
    dif_v = ps.verts[indexes[:, 0], :] - ps.verts[indexes[:, 1], :]
    dist = np.linalg.norm(dif_v, axis=1)
    mask = sum_rad > dist

    index_inter = indexes[mask]
    some_collisions = use_collide and len(index_inter) > 0
    some_attractions = use_attract and(len(index_inter) < len(indexes))

    if some_collisions or some_attractions:
        result = np.zeros((ps.v_len, ps.v_len, 3), dtype=np.float64)
        dist_cor = np.clip(dist, 1e-6, 1e4)
        normal_v = dif_v/dist_cor[:, np.newaxis]

        if some_collisions:
            self_collision_force(result, dist, sum_rad, index_inter, mask, normal_v, collision)
        if some_attractions:
            antimask = np.invert(mask)
            attract_force(result, dist_cor, antimask, indexes, normal_v, att_params)

        ps.r += np.sum(result, axis=1)

    if use_grow:
        fit_force(ps, index_inter, fit_params)
        ps.mass = ps.density * np.power(ps.rads, 3)


def self_collision_force(result, dist, sum_rad, index_inter, mask, normal_v, self_collision):
    '''apply collision forces between particles'''

    id0 = index_inter[:, 0]
    id1 = index_inter[:, 1]

    le = dist[mask, np.newaxis] - sum_rad[mask, np.newaxis]
    no = normal_v[mask]
    variable_coll = len(self_collision) > 1
    sf = self_collision[:, np.newaxis]
    len0, len1 = [sf[id1], sf[id0]] if variable_coll else [sf, sf]

    result[id0, id1, :] = -no * le * len0
    result[id1, id0, :] = no * le * len1


def attract_force(result, dist, mask, index, norm_v, att_params):
    '''apply attractions between particles'''
    attract, att_decay, mass_product = att_params

    dist2 = np.power(dist, att_decay)[mask, np.newaxis]
    index_non_inter = index[mask]
    id0 = index_non_inter[:, 0]
    id1 = index_non_inter[:, 1]

    direction = norm_v[mask] / dist2 * mass_product[mask, np.newaxis]

    variable_att = len(attract) > 1

    att = attract
    len0, len1 = [att[id1], att[id0]] if variable_att else [att, att]

    result[id0, id1, :] = - direction * len0
    result[id1, id0, :] = direction * len1


def fit_force(ps, index_inter, fit_params):
    '''the untouched particles will grow, the ones that collide will shrink'''
    grow, min_rad, max_rad = fit_params
    touch = np.unique(index_inter)
    free = np.setdiff1d(np.arange(ps.v_len, dtype=np.int16), touch)
    v_grow = len(grow) > 1
    grow_un, grow_tou = [grow[free], grow[touch]] if v_grow else [grow, grow]
    ps.rads[free] += grow_un*0.1
    ps.rads[touch] -= grow_tou*0.1

    ps.rads = np.clip(ps.rads, min_rad, max_rad)


def self_react_setup(ps, dicti, forces_composite):
    '''prepare self reacting data'''
    local_func, local_gates, local_params = dicti
    collision, attract, att_decay, grow, min_rad, max_rad = local_params
    use_self_collision, use_attract, use_grow = local_gates

    np_collision = np.array(collision)
    use_self_collision = use_self_collision and np.any(np_collision > 0)
    np_attract = np.array(attract)[:, np.newaxis]
    use_attract = use_attract and np.any(np_attract != 0)
    np_grow = np.array(grow)
    use_grow = use_grow and np.any(np_grow != 0)

    use_self_react = (use_attract or use_self_collision or use_grow)

    if not use_self_react:
        return

    ps.params['indexes'] = cross_indices3(ps.v_len)
    sum_rad = ps.rads[ps.params['indexes'][:, 0]] + ps.rads[ps.params['indexes'][:, 1]]

    att_params = att_setup(use_attract, ps, np_attract, att_decay)
    fit_params = fit_setup(use_grow, np_grow, min_rad, max_rad)

    gates = [use_self_collision, use_attract, use_grow]
    params = [ps, np_collision, sum_rad, gates, att_params, fit_params]
    forces_composite[0].append(local_func)
    forces_composite[1].append(params)


def att_setup(use_attract, ps, np_attract, attract_decay):
    '''Prepare self-attracting data'''
    if use_attract:
        np_att_decay = np.array(attract_decay)
        indexes = ps.params['indexes']
        mass_product = ps.mass[indexes[:, 0]] * ps.mass[indexes[:, 1]]
        att_params = [np_attract, np_att_decay, mass_product]
    else:
        att_params = []

    return att_params


def fit_setup(use_grow, np_grow, min_rad, max_rad):
    '''Prepare fitting data'''
    if use_grow:
        np_min_rad = np.array(min_rad)
        np_max_rad = np.array(max_rad)
        fit_params = [np_grow, np_min_rad, np_max_rad]
    else:
        fit_params = []

    return fit_params


def attractors_setup(ps, dicti, forces_composite):
    '''prepare attractors system and data'''
    local_func, use_attractors, local_params = dicti
    if use_attractors:
        attractors, att_force, att_clamp, att_decay_power = local_params
        np_attrac = np.array(attractors)
        np_attrac_f = np.array(att_force)
        np_attrac_clamp = np.array(att_clamp)
        np_attrac_decay_pow = np.array(att_decay_power)
        params = [np_attrac, np_attrac_f, np_attrac_clamp, np_attrac_decay_pow]

        forces_composite[0].append(local_func)
        forces_composite[1].append([ps] + numpy_match_long_repeat(params))


def attractors_force(params):
    '''apply attractors force (as planets)'''
    ps, np_attrac, np_attrac_f, np_attrac_clamp, decay = params
    v_attract = ps.verts[np.newaxis, :, :] - np_attrac[:, np.newaxis, :]
    dist_attract = np.linalg.norm(v_attract, axis=2)
    mask = dist_attract > np_attrac_clamp[:, np.newaxis]
    mask_true = np.invert(mask)
    dist_attract2 = np.power(dist_attract, decay[:, np.newaxis])
    dist_attract_cor = np.clip(dist_attract2[mask_true], 1e-2, 1e4)

    v_attract *= np_attrac_f[:, np.newaxis, np.newaxis]
    v_attract_normal = v_attract[mask_true] / dist_attract_cor[:, np.newaxis]

    v_attract[mask_true] = -v_attract_normal
    v_attract[mask, :] = 0

    r_attract = np.sum(v_attract, axis=0)
    ps.r += r_attract


def calc_rest_length(np_verts, np_springs):
    '''calculate edges length'''
    pairs_springs = np_verts[np_springs, :]
    vect_rest = (pairs_springs[:, 0, :] - pairs_springs[:, 1, :])
    dist_rest = np.linalg.norm(vect_rest, axis=1)
    return dist_rest


def spring_setup(ps, dicti, forces_composite):
    '''prepare spring system and data'''
    local_func, local_gates, local_params = dicti
    use_springs, use_fix_len = local_gates
    if use_springs:
        springs, fixed_len, spring_k = local_params
        spring_k = np.array(spring_k)
        if np.any(spring_k != 0):
            springs = np.array(springs)

            if use_fix_len or fixed_len[0] > 0:
                dist_rest = fixed_len
            else:
                dist_rest = calc_rest_length(ps.verts, springs)
            spring_params = [ps, springs, dist_rest, spring_k]
            forces_composite[0].append(local_func)
            forces_composite[1].append(spring_params)


def spring_force(spring_params):
    '''apply spring forces related to edges resistance'''
    ps, np_springs, dist_rest, spring_k = spring_params

    pairs = ps.verts[np_springs, :]
    dif_v = pairs[:, 0, :] - pairs[:, 1, :]
    dist = np.linalg.norm(dif_v, axis=1)
    dif_l = dist - dist_rest
    dist[dist == 0] = 1
    normal_v = dif_v / dist[:, np.newaxis]
    x = dif_l[:, np.newaxis]
    k = spring_k[:, np.newaxis]

    result = np.zeros((ps.v_len, 3), dtype=np.float64)
    np.add.at(result, np_springs[:, 0], -normal_v * x * k)
    np.add.at(result, np_springs[:, 1], normal_v * x * k)

    ps.r += result


def inflate_setup(ps, dicti, forces_composite):
    '''prepare data to inflate'''
    local_func, use_inflate, local_params = dicti
    if use_inflate:
        pols, inflate = local_params
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

        inflate_params = [ps, np_pols, pol_side_max, pols_sides, inflate, p_regular]
        forces_composite[0].append(local_func)
        forces_composite[1].append(inflate_params)


def pols_normals(pol_v, mag):
    '''get actual polygons normal with controlled magnitude'''
    v1 = pol_v[:, 1, :] - pol_v[:, 0, :]
    v2 = pol_v[:, 2, :] - pol_v[:, 0, :]
    pols_normal = np.cross(v1, v2)
    pols_normal_d = np.linalg.norm(pols_normal, axis=1)
    return pols_normal / pols_normal_d[:, np.newaxis] * mag


def inflate_force(inflate_params):
    '''apply force based on normals'''
    ps, np_pols, pol_side_max, pols_sides, inflate, p_regular = inflate_params

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


def drag_setup(ps, dicti, forces_composite):
    '''prepare drag data'''
    local_func, local_gates, local_params = dicti
    use_drag, use_grow = local_gates
    if use_drag:
        drag_force = local_params
        np_drag_force = np.array(drag_force)[:, np.newaxis]
        use_drag = np.any(np_drag_force > 0)
        if use_drag:
            surf = np.power(ps.rads, 2)
            drag_params = [ps, use_grow, np_drag_force, surf]
            forces_composite[0].append(local_func)
            forces_composite[1].append(drag_params)


def drag_force_apply(params):
    '''apply drag force (resistance from environment)'''
    ps, use_grow, drag_mag, surf = params
    vel_mag = np.linalg.norm(ps.vel, axis=1)
    vel_mag_zero = vel_mag == 0
    vel_mag[vel_mag_zero] = 1
    # squaring the speed is more accurate but harder to control
    # vel_mag2 = vel_mag * vel_mag
    vel_mag2 = vel_mag
    vel_norm = ps.vel/vel_mag[:, np.newaxis]
    if use_grow:
        surf = np.power(ps.rads, 2)
    drag = -vel_norm * drag_mag * vel_mag2[:, np.newaxis] * surf[:, np.newaxis]

    ps.r += drag


def random_setup(ps, dicti, forces_composite):
    '''initialize random force'''
    local_func, local_gate, local_params = dicti
    if local_gate:
        random_seed, random_force, random_variation = local_params
        np_random_force = np.array(random_force)
        if any(np_random_force != 0):
            np_random_variation = np.array(random_variation)
            random_force = np_random_force[:, np.newaxis]
            random_variation = np_random_variation[:, np.newaxis]
            random_variate = any(random_variation != 0)
            np.random.seed(random_seed[0])
            ps.random_v = random_force * np.random.random((ps.v_len, 3)) - random_force / 2
            random_params = [ps, random_force, random_variate, random_variation]
            forces_composite[0].append(local_func)
            forces_composite[1].append(random_params)


def random_force_apply(params):
    '''apply random vectors and change it'''
    ps, random_force, random_variate, random_variation = params
    if random_variate:
        random_var = 2 * random_force * np.random.random((ps.v_len, 3)) - random_force
        ps.random_v = ps.random_v * (1 - random_variation) + random_var * random_variation
    ps.r += ps.random_v


def baricentric_mask(p_triang, edges, np_pol_v, coll_normals, ed_id, rad_axis):
    '''helper function to mask which points are inside the triangles'''
    edge = edges[:, ed_id, :]
    v0 = np_pol_v[:, ed_id, :]
    vp0 = p_triang - v0[:, np.newaxis, :]
    cross = np.cross(edge[:, np.newaxis, :], vp0)
    return np.sum(coll_normals * cross, axis=2) > -rad_axis


def collisions_setup(ps, dicti, limits_composite):
    '''prepare collision data'''
    local_func, use_collide, local_params = dicti
    if use_collide:
        obstacles, obstacles_pols, obstacles_bounce = local_params

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
        collide_params = [ps, coll_p_co, coll_norm, np_pol_v, bounce, edges]
        limits_composite[0].append(local_func)
        limits_composite[1].append(collide_params)


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


def collisions_apply(collide_params):
    '''apply collisions with obstacles'''
    ps, collide_p_co, collide_normals, pol_v, bounce, edges = collide_params

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


def b_box_setup(ps, dicti, limits_composite):
    '''prepare b_box data'''
    local_func, use_b_box, b_box = dicti
    if use_b_box:
        np_bbox = np.array(b_box)
        bbox_max = np.amax(np_bbox, axis=0)
        bbox_min = np.amin(np_bbox, axis=0)
        b_box_params = [ps, bbox_min, bbox_max]
        limits_composite[0].append(local_func)
        limits_composite[1].append(b_box_params)


def b_box_apply(b_box_params):
    '''apply hard limit to verts'''
    ps, bbox_min, bbox_max = b_box_params
    ps.verts = np.clip(ps.verts, bbox_min + ps.rads[:, np.newaxis], bbox_max - ps.rads[:, np.newaxis])


def world_forces_setup(ps, dicti, forces_composite):
    '''prepare world forces data'''
    local_func, gates, params = dicti
    use_world_f, size_change = gates
    world_forces, wind = params
    if use_world_f:
        np_world_f = np.array(world_forces)
        np_wind = np.array(wind)
        if len(world_forces) > 1:
            np_world_f = numpy_fit_long_repeat([np_world_f], ps.v_len)[0]
        if not size_change:
            np_world_f = np_world_f * ps.mass[:, np.newaxis]
            func = local_func[0]
        else:
            func = local_func[1]
        if len(np_wind)> 1:
            np_wind = numpy_fit_long_repeat([np_wind], ps.v_len)[0]

        ps.params['gravity'] = np_world_f
        ps.params['wind'] = np_wind
        forces_composite[0].append(func)
        forces_composite[1].append(ps)


def world_forces_apply(ps):
    '''apply constant forces'''
    ps.r += ps.params['gravity'] + ps.params['wind']


def world_forces_apply_var(ps):
    '''apply constant forces'''

    ps.r += ps.params['gravity']  * ps.mass[:, np.newaxis] + ps.params['wind']


def pins_setup(ps, dicti, forces_composite):
    '''prepare pins data'''

    ps.pins_init(dicti, forces_composite)


def pins_apply(ps):
    '''apply pin mask'''
    ps.apply_pins()


def apply_forces_setup(ps, dicti, forces_composite):
    '''prepare applying all forces process'''
    local_func, _, _ = dicti
    forces_composite[0].append(local_func)
    forces_composite[1].append(ps)


def apply_all_forces(ps):
    '''applying forces and reseting resultant'''
    ps.apply_forces()


def limit_speed(np_vel, max_vel):
    ''''constrain speed magniture'''
    vel_mag = np.linalg.norm(np_vel, axis=1)
    vel_exceded = vel_mag > max_vel
    np_vel[vel_exceded] = np_vel[vel_exceded] / vel_mag[vel_exceded, np.newaxis] * max_vel

FORCE_CHAIN = ["self_react", "Springs", "drag", "inflate", "random", "attractors", "world_f", "Pins", "apply_f", "b_box", "Obstacles"]

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

    def main_setup(self, local_params):
        '''prepare main data'''
        p = self.params
        initial_pos, rads_in, initial_vel, max_vel, density = local_params
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
        p["Pins Reactions"] = []

    def hard_update(self, cache, size_change, pins_gates):
        '''replace verts, rads and vel (in NumPy)'''
        verts, rads, vel, react = cache
        if len(verts) == self.v_len:
            if pins_gates[0] and pins_gates[1]:
                unpinned = self.params['unpinned']
                self.verts[unpinned] = verts[unpinned]
            else:
                self.verts = verts
            self.vel = vel
            if not size_change:
                self.rads = rads

    def hard_update_list(self, cache, size_change, pins_gates):
        '''replace verts, rads and velocity'''
        verts, rads, vel, react = cache
        if type(verts) == list:
            if len(verts) == self.v_len:
                if pins_gates[0] and pins_gates[1]:
                    unpinned = self.params['unpinned']
                    self.verts[unpinned] = np.array(verts)[unpinned]
                else:
                    self.verts = np.array(verts)
                if not size_change:
                    self.rads = np.array(rads)
                self.vel = np.array(vel)
        else:
            self.hard_update(cache, size_change, pins_gates)

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


FUNC_DICT = {
    "self_react": self_react,
    "Springs":    spring_force,
    "drag":       drag_force_apply,
    "inflate":    inflate_force,
    "random":     random_force_apply,
    "attractors": attractors_force,
    "world_f":    (world_forces_apply, world_forces_apply_var),
    "Pins":       PulgaSystem.apply_pins,
    "apply_f":    PulgaSystem.apply_forces,
    "b_box":      b_box_apply,
    "Obstacles":  collisions_apply

    }
INIT_FUNC_DICT = {
    "self_react": self_react_setup,
    "Springs":    spring_setup,
    "drag":       drag_setup,
    "inflate":    inflate_setup,
    "random":     random_setup,
    "attractors": attractors_setup,
    "world_f":    world_forces_setup,
    "Pins":       pins_setup,
    "apply_f":    apply_forces_setup,
    "b_box":      b_box_setup,
    "Obstacles":  collisions_setup

    }


PARAMS_GROUPS = {
    "main":    ("Initial_Pos", "rads_in", 'Initial Velocity', "max_vel", "Density"),
    "Springs": ("Springs", "fixed_len", "spring_k" ),
    "Pins": ("Pins", "Pins Goal Position"),
    "self_react": ("self_collision",  "self_attract", "attract_decay", "grow", "min_rad", "max_rad"),
    "inflate": ("Pols", "inflate"),
    "drag": ("drag_force"),
    "attractors": ("Attractors", "att_force", "att_clamp", "att_decay_power"),
    "random": ("random_seed", "random_force", "random_variation"),
    "world_f": ("Gravity", "Wind"),
    "b_box": ("Bounding Box"),
    "Obstacles": ("Obstacles", "Obstacles_pols", "obstacles_bounce"),

}
def fill_params_dict(p_dict, parameters, par):
    '''redistribute parameters'''
    for x in PARAMS_GROUPS:
        if type(PARAMS_GROUPS[x]) == tuple:
            p_dict[x] = [par[p] for p in PARAMS_GROUPS[x] ]
        else:
            p_dict[x] = par[PARAMS_GROUPS[x]]


    p_dict["apply_f"] = True


def local_dict(dictionaries, name):
    '''get all related to the name'''
    return [dictionaries[0][name], dictionaries[1][name], dictionaries[2][name]]


def pulga_system_init(params, parameters, gates, out_lists, cache):
    '''the main function of the engine'''

    dictionaries = [FUNC_DICT, gates, {}]
    fill_params_dict(dictionaries[2], parameters, params)
    force_map = []
    force_parameters = []
    forces_composite = [force_map, force_parameters]
    ps = PulgaSystem(dictionaries[2]["main"])
    for force in FORCE_CHAIN:
        INIT_FUNC_DICT[force](ps, local_dict(dictionaries, force), forces_composite)

    iterations = parameters[1]
    iterations_max = max(iterations)
    iterations_rec = [i-1 for i in iterations]
    out_params = [iterations_rec, ps, dictionaries[1]["output"], out_lists]

    if dictionaries[1]["accumulate"]:
        if len(cache) > 0:
            ps.hard_update_list(cache, gates["self_react"][2], gates["Pins"])

    iterate(iterations_max, force_map, force_parameters, out_params)

    return ps.verts, ps.rads, ps.vel, ps.params["Pins Reactions"]


def iterate(iterations_max, force_map, force_parameters, out_params):
    ''' execute repeatedly the defined force map'''
    num_forces = len(force_map)
    for it in range(iterations_max):
        for i in range(num_forces):
            force_map[i](force_parameters[i])
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