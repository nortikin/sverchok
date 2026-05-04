"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in focal_pt v d=[(0,0,10)] n=0
enum = Perspective Parallel Top Front Side
out v_out v
out p_out s
# Узел: PF Projector С (@il_de_signer)
"""

import numpy as np
import bpy
from shapely import polygons as sh_polygons, union_all, make_valid
from shapely.geometry import MultiPolygon, Polygon

def ui(self, context, layout):
    # ОФОРМЛЕНИЕ
    layout.label(text="Projection logic", icon='MOD_DYNAMICPAINT')
    
    col = layout.column(align=True)
    row1 = col.row(align=True)
    row1.prop_enum(self, "custom_enum", "Perspective")
    row1.prop_enum(self, "custom_enum", "Parallel")
    row2 = col.row(align=True)
    row2.prop_enum(self, "custom_enum", "Top")
    row2.prop_enum(self, "custom_enum", "Front")
    row2.prop_enum(self, "custom_enum", "Side")
    
    layout.separator()
    
    # Инфо-блок
    box = layout.box()
    mode = self.custom_enum
    if mode == 'Perspective':
        box.label(text="Style: Point Shadow", icon='LIGHT_POINT')
    elif mode == 'Parallel':
        box.label(text="Style: Directional Sun", icon='LIGHT_SUN')
    elif mode == 'Top':
        box.label(text="Plane: XY", icon='AXIS_TOP')
    elif mode == 'Front':
        box.label(text="Plane: XZ", icon='AXIS_FRONT')
    elif mode == 'Side':
        box.label(text="Plane: YZ", icon='AXIS_SIDE')

def unwrap_point(val, default=(0, 0, 10)):
    try:
        while isinstance(val, (list, tuple)) and len(val) > 0:
            if not isinstance(val[0], (list, tuple, np.ndarray)): break
            val = val[0]
        if len(val) >= 3: return np.array([float(val[0]), float(val[1]), float(val[2])])
        elif len(val) == 2: return np.array([float(val[0]), float(val[1]), 0.0])
    except: pass
    return np.array(default)

def run():
    if not verts_in or not poly_in:
        return [[]], [[]]

    # 1. Распаковка
    v_raw = verts_in[0] if isinstance(verts_in[0][0], (list, tuple, np.ndarray)) else verts_in
    p_raw = poly_in[0] if isinstance(poly_in[0][0], (list, tuple, int)) else poly_in
    f_p = unwrap_point(focal_pt)
    v_np = np.array(v_raw)
    
    if v_np.shape[1] == 2:
        v_np = np.column_stack([v_np, np.zeros(len(v_np))])
    
    mode_map = {'Perspective': 0, 'Parallel': 1, 'Top': 2, 'Front': 3, 'Side': 4}
    m_idx = mode_map.get(self.custom_enum, 2)
    plane_z = 0.0

    # 2. Проекция
    if m_idx == 0:
        rays = v_np - f_p
        denom = np.where(np.abs(rays[:, 2]) < 1e-10, 1e-10, rays[:, 2])
        t = (plane_z - f_p[2]) / denom
        local_v = (f_p + rays * t[:, np.newaxis])[:, :2]
    elif m_idx == 1:
        l_dir = f_p / (np.linalg.norm(f_p) + 1e-10)
        denom = l_dir[2] if abs(l_dir[2]) > 1e-10 else -1e-10
        t = (plane_z - v_np[:, 2]) / denom
        local_v = (v_np + t[:, np.newaxis] * l_dir)[:, :2]
    elif m_idx == 2: local_v = v_np[:, [0, 1]]
    elif m_idx == 3: local_v = v_np[:, [0, 2]]
    elif m_idx == 4: local_v = v_np[:, [1, 2]]

    # 3. Слияние
    face_groups = {}
    for face in p_raw:
        n = len(face)
        if n >= 3: face_groups.setdefault(n, []).append(face)

    all_polys = []
    for n, group in face_groups.items():
        coords = local_v[np.array(group)]
        all_polys.append(make_valid(sh_polygons(coords)))

    if not all_polys: return [[]], [[]]
    polys_arr = np.concatenate(all_polys)

    try:
        merged = union_all(polys_arr)
    except:
        merged = union_all(make_valid(polys_arr))

    final_islands = []
    if hasattr(merged, 'geoms'):
        for g in merged.geoms:
            if g.geom_type in ('Polygon', 'MultiPolygon') and not g.is_empty:
                if isinstance(g, MultiPolygon): final_islands.extend(g.geoms)
                else: final_islands.append(g)
    else:
        if merged.geom_type == 'Polygon': final_islands = [merged]
        elif merged.geom_type == 'MultiPolygon': final_islands = list(merged.geoms)

    # 4. Сборка
    res_v, res_p, v_off = [], [], 0
    for island in final_islands:
        if island.area < 1e-8: continue
        for ring in [island.exterior] + list(island.interiors):
            ext = np.array(ring.coords[:-1]); n = len(ext)
            if m_idx in (0, 1, 2): xyz = np.column_stack([ext, np.full(n, plane_z)])
            elif m_idx == 3:       xyz = np.column_stack([ext[:,0], np.full(n, plane_z), ext[:,1]])
            else:                  xyz = np.column_stack([np.full(n, plane_z), ext[:,0], ext[:,1]])
            res_v.append(xyz)
            res_p.append(list(range(v_off, v_off + n)))
            v_off += n

    out_v = np.vstack(res_v).tolist() if res_v else []
    return [out_v], [res_p]

v_out, p_out = run()