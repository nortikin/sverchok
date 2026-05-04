"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in flap_points v d=[] n=0
in meta_data s d=[] n=0
in unfold_factor s d=1.0 n=2
in position_factor s d=0.0 n=2
out verts_out v
out poly_out s
out flap_points_out v
"""
from mathutils import Vector, Matrix
import math

def run():
    # Универсальная распаковка
    def deep_unpack(data, is_dict=False):
        if not data: return []
        curr = data
        if is_dict:
            while isinstance(curr, (list, tuple)) and len(curr) > 0 and not isinstance(curr[0], dict):
                curr = curr[0]
            return curr
        while isinstance(curr, (list, tuple)) and len(curr) > 0:
            if not isinstance(curr[0], (list, tuple)): return curr
            if len(curr[0]) > 0 and not isinstance(curr[0][0], (list, tuple)): return curr
            curr = curr[0]
        return curr

    v_raw = deep_unpack(verts_in)
    p_raw = deep_unpack(poly_in)
    m_raw = deep_unpack(meta_data, is_dict=True)
    fp_raw = deep_unpack(flap_points)

    if not v_raw or not m_raw:
        return [[]], [[]], [[]]

    def get_val(v, default=0):
        if isinstance(v, (list, tuple)):
            return get_val(v[0], default) if v else default
        try: return float(v)
        except: return default

    unfold_val = get_val(unfold_factor, 1.0)
    position_val = get_val(position_factor, 0.0)
    
    res_verts = [Vector(v[:3]) for v in v_raw]
    res_flap_pts = []
    
    v_ptr = 0
    fp_ptr = 0
    
    for island in m_raw:
        if not isinstance(island, dict) or 'faces' not in island:
            continue
            
        faces_meta = island['faces']
        parent_child = island.get('parent_child', {})
        internal_edges = set()
        for val in parent_child.values():
            internal_edges.add(tuple(val[1]))
            
        def get_f_meta(idx):
            return faces_meta.get(idx) or faces_meta.get(str(idx))
            
        children_map = {}
        for c_idx_str, val in parent_child.items():
            p_idx = int(val[0])
            children_map.setdefault(p_idx, []).append(int(c_idx_str))
            
        root_f = int(island['root_f'])
        sorted_f_indices = sorted([int(k) for k in faces_meta.keys()])
        
        f_to_range = {}
        ptr = v_ptr
        for f_idx in sorted_f_indices:
            f_m = get_f_meta(f_idx)
            num_v = len(f_m['v_orig'])
            f_to_range[f_idx] = (ptr, ptr + num_v)
            ptr += num_v
        v_ptr = ptr
        
        face_matrices = {}

        def fold_recursive(f_idx, current_m, processed):
            if f_idx in processed: return
            processed.add(f_idx)
            face_matrices[f_idx] = current_m
            
            f_meta = get_f_meta(f_idx)
            if not f_meta or f_idx not in f_to_range: return
            
            start, end = f_to_range[f_idx]
            v_orig_list = [Vector(v) for v in f_meta['v_orig']]
            
            # Трансформируем
            for i in range(end - start):
                v_flat = Vector(v_raw[start + i][:3])
                res_verts[start + i] = (current_m @ v_flat) * (1 - position_val) + v_orig_list[i] * position_val
            
            # Рекурсия
            if f_idx in children_map:
                for c_idx in children_map[f_idx]:
                    c_meta = get_f_meta(c_idx)
                    if not c_meta: continue
                    pc_data = parent_child.get(str(c_idx)) or parent_child.get(c_idx)
                    edge_topo = pc_data[1]
                    poly_indices = f_meta['poly_indices']
                    try:
                        idx_a, idx_b = poly_indices.index(edge_topo[0]), poly_indices.index(edge_topo[1])
                    except: continue
                    
                    p1_flat, p2_flat = Vector(v_raw[start + idx_a][:3]), Vector(v_raw[start + idx_b][:3])
                    axis_flat, edge_center_flat = (p2_flat - p1_flat).normalized(), (p1_flat + p2_flat) * 0.5
                    n_p, n_c = Vector(f_meta['f_normal']), Vector(c_meta['f_normal'])
                    angle = math.acos(max(-1, min(1, n_p.dot(n_c))))
                    v_orig_p1, v_orig_p2 = Vector(v_orig_list[idx_a]), Vector(v_orig_list[idx_b])
                    if n_p.cross(n_c).dot((v_orig_p2 - v_orig_p1).normalized()) < 0: angle = -angle
                    
                    m_rot = Matrix.Translation(edge_center_flat) @ Matrix.Rotation(angle * (1 - unfold_val), 4, axis_flat) @ Matrix.Translation(-edge_center_flat)
                    fold_recursive(c_idx, current_m @ m_rot, processed)

        fold_recursive(root_f, Matrix.Identity(4), set())

        # Трансформируем
        for f_idx in sorted_f_indices:
            f_meta = get_f_meta(f_idx)
            m = face_matrices.get(f_idx, Matrix.Identity(4))
            poly_indices = f_meta['poly_indices']
            v_orig_list = [Vector(v) for v in f_meta['v_orig']]
            for i in range(len(poly_indices)):
                v1_idx, v2_idx = poly_indices[i], poly_indices[(i+1)%len(poly_indices)]
                edge_topo = tuple(sorted([v1_idx, v2_idx]))
                if edge_topo not in internal_edges:
                    if fp_ptr < len(fp_raw):
                        p_flat = Vector(fp_raw[fp_ptr][:3])
                        p_folded = m @ p_flat
                        p1_3d, p2_3d = v_orig_list[i], v_orig_list[(i+1)%len(poly_indices)]
                        p_3d = (p1_3d + p2_3d) * 0.5
                        res_flap_pts.append((p_folded * (1 - position_val) + p_3d * position_val)[:])
                        fp_ptr += 1

    return [[v[:] for v in res_verts]], [p_raw], [res_flap_pts]

verts_out, poly_out, flap_points_out = run()