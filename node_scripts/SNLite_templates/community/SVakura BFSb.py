"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in selected_edges s d=[] n=0
in mode s d=0 n=2
in seed s d=0 n=2
in limit_angle s d=60.0 n=2
in gap s d=1.0 n=2
in use_original_ids s d=1 n=2
in index_all_edges s d=1 n=2
out verts v
out poly s
out flap_points v
out flap_ids s
out meta_data s
"""
import numpy as np
from mathutils import Vector, Matrix, geometry
import math
import random
import heapq # Для быстрой очереди

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

    # 0. Обработка принудительных разрезов (selected_edges)
    s_edges = ensure_nesting(selected_edges)
    forced_cuts = set()
    for e in s_edges:
        if isinstance(e, (list, tuple)) and len(e) >= 2:
            forced_cuts.add(tuple(sorted([int(e[0]), int(e[1])])))

    def get_val(v, default=0):
        if isinstance(v, (list, tuple)):
            return get_val(v[0], default) if v else default
        try: return float(v)
        except: return default

    dist_gap = get_val(gap, 1.0)
    m_type = int(get_val(mode, 0))
    s_val = int(get_val(seed, 0))
    ang_lim = get_val(limit_angle, 60.0)
    cos_threshold = math.cos(math.radians(ang_lim))
    use_original = int(get_val(use_original_ids, 1)) == 1
    index_all = int(get_val(index_all_edges, 1)) == 1
    
    all_final_verts, all_final_polys = [], []
    flap_pts_all, flap_ids_all = [], []
    global_v_ptr, current_x_offset = 0, 0.0

    # 1. Быстрая топология
    edge_to_faces, edge_id_map, edge_original_id = {}, {}, {}
    f_normals, f_centers, edge_counter = [], [], 0
    
    for f_idx, face in enumerate(polys):
        pts = [v_orig[i] for i in face]
        f_centers.append(sum(pts, Vector()) / len(pts))
        n = Vector((0,0,0))
        for i in range(len(pts)): n += pts[i-1].cross(pts[i])
        f_normals.append(n.normalized() if n.length > 1e-8 else Vector((0,0,1)))
        for i in range(len(face)):
            e_topo = tuple(sorted([face[i], face[(i+1)%len(face)]]))
            if e_topo not in edge_to_faces:
                edge_counter += 1
                edge_original_id[e_topo] = edge_counter
            edge_to_faces.setdefault(e_topo, []).append(f_idx)

    # 2. Индексация ребер (для меток клапанов)
    next_edge_id, next_global_id, global_edge_pairs = 1, 1, {}
    for e, f_idxs in edge_to_faces.items():
        if len(f_idxs) == 2:
            edge_id_map[e] = edge_original_id[e] if use_original else next_edge_id
            if not use_original: next_edge_id += 1
        elif len(f_idxs) == 1 and index_all:
            v1, v2 = v_orig[e[0]], v_orig[e[1]]
            e_key = tuple(sorted([(round(v.x,4), round(v.y,4), round(v.z,4)) for v in [v1, v2]]))
            if e_key in global_edge_pairs: edge_id_map[e] = global_edge_pairs[e_key]
            else:
                new_id = edge_original_id[e] if use_original else next_global_id
                if not use_original: next_global_id += 1
                edge_id_map[e] = global_edge_pairs[e_key] = new_id

    # 3. Граф смежности (с учетом ручных разрезов)
    adj, rng = {}, random.Random(s_val)
    for e_topo, f_idxs in edge_to_faces.items():
        if len(f_idxs) == 2:
            # Если ребро в списке выбранных — разрываем связь (разрез)
            if e_topo in forced_cuts:
                continue
            f1, f2 = f_idxs
            if f_normals[f1].dot(f_normals[f2]) >= cos_threshold:
                w = rng.random()
                adj.setdefault(f1, []).append((f2, e_topo, w))
                adj.setdefault(f2, []).append((f1, e_topo, w))

    def get_basis(p1, p2, normal):
        x = (p2 - p1).normalized()
        z = normal.normalized()
        y = z.cross(x).normalized()
        return Matrix((x, y, z)).transposed().to_4x4()

    # Оптимизированная функция проверки наложений (без Shapely)
    def is_overlapping_fast(new_coords, new_bbox, island_2d, island_bboxes):
        for f_idx, placed_coords in island_2d.items():
            p_bbox = island_bboxes[f_idx]
            if (new_bbox[1] < p_bbox[0] - 1e-4 or new_bbox[0] > p_bbox[1] + 1e-4 or 
                new_bbox[3] < p_bbox[2] - 1e-4 or new_bbox[2] > p_bbox[3] + 1e-4):
                continue
            for i in range(len(new_coords)):
                a, b = new_coords[i].xy, new_coords[(i+1)%len(new_coords)].xy
                for j in range(len(placed_coords)):
                    c, d = placed_coords[j].xy, placed_coords[(j+1)%len(placed_coords)].xy
                    if (a-c).length < 1e-4 or (a-d).length < 1e-4 or (b-c).length < 1e-4 or (b-d).length < 1e-4:
                        continue
                    if geometry.intersect_line_line_2d(a, b, c, d): return True
        return False

    def get_bbox(pts):
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return (min(xs), max(xs), min(ys), max(ys))

    visited_global = set()
    all_meta = []

    # 4. Основной цикл развертки
    for root_f_candidate in range(len(polys)):
        if root_f_candidate in visited_global: continue
        available = [i for i in range(len(polys)) if i not in visited_global]
        if not available: break
        root_f = root_f_candidate

        island_2d, island_bboxes, island_edges_internal, parent_child_map = {}, {}, set(), {}
        
        f0 = polys[root_f]
        rot = f_normals[root_f].rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()
        island_2d[root_f] = [rot @ (v_orig[i] - v_orig[f0[0]]) for i in f0]
        island_bboxes[root_f] = get_bbox(island_2d[root_f])
        visited_global.add(root_f)
        
        queue = [] 
        def add_to_q(f_idx):
            if f_idx not in adj: return
            for nei, e, w in adj[f_idx]:
                if nei in visited_global: continue
                prio = -w 
                if m_type == 1: prio += len(island_2d) * 2.0
                heapq.heappush(queue, (prio, f_idx, nei, e))

        add_to_q(root_f)
        while queue:
            _, p_idx, c_idx, edge_topo = heapq.heappop(queue)
            if c_idx in visited_global: continue
            
            p_face, c_face, p_2d = polys[p_idx], polys[c_idx], island_2d[p_idx]
            p1_2d, p2_2d = p_2d[p_face.index(edge_topo[0])], p_2d[p_face.index(edge_topo[1])]
            p1_3d, p2_3d = v_orig[edge_topo[0]], v_orig[edge_topo[1]]
            
            n_c_3d, n_n_3d = f_normals[p_idx], f_normals[c_idx]
            axis = (p2_3d - p1_3d).normalized()
            ang = math.atan2(n_n_3d.dot(n_c_3d.cross(axis)), n_n_3d.dot(n_c_3d))
            
            m_final = Matrix.Translation(p1_2d) @ get_basis(p1_2d, p2_2d, Vector((0,0,1))) @ \
                       get_basis(p1_3d, p2_3d, n_c_3d).inverted() @ \
                       Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-p1_3d)
            
            new_coords = [m_final @ v_orig[idx] for idx in c_face]
            new_bbox = get_bbox(new_coords)
            
            if not is_overlapping_fast(new_coords, new_bbox, island_2d, island_bboxes):
                island_2d[c_idx] = new_coords
                island_bboxes[c_idx] = new_bbox
                island_edges_internal.add(edge_topo)
                visited_global.add(c_idx)
                parent_child_map[c_idx] = (p_idx, edge_topo)
                add_to_q(c_idx)

        # 5. Сборка и упаковка острова
        patch_pts = [p for f in island_2d.values() for p in f]
        if not patch_pts: continue
        min_x, max_x = min(p.x for p in patch_pts), max(p.x for p in patch_pts)
        shift = Vector((current_x_offset - min_x, 0, 0))
        
        island_meta = {'root_f': root_f, 'faces': {}, 'parent_child': {str(k): v for k, v in parent_child_map.items()}}
        for f_idx in sorted(island_2d.keys()):
            pts = [p + shift for p in island_2d[f_idx]]
            island_meta['faces'][f_idx] = {'v_orig': [v_orig[idx][:] for idx in polys[f_idx]], 'f_normal': f_normals[f_idx][:], 'poly_indices': polys[f_idx]}
            all_final_verts.extend([p[:] for p in pts])
            all_final_polys.append(list(range(global_v_ptr, global_v_ptr + len(pts))))
            for i in range(len(polys[f_idx])):
                idx_a, idx_b = polys[f_idx][i], polys[f_idx][(i+1)%len(polys[f_idx])]
                e_key = tuple(sorted([idx_a, idx_b]))
                if e_key not in island_edges_internal:
                    mid = (pts[i] + pts[(i+1)%len(pts)]) / 2
                    flap_pts_all.append(mid[:])
                    e_id = edge_id_map.get(e_key)
                    flap_ids_all.append(str(e_id) if e_id is not None else "0")
            global_v_ptr += len(pts)
        all_meta.append(island_meta)
        current_x_offset += (max_x - min_x) + dist_gap

    return [all_final_verts], [all_final_polys], [flap_pts_all], [flap_ids_all], [all_meta]

verts, poly, flap_points, flap_ids, meta_data = run()