"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in mask s d=[] n=0
enum = CUT RHOMB ARC SQURE CIRCLE
enum2 = ETRI EMONO FTRI FMONO
in offset s d=0.2 n=2
in bulge s d=0.1 n=2
in segments s d=8 n=2
out verts_out v
out poly_out s
"""

import bpy
import numpy as np

def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)
    layout.prop(self, 'custom_enum_2', expand=True)

# Проверка
if not verts_in or not poly_in:
    verts_out, poly_out = [[]], [[]]
else:
    # Распаковка
    v_src = verts_in[0] if isinstance(verts_in[0], list) and isinstance(verts_in[0][0], (list, tuple)) else verts_in
    p_src = poly_in[0] if isinstance(poly_in[0], list) and isinstance(poly_in[0][0], (list, tuple)) else poly_in
    m_src = mask[0] if mask and isinstance(mask[0], list) else (mask if mask else [])

    all_v, all_f = [], []
    v_cnt = 0
    mode = self.custom_enum
    match mode:
        case 'CUT':
            m_type = 0
        case 'RHOMB':
            m_type = 1
        case 'ARC':
            m_type = 2
        case 'SQURE':
            m_type = 3
        case 'CIRCLE':
            m_type = 4
    res = int(segments)
    off_val, b_param = float(offset), float(bulge)
    monotone = self.custom_enum_2
    match monotone:
        case 'ETRI':
            is_monotone = 0
            fill = 0
        case 'EMONO':
            is_monotone = 1
            fill = 0
        case 'FTRI':
            is_monotone = 0
            fill = 1
        case 'FMONO':
            is_monotone = 1
            fill = 1

    for face in p_src:
        if not face or len(face) < 3: continue
        
        f_coords = [np.array(v_src[idx]) for idx in face]
        num_v = len(f_coords)
        center_poly = [] 

        for i in range(num_v):
            idx_orig = face[i]
            v_curr = f_coords[i]
            
            is_active = True
            if m_src and idx_orig < len(m_src):
                if not m_src[idx_orig]: is_active = False

            if not is_active:
                center_poly.append(v_cnt)
                all_v.append(v_curr.tolist()); v_cnt += 1
                continue

            v_prev, v_next = f_coords[i-1], f_coords[(i+1) % num_v]
            d_p, d_n = v_prev - v_curr, v_next - v_curr
            l_p, l_n = np.linalg.norm(d_p), np.linalg.norm(d_n)
            
            if l_p < 1e-8 or l_n < 1e-8:
                center_poly.append(v_cnt); all_v.append(v_curr.tolist()); v_cnt += 1
                continue

            o_p, o_n = min(off_val, l_p * 0.5), min(off_val, l_n * 0.5)
            u_p, u_n = d_p / l_p, d_n / l_n
            p_s, p_e = v_curr + u_p * o_p, v_curr + u_n * o_n
            
            mid = (p_s + p_e) * 0.5
            p_vec = mid - v_curr
            p_len = np.linalg.norm(p_vec)
            p_dir = p_vec / (p_len + 1e-9)

            arc_pts = []
            
            if m_type == 0: # Chamfer
                arc_pts = [p_s, p_e]
            elif m_type == 1: # Rhomb
                arc_pts = [p_s, v_curr + u_p * o_p + u_n * o_n, p_e]
            elif m_type == 2: # Bezier
                ctrl = mid + p_dir * b_param
                for t in np.linspace(0, 1, max(res, 2)):
                    arc_pts.append((1-t)**2 * p_s + 2*(1-t)*t * ctrl + t**2 * p_e)
            elif m_type == 3: # Miter
                dot = np.dot(u_p, u_n)
                denom = 1.0 - dot**2
                if abs(denom) > 1e-6:
                    tp, tn = (o_p - o_n * dot)/denom, (o_n - o_p * dot)/denom
                    arc_pts = [p_s, v_curr + u_p * tp + u_n * tn, p_e]
                else: 
                    arc_pts = [p_s, v_curr + u_p * o_p + u_n * o_n, p_e]
            elif m_type == 4: # Arc
                dot = np.clip(np.dot(u_p, u_n), -1.0, 1.0)
                angle = np.arccos(dot)
                steps = max(res, 2)
                sin_a = np.sin(angle)
                if abs(sin_a) < 1e-6:
                    arc_pts = [p_s, p_e]
                elif b_param >= 0:
                    radius = (o_p + o_n) * 0.5
                    for t in np.linspace(0, 1, steps):
                        curr_angle = t * angle
                        v_arc = (u_p * np.sin(angle - curr_angle) + u_n * np.sin(curr_angle)) / sin_a
                        arc_pts.append(v_curr + v_arc * radius)
                else:
                    denom = 1.0 - dot**2
                    if abs(denom) > 1e-6:
                        tp, tn = (o_p - o_n * dot)/denom, (o_n - o_p * dot)/denom
                        v_ext = v_curr + u_p * tp + u_n * tn
                    else:
                        v_ext = v_curr + u_p * o_p + u_n * o_n
                    r_vec_s, r_vec_e = p_s - v_ext, p_e - v_ext
                    u_rs, u_re = r_vec_s / (np.linalg.norm(r_vec_s) + 1e-9), r_vec_e / (np.linalg.norm(r_vec_e) + 1e-9)
                    angle_inv = np.arccos(np.clip(np.dot(u_rs, u_re), -1.0, 1.0))
                    sin_inv = np.sin(angle_inv)
                    if abs(sin_inv) < 1e-6: arc_pts = [p_s, p_e]
                    else:
                        r_avg = (np.linalg.norm(r_vec_s) + np.linalg.norm(r_vec_e)) * 0.5
                        for t in np.linspace(0, 1, steps):
                            curr_a = t * angle_inv
                            v_arc = (u_rs * np.sin(angle_inv - curr_a) + u_re * np.sin(curr_a)) / sin_inv
                            arc_pts.append(v_ext + v_arc * r_avg)

            # Сборка
            a_idx = v_cnt
            all_v.append(v_curr.tolist()); v_cnt += 1
            added = []
            for pt in arc_pts:
                if not added or np.linalg.norm(pt - np.array(all_v[-1])) > 1e-6:
                    all_v.append(pt.tolist())
                    center_poly.append(v_cnt)
                    added.append(v_cnt)
                    v_cnt += 1
            
            if is_monotone:
                if len(added) > 1:
                    all_f.append([a_idx] + added[::-1])
            else:
                for j in range(len(added) - 1):
                    all_f.append([a_idx, added[j+1], added[j]])

        # Заполнение центра
        if fill == 1 and len(center_poly) >= 3:
            cp = []
            for idx in center_poly:
                if not cp or idx != cp[-1]: cp.append(idx)
            if len(cp) > 2 and cp[0] == cp[-1]: cp.pop()
            if len(set(cp)) >= 3: all_f.append(cp)

    verts_out, poly_out = [all_v], [all_f]
