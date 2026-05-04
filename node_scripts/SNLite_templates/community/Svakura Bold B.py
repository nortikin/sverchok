"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in mode s d=0 n=2
in seed s d=0 n=2
in limit_angle s d=60.0 n=2
in tab_size s d=0.1 n=2
in taper_angle s d=30.0 n=2
in gap_size s d=0.00 n=2
in edge_inset s d=0.00 n=2
in use_original_ids s d=1 n=2
in index_all_edges s d=1 n=2
in unfold_factor s d=1.0 n=2
in position_factor s d=0.0 n=2
in gap s d=1.0 n=2
out verts_out v
out poly_out s
out tabs_v v
out tabs_p s
out flap_points v
out flap_ids s
"""

import numpy as np
from mathutils import Vector, Matrix, geometry
import math
import random
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

def run():
    # 1. Проверка входов
    if not verts_in or not poly_in:
        return [[]], [[]], [[]], [[]], [[]], [[]]

    def ensure_nesting(data):
        if not data: return []
        if isinstance(data, (list, tuple)) and len(data) > 0:
            if not isinstance(data[0], (list, tuple, Vector)): return [data]
        return data

    v_objects = ensure_nesting(verts_in)
    p_objects = ensure_nesting(poly_in)
    
    final_verts, final_polys = [], []
    final_tabs_v, final_tabs_p = [], []
    flap_pts_all, flap_ids_all = [], []
    
    # Реестр
    used_tabs_global = set()

    # Сохраняем переменные
    m_val, ang_lim, s_val, g_val, t_val, u_orig, i_all, unfold, pos, tap_ang, g_sz, e_ins = mode, limit_angle, seed, gap, tab_size, use_original_ids, index_all_edges, unfold_factor, position_factor, taper_angle, gap_size, edge_inset
    dist_gap = float(g_val)
    m_type = int(m_val)
    use_original = int(u_orig) == 1
    index_all = int(i_all) == 1
    cos_threshold = math.cos(math.radians(float(ang_lim)))
    current_x_offset = 0.0
    t_size = float(t_val)
    unfold_val = float(unfold)  # 0 - свернуто, 1 - развернуто
    position_val = float(pos)    # 0 - в ряд, 1 - в позиции исходной модели
    
    # Новые параметры для ушек
    taper_rad = np.radians(float(tap_ang))
    t_gap = float(g_sz)
    t_inset = float(e_ins)

    global_edge_pairs = {}
    next_global_id = 1

    def is_overlapping(new_poly, placed_polys):
        for placed in placed_polys:
            for i in range(len(new_poly)):
                a, b = new_poly[i].xy, new_poly[(i+1)%len(new_poly)].xy
                for j in range(len(placed)):
                    c, d = placed[j].xy, placed[(j+1)%len(placed)].xy
                    if (a-c).length < 1e-4 or (a-d).length < 1e-4 or (b-c).length < 1e-4 or (b-d).length < 1e-4:
                        continue
                    if geometry.intersect_line_line_2d(a, b, c, d): return True
        return False

    for obj_idx in range(len(v_objects)):
        v_raw, p_raw = v_objects[obj_idx], p_objects[obj_idx] if obj_idx < len(p_objects) else []
        if not p_raw: continue
        
        v_orig = [Vector(v[:3]) for v in v_raw]
        
        # СОХРАНЯЕМ ИСХОДНЫЕ ПОЗИЦИИ ВЕРШИН ДЛЯ КАЖДОЙ ГРАНИ
        original_face_verts = []
        for face in p_raw:
            face_verts = [v_orig[i].copy() for i in face]
            original_face_verts.append(face_verts)
        
        edge_to_faces, edge_id_map, edge_original_id = {}, {}, {}
        next_edge_id, edge_counter, f_normals = 1, 0, []

        for f_idx, face in enumerate(p_raw):
            pts = [v_orig[i] for i in face]
            n = Vector((0,0,0))
            for i in range(len(pts)): n += pts[i-1].cross(pts[i])
            f_normals.append(n.normalized() if n.length > 1e-8 else Vector((0,0,1)))
            for i in range(len(face)):
                e = tuple(sorted([face[i], face[(i+1)%len(face)]]))
                if e not in edge_to_faces:
                    edge_counter += 1
                    edge_original_id[e] = edge_counter
                edge_to_faces.setdefault(e, []).append(f_idx)
        
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

        adj, rng = {}, random.Random(int(s_val))
        for e, f_idxs in edge_to_faces.items():
            if len(f_idxs) == 2:
                f1, f2 = f_idxs
                if f_normals[f1].dot(f_normals[f2]) >= cos_threshold:
                    w = rng.random()
                    adj.setdefault(f1, []).append((f2, e, w))
                    adj.setdefault(f2, []).append((f1, e, w))

        visited = set()
        
        # Словарь для хранения связей родитель-потомок и матриц трансформации между гранями
        edge_transforms = {}  # (parent_idx, child_idx) -> transform matrix
        
        for start_f in range(len(p_raw)):
            if start_f in visited: continue
            island_coords, island_faces, used_edges_2d = {start_f: []}, [start_f], set()
            f0 = p_raw[start_f]
            rot = f_normals[start_f].rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()
            island_coords[start_f] = [rot @ (v_orig[i] - v_orig[f0[0]]) for i in f0]
            visited.add(start_f)
            
            queue = []
            def add_to_q(f_idx):
                if f_idx not in adj: return
                for nei, e, w in adj[f_idx]:
                    if nei in visited: continue
                    prio = w
                    if m_type == 1: prio -= len(island_faces) * 2.0
                    queue.append((prio, f_idx, nei, e))

            add_to_q(start_f)
            while queue:
                queue.sort(key=lambda x: x[0], reverse=True)
                _, p_idx, c_idx, edge_v = queue.pop(0)
                if c_idx in visited: continue
                
                p_face, c_face, p_2d = p_raw[p_idx], p_raw[c_idx], island_coords[p_idx]
                v1, v2 = edge_v
                p1_2d, p2_2d = p_2d[p_face.index(v1)], p_2d[p_face.index(v2)]
                p1_3d, p2_3d = v_orig[v1], v_orig[v2]
                axis = (p2_3d - p1_3d).normalized()
                y_p = f_normals[p_idx].cross(axis).normalized()
                ang = math.atan2(f_normals[c_idx].dot(y_p), f_normals[c_idx].dot(f_normals[p_idx]))
                m_3d = Matrix((axis, y_p, f_normals[p_idx])).transposed().to_4x4()
                ax2d = (p2_2d - p1_2d).normalized()
                m_2d = Matrix((ax2d, Vector((0,0,1)).cross(ax2d).normalized(), Vector((0,0,1)))).transposed().to_4x4()
                m_final = Matrix.Translation(p1_2d) @ m_2d @ m_3d.inverted() @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-p1_3d)
                new_c = [m_final @ v_orig[idx] for idx in c_face]
                
                # Сохраняем матрицу трансформации для этого ребра
                edge_transforms[(p_idx, c_idx)] = m_final
                
                if not is_overlapping(new_c, list(island_coords.values())):
                    island_coords[c_idx] = new_c
                    island_faces.append(c_idx); visited.add(c_idx)
                    used_edges_2d.add(edge_v)
                    add_to_q(c_idx)

            iv, ip, i_ptr = [], [], 0
            tv, tp, t_ptr = [], [], 0
            flat_pts = [p for f in island_coords.values() for p in f]
            if not flat_pts: continue
            min_x, max_x = min(p.x for p in flat_pts), max(p.x for p in flat_pts)
            shift = Vector((current_x_offset - min_x, 0, 0))
            
            # Сдвигаем все плоские координаты для размещения в ряд
            shifted_coords = {}
            for f_idx, coords in island_coords.items():
                shifted_coords[f_idx] = [c + shift for c in coords]
            
            # ПРИМЕНЯЕМ СВОРАЧИВАНИЕ С УЧЕТОМ ТОПОЛОГИИ
            if unfold_val < 1.0:
                # Сначала находим корневые грани (те, которые были развернуты первыми)
                # В очереди построения первая грань - start_f
                root_faces = [start_f]
                
                # Строим дерево зависимостей
                children_of = {}
                for (p, c) in edge_transforms.keys():
                    if p not in children_of:
                        children_of[p] = []
                    children_of[p].append(c)
                
                # Функция для применения трансформаций с учетом unfold_factor
                def apply_fold_transforms(face_idx, current_transform, processed):
                    if face_idx in processed:
                        return
                    processed.add(face_idx)
                    
                    # Применяем текущую трансформацию к вершинам грани
                    flat_verts = shifted_coords[face_idx]
                    
                    # Для всех вершин грани применяем трансформацию
                    transformed = [current_transform @ v for v in flat_verts]
                    
                    # Сохраняем результат
                    island_coords[face_idx] = transformed
                    
                    # Обрабатываем детей
                    if face_idx in children_of:
                        for child_idx in children_of[face_idx]:
                            if (face_idx, child_idx) in edge_transforms:
                                # Получаем матрицу трансформации для этого ребра
                                edge_mat = edge_transforms[(face_idx, child_idx)]
                                
                                # Вычисляем угол между нормалями в исходной модели
                                normal_parent = f_normals[face_idx]
                                normal_child = f_normals[child_idx]
                                
                                dot_product = normal_parent.dot(normal_child)
                                total_angle = math.acos(max(-1, min(1, dot_product)))
                                
                                # Определяем направление вращения
                                v1_idx, v2_idx = None, None
                                for e, faces in edge_to_faces.items():
                                    if len(faces) == 2 and face_idx in faces and child_idx in faces:
                                        v1_idx, v2_idx = e
                                        break
                                
                                if v1_idx is not None:
                                    v1_orig = v_orig[v1_idx]
                                    v2_orig = v_orig[v2_idx]
                                    axis_orig = (v2_orig - v1_orig).normalized()
                                    cross_prod = normal_parent.cross(normal_child)
                                    sign = 1 if cross_prod.dot(axis_orig) > 0 else -1
                                    
                                    # Вычисляем текущий угол сворачивания
                                    current_angle = total_angle * (1 - unfold_val) * sign
                                    
                                    # Получаем вершины ребра в плоской развертке
                                    p_face = p_raw[face_idx]
                                    c_face = p_raw[child_idx]
                                    
                                    parent_v1_idx = p_face.index(v1_idx) if v1_idx in p_face else p_face.index(v2_idx)
                                    parent_v2_idx = p_face.index(v2_idx) if v2_idx in p_face else p_face.index(v1_idx)
                                    
                                    p1_flat = flat_verts[parent_v1_idx]
                                    p2_flat = flat_verts[parent_v2_idx]
                                    
                                    # Центр ребра
                                    edge_center_flat = (p1_flat + p2_flat) / 2
                                    
                                    # Ось вращения в плоском пространстве
                                    axis_flat = (p2_flat - p1_flat).normalized()
                                    
                                    # Создаем матрицу вращения для этого ребра с учетом unfold_factor
                                    rot_matrix = Matrix.Rotation(current_angle, 4, axis_flat)
                                    
                                    # Матрица трансформации для ребенка относительно родителя
                                    child_rel_transform = Matrix.Translation(edge_center_flat) @ rot_matrix @ Matrix.Translation(-edge_center_flat)
                                    
                                    # Комбинируем с текущей трансформацией родителя
                                    child_transform = current_transform @ child_rel_transform
                                    
                                    # Рекурсивно обрабатываем ребенка
                                    apply_fold_transforms(child_idx, child_transform, processed)
                    
                # Применяем сворачивание для всех корневых граней
                processed_faces = set()
                for root_f in root_faces:
                    apply_fold_transforms(root_f, Matrix.Identity(4), processed_faces)
            
            else:
                # Если unfold_val >= 1.0, используем сдвинутые плоские координаты
                island_coords = shifted_coords
            
            # Временное хранение координат для интерполяции с position_factor
            final_island_coords = {}
            
            # ПРИМЕНЯЕМ ПОЗИЦИОНИРОВАНИЕ (работаем только с position_factor)
            for f_idx in island_faces:
                face = p_raw[f_idx]
                # Берем исходные мировые координаты грани из v_orig
                world_coords = [v_orig[idx].copy() for idx in face]
                # Текущие координаты (разложенные в ряд)
                current_coords = island_coords[f_idx]
                
                # Интерполяция между мировыми и разложенными координатами
                if position_val == 0:
                    final_island_coords[f_idx] = current_coords
                elif position_val == 1:
                    final_island_coords[f_idx] = world_coords
                else:
                    blended = []
                    for i in range(len(current_coords)):
                        # Линейная интерполяция
                        blended.append(current_coords[i] * (1 - position_val) + world_coords[i] * position_val)
                    final_island_coords[f_idx] = blended
            
            # Собираем финальную геометрию
            for f_idx in island_faces:
                face = p_raw[f_idx]
                pts = final_island_coords[f_idx]
                
                iv.extend([p[:] for p in pts])
                ip.append(list(range(i_ptr, i_ptr + len(pts))))
                i_ptr += len(pts)
                
                # Собираем все точки для flap_pts (как было)
                for i in range(len(face)):
                    v_a, v_b = face[i], face[(i+1)%len(face)]
                    e_key = tuple(sorted([v_a, v_b]))
                    p_a, p_b = pts[i], pts[(i+1)%len(pts)]
                    
                    e_id = edge_id_map.get(e_key)
                    if e_id is not None:
                        mid = (p_a + p_b) / 2
                        flap_pts_all.append([mid.x, mid.y, mid.z])
                        flap_ids_all.append(str(e_id))
            
            # ===== НОВЫЙ БЛОК ГЕНЕРАЦИИ УШЕК С ПАРАМЕТРАМИ =====
            # Создаем единый полигон модели из текущего острова
            face_polys = []
            for f_idx in island_faces:
                face = p_raw[f_idx]
                coords = [(final_island_coords[f_idx][i][0], final_island_coords[f_idx][i][1]) for i in range(len(face))]
                if len(coords) >= 3:
                    face_polys.append(Polygon(coords))
            
            if face_polys:
                model_poly = unary_union(face_polys)
                
                # Проходим по всем ребрам острова для генерации ушек
                for f_idx in island_faces:
                    face = p_raw[f_idx]
                    pts = final_island_coords[f_idx]
                    
                    for i in range(len(face)):
                        v_a, v_b = face[i], face[(i+1)%len(face)]
                        e_key = tuple(sorted([v_a, v_b]))
                        p_a, p_b = pts[i], pts[(i+1)%len(pts)]
                        
                        e_id = edge_id_map.get(e_key)
                        if e_id is not None and e_key not in used_edges_2d and t_size > 0:
                            if e_id not in used_tabs_global:
                                used_tabs_global.add(e_id)
                                
                                # Координаты ребра
                                p1 = np.array([p_a.x, p_a.y])
                                p2 = np.array([p_b.x, p_b.y])
                                
                                edge_vec = p2 - p1
                                length = np.linalg.norm(edge_vec)
                                if length < (t_inset * 2.1): 
                                    continue  # Ребро слишком короткое для инсета
                                
                                unit = edge_vec / length
                                perp = np.array([-unit[1], unit[0]])  # Перпендикуляр
                                
                                # Определяем направление "наружу"
                                mid = (p1 + p2) * 0.5
                                test_point = Point(mid[0] + perp[0] * (t_size * 0.1), 
                                                  mid[1] + perp[1] * (t_size * 0.1))
                                
                                if model_poly.contains(test_point):
                                    perp = -perp  # Меняем направление
                                
                                # 1. Сдвигаем точки внутрь ребра на edge_inset
                                p1_i = p1 + unit * t_inset
                                p2_i = p2 - unit * t_inset
                                
                                # 2. Сдвигаем основание ушка от ребра на gap_size
                                p1_base = p1_i + perp * t_gap
                                p2_base = p2_i + perp * t_gap
                                
                                # 3. Рассчитываем скос трапеции
                                t_off = min(t_size * np.tan(taper_rad), (length - 2*t_inset) * 0.4)
                                
                                # 4. Формируем вершины ушка
                                p3 = p2_base - unit * t_off + perp * t_size
                                p4 = p1_base + unit * t_off + perp * t_size
                                
                                # Создаем полигон ушка
                                raw_tab = Polygon([p1_base, p2_base, p3, p4])
                                
                                # ОБРЕЗКА - вычитаем модель с небольшим буфером
                                try:
                                    clean_tab = raw_tab.difference(model_poly.buffer(1e-5))
                                except:
                                    continue
                                
                                if not clean_tab.is_empty:
                                    # Обрабатываем результат (может быть MultiPolygon)
                                    geoms = clean_tab.geoms if hasattr(clean_tab, 'geoms') else [clean_tab]
                                    
                                    for part in geoms:
                                        if not hasattr(part, 'exterior'): 
                                            continue
                                        coords = list(part.exterior.coords)[:-1]  # Убираем последнюю точку
                                        
                                        if len(coords) < 3:
                                            continue  # Пропускаем вырожденные полигоны
                                        
                                        # Добавляем вершины
                                        start_idx = len(tv)
                                        for c in coords:
                                            tv.append([c[0], c[1], 0.0])
                                        
                                        # Добавляем полигон с перевернутыми нормалями (для правильного отображения)
                                        face_indices = list(range(start_idx, start_idx + len(coords)))
                                        tp.append(face_indices[::-1])  # Flip для правильных нормалей
                                        t_ptr += len(coords)
            
            final_verts.append(iv); final_polys.append(ip)
            if tv:
                final_tabs_v.append(tv); final_tabs_p.append(tp)
            current_x_offset += (max_x - min_x) + dist_gap

    # Корректные выходы для Sverchok
    res_tv = final_tabs_v if final_tabs_v else [[]]
    res_tp = final_tabs_p if final_tabs_p else [[]]

    return final_verts, final_polys, res_tv, res_tp, [flap_pts_all], [flap_ids_all]

# Вывод результатов
verts_out, poly_out, tabs_v, tabs_p, flap_points, flap_ids = run()