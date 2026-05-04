"""
in verts_in v
in faces_in s
in face_index1 s d=0 n=2
in face_index2 s d=1 n=2
in twist s d=0 n=2
in reverse s d=0 n=2
in segments s d=1 n=2
out verts_out v
out faces_out s
# Bridge maker @Johanntelemann
"""


import bmesh
from mathutils import Vector
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh

def to_int(val, default=0):
    if val is None: return default
    if isinstance(val, (int, float)): return int(val)
    if isinstance(val, (list, tuple)) and len(val) > 0: return int(val[0])
    return default

def get_first_mesh(verts_in, faces_in):
    if not verts_in or not faces_in:
        return None, None
    if isinstance(verts_in[0], (list, tuple)) and len(verts_in[0]) == 3 and isinstance(verts_in[0][0], (int, float)):
        return verts_in, faces_in
    if isinstance(verts_in[0], list) and isinstance(faces_in[0], list):
        return verts_in[0], faces_in[0]
    return None, None

# === Основной код ===
verts_out = [[]]
faces_out = [[]]

V, F = get_first_mesh(verts_in, faces_in)
if not V or not F:
    pass
else:
    idx1 = to_int(face_index1, 0)
    idx2 = to_int(face_index2, 1)
    tw = to_int(twist, 0)
    rev = to_int(reverse, 0)
    segs = max(1, to_int(segments, 1))

    if idx1 < 0 or idx1 >= len(F) or idx2 < 0 or idx2 >= len(F) or idx1 == idx2:
        pass
    else:
        bm = bmesh.new()
        bm_verts = [bm.verts.new(co) for co in V]
        bm.verts.ensure_lookup_table()
        for face in F:
            try:
                bm.faces.new([bm_verts[i] for i in face])
            except:
                pass
        bm.faces.ensure_lookup_table()

        if idx1 < len(bm.faces) and idx2 < len(bm.faces):
            f1 = bm.faces[idx1]
            f2 = bm.faces[idx2]

            # Получаем вершины в порядке обхода
            loop1 = list(f1.verts)
            loop2 = list(f2.verts)

            # Применяем reverse и twist к первому циклу
            if rev:
                loop1.reverse()
            if tw:
                tw = tw % len(loop1)
                loop1 = loop1[tw:] + loop1[:tw]

            # Удаляем исходные грани
            bm.faces.remove(f1)
            bm.faces.remove(f2)
            bm.faces.ensure_lookup_table()
            bm.edges.ensure_lookup_table()

            # Количество вершин в циклах должно совпадать
            if len(loop1) != len(loop2):
                # Если не совпадает, можно попробовать адаптировать, но пока пропускаем
                pass
            else:
                n = len(loop1)

                # Создаём промежуточные кольца вершин для сегментации
                rings = []
                # Исходные вершины первого кольца
                rings.append(loop1)
                # Промежуточные кольца
                for s in range(1, segs):
                    t = s / segs
                    ring = []
                    for j in range(n):
                        # Линейная интерполяция между соответствующими вершинами
                        v1 = loop1[j].co
                        v2 = loop2[j].co
                        ring.append(bm.verts.new(v1.lerp(v2, t)))
                    rings.append(ring)
                # Последнее кольцо
                rings.append(loop2)

                # Строим грани между кольцами
                for s in range(len(rings)-1):
                    A = rings[s]
                    B = rings[s+1]
                    for j in range(n):
                        j2 = (j+1) % n
                        try:
                            bm.faces.new([A[j], A[j2], B[j2], B[j]])
                        except ValueError:
                            pass  # грань уже существует

                # Создаём рёбра для первого и последнего кольца, чтобы они оставались замкнутыми (на случай, если нужны рёбра)
                # Но это не обязательно, т.к. грани уже всё соединили.

            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            v_out, _, f_out = pydata_from_bmesh(bm)
            bm.free()


            if v_out:
                verts_out = [v_out]
                faces_out = [f_out] if f_out else [[]]
