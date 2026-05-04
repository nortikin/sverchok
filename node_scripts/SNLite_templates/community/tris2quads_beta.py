"""
in verts_in v
in faces_in s
in max_angle s d=0 n=2
in max_shape_angle s d=0 n=2
in aspect_ratio s d=0 n=2
out verts_out v
out faces_out s
# tris to quads beta @Johanntelemann
"""

import bmesh
from math import radians, pi
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh

def get_first_mesh(verts_input, faces_input):
    if not verts_input or not faces_input:
        return None, None
    if isinstance(verts_input[0], (list, tuple)) and len(verts_input[0]) == 3 and isinstance(verts_input[0][0], (int, float)):
        return verts_input, faces_input
    if isinstance(verts_input[0], list) and isinstance(faces_input[0], list):
        return verts_input[0], faces_input[0]
    return None, None

def to_int(val, default=0):
    if val is None: return default
    if isinstance(val, (int, float)): return int(val)
    if isinstance(val, (list, tuple)):
        if len(val) > 0: return int(val[0])
    return default

def quad_quality(verts, max_angle, ratio_limit):
    if len(verts) != 4:
        return False
    if max_angle > 0:
        for i in range(4):
            a = verts[i].co
            b = verts[(i+1)%4].co
            c = verts[(i+2)%4].co
            v1 = a - b
            v2 = c - b
            if v1.length < 1e-6 or v2.length < 1e-6:
                return False
            ang = v1.angle(v2)
            if abs(ang - pi/2) > radians(max_angle):
                return False
    if ratio_limit > 0:
        d1 = (verts[0].co - verts[2].co).length
        d2 = (verts[1].co - verts[3].co).length
        if d1 > 0 and d2 > 0:
            ratio = max(d1, d2) / min(d1, d2)
            if ratio > ratio_limit:
                return False
    return True

V, F = get_first_mesh(verts_in, faces_in)
if not V or not F:
    verts_out, faces_out = [], []
else:
    # Получаем целые значения и преобразуем в дробные
    max_angle_int = to_int(max_angle, 0)          # градусы, 0..180
    shape_int = to_int(max_shape_angle, 0)        # 0..180 (градусы, шаг 1°)
    ratio_int = to_int(aspect_ratio, 0)           # 0..100 (соотношение * 10)
    
    max_angle_deg = max_angle_int * 1.0           # уже в градусах
    max_shape_deg = shape_int * 1.0               # градусы
    aspect_ratio_val = ratio_int / 10.0           # преобразуем обратно в дробное

    bm = bmesh.new()
    bm_verts = [bm.verts.new(co) for co in V]
    bm.verts.ensure_lookup_table()
    for face in F:
        try:
            bm.faces.new([bm_verts[i] for i in face])
        except:
            pass
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.normal_update()

    # Собираем всех кандидатов
    candidates_all = []
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        f1, f2 = edge.link_faces
        if len(f1.verts) != 3 or len(f2.verts) != 3:
            continue
        candidates_all.append(edge)

    # 1. Фильтр по углу между нормалями (max_angle)
    candidates = []
    if max_angle_deg > 0:
        angle_limit = radians(max_angle_deg)
        for edge in candidates_all:
            n1, n2 = edge.link_faces[0].normal, edge.link_faces[1].normal
            if n1.length < 1e-6 or n2.length < 1e-6:
                continue
            if n1.angle(n2) <= angle_limit:
                candidates.append(edge)
    else:
        candidates = candidates_all


    # 2. Фильтр по форме (только если задан хотя бы один из параметров)
    if candidates and (max_shape_deg > 0 or aspect_ratio_val > 0):
        filtered = []
        for edge in candidates:
            f1, f2 = edge.link_faces
            merged_verts = set()
            for v in f1.verts: merged_verts.add(v.index)
            for v in f2.verts: merged_verts.add(v.index)
            if len(merged_verts) != 4:
                continue
            verts_4 = []
            for v in f1.verts:
                if v.index in merged_verts and v not in verts_4:
                    verts_4.append(v)
            for v in f2.verts:
                if v.index in merged_verts and v not in verts_4:
                    verts_4.append(v)
            if len(verts_4) != 4:
                continue
            if quad_quality(verts_4, max_shape_deg, aspect_ratio_val):
                filtered.append(edge)
        candidates = filtered

    # Жадное растворение
    if candidates:
        candidates.sort(key=lambda e: e.calc_length(), reverse=True)
        dissolved = set()
        processed_tris = set()
        for e in candidates:
            f1, f2 = e.link_faces
            if f1 in processed_tris or f2 in processed_tris:
                continue
            dissolved.add(e)
            processed_tris.add(f1)
            processed_tris.add(f2)
        if dissolved:
            bmesh.ops.dissolve_edges(bm, edges=list(dissolved), use_verts=False, use_face_split=False)

    bm.verts.index_update()
    bm.faces.index_update()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    v_out, _, f_out = pydata_from_bmesh(bm)
    bm.free()

    verts_out = [v_out] if v_out else []
    faces_out = [f_out] if f_out else []
