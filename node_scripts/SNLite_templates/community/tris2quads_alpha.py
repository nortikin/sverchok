"""
in verts_in v
in faces_in s
in max_angle s d=40 n=2
out verts_out v
out faces_out s
# tris to quads (324) alpha @Johanntelemann
"""

import bmesh
from math import radians

def get_first_mesh(verts_input, faces_input):
    if not verts_input or not faces_input:
        return None, None
    if isinstance(verts_input[0], (list, tuple)) and len(verts_input[0]) == 3 and isinstance(verts_input[0][0], (int, float)):
        return verts_input, faces_input
    if isinstance(verts_input[0], list) and isinstance(faces_input[0], list):
        return verts_input[0], faces_input[0]
    return None, None

def to_float(val, default=0.0):
    if val is None: return default
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, (list, tuple)):
        if len(val) > 0: return float(val[0])
    return default

V, F = get_first_mesh(verts_in, faces_in)
if not V or not F:
    verts_out, faces_out = [], []
else:
    max_ang = to_float(max_angle, 40.0)
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

    # Собираем всех кандидатов
    candidates_all = []
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            continue
        f1, f2 = edge.link_faces
        if len(f1.verts) != 3 or len(f2.verts) != 3:
            continue
        candidates_all.append(edge)

    # Вычисляем максимальный и средний угол (для информации)
    angles_all = []
    for edge in candidates_all:
        f1, f2 = edge.link_faces
        n1, n2 = f1.normal, f2.normal
        if n1.length < 1e-6 or n2.length < 1e-6:
            angles_all.append(0.0)
        else:
            angles_all.append(n1.angle(n2))
    if angles_all:
        print(f"DEBUG: max angle = {max(angles_all):.2f} rad ({max(angles_all)*180.0/3.14159:.1f}°), "
              f"avg angle = {sum(angles_all)/len(angles_all):.2f} rad")
    
    # Применяем фильтр угла, только если max_angle > 0
    candidates = []
    if max_ang > 0:
        max_angle_rad = radians(max_ang)
        for edge, ang in zip(candidates_all, angles_all):
            if ang <= max_angle_rad:
                candidates.append(edge)
    else:
        # Если max_angle = 0 – фильтр отключён
        candidates = candidates_all

    print(f"DEBUG: Всего кандидатов: {len(candidates_all)}, после фильтра по углу: {len(candidates)}")

    # Жадное растворение (как в mode=1)
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

        print(f"DEBUG: Растворено рёбер: {len(dissolved)}")

        if dissolved:
            bmesh.ops.dissolve_edges(bm, edges=list(dissolved), use_verts=False, use_face_split=False)

    bm.verts.index_update()
    bm.faces.index_update()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    verts_out = [[v.co[:] for v in bm.verts]]
    faces_out = [[[v.index for v in f.verts] for f in bm.faces]]
    bm.free()
