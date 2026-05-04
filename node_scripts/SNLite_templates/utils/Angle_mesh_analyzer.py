"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in mask s d=[] n=0
in arc_size s d=0.3 n=2
in arc_res s d=24 n=2
enum = CORNERS NODES DIHEDRAL
enum2 = COMPL NONCOMPL
out verts_out v
out poly_out s
out gizmo_centers v
out angle_data s
out gizmo_v v
out gizmo_s s
"""

import bpy
import numpy as np
from mathutils import Vector, Matrix
import math

def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)
    layout.prop(self, 'custom_enum_2', expand=True)

def run_logic():
    # 1. Распаковка
    if not verts_in or not isinstance(verts_in, (list, tuple)):
        return [[]], [[]], [[]], [[]], [[]], [[]]
    
    v_data = verts_in
    while v_data and isinstance(v_data[0], (list, tuple)) and not isinstance(v_data[0][0], (float, int)):
        v_data = v_data[0]
    v_src = [Vector(v[:3]) for v in v_data]
    
    # 2. Распаковка
    p_src = poly_in
    while p_src and isinstance(p_src[0], (list, tuple)) and isinstance(p_src[0][0], (list, tuple)):
        p_src = p_src[0]

    # 3. Маски
    m_src = mask
    if m_src and isinstance(m_src, (list, tuple)) and isinstance(m_src[0], (list, tuple)):
        m_src = m_src[0]

    # 4. Распаковка параметров
    def to_val(x, default):
        if isinstance(x, (list, tuple)): return to_val(x[0], default) if x else default
        return x

    mode = self.custom_enum
    match mode:
        case 'CORNERS':
            m_mode = 0
        case 'NODES':
            m_mode = 1
        case 'DIHEDRAL':
            m_mode = 2
    compl_mode = self.custom_enum_2
    match compl_mode:
        case 'COMPL':
            c_type = 1
        case 'NONCOMPL':
            c_type = 0
    
    a_size = float(to_val(arc_size, 0.3))
    a_res = max(int(to_val(arc_res, 24)), 2)

    angles, g_verts, g_polys, g_centers = [], [], [], []
    v_ptr = 0

    def create_arc_logic(center, d1, d2, radius, res, c_logic, custom_axis=None):
        nonlocal v_ptr
        dot = max(-1.0, min(1.0, d1.dot(d2)))
        base_angle = math.acos(dot)
        if base_angle < 1e-6: return None
        
        draw_angle = base_angle
        if c_logic == 1: draw_angle = -(2 * math.pi - base_angle)
        elif c_logic == 2: draw_angle = math.pi - base_angle
        elif c_logic == 3: draw_angle = math.pi/2 - base_angle

        if custom_axis:
            axis = custom_axis
            if d1.cross(d2).dot(axis) < 0: axis = -axis
        else:
            axis = d1.cross(d2)
            if axis.length < 1e-7:
                axis = Vector((0,0,1)) if abs(d1.z) < 0.9 else Vector((0,1,0))
                axis = d1.cross(axis)
        axis.normalize()
        
        pts = [[center.x, center.y, center.z]]
        for i in range(res + 1):
            t = i / res
            rot_mat = Matrix.Rotation(draw_angle * t, 4, axis)
            pt = center + (rot_mat @ d1) * radius
            pts.append([pt.x, pt.y, pt.z])
        
        mid_rot = Matrix.Rotation(draw_angle * 0.5, 4, axis)
        c_pos = center + (mid_rot @ d1) * (radius * 1.1)
        
        poly_ind = [v_ptr + j for j in range(len(pts))]
        v_ptr += len(pts)
        
        val = abs(math.degrees(draw_angle)) if c_logic != 1 else math.degrees(2*math.pi-base_angle)
        return {'pts': pts, 'poly': poly_ind, 'ang': round(val, 12), 'center': [c_pos.x, c_pos.y, c_pos.z]}

    # --- РЕЖИМЫ ---
    if m_mode == 0: # CORNERS
        for face in p_src:
            if not isinstance(face, (list, tuple)) or len(face) < 3: continue
            for i in range(len(face)):
                idx = face[i]
                if m_src and idx < len(m_src) and not m_src[idx]: continue
                c, p, n = v_src[idx], v_src[face[i-1]], v_src[face[(i+1)%len(face)]]
                res = create_arc_logic(c, (p-c).normalized(), (n-c).normalized(), a_size, a_res, c_type)
                if res:
                    g_verts.extend(res['pts']); g_polys.append(res['poly'])
                    angles.append(res['ang']); g_centers.append(res['center'])

    elif m_mode == 1: # NODES
        adj = {}
        for item in p_src:
            if not isinstance(item, (list, tuple)): continue
            for i in range(len(item)):
                # Логика
                v1 = item[i]
                v2 = item[(i+1)%len(item)]
                if len(item) == 2 and i == 1: continue 
                if v1 == v2: continue
                adj.setdefault(v1, set()).add(v2)
                adj.setdefault(v2, set()).add(v1)
        
        for idx in sorted(adj.keys()):
            if m_src and idx < len(m_src) and not m_src[idx]: continue
            nb = list(adj[idx])
            for i in range(len(nb)):
                for j in range(i + 1, len(nb)):
                    c, p, n = v_src[idx], v_src[nb[i]], v_src[nb[j]]
                    res = create_arc_logic(c, (p-c).normalized(), (n-c).normalized(), a_size, a_res, c_type)
                    if res:
                        g_verts.extend(res['pts']); g_polys.append(res['poly'])
                        angles.append(res['ang']); g_centers.append(res['center'])

    elif m_mode == 2: # DIHEDRAL
        edge_to_faces, face_centers = {}, []
        for f_idx, face in enumerate(p_src):
            if len(face) < 3: face_centers.append(Vector()); continue
            face_centers.append(sum([v_src[j] for j in face], Vector()) / len(face))
            for i in range(len(face)):
                e = tuple(sorted((face[i], face[i-1])))
                edge_to_faces.setdefault(e, []).append(f_idx)
        
        for edge, f_idxs in edge_to_faces.items():
            if len(f_idxs) == 2:
                if m_src:
                    v1, v2 = edge[0], edge[1]
                    m1 = m_src[v1] if v1 < len(m_src) else False
                    m2 = m_src[v2] if v2 < len(m_src) else False
                    if not (m1 and m2): continue
                
                p1, p2 = v_src[edge[0]], v_src[edge[1]]
                edge_vec = (p2 - p1).normalized()
                cp = (p1 + p2) * 0.5
                d1 = (face_centers[f_idxs[0]] - cp); d1 = (d1 - d1.dot(edge_vec) * edge_vec).normalized()
                d2 = (face_centers[f_idxs[1]] - cp); d2 = (d2 - d2.dot(edge_vec) * edge_vec).normalized()
                res = create_arc_logic(cp, d1, d2, a_size, a_res, c_type, custom_axis=edge_vec)
                if res:
                    g_verts.extend(res['pts']); g_polys.append(res['poly'])
                    angles.append(res['ang']); g_centers.append(res['center'])

    return [v_data], [p_src], [g_centers], [angles], [g_verts], [g_polys]

res_all = run_logic()
verts_out, poly_out, gizmo_centers, angle_data, gizmo_v, gizmo_s = res_all
