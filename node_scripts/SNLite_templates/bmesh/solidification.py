"""
in thickness s d=0.1 n=2
in even_thickness s d=0 n=2
in high_quality_thickness s d=0 n=2
in fix_intersections s d=0 n=2
in verts v d=[] n=0
in edges s d=[] n=0
in faces s d=[] n=0
enum = NONE INNER OUTER
enum2 = NONE ONLY_CLEAN ONLY_FULL CLEAN FULL
out verts_out v
out edges_out s
out faces_out s
"""

import bpy
import bmesh
from mathutils import Vector
from math import *
import itertools
from typing import NamedTuple

def ui(self, context, layout):
    layout.prop(self, 'custom_enum', expand=True)
    layout.prop(self, 'custom_enum_2', expand=True)


def manifold_solidify(thickness, even_thickness, high_quality_thickness, fix_intersections, boundary_fix, rim, input_verts, input_edges, input_faces):
    # validate parameters
    #assert boundary_fix in ('NONE', 'INNER', 'OUTER'), "Invalid boundary fix '{}'".format(boundary_fix)
    #assert rim in ('NONE', 'ONLY_CLEAN', 'ONLY_FULL', 'CLEAN', 'FULL'), "Invalid rim option '{}'".format(rim)
    
    # data types
    class EdgeData(NamedTuple):
        verts: list
        edge: bmesh.types.BMEdge
        faces: list
        link_edge_groups: list
        new_verts: dict
        def __hash__(self):
            return id(self)
        def other_group(self, edge_group):
            if self.link_edge_groups[0] == edge_group:
                return self.link_edge_groups[1]
            elif self.link_edge_groups[1] == edge_group:
                return self.link_edge_groups[0]
            else:
                return None
    
    class VertData():
        __slots__ = ["_vert", "_normal", "_normals", "_positions", "_tested", "copy_data"]
        def __init__(self, vert:bmesh.types.BMVert, normal:Vector):
            self._vert = vert
            self._normal = normal
            self._normals = []
            self._positions = []
            self._tested = set()
            self.copy_data = None
        def __getattr__(self, item):
            return self.get_data().__getattribute__('_' + item)
        def get_data(self):
            return self.copy_data == None and self or self.copy_data.get_data()
        def merge(self, other):
            data = self.get_data()
            other_data = other.get_data()
            other_data._normals.extend(data._normals)
            other_data._positions.extend(data._positions)
            other_data._tested.update(data._tested)
            self.copy_data = other_data
    
    class EdgeGroup(list):
        def __init__(self, iterable=None, closed=False):
            self.topology_groups = set()
            self.closed = closed
            if iterable:
                list.__init__(self, iterable)
            else:
                list.__init__(self)
        def __hash__(self):
            return id(self)
    
    class HashableList(list):
        def __hash__(self):
            return id(self)
    
    class FaceData():
        face: bmesh.types.BMFace
        reversed: bool
        link_edges: list
        def __init__(self, face, reversed):
            self.face = face
            self.reversed = reversed
            self.link_edges = [None] * len(self.face.loops)
        def __hash__(self):
            return id(self)
    
    # function to project vector p on to plane n (normalized) going through O
    def project(p, n):
        return p - n * Vector.dot(n, p)
    
    # expects n and ref_n to be projected like project(n, edge_dir)
    def angle_around_edge(n, ref_n, edge_dir):
        d = Vector.dot(n, ref_n)
        angle_diff = acos(max(-1, min(1, d)))
        if Vector.dot(Vector.cross(n, ref_n), edge_dir) >= 0:
            angle_diff = 2 * pi - angle_diff
        return angle_diff
    
    # displacement from surface
    disp = thickness / 2
    
    # create bmesh from input data
    bm = bmesh.new()
    
    # add vertices
    for v_co in input_verts:
        bm.verts.new(v_co)
    bm.verts.ensure_lookup_table()
    
    # add edges and faces
    if input_faces:
        # если есть faces, создаем их (edges будут созданы автоматически)
        #print('faces:',input_faces)
        for face_indices in input_faces:
            face_verts = [bm.verts[i] for i in face_indices if i < len(bm.verts)]
            if len(face_verts) >= 3:
                try:
                    bm.faces.new(face_verts)
                except Exception as e:
                    print(f"Error creating face: {e}")
    elif input_edges:
        # если только edges, создаем их
        for edge_indices in input_edges:
            if len(edge_indices) >= 2:
                v1_idx, v2_idx = edge_indices[0], edge_indices[1]
                if v1_idx < len(bm.verts) and v2_idx < len(bm.verts):
                    bm.edges.new((bm.verts[v1_idx], bm.verts[v2_idx]))
    
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    
    # select all geometry for processing
    for vert in bm.verts:
        vert.select = True
    for edge in bm.edges:
        edge.select = True
    for face in bm.faces:
        face.select = True
    
    # cache the data that will be modified
    original_verts = [v for v in bm.verts]
    original_edges = [e for e in bm.edges]
    original_faces = [f for f in bm.faces]
    
    # Get data layers
    loops_data = []
    for layer in bm.loops.layers.color.values():
        loops_data.append(layer)
    for layer in bm.loops.layers.uv.values():
        loops_data.append(layer)
    
    verts_data = []
    for layer in bm.verts.layers.deform.values():
        verts_data.append(layer)
    if hasattr(bm.verts.layers, 'paint_mask'):
        for layer in bm.verts.layers.paint_mask.values():
            verts_data.append(layer)
    if hasattr(bm.verts.layers, 'bevel_weight'):
        for layer in bm.verts.layers.bevel_weight.values():
            verts_data.append(layer)
    
    edge_crease = bm.edges.layers.crease.active if hasattr(bm.edges.layers, 'crease') else None
    
    # create face_data
    def create_face_data(original_faces):
        face_sides = {}
        for face in original_faces:
            face_sides[face] = (FaceData(face, False), FaceData(face, True))
        print('create_face_data')
        return face_sides
    
    # create edge data
    def create_edge_data(original_edges, face_sides):
        original_edge_data_map = {}
        for edge in original_edges:
            edge_v0 = edge.verts[0]
            edge_v1 = edge.verts[1]
            edge_vec = edge_v1.co - edge_v0.co
            edge_dir = edge_vec.normalized()
            if edge_dir.length == 0:
                continue  # skip zero-length edges
            
            adj_faces = [f for f in edge.link_faces]
            if len(adj_faces) > 0:
                face_reverse = {}
                normal = None
                if len(adj_faces) > 1:
                    face_angle = {}
                    ref_normal = None
                    for face in adj_faces:
                        reverse = next((-1 for loop in face.loops if loop.edge == edge and loop.vert == edge_v1), 1)
                        normal = face.normal * reverse
                        normal_projected = len(face.verts) > 3 and project(normal, edge_dir) or normal
                        normal_projected.normalize()
                        face_reverse[face] = reverse < 0
                        if not ref_normal:
                            ref_normal = normal_projected
                            face_angle[face] = 0
                        else:
                            face_angle[face] = angle_around_edge(normal_projected, ref_normal, edge_dir)
                    adj_faces = sorted(adj_faces, key=lambda x: face_angle[x])
                else:
                    normal = adj_faces[0].normal
                    face_reverse[adj_faces[0]] = False
                
                edge_data_list = []
                for i in range(0, len(adj_faces)):
                    face = adj_faces[i]
                    next_face = adj_faces[(i + 1) % len(adj_faces)]
                    for j in range(0, face == next_face and 2 or 1):
                        n = j == 0 and normal or -normal
                        faces = None
                        if face == next_face:
                            faces = [face_sides[face][face_reverse[face] == (j == 0) and 1 or 0]]
                        else:
                            faces = [face_sides[face][face_reverse[face] and 1 or 0], face_sides[next_face][not face_reverse[next_face] and 1 or 0]]
                        edge_data = EdgeData([edge_v0, edge_v1], edge, faces, [None, None], {})
                        edge_data_list.append(edge_data)
                        for f in faces:
                            f.link_edges[list(f.face.edges).index(edge)] = edge_data
                
                original_edge_data_map[edge] = edge_data_list
        print('create_edge_data')
        return original_edge_data_map
    
    # create groups of edges that form vertices
    def create_groups(original_verts, original_edge_data_map):
        original_vert_groups_map = {}
        for vert in original_verts:
            adj_edges = [e for e in vert.link_edges if e in original_edge_data_map]
            if len(adj_edges) <= 1:
                continue
            
            adj_new_edge_data = [original_edge_data_map[e] for e in adj_edges]
            unassigned_edge_data = list(itertools.chain(*adj_new_edge_data))
            edge_groups = [[]]
            
            while len(unassigned_edge_data) > 0:
                found_edges = []
                if len(edge_groups[-1]) == 0:
                    found_edges.append(next(iter(unassigned_edge_data)))
                else:
                    edge_group_faces = set(itertools.chain(*[e.faces for e in edge_groups[-1]]))
                    for edge in unassigned_edge_data:
                        if not edge_group_faces.isdisjoint(edge.faces):
                            found_edges.append(edge)
                
                if len(found_edges) > 0:
                    edge_groups[-1].extend(found_edges)
                    for found_edge in found_edges:
                        unassigned_edge_data.remove(found_edge)
                else:
                    edge_groups.append([])
            
            sorted_edge_groups = []
            contains_open_groups = False
            contains_long_groups = False
            
            for g in edge_groups:
                if not g:
                    continue
                    
                head = next((h for h in g if len(h.faces) > 1), g[0])
                start_face_direction = len(head.faces) > 1 and head.verts[0] == vert and 1 or 0
                head_face = head.faces[start_face_direction]
                sorted_g = [head]
                g_set = set(g)
                g_set.remove(head)
                reversed_flag = False
                
                while True:
                    next_head = None
                    if head_face:
                        for e in head_face.link_edges:
                            if e in g_set:
                                next_head = e
                                if e.faces[0] == head_face:
                                    if len(e.faces) > 1:
                                        head_face = e.faces[1]
                                    else:
                                        head_face = None
                                else:
                                    head_face = e.faces[0]
                                break
                        if next_head:
                            sorted_g.append(next_head)
                            g_set.remove(next_head)
                            head = next_head
                    
                    if not next_head and len(g_set) > 0:
                        if reversed_flag:
                            break
                        head = sorted_g[0]
                        head_face = head.faces[1 - start_face_direction]
                        sorted_g.reverse()
                        reversed_flag = True
                    elif not next_head:
                        break
                
                if not reversed_flag:
                    sorted_g.reverse()
                
                open = len(sorted_g[0].faces) == 1
                if open:
                    contains_open_groups = True
                if not contains_long_groups and len(sorted_g) > 3:
                    contains_long_groups = True
                
                sorted_edge_groups.append(EdgeGroup(sorted_g, not open))
            
            edge_groups = sorted_edge_groups
            
            if contains_open_groups:
                sorted_groups = []
                open_groups_count = 0
                reject_streak_start = None
                
                while len(edge_groups) > 0:
                    g = edge_groups[-1]
                    edge_groups.remove(g)
                    
                    if len(g[0].faces) > 1 or len(g) < 3:
                        sorted_groups.append(g)
                    else:
                        if open_groups_count == 0:
                            sorted_groups.insert(0, g)
                            open_groups_count += 1
                        else:
                            found_insert = None
                            start_edge, end_edge = g[0].edge, g[-1].edge
                            for i in range(0, open_groups_count):
                                existing_g = sorted_groups[i]
                                ex_start_edge, ex_end_edge = existing_g[0].edge, existing_g[-1].edge
                                if ex_end_edge == start_edge:
                                    found_insert = i + 1
                                elif ex_start_edge == end_edge:
                                    found_insert = i
                            
                            if found_insert is not None:
                                reject_streak_start = None
                                sorted_groups.insert(found_insert, g)
                                open_groups_count += 1
                            else:
                                if not reject_streak_start:
                                    reject_streak_start = g
                                    edge_groups.insert(0, g)
                                elif reject_streak_start == g:
                                    sorted_groups.append(g)
                                    open_groups_count += 1
                                else:
                                    edge_groups.insert(0, g)
                
                edge_groups = sorted_groups
            
            if contains_long_groups:
                split_groups = []
                while len(edge_groups) > 0:
                    g = edge_groups[-1]
                    edge_groups.remove(g)
                    
                    if len(g) < 4:
                        split_groups.append(g)
                        continue
                    
                    unique = list(g)
                    has_doubles = False
                    for i in range(0, len(g)):
                        e_i = g[i].edge
                        for j in range(i + 1, len(g)):
                            if e_i == g[j].edge:
                                unique[i] = None
                                unique[j] = None
                                has_doubles = True
                    
                    if not has_doubles:
                        split_groups.append(g)
                        continue
                    
                    current_split_groups_size = len(split_groups)
                    unique_start = None
                    first_unique_end = None
                    last_split = None
                    first_split = None
                    real_i = 0
                    
                    while real_i < len(g) or (g.closed and (real_i <= (first_unique_end or 0) + len(g) or first_split != last_split)):
                        i = real_i % len(g)
                        if unique[i]:
                            if first_unique_end is not None and unique_start is None:
                                unique_start = real_i
                        elif first_unique_end is None:
                            first_unique_end = i
                        elif unique_start is not None:
                            split = ceil((unique_start + real_i) / 2) % len(g)
                            if last_split is not None:
                                if last_split > split:
                                    split_groups.append(EdgeGroup(g[last_split:] + g[:split], False))
                                else:
                                    split_groups.append(EdgeGroup(g[last_split:split], False))
                            last_split = split
                            if first_split is None:
                                first_split = split
                            unique_start = None
                        real_i += 1
                    
                    if first_split is None:
                        split_groups.append(g)
                    elif not g.closed:
                        split_groups.insert(current_split_groups_size, EdgeGroup(g[:first_split], False))
                        split_groups.append(EdgeGroup(g[last_split:], False))
                
                edge_groups = split_groups
            
            original_vert_groups_map[vert] = edge_groups
            
            for g in edge_groups:
                for e in g:
                    e.link_edge_groups[e.verts.index(vert)] = g
        
        print('create_groups')
        return original_vert_groups_map
    
    def create_regions(original_vert_groups_map):
        regions = []
        unassigned_edge_groups = set(itertools.chain(*original_vert_groups_map.values()))
        regions.append([])
        
        while len(unassigned_edge_groups) > 0:
            found_edges = []
            if len(regions[-1]) == 0:
                found_edges.append(next(iter(unassigned_edge_groups), None))
            else:
                region_edges = set(itertools.chain(*[g for g in regions[-1]]))
                for e_g in set(itertools.chain(*[[e.other_group(g) for e in g if e.other_group(g) in unassigned_edge_groups] for g in regions[-1]])):
                    if not region_edges.isdisjoint(e_g):
                        found_edges.append(e_g)
            
            if len(found_edges) > 0:
                regions[-1].extend(found_edges)
                for e in found_edges:
                    unassigned_edge_groups.remove(e)
            else:
                regions.append([])
        
        topology_groups = []
        for edge_groups in regions:
            topology = []
            inside = HashableList(edge_groups)
            
            for e_g in edge_groups:
                if not e_g.closed:
                    open_edges = set([e for e in [e_g[0], e_g[-1]] if len(e.faces) == 1])
                    intersections = [t_g for t_g in topology if any((not open_edges.isdisjoint(t_e_g) for t_e_g in t_g))]
                    topology_group = len(intersections) > 0 and intersections[0] or HashableList()
                    
                    for i in range(1, len(intersections)):
                        intersections[0].extend(intersections[i])
                        topology.remove(intersections[i])
                    
                    inside.remove(e_g)
                    topology_group.append(e_g)
                    if len(intersections) == 0:
                        topology.append(topology_group)
            
            topology.insert(0, inside)
            
            for topology_group in topology:
                for edge_group in topology_group:
                    edge_group.topology_groups.add(topology_group)
            
            topology_groups.extend(topology)
        
        print('create_regions')
        return topology_groups
    
    def make_crossings(original_vert_groups_map):
        """Создает новые вершины для offset геометрии на основе графов реберных групп"""
        
        merged_vert_data = []  # Список вершин, которые были объединены из-за пересечений
        new_verts = []         # Список новых вершин BMesh
        vert_open_verts_map = {}  # Карта: оригинальная вершина -> список (новая_вершина, crease_value)
        
        # Обрабатываем каждую оригинальную вершину
        for vert, edge_groups in original_vert_groups_map.items():
            open_verts = []  # Вершины на открытых границах для этого vert
            vert_open_verts_map[vert] = open_verts
            
            # Обрабатываем каждую группу ребер, связанную с вершиной
            for g in edge_groups:
                normals = []  # Нормали граней, связанных с этой группой
                first_edge = None
                
                # Собираем нормали граней, связанных с ребрами группы (каждое второе ребро)
                for i in range(0, len(g), 2):
                    e = g[i]
                    for f in e.faces:
                        # Добавляем нормаль грани с учетом ориентации (reversed)
                        if not first_edge or f not in first_edge.faces:
                            normals.append(f.face.normal * (f.reversed and -1 or 1))
                    if not first_edge:
                        first_edge = e
                
                # Инициализация вектора смещения и вектора свободного движения
                normal = Vector((0, 0, 0))
                move_normal = None
                
                # ВЫЧИСЛЕНИЕ НОРМАЛИ СМЕЩЕНИЯ
                if not high_quality_thickness:
                    # Простой метод вычисления нормали
                    total_angle = 0
                    first_edge = None
                    
                    for i in range(0, len(g), 2):
                        e = g[i]
                        for f in e.faces:
                            if not first_edge or f not in first_edge.faces:
                                angle = 1
                                if even_thickness:
                                    # Вычисляем угол между ребрами для взвешивания
                                    loop = next((l for l in f.face.loops if l.vert == vert), None)
                                    if loop:
                                        e0 = (loop.edge.other_vert(loop.vert).co - loop.vert.co).normalized()
                                        e1 = (loop.link_loop_prev.edge.other_vert(loop.vert).co - loop.vert.co).normalized()
                                        angle = acos(max(-1, min(1, Vector.dot(e0, e1))))
                                # Накопление взвешенных нормалей
                                normal += f.face.normal * (angle * (f.reversed and -1 or 1))
                                #print('nor,facenor,angle,reversed:',normal,f.face.normal, angle, f.reversed)
                                total_angle += angle
                        if not first_edge:
                            first_edge = e
                    
                    # Нормализация результата
                    if total_angle > 0:
                        normal /= total_angle
                    
                    if even_thickness:
                        # Дополнительная нормализация для равномерной толщины
                        d = Vector.dot(normal, normal)
                        if d > 0.001:
                            normal /= d
                    else:
                        if normal.length > 0:
                            normal.normalize()
                    
                    # Применение толщины (смещения)
                    #print('lq:',normal,disp)
                    normal *= disp
                    
                    # Вычисление вектора свободного движения для граничных вершин
                    move_normal = len(g) > 2 and Vector((0, 0, 0)) or None
                    for i in range(1, len(g) - 1):
                        e = g[i].edge.other_vert(vert).co - vert.co
                        if e.length > 0:
                            if move_normal:
                                move_normal += e.normalized()
                            else:
                                move_normal = e.normalized()
                
                else:
                    # Высококачественный метод с группировкой нормалей
                    normals_query = list(normals)
                    normal_groups = []
                    
                    # Группируем нормали в 1-3 группы в зависимости от их направления
                    while len(normals_query) > 0:
                        if len(normal_groups) == 0:
                            if len(normals_query) <= 2:
                                normal_groups.extend([v.copy() for v in normals_query])
                                normals_query.clear()
                            else:
                                # Находим две самые разные нормали
                                min_projection = 2
                                min_normal0 = None
                                min_normal1 = None
                                
                                for i in range(0, len(normals_query)):
                                    n0 = normals_query[i]
                                    for j in range(i + 1, len(normals_query)):
                                        n1 = normals_query[j]
                                        p = Vector.dot(n0, n1)
                                        if p < min_projection:
                                            min_projection = p
                                            min_normal0 = n0
                                            min_normal1 = n1
                                
                                if min_normal0 and min_normal1:
                                    normal_groups.append(min_normal0.copy())
                                    normal_groups.append(min_normal1.copy())
                                    normals_query.remove(min_normal0)
                                    normals_query.remove(min_normal1)
                                    
                                    # Пытаемся найти третью, сильно отличающуюся нормаль
                                    min_projection = 1
                                    min_normal2 = None
                                    for n in normals_query:
                                        max_p = -1
                                        for n_g in normal_groups:
                                            max_p = max(max_p, Vector.dot(n_g.normalized(), n))
                                        if max_p < min_projection:
                                            min_projection = max_p
                                            min_normal2 = n
                                    
                                    if min_projection < 0.7 and min_normal2:
                                        normal_groups.append(min_normal2.copy())
                                        normals_query.remove(min_normal2)
                        else:
                            # Присоединяем оставшиеся нормали к ближайшим группам
                            closest_projection = -1
                            closest_normal = None
                            closest_group_normal = None
                            
                            for n in normals_query:
                                for n_g in normal_groups:
                                    p = Vector.dot(n_g.normalized(), n)
                                    if p > closest_projection:
                                        closest_projection = p
                                        closest_normal = n
                                        closest_group_normal = n_g
                            
                            if closest_normal and closest_group_normal:
                                closest_group_normal += closest_normal
                                normals_query.remove(closest_normal)
                    
                    # Нормализация групповых нормалей
                    for n_g in normal_groups:
                        if n_g.length > 0:
                            n_g.normalize()
                    
                    # Вычисление итоговой нормали в зависимости от количества групп
                    if len(normal_groups) == 1:
                        # Одна группа - просто используем ее
                        normal += normal_groups[0]
                        move_normal = None
                    elif len(normal_groups) == 2:
                        # Две группы - среднее значение
                        normal += (normal_groups[0] + normal_groups[1]) * 0.5
                        d = Vector.dot(normal, normal)
                        if d > 0:
                            normal /= d
                        move_normal = Vector.cross(normal_groups[0], normal_groups[1])
                    elif len(normal_groups) == 3:
                        # Три группы - решение системы уравнений
                        normal += (normal_groups[0] + normal_groups[1]) * 0.5
                        d = Vector.dot(normal, normal)
                        if d > 0:
                            normal /= d
                        free_n = Vector.cross(normal_groups[0], normal_groups[1])
                        d = Vector.dot(normal_groups[2], free_n)
                        if d != 0:
                            normal -= free_n * Vector.dot(normal_groups[2], normal - normal_groups[2]) / d
                        move_normal = None
                    
                    # Применение толщины
                    #print('hq:',normal)
                    normal *= disp
                
                # КОРРЕКЦИЯ ДЛЯ ГРАНИЧНЫХ ВЕРШИН
                if move_normal and boundary_fix != 'NONE' and len(g) > 2 and len(g[0].faces) == 1 and len(g[-1].faces) == 1:
                    e0 = g[0].edge.other_vert(vert).co - vert.co
                    e1 = g[-1].edge.other_vert(vert).co - vert.co
                    
                    if boundary_fix == 'OUTER':
                        # Для внешних границ - нормаль как перпендикуляр к граничным ребрам
                        constraint_normal = Vector.cross(e0, e1)
                    else:
                        # Для внутренних границ - комбинация нормалей от граничных граней
                        f0 = g[0].faces[0].face.normal * (g[0].faces[0].reversed and -1 or 1)
                        n0 = Vector.cross(e0, f0)
                        if n0.length > 0:
                            n0.normalize()
                        
                        f1 = g[-1].faces[0].face.normal * (g[-1].faces[0].reversed and 1 or -1)
                        n1 = Vector.cross(e1, f1)
                        if n1.length > 0:
                            n1.normalize()
                        
                        constraint_normal = n0 + n1
                    
                    # Проекция нормали на ограничивающую плоскость
                    if constraint_normal.length > 0:
                        d = Vector.dot(constraint_normal, move_normal)
                        if d != 0:
                            normal -= move_normal * Vector.dot(constraint_normal, normal) / d
                            #print(normal)
                
                # СОЗДАНИЕ НОВОЙ ВЕРШИНЫ
                vert_data = None
                pos = vert.co + normal  # Позиция смещенной вершины
                
                # ПРОВЕРКА ПЕРЕСЕЧЕНИЙ (если включена)
                if fix_intersections:
                    current_vert_topology_groups = g.topology_groups
                    
                    def test_intersections(vert_p, vert_co, other_verts, intersections=None):
                        """Проверяет пересечения с другими вершинами и объединяет их при необходимости"""
                        vert_data = None
                        if intersections is None:
                            intersections = set()
                        
                        vert_tested = []
                        for other_vert_data, other_edge_group in other_verts:
                            other_positions = other_vert_data.positions
                            # Проверка: если векторы указывают в противоположных направлениях
                            if any((Vector.dot(v.co - vert_co, p - vert_p) < 0 for p, v in other_positions)):
                                # Обнаружено пересечение - используем существующую вершину
                                vert_data = other_vert_data.get_data()
                                intersections.add(vert_data)
                                if vert_data not in merged_vert_data:
                                    merged_vert_data.append(vert_data)
                            else:
                                # Нет пересечения - запоминаем для дальнейшего тестирования
                                vert_tested.append(other_vert_data)
                        
                        # Объединение нескольких пересекающихся вершин
                        if len(intersections) >= 2:
                            for ol in intersections:
                                if ol != vert_data:
                                    # Удаляем дублирующиеся вершины
                                    if set([v[1] for v in ol.positions]).isdisjoint([v[1] for v in vert_data.positions]):
                                        new_verts.remove(ol.vert)
                                        bm.verts.remove(ol.vert)
                                        if ol in merged_vert_data:
                                            merged_vert_data.remove(ol)
                                        ol.merge(vert_data)
                        
                        return vert_data, len(intersections), vert_tested
                    
                    # Получаем уже созданные вершины для смежных ребер
                    other_verts = []
                    for e in g:
                        if e.edge.other_vert(vert) in e.new_verts:
                            other_vert_info = e.new_verts[e.edge.other_vert(vert)]
                            if not current_vert_topology_groups.isdisjoint(other_vert_info[1].topology_groups):
                                other_verts.append(other_vert_info)
                    
                    # Тестируем пересечения
                    vert_data, intersection_count, vert_tested = test_intersections(pos, vert.co, other_verts)
                    
                    # Создаем новую вершину, если не было пересечений
                    if not vert_data:
                        vert_data = VertData(bm.verts.new(pos), normal)
                        new_verts.append(vert_data.vert)
                    
                    # Обновляем списки тестированных вершин
                    for tested_vert_data in vert_tested:
                        vert_data.tested.add(tested_vert_data)
                    
                    # Рекурсивная проверка пересечений для связанных вершин
                    if intersection_count >= 1:
                        for tested_vert_data in list(vert_data.tested):
                            tested_vert_data = tested_vert_data.get_data()
                            for other_vert_p, other_vert in list(tested_vert_data.positions):
                                new_other_vert_data, other_intersection_count, other_tested_lists = test_intersections(
                                    other_vert_p, other_vert.co, [(vert_data, g)], set([tested_vert_data]))
                                if other_intersection_count > 1:
                                    vert_data = new_other_vert_data
                else:
                    # Без проверки пересечений - просто создаем новую вершину
                    vert_data = VertData(bm.verts.new(pos), normal)
                    new_verts.append(vert_data.vert)
                
                # СОХРАНЕНИЕ ДАННЫХ О ВЕРШИНЕ
                # Нормали для последующей корректировки
                for n in normals:
                    vert_data.normals.append((pos, n))
                # Позиции оригинальных вершин для этого смещения
                vert_data.positions.append((pos, vert))
                
                # Копирование данных слоев с оригинальной вершины
                for data_layer in verts_data:
                    vert_data.vert[data_layer] = vert[data_layer]
                
                # Для открытых границ - сохранение информации о crease
                if not g.closed:
                    g_max_inner_crease = 0
                    if edge_crease:
                        for e in g:
                            if e.edge[edge_crease] > g_max_inner_crease and len([f for f in e.edge.link_faces]) > 1:
                                g_max_inner_crease = e.edge[edge_crease]
                    open_verts.append((vert_data, g_max_inner_crease))
                
                # Регистрация новой вершины в ребрах
                for e in g:
                    e.new_verts[vert] = (vert_data, g)
        
        # КОРРЕКЦИЯ ПОЛОЖЕНИЯ ОБЪЕДИНЕННЫХ ВЕРШИН (при включенной проверке пересечений)
        if fix_intersections:
            for vert_data in merged_vert_data:
                normals = vert_data.normals
                positions = vert_data.positions
                
                if not positions:
                    continue
                
                # Средняя позиция из всех объединенных позиций
                v_co = Vector((0, 0, 0))
                for p, co in positions:
                    v_co += p
                v_co /= len(positions)
                
                # Итеративная корректировка для высококачественного режима
                if high_quality_thickness:
                    last_max_r = 10000
                    reset_co = v_co.copy()
                    for _ in range(100):
                        max_r = 0
                        for pos, n in normals:
                            # Расстояние до плоскости, определяемой нормалью
                            r = Vector.dot(n, pos - v_co)
                            if r > 0:
                                max_r = max(max_r, r)
                                v_co += n * r  # Корректируем позицию
                        
                        if max_r < 0.01:  # Достигнута достаточная точность
                            break
                        
                        if max_r > last_max_r * 0.99:  # Расходимость - сброс
                            v_co = reset_co
                            break
                        
                        last_max_r = max_r
                
                # Установка финальной позиции
                vert_data.vert.co = v_co
        
        print('make_crossings, most hard definition seems')
        return new_verts, vert_open_verts_map
    
    def make_boundary_faces(original_edges, vert_open_verts_map, original_vert_groups_map, face_sides):
        for vert, open_verts_data in vert_open_verts_map.items():
            try:
                open_verts = [v[0].vert for v in open_verts_data]
                max_inner_crease = [v[1] for v in open_verts_data]
                
                if len(open_verts) > 2:
                    new_face = bm.faces.new(open_verts)
                    if rim == 'FULL' or rim == 'ONLY_FULL':
                        if vert in original_vert_groups_map and original_vert_groups_map[vert]:
                            g = original_vert_groups_map[vert][0]
                            if g and g[0].faces:
                                old_loop = next((l for l in g[0].faces[0].face.loops if l.vert == vert), None)
                                if old_loop:
                                    for new_loop in new_face.loops:
                                        for data_layer in loops_data:
                                            new_loop[data_layer] = old_loop[data_layer]
                                    new_face.material_index = g[0].faces[0].face.material_index
                    
                    if edge_crease:
                        for i in range(0, len(open_verts)):
                            new_edge = new_face.loops[i].edge
                            crease = min(max_inner_crease[i], max_inner_crease[(i + 1) % len(open_verts)])
                            new_edge[edge_crease] = crease
                elif len(open_verts) == 2 and edge_crease:
                    new_edge = bm.edges.new(open_verts)
                    crease = max(max_inner_crease[0], max_inner_crease[1])
                    new_edge[edge_crease] = crease
            except Exception:
                pass
        
        for edge in original_edges:
            adj_faces = [f for f in edge.link_faces]
            if len(adj_faces) == 1:
                bm_face = adj_faces[0]
                loop_index = next((i for i in range(0, len(bm_face.loops)) if bm_face.loops[i].edge == edge), None)
                if loop_index is not None:
                    loop = bm_face.loops[loop_index]
                    if bm_face in face_sides:
                        adj_face_sides = face_sides[bm_face]
                        verts = []
                        for i in range(0, 4):
                            reverse = i == 1 or i == 2
                            e = adj_face_sides[reverse and 1 or 0].link_edges[loop_index]
                            v = loop.vert
                            if i > 1:
                                v = loop.edge.other_vert(v)
                            if v in e.new_verts:
                                new_v = e.new_verts[v][0].vert
                                if new_v not in verts:
                                    verts.append(new_v)
                        
                        if len(verts) > 2:
                            try:
                                new_face = bm.faces.new(verts)
                                if rim == 'FULL' or rim == 'ONLY_FULL':
                                    for i in range(0, len(verts)):
                                        new_loop = new_face.loops[i]
                                        old_loop = i > 1 and loop.link_loop_next or loop
                                        new_loop.copy_from(old_loop)
                                    new_face.material_index = bm_face.material_index
                            except Exception:
                                pass
        print('make_boundary_faces')
    
    def make_faces(face_sides):
        for bm_face, faces in face_sides.items():
            for face in faces:
                verts = []
                loops = []
                i = 0
                
                for loop in bm_face.loops:
                    v0 = loop.vert
                    v1 = loop.link_loop_next.vert
                    edge = face.link_edges[i]
                    
                    if v0 in edge.new_verts:
                        new_v0 = edge.new_verts[v0][0].vert
                        if len(verts) == 0 or verts[-1] != new_v0:
                            if new_v0 not in verts:
                                verts.append(new_v0)
                                loops.append(loop)
                    
                    if v1 in edge.new_verts:
                        new_v1 = edge.new_verts[v1][0].vert
                        if len(verts) <= 1 or verts[0] != new_v1:
                            if new_v1 not in verts:
                                verts.append(new_v1)
                                loops.append(loop.link_loop_next)
                    i += 1
                
                if face.reversed:
                    verts.reverse()
                    loops.reverse()
                
                if len(verts) > 2:
                    try:
                        new_face = bm.faces.new(verts)
                        for i in range(0, len(verts)):
                            new_loop = new_face.loops[i]
                            old_loop = loops[i]
                            if face.reversed:
                                if old_loop.link_loop_prev:
                                    new_loop.edge.copy_from(old_loop.link_loop_prev.edge)
                            else:
                                new_loop.edge.copy_from(old_loop.edge)
                            new_loop.copy_from(old_loop)
                        new_face.copy_from(bm_face)
                    except Exception:
                        pass
        print('make_faces')
    
    def remove_loose_verts(new_verts):
        verts_to_delete = [v for v in new_verts if len(v.link_faces) == 0]
        if verts_to_delete:
            bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
    
    def remove_original_mesh():
        bmesh.ops.delete(bm, geom=original_faces, context='FACES')
    
    # prepare data
    face_sides = create_face_data(original_faces)
    original_edge_data_map = create_edge_data(original_edges, face_sides)
    original_vert_groups_map = create_groups(original_verts, original_edge_data_map)
    
    if fix_intersections:
        create_regions(original_vert_groups_map)
    
    # generate new mesh
    new_verts_list, vert_open_verts_map = make_crossings(original_vert_groups_map)
    
    if rim != 'NONE':
        make_boundary_faces(original_edges, vert_open_verts_map, original_vert_groups_map, face_sides)
    
    if rim != 'ONLY_CLEAN' and rim != 'ONLY_FULL':
        make_faces(face_sides)
    
    # cleanup
    remove_loose_verts(new_verts_list)
    remove_original_mesh()
    bm.normal_update()
    
    # extract final geometry
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    output_verts = [vert.co[:] for vert in bm.verts]
    output_edges = [[edge.verts[0].index, edge.verts[1].index] for edge in bm.edges]
    output_faces = [[vert.index for vert in face.verts] for face in bm.faces]
    
    bm.free()
    
    print('manifold_solidify')
    return output_verts, output_edges, output_faces

# Main entry point for Sverchok
if verts:
    # Convert boolean inputs
    even_thickness_bool = bool(even_thickness)
    high_quality_thickness_bool = bool(high_quality_thickness)
    fix_intersections_bool = bool(fix_intersections)
    
    boundary_fix = self.custom_enum
    rim = self.custom_enum_2
    
    # Process each mesh in the list
    all_verts = []
    all_edges = []
    all_faces = []
    
    for i in range(len(verts)):
        current_verts = verts[i] if i < len(verts) else []
        current_edges = edges[i] if i < len(edges) else []
        current_faces = faces[i] if i < len(faces) else []
        
        if current_verts:
            v, e, f = manifold_solidify(
                thickness=thickness,
                even_thickness=even_thickness_bool,
                high_quality_thickness=high_quality_thickness_bool,
                fix_intersections=fix_intersections_bool,
                boundary_fix=boundary_fix,
                rim=rim,
                input_verts=current_verts,
                input_edges=current_edges,
                input_faces=current_faces
            )
            
            all_verts.append(v)
            all_edges.append(e)
            all_faces.append(f)
    
    verts_out = all_verts
    edges_out = all_edges
    faces_out = all_faces
else:
    verts = []
    edges = []
    faces = []