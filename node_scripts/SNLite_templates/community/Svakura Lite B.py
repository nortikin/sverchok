"""
in verts_in v d=[] n=0
in poly_in s d=[] n=0
in tab_size s d=0.1 n=2
in taper_angle s d=30.0 n=2
in gap_size s d=0.00 n=2
in edge_inset s d=0.00 n=2
in unfold_factor s d=1.0 n=2
in position_factor s d=0.0 n=2
in gap s d=1.0 n=2
# in use_original_ids s d=1 n=2 х-ня на доработку
# in index_all_edges s d=1 n=2 х-ня на доработку
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
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

def run():
    if not verts_in or not poly_in:
        return [[]], [[]], [[]], [[]], [[]], [[]]

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

    dist_gap = float(gap)
    t_size = float(tab_size)
    unfold_val = float(unfold_factor)  # 0 - свернуто, 1 - развернуто
    position_val = float(position_factor)  # 0 - в ряд, 1 - в позиции исходной модели
    
    # Новые параметры для ушек
    taper_rad = np.radians(float(taper_angle))
    t_gap = float(gap_size)
    t_inset = float(edge_inset)
    
    all_final_verts, all_final_polys = [], []
    final_tabs_v, final_tabs_p = [], []
    flap_pts_all, flap_ids_all = [], []
    
    used_tabs_global = set()
    global_edge_registry = {}
    next_id = 1
    global_v_ptr = 0
    global_t_ptr = 0
    current_x_offset = 0.0

    # 1. ТОПОЛОГИЯ И ИНДЕКСАЦИЯ
    edge_to_faces = {}
    f_normals = []
    edge_id_map = {}
    
    for f_idx, face in enumerate(polys):
        pts = [v_orig[i] for i in face]
        n = Vector((0,0,0))
        for i in range(len(pts)): n += pts[i-1].cross(pts[i])
        f_normals.append(n.normalized() if n.length > 1e-8 else Vector((0,0,1)))
        
        for i in range(len(face)):
            v1_idx, v2_idx = face[i], face[(i+1)%len(face)]
            v1, v2 = v_orig[v1_idx], v_orig[v2_idx]
            e_key_3d = tuple(sorted([(round(v.x,4), round(v.y,4), round(v.z,4)) for v in [v1, v2]]))
            
            if e_key_3d not in global_edge_registry:
                global_edge_registry[e_key_3d] = next_id
                next_id += 1
            
            e_topo = tuple(sorted([v1_idx, v2_idx]))
            edge_id_map[e_topo] = global_edge_registry[e_key_3d]
            edge_to_faces.setdefault(e_topo, []).append(f_idx)

    def get_basis(p1, p2, normal):
        x = (p2 - p1).normalized()
        z = normal.normalized()
        y = z.cross(x).normalized()
        return Matrix((x, y, z)).transposed().to_4x4()

    # Сохраняем исходные позиции вершин для каждой грани
    original_face_verts = []
    for face in polys:
        face_verts = [v_orig[i].copy() for i in face]
        original_face_verts.append(face_verts)

    # 2. BFS РАЗВЕРТКА
    visited_global = set()
    
    # Словарь для хранения связей родитель-потомок и матриц трансформации
    parent_child_map = {}  # child_idx -> (parent_idx, edge)
    edge_transforms = {}   # (parent_idx, child_idx) -> transform matrix

    for root_f in range(len(polys)):
        if root_f in visited_global: continue
        
        island_2d = {}
        island_edges_internal = set()
        f0 = polys[root_f]
        p_ref = v_orig[f0[0]]
        rot = f_normals[root_f].rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()
        island_2d[root_f] = [rot @ (v_orig[i] - p_ref) for i in f0]
        
        visited_global.add(root_f)
        queue = [root_f]

        while queue:
            c_idx = queue.pop(0)
            c_face, c_2d, n_c_3d = polys[c_idx], island_2d[c_idx], f_normals[c_idx]

            for i in range(len(c_face)):
                v1, v2 = c_face[i], c_face[(i+1)%len(c_face)]
                edge_topo = tuple(sorted([v1, v2]))

                for n_idx in edge_to_faces.get(edge_topo, []):
                    if n_idx in visited_global: continue

                    p1_3d, p2_3d = v_orig[v1], v_orig[v2]
                    p1_2d, p2_2d = c_2d[i], c_2d[(i+1)%len(c_face)]
                    n_n_3d = f_normals[n_idx]

                    axis = (p2_3d - p1_3d).normalized()
                    ang = math.atan2(n_n_3d.dot(n_c_3d.cross(axis)), n_n_3d.dot(n_c_3d))

                    m_final = Matrix.Translation(p1_2d) @ get_basis(p1_2d, p2_2d, Vector((0,0,1))) @ \
                              get_basis(p1_3d, p2_3d, n_c_3d).inverted() @ \
                              Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-p1_3d)

                    island_2d[n_idx] = [m_final @ v_orig[idx] for idx in polys[n_idx]]
                    island_edges_internal.add(edge_topo)
                    visited_global.add(n_idx)
                    queue.append(n_idx)
                    
                    # Сохраняем связь родитель-потомок и матрицу трансформации
                    parent_child_map[n_idx] = (c_idx, edge_topo)
                    edge_transforms[(c_idx, n_idx)] = m_final

        # 3. ПРИМЕНЕНИЕ СВОРАЧИВАНИЯ
        if unfold_val < 1.0:
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
                flat_verts = island_2d[face_idx]
                transformed = [current_transform @ v for v in flat_verts]
                
                # Сохраняем результат
                island_2d[face_idx] = transformed
                
                # Обрабатываем детей
                if face_idx in children_of:
                    for child_idx in children_of[face_idx]:
                        if (face_idx, child_idx) in edge_transforms:
                            # Получаем исходную матрицу трансформации для этого ребра
                            edge_mat = edge_transforms[(face_idx, child_idx)]
                            
                            # Вычисляем угол между нормалями в исходной модели
                            normal_parent = f_normals[face_idx]
                            normal_child = f_normals[child_idx]
                            
                            dot_product = normal_parent.dot(normal_child)
                            total_angle = math.acos(max(-1, min(1, dot_product)))
                            
                            # Определяем направление вращения
                            v1_idx, v2_idx = parent_child_map[child_idx][1]
                            
                            v1_orig = v_orig[v1_idx]
                            v2_orig = v_orig[v2_idx]
                            axis_orig = (v2_orig - v1_orig).normalized()
                            cross_prod = normal_parent.cross(normal_child)
                            sign = 1 if cross_prod.dot(axis_orig) > 0 else -1
                            
                            # Вычисляем текущий угол сворачивания
                            current_angle = total_angle * (1 - unfold_val) * sign
                            
                            # Получаем вершины ребра в плоской развертке
                            p_face = polys[face_idx]
                            c_face = polys[child_idx]
                            
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
            apply_fold_transforms(root_f, Matrix.Identity(4), processed_faces)

        # 4. СБОРКА С УЧЕТОМ POSITION_FACTOR
        patch_pts = [p for f in island_2d.values() for p in f]
        if not patch_pts: continue
        min_x, max_x = min(p.x for p in patch_pts), max(p.x for p in patch_pts)
        shift = Vector((current_x_offset - min_x, 0, 0))

        # Временное хранение координат для интерполяции с position_factor
        final_island_coords = {}
        
        # Применяем позиционирование
        for f_idx in island_2d.keys():
            face = polys[f_idx]
            # Берем исходные мировые координаты грани из v_orig
            world_coords = [v_orig[idx].copy() for idx in face]
            # Текущие координаты (со сдвигом в ряд)
            current_coords = [p + shift for p in island_2d[f_idx]]
            
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

        # Собираем основную геометрию и flap_points
        for f_idx in sorted(island_2d.keys()):
            face = polys[f_idx]
            pts = final_island_coords[f_idx]
            
            all_final_verts.extend([p[:] for p in pts])
            all_final_polys.append(list(range(global_v_ptr, global_v_ptr + len(pts))))
            
            # Собираем flap_points
            for i in range(len(face)):
                idx_a, idx_b = face[i], face[(i+1)%len(face)]
                edge_topo = tuple(sorted([idx_a, idx_b]))
                p_a, p_b = pts[i], pts[(i+1)%len(face)]
                e_id = edge_id_map[edge_topo]
                
                if edge_topo not in island_edges_internal:
                    mid = (p_a + p_b) / 2
                    flap_pts_all.append(mid[:]); flap_ids_all.append(str(e_id))
            
            global_v_ptr += len(pts)

        # ===== НОВЫЙ БЛОК ГЕНЕРАЦИИ УШЕК С ПАРАМЕТРАМИ =====
        # Создаем единый полигон модели из текущего острова
        face_polys = []
        for f_idx in island_2d.keys():
            face = polys[f_idx]
            coords = [(final_island_coords[f_idx][i][0], final_island_coords[f_idx][i][1]) for i in range(len(face))]
            if len(coords) >= 3:
                face_polys.append(Polygon(coords))
        
        if face_polys:
            model_poly = unary_union(face_polys)
            
            # Проходим по всем ребрам острова для генерации ушек
            tv = []  # временные вершины ушек для этого острова
            tp = []  # временные полигоны ушек для этого острова
            
            for f_idx in island_2d.keys():
                face = polys[f_idx]
                pts = final_island_coords[f_idx]
                
                for i in range(len(face)):
                    v_a, v_b = face[i], face[(i+1)%len(face)]
                    e_key = tuple(sorted([v_a, v_b]))
                    p_a, p_b = pts[i], pts[(i+1)%len(pts)]
                    
                    e_id = edge_id_map[e_key]
                    
                    # Генерируем ушко только для внешних ребер
                    if e_key not in island_edges_internal and t_size > 0:
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
                                    
                                    # Добавляем полигон с перевернутыми нормалями
                                    face_indices = list(range(start_idx, start_idx + len(coords)))
                                    tp.append(face_indices[::-1])  # Flip для правильных нормалей
            
            if tv:
                final_tabs_v.extend(tv)
                # Корректируем индексы для глобального списка
                for poly in tp:
                    adjusted_poly = [idx + global_t_ptr for idx in poly]
                    final_tabs_p.append(adjusted_poly)
                global_t_ptr += len(tv)
        
        current_x_offset += (max_x - min_x) + dist_gap

    return [all_final_verts], [all_final_polys], [final_tabs_v], [final_tabs_p], [flap_pts_all], [flap_ids_all]

verts_out, poly_out, tabs_v, tabs_p, flap_points, flap_ids = run()