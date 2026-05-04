"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in selected_edges s d=[] n=0
in mode s d=0 n=2
in gap s d=1.0 n=2
in strictness s d=1000.0 n=2
in z_sensitivity s d=0.01 n=2
out verts v
out poly s
out flap_points v
out flap_ids s
out meta_data s
"""
import numpy as np
from mathutils import Vector, Matrix
import math

def run():
    if not verts_in or not poly_in:
        return [[]], [[]], [[]], [[]], [[]]

    def ensure_nesting(data):
        if not data: return []
        if isinstance(data, (list, tuple)) and len(data) > 0:
            if isinstance(data[0], (list, tuple)) and not isinstance(data[0][0], (float, int)):
                return ensure_nesting(data[0])
        return data

    v_raw = ensure_nesting(verts_in)
    p_raw = ensure_nesting(poly_in)
    v_orig = [Vector(v[:3]) for v in v_raw]
    polys = p_raw

    # Process forced cuts from selected_edges
    s_edges = ensure_nesting(selected_edges)
    forced_cuts = set()
    for e in s_edges:
        if isinstance(e, (list, tuple)) and len(e) >= 2:
            forced_cuts.add(tuple(sorted([int(e[0]), int(e[1])])))

    def get_val(v, default=0):
        if isinstance(v, (list, tuple)):
            if len(v) > 0: return get_val(v[0], default)
            return default
        try: return float(v)
        except: return default

    dist_gap = get_val(gap, 1.0)
    m_val = int(get_val(mode, 0))
    s_val = get_val(strictness, 1000.0)
    z_sens = get_val(z_sensitivity, 0.01)
    
    all_final_verts, all_final_polys = [], []
    flap_pts_all, flap_ids_all = [], []
    global_edge_registry = {}
    next_id = 1
    global_v_ptr = 0
    current_x_offset = 0.0

    edge_to_faces = {}
    f_normals = []
    edge_id_map = {}
    f_centers = []
    
    for f_idx, face in enumerate(polys):
        pts = [v_orig[i] for i in face]
        f_centers.append(sum(pts, Vector()) / len(pts))
        n = Vector((0,0,0))
        for i in range(len(pts)): n += pts[i-1].cross(pts[i])
        f_normals.append(n.normalized() if n.length > 1e-8 else Vector((0,0,1)))
        for i in range(len(face)):
            v1_idx, v2_idx = face[i], face[(i+1)%len(face)]
            e_key_3d = tuple(sorted([(round(v.x,4), round(v.y,4), round(v.z,4)) for v in [v_orig[v1_idx], v_orig[v2_idx]]]))
            if e_key_3d not in global_edge_registry:
                global_edge_registry[e_key_3d] = next_id
                next_id += 1
            e_topo = tuple(sorted([v1_idx, v2_idx]))
            edge_id_map[e_topo] = global_edge_registry[e_key_3d]
            edge_to_faces.setdefault(e_topo, []).append(f_idx)

    def get_basis(p1, p2, normal):
        x = (p2 - p1).normalized()
        z = normal.normalized()
        y = z.cross(x).normalized()
        return Matrix((x, y, z)).transposed().to_4x4()

    visited_global = set()
    all_meta = []

    for root_f_candidate in range(len(polys)):
        if root_f_candidate in visited_global: continue
        
        if m_val == 1: root_f = max([i for i in range(len(polys)) if i not in visited_global], key=lambda i: f_centers[i].z)
        elif m_val == 2: root_f = min([i for i in range(len(polys)) if i not in visited_global], key=lambda i: abs(f_centers[i].z))
        else: root_f = root_f_candidate

        island_2d = {}
        island_edges_internal = set()
        parent_child_map = {}
        edge_transforms = {}
        
        f0 = polys[root_f]
        p_ref = v_orig[f0[0]]
        rot = f_normals[root_f].rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()
        island_2d[root_f] = [rot @ (v_orig[i] - p_ref) for i in f0]
        visited_global.add(root_f)
        queue = [(0.0, root_f)]

        while queue:
            if m_val > 0: queue.sort()
            _, c_idx = queue.pop(0)
            c_face, c_2d, n_c_3d = polys[c_idx], island_2d[c_idx], f_normals[c_idx]
            for i in range(len(c_face)):
                v1, v2 = c_face[i], c_face[(i+1)%len(c_face)]
                edge_topo = tuple(sorted([v1, v2]))
                
                # Check for forced cuts
                if edge_topo in forced_cuts:
                    continue
                    
                for n_idx in edge_to_faces.get(edge_topo, []):
                    if n_idx in visited_global: continue
                    p1_3d, p2_3d = v_orig[v1], v_orig[v2]
                    p1_2d, p2_2d = c_2d[i], c_2d[(i+1)%len(c_face)]
                    n_n_3d = f_normals[n_idx]
                    axis = (p2_3d - p1_3d).normalized()
                    ang = math.atan2(n_n_3d.dot(n_c_3d.cross(axis)), n_n_3d.dot(n_c_3d))
                    m_final = Matrix.Translation(p1_2d) @ get_basis(p1_2d, p2_2d, Vector((0,0,1))) @ \
                               get_basis(p1_3d, p2_3d, n_c_3d).inverted() @ \
                               Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-p1_3d)
                    island_2d[n_idx] = [m_final @ v_orig[idx] for idx in polys[n_idx]]
                    island_edges_internal.add(edge_topo)
                    visited_global.add(n_idx)
                    prio = 0.0
                    if m_val == 1: prio = -f_centers[n_idx].z + (s_val if abs(f_centers[c_idx].z - f_centers[n_idx].z) < z_sens else 0.0)
                    elif m_val == 2: prio = abs(f_centers[n_idx].z) + (s_val if abs(f_centers[c_idx].z - f_centers[n_idx].z) > z_sens else 0.0)
                    queue.append((float(prio), n_idx))
                    parent_child_map[n_idx] = (c_idx, edge_topo)
                    edge_transforms[(c_idx, n_idx)] = [list(row) for row in m_final]

        patch_pts = [p for f in island_2d.values() for p in f]
        min_x, max_x = min(p.x for p in patch_pts), max(p.x for p in patch_pts)
        shift = Vector((current_x_offset - min_x, 0, 0))
        
        island_meta = {
            'root_f': root_f,
            'faces': {},
            'parent_child': {str(k): v for k, v in parent_child_map.items()},
            'transforms': {f"{k[0]}_{k[1]}": v for k, v in edge_transforms.items()}
        }

        for f_idx in sorted(island_2d.keys()):
            pts = [p + shift for p in island_2d[f_idx]]
            island_meta['faces'][f_idx] = {
                'v_orig': [v_orig[idx][:] for idx in polys[f_idx]],
                'f_normal': f_normals[f_idx][:],
                'poly_indices': polys[f_idx]
            }
            all_final_verts.extend([p[:] for p in pts])
            all_final_polys.append(list(range(global_v_ptr, global_v_ptr + len(pts))))
            for i in range(len(polys[f_idx])):
                idx_a, idx_b = polys[f_idx][i], polys[f_idx][(i+1)%len(polys[f_idx])]
                edge_topo = tuple(sorted([idx_a, idx_b]))
                if edge_topo not in island_edges_internal:
                    mid = (pts[i] + pts[(i+1)%len(pts)]) / 2
                    flap_pts_all.append(mid[:]); flap_ids_all.append(str(edge_id_map[edge_topo]))
            global_v_ptr += len(pts)
        
        all_meta.append(island_meta)
        current_x_offset += (max_x - min_x) + dist_gap

    return [all_final_verts], [all_final_polys], [flap_pts_all], [flap_ids_all], [all_meta]

verts, poly, flap_points, flap_ids, meta_data = run()