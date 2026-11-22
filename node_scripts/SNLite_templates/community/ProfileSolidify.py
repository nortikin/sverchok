"""
in verts v d=[] n=0
in faces s d=[] n=0
in thickness s d=0.1 n=2
in offset s d=0.0 n=2
in loops s d=2 n=2
in bulge s d=0.02 n=2
in profile_type s d=0 n=2
in curve_vals s d=[] n=0
out verts_out v
out faces_out s
"""

# @Johanntelemann author

import bpy
import bmesh
import math
from mathutils import Vector

def profile_value(t, kind=0):
    kind = int(kind)
    if kind == 0: return math.sin(math.pi * t)
    if kind == 1: return 1.0 - abs(2.0 * t - 1.0)
    if kind == 2:
        s = 1.0 - abs(2.0 * t - 1.0)
        return s * s * (3.0 - 2.0 * s)
    if kind == 3: return 1.0
    return 0.0

def evaluate_curve(curve, t):
    if not curve: return 0.0
    if len(curve) == 1: return curve[0]
    pos = t * (len(curve) - 1)
    idx0 = int(math.floor(pos))
    idx1 = min(idx0 + 1, len(curve) - 1)
    frac = pos - idx0
    return curve[idx0] * (1.0 - frac) + curve[idx1] * frac

def solidify_bm(bm, thickness, offset, loops, bulge, profile_type, curve_vals):
    if abs(thickness) < 1e-9: return

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    
    orig_verts = set(bm.verts)
    orig_faces = list(bm.faces)

    shift = (offset + 1.0) * 0.5 * thickness
    if shift != 0.0:
        for v in orig_verts: v.co += v.normal * shift
        bm.normal_update()

    bmesh.ops.solidify(bm, geom=orig_faces, thickness=thickness)
    bm.normal_update()

    if loops <= 0: return

    rim_faces = []
    for f in bm.faces:
        if f in orig_faces or len(f.loops) != 4: continue
        types = ['O' if v in orig_verts else 'F' for v in f.verts]
        if 0 < types.count('O') < 4: rim_faces.append(f)

    if not rim_faces: return

    rim_data = []
    cross_edge_normals = {}

    for f in rim_faces:
        f.normal_update()
        
        ordered = [loop.vert for loop in f.loops]
        types = ['O' if v in orig_verts else 'F' for v in ordered]
        s = ''.join(types)
        idx = (s + s).find('OO')
        if idx < 0 or idx >= 4: continue
        ordered = ordered[idx:] + ordered[:idx]
        if types != ['O', 'O', 'F', 'F']: continue

        orig_v0, orig_v1, off_v0, off_v1 = ordered
        normal = f.normal.copy()
        rim_data.append((orig_v0, orig_v1, off_v0, off_v1))

        for pair in ((orig_v0, off_v1), (orig_v1, off_v0)):
            rev_pair = (pair[1], pair[0])
            if pair in cross_edge_normals: cross_edge_normals[pair] += normal
            elif rev_pair in cross_edge_normals: cross_edge_normals[rev_pair] += normal
            else: cross_edge_normals[pair] = normal.copy()

    for k, n in cross_edge_normals.items():
        if n.length > 1e-9: n.normalize()

    bmesh.ops.delete(bm, geom=rim_faces, context='FACES')

    N = int(loops) + 1
    intermediate = {}

    def get_mid(orig_v, off_v, i):
        key1, key2 = (orig_v, off_v, i), (off_v, orig_v, i)
        v = intermediate.get(key1) or intermediate.get(key2)
        if v: return v
            
        t = i / N
        
        if curve_vals and len(curve_vals) > 1:
            p_val = evaluate_curve(curve_vals, t)
        else:
            p_val = profile_value(t, profile_type)

        v = bm.verts.new(orig_v.co.lerp(off_v.co, t))
        if bulge != 0.0:
            n = cross_edge_normals.get((orig_v, off_v)) or cross_edge_normals.get((off_v, orig_v))
            if n: v.co += n * (bulge * p_val)
        
        intermediate[key1] = v
        return v

    for orig_v0, orig_v1, off_v0, off_v1 in rim_data:
        a_o, a_f = orig_v0, off_v1
        b_o, b_f = orig_v1, off_v0
        for i in range(N):
            a0 = a_o if i == 0 else get_mid(a_o, a_f, i)
            b0 = b_o if i == 0 else get_mid(b_o, b_f, i)
            a1 = a_f if i == N - 1 else get_mid(a_o, a_f, i + 1)
            b1 = b_f if i == N - 1 else get_mid(b_o, b_f, i + 1)
            try: bm.faces.new((a0, b0, b1, a1))
            except ValueError: pass

# ==========================================
# Обвязка для Sverchok
# ==========================================
out_v, out_f = [], []

def get_scalar(val, index, default=0.0):
    if isinstance(val, (int, float)): return val
    if isinstance(val, (list, tuple)):
        if not val: return default
        v1 = val[index] if index < len(val) else val[0]
        if isinstance(v1, (int, float)): return v1
        if isinstance(v1, (list, tuple)) and len(v1) > 0: return v1[0] 
    return default

def flatten_list(lst):
    res = []
    for item in lst:
        if isinstance(item, (list, tuple)):
            res.extend(flatten_list(item))
        elif isinstance(item, (int, float)):
            res.append(float(item))
    return res

def get_list(val, index):
    # Если пришло просто одно число (не список)
    if isinstance(val, (int, float)):
        return [float(val)]
    # Если пришел список любой вложенности
    if isinstance(val, (list, tuple)):
        return flatten_list(val)
    return []

if not verts: verts = []

for i, in_v in enumerate(verts):
    in_f = faces[i] if isinstance(faces, (list, tuple)) and i < len(faces) else []

    th = get_scalar(thickness, i, 0.1)
    off = get_scalar(offset, i, 0.0)
    lp = int(get_scalar(loops, i, 2))
    blg = get_scalar(bulge, i, 0.02)
    p_type = int(get_scalar(profile_type, i, 0))
    
    c_vals = get_list(curve_vals, i)
    
    # --- ДЕБАГ ВЫВОД ---
    if i == 0: 
        print("SVERCHOK DEBUG RAW:", curve_vals)
        print("SVERCHOK DEBUG Parsed:", c_vals)
    # -------------------

    if not in_v: 
        out_v.append([])
        out_f.append([])
        continue

    bm = bmesh.new()
    bm_verts = [bm.verts.new(co) for co in in_v]
    bm.verts.ensure_lookup_table()

    for f in in_f:
        try: bm.faces.new([bm_verts[idx] for idx in f])
        except ValueError: pass 

    solidify_bm(bm, th, off, lp, blg, p_type, c_vals)

    bm.verts.index_update()
    bm.faces.index_update()

    out_v.append([v.co[:] for v in bm.verts])
    out_f.append([[v.index for v in f.verts] for f in bm.faces])
    bm.free()

verts_out = out_v
faces_out = out_f
