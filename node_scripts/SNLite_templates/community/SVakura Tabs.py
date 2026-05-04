"""
in verts v d=[] n=0
in poly s d=[] n=0
in flap_points v d=[] n=0
in flap_ids s d=[] n=0
in tab_size s d=0.1 n=2
in taper_angle s d=30.0 n=2
in gap_size s d=0.0 n=2
in edge_inset s d=0.0 n=2
out tabs_v v
out tabs_p s
"""
import numpy as np
try:
    from shapely.geometry import Polygon, Point
    from shapely.strtree import STRtree
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

def run():
    def deep_unpack(data):
        if not data: return []
        curr = data
        while isinstance(curr, (list, tuple)) and len(curr) > 0:
            if isinstance(curr[0], (list, tuple)):
                if len(curr[0]) > 0 and isinstance(curr[0][0], (float, int)) and not isinstance(curr[0][0], (list, tuple)):
                    return curr
                curr = curr[0]
            else:
                return curr
        return curr

    v_raw = deep_unpack(verts)
    p_raw = deep_unpack(poly)
    fp_raw = deep_unpack(flap_points)
    fi_raw = deep_unpack(flap_ids)
    
    if not v_raw or not p_raw or not HAS_SHAPELY or not fp_raw:
        return [[]], [[]]

    def get_val(v, default=0):
        if isinstance(v, (list, tuple)):
            return get_val(v[0], default) if v else default
        try: return float(v)
        except: return default

    t_size = get_val(tab_size, 0.1)
    taper_rad = np.radians(get_val(taper_angle, 30.0))
    t_gap = get_val(gap_size, 0.0)
    t_inset = get_val(edge_inset, 0.0)

    final_tabs_v, final_tabs_p = [], []
    used_ids = set()
    
    # 1. Оптимизация: Создаем полигоны и дерево коллизий
    face_polys = []
    for face in p_raw:
        coords = [(v_raw[i][0], v_raw[i][1]) for i in face if i < len(v_raw)]
        if len(coords) >= 3:
            face_polys.append(Polygon(coords))
    
    if not face_polys: return [[]], [[]]
    tree = STRtree(face_polys)

    # 2. ГЛАВНОЕ УСКОРЕНИЕ: Хеш-карта ребер
    # Ключ: (x, y) центра ребра, Значение: данные о ребре
    edge_lookup = {}
    for f_idx, face in enumerate(p_raw):
        for i in range(len(face)):
            idx1, idx2 = face[i], face[(i+1)%len(face)]
            if idx1 >= len(v_raw) or idx2 >= len(v_raw): continue
            
            p1, p2 = v_raw[idx1][:2], v_raw[idx2][:2]
            # Округляем до 4 знаков, чтобы избежать проблем с точностью float
            mid_key = (round((p1[0] + p2[0]) * 0.5, 4), 
                       round((p1[1] + p2[1]) * 0.5, 4))
            
            edge_lookup[mid_key] = {
                'f_idx': f_idx, 
                'p1': np.array(p1), 
                'p2': np.array(p2)
            }

    # 3. Быстрая генерация
    tan_taper = np.tan(taper_rad)
    
    for i, f_id in enumerate(fi_raw):
        if isinstance(f_id, (list, tuple)):
            f_id = f_id[0] if f_id else None
        
        h_id = str(f_id)
        if h_id == "0" or h_id in used_ids or i >= len(fp_raw): 
            continue 
        
        # Мгновенный поиск ребра по координатам центра
        target_pt = fp_raw[i]
        target_key = (round(target_pt[0], 4), round(target_pt[1], 4))
        
        edge_data = edge_lookup.get(target_key)
        if not edge_data: continue
        
        p1, p2 = edge_data['p1'], edge_data['p2']
        parent_poly = face_polys[edge_data['f_idx']]
        
        edge_vec = p2 - p1
        length = np.linalg.norm(edge_vec)
        if length < (t_inset * 2.05) or t_size <= 0: continue
        
        unit = edge_vec / length
        perp = np.array([-unit[1], unit[0]])
        
        # Проверка ориентации
        if parent_poly.contains(Point((p1 + p2) * 0.5 + perp * (t_size * 0.1))):
            perp = -perp
            
        p1_b, p2_b = p1 + unit * t_inset + perp * t_gap, p2 - unit * t_inset + perp * t_gap
        t_off = min(t_size * tan_taper, (length - 2*t_inset) * 0.4)
        p3, p4 = p2_b - unit * t_off + perp * t_size, p1_b + unit * t_off + perp * t_size
        
        try:
            tab_poly = Polygon([p1_b, p2_b, p3, p4])
            if not tab_poly.is_valid: continue
            
            # Быстрая проверка пересечений через дерево
            hits = tree.query(tab_poly)
            clean_tab = tab_poly
            for h_idx in hits:
                neighbor = face_polys[h_idx] if isinstance(h_idx, (int, np.integer)) else h_idx
                if neighbor == parent_poly: continue
                if clean_tab.intersects(neighbor):
                    clean_tab = clean_tab.difference(neighbor.buffer(1e-6))
            
            if not clean_tab.is_empty:
                used_ids.add(h_id)
                for part in (clean_tab.geoms if hasattr(clean_tab, 'geoms') else [clean_tab]):
                    if isinstance(part, Polygon):
                        coords = list(part.exterior.coords)[:-1]
                        start_idx = len(final_tabs_v)
                        for c in coords: final_tabs_v.append([c[0], c[1], 0.0])
                        final_tabs_p.append(list(range(start_idx, start_idx + len(coords)))[::-1])
        except: continue

    return [final_tabs_v], [final_tabs_p]

tabs_v, tabs_p = run()