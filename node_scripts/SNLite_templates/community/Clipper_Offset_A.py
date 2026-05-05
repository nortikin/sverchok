"""
in Vertices_in v d=[] n=1
in Path_indices s d=[] n=1
in Distance s d=0.1 n=2
in Miter_limit s d=2.0 n=2
in Arc_tol s d=0.001 n=2
in Iterations s d=1 n=2
enum = Miter Round Square
enum2 = Polygon ClosedLine OpenButt OpenSquare OpenRound
out Vertices_out v
out Edges_out s
# Clipper Offset A @il_de_signer
"""

import pyclipper
from mathutils import Vector
import numpy as np

def edges_to_paths(verts, edges):
    """ Группирует ребра в непрерывные цепочки (пути) """
    if not edges:
        return []
    
    impor collections
    adj = collections.defaultdict(list)
    for i, e in enumerate(edges):
        if len(e) < 2: continue
        u, v = e[0], e[1]
        adj[u].append((v, i))
        adj[v].append((u, i))
    
    used_edges = set()
    paths = []
    
    for i, e in enumerate(edges):
        if i in used_edges or len(e) < 2: continue
        
        path_idx = [e[0], e[1]]
        used_edges.add(i)
        
        # Проход вперед
        curr = e[1]
        while True:
            found = False
            for neighbor, edge_idx in adj[curr]:
                if edge_idx not in used_edges:
                    path_idx.append(neighbor)
                    used_edges.add(edge_idx)
                    curr = neighbor
                    found = True
                    break
            if not found: break
            
        # Проход назад
        curr = e[0]
        while True:
            found = False
            for neighbor, edge_idx in adj[curr]:
                if edge_idx not in used_edges:
                    path_idx.insert(0, neighbor)
                    used_edges.add(edge_idx)
                    curr = neighbor
                    found = True
                    break
            if not found: break
        
        # Если путь замкнут
        if len(path_idx) > 2 and path_idx[0] == path_idx[-1]:
            path_idx.pop()
            
        paths.append([verts[idx] for idx in path_idx])
    return paths

def ui(self, context, layout):
    layout.label(text="Join Type:", icon='MOD_SKIN')
    row = layout.row(align=True)
    row.prop_enum(self, "custom_enum", "Miter")
    row.prop_enum(self, "custom_enum", "Round")
    row.prop_enum(self, "custom_enum", "Square")
    
    layout.label(text="End Type:", icon='MOD_OUTLINE')
    col = layout.column(align=True)
    row2 = col.row(align=True)
    row2.prop_enum(self, "custom_enum_2", "Polygon")
    row2.prop_enum(self, "custom_enum_2", "ClosedLine")
    
    row3 = col.row(align=True)
    row3.prop_enum(self, "custom_enum_2", "OpenButt")
    row3.prop_enum(self, "custom_enum_2", "OpenSquare")
    row3.prop_enum(self, "custom_enum_2", "OpenRound")

    # Инфо-блок
    box = layout.box()
    box.label(text=f"Mode: {self.custom_enum} / {self.custom_enum_2}", icon='TOOL_SETTINGS')
    box.label(text=f"Iterations: {int(Iterations) if Iterations is not None else 1}", icon='LOOP_FORWARDS')

def run():
    if not Vertices_in:
        return [[]], [[]]

    SCALE = 1000000
    m_limit = float(Miter_limit if Miter_limit is not None else 2.0)
    a_tol = float(Arc_tol if Arc_tol is not None else 0.1)
    d_val = float(Distance if Distance is not None else 0.1)
    iters = int(max(1, Iterations)) if Iterations is not None else 1
    
    jt_map = {
        'Miter': pyclipper.JT_MITER,
        'Round': pyclipper.JT_ROUND,
        'Square': pyclipper.JT_SQUARE
    }
    et_map = {
        'Polygon': pyclipper.ET_CLOSEDPOLYGON,
        'ClosedLine': pyclipper.ET_CLOSEDLINE,
        'OpenButt': pyclipper.ET_OPENBUTT,
        'OpenSquare': pyclipper.ET_OPENSQUARE,
        'OpenRound': pyclipper.ET_OPENROUND
    }
    
    join_type = jt_map.get(self.custom_enum, pyclipper.JT_MITER)
    end_type = et_map.get(self.custom_enum_2, pyclipper.ET_CLOSEDPOLYGON)

    paths_raw = []
    used_indices = set()
    
    # Микро-смещение для эмуляции точки как пути (чтобы Clipper мог его офсетить)
    EPS = 0.00001

    # 1. Сбор путей
    if Path_indices:
        all_indices = Path_indices if isinstance(Path_indices[0], (list, tuple)) else [Path_indices]
        
        # Ребра или полигоны
        is_edges = all(len(idx) == 2 for idx in all_indices)
        
        for idx_list in all_indices:
            used_indices.update(idx_list)
            
        if is_edges:
            paths_raw = edges_to_paths(Vertices_in, all_indices)
        else:
            for idx_list in all_indices:
                if len(idx_list) == 1: # Это отдельная точка в индексах
                    v = Vertices_in[idx_list[0]]
                    paths_raw.append([v, [v[0] + EPS, v[1] + EPS, v[2]]])
                elif len(idx_list) >= 2:
                    paths_raw.append([Vertices_in[i] for i in idx_list])
                    
        # Ищем вершины, которые не вошли ни в одно ребро/полигон
        for i in range(len(Vertices_in)):
            if i not in used_indices:
                v = Vertices_in[i]
                paths_raw.append([v, [v[0] + EPS, v[1] + EPS, v[2]]])
    else:
        # Если индексов нет - проверяем формат данных
        if isinstance(Vertices_in[0][0], (list, tuple, np.ndarray)):
            # Список списков: трактуем как готовые пути
            paths_raw = Vertices_in
        else:
            # Плоский список: трактуем как один путь по старинке
            paths_raw = [Vertices_in]

    output_v = []
    output_e = []

    # 2. Итерации офсета
    for step in range(1, iters + 1):
        pco = pyclipper.PyclipperOffset()
        pco.MiterLimit = m_limit
        pco.ArcTolerance = int(a_tol * SCALE)
        
        for p in paths_raw:
            if len(p) < 2: continue
            scaled_path = [[int(v[0] * SCALE), int(v[1] * SCALE)] for v in p]
            pco.AddPath(scaled_path, join_type, end_type)
        
        current_dist = d_val * step
        solution = pco.Execute(int(current_dist * SCALE))
        
        final_v = []
        final_e = []
        v_off = 0
        
        for poly in solution:
            n = len(poly)
            if n < 2: continue
            p_verts = [[p[0]/SCALE, p[1]/SCALE, 0.0] for p in poly]
            final_v.extend(p_verts)
            for i in range(n):
                final_e.append([v_off + i, v_off + (i + 1) % n])
            v_off += n
        
        if final_v:
            output_v.append(final_v)
            output_e.append(final_e)

    if not output_v:
        return [[]], [[]]

    return output_v, output_e

# Выход
Vertices_out, Edges_out = run()
