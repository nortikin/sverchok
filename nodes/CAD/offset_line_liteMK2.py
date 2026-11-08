# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty
import math
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.sv_custom_exceptions import SvNotFullyConnected

from collections import defaultdict
from mathutils import Vector


# ---------------------------------------------------------------------------
#  Геометрические утилиты
# ---------------------------------------------------------------------------

def _v2(p, plane):
    return Vector((float(p[plane[0]]), float(p[plane[1]])))


def _seg_normal(p0, p1):
    """Левая единичная нормаль сегмента p0->p1 (2D)."""
    d = p1 - p0
    l = d.length
    if l < 1e-12:
        return Vector((0.0, 0.0)), d
    u = d / l
    return Vector((-u.y, u.x)), u


def offset_polyline(pts, dist, plane=(0, 1), miter_limit=4.0, closed=False):
    """
    Офсет полилинии. pts — список [x,y,z] (или [x,y]).
    dist>0 — влево от направления обхода, dist<0 — вправо.
    closed=True — обрабатывать как замкнутую: офсетятся все вершины,
    сегментов на один больше (последний -> первый).
    """
    if len(pts) < 2:
        return [list(p) for p in pts], closed

    P = [_v2(p, plane) for p in pts]
    n = len(P)

    # --- сегменты ---------------------------------------------------------
    if closed:
        # (n) сегментов для замкнутой линии
        seg_pairs = [(P[i], P[(i + 1) % n]) for i in range(n)]
    else:
        seg_pairs = [(P[i], P[i + 1]) for i in range(n - 1)]

    normals = []          # левые нормали сегментов
    dirs = []             # единичные направления сегментов
    for a, b in seg_pairs:
        nr, u = _seg_normal(a, b)
        normals.append(nr)
        dirs.append(u)

    out = [None] * n

    def _miter(idx_prev_nr, idx_cur_nr, pivot):
        """Miter-смещение вершины по двум соседним нормалям."""
        n0 = normals[idx_prev_nr]
        n1 = normals[idx_cur_nr]
        m = n0 + n1
        lm = m.length
        if lm < 1e-9:
            # разворот на 180° — берём нормаль одного сегмента
            return pivot + n0 * dist
        m = m / lm
        cos_half = max(m.dot(n0), 1.0 / miter_limit)
        if cos_half <= 1e-9:
            cos_half = 1.0 / miter_limit
        return pivot + m * (dist / cos_half)

    if closed:
        for i in range(n):
            i_prev = (i - 1) % n
            i_cur = i % n
            out[i] = _miter(i_prev, i_cur, P[i])
    else:
        # первая точка — по нормали первого сегмента
        out[0] = P[0] + normals[0] * dist
        # последняя точка — по нормали последнего сегмента
        out[-1] = P[-1] + normals[-1] * dist
        # внутренние — miter
        for i in range(1, n - 1):
            out[i] = _miter(i - 1, i, P[i])

    # --- возврат в 3D ----------------------------------------------------
    res = []
    if len(pts[0]) == 3:
        for i, p in enumerate(pts):
            q = list(p)
            q[plane[0]] = out[i].x
            q[plane[1]] = out[i].y
            res.append(q)
    else:
        res = [[out[i].x, out[i].y] for i in range(n)]

    return res, closed


# ---------------------------------------------------------------------------
#  fix_intersections — перенос логики из solidification.py
# ---------------------------------------------------------------------------

def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def fix_offset_intersections(orig_pts, off_pts, closed, plane=(0, 1),
                             iterations=100, tol=0.01, merge_tol=1e-6):
    """
    Порт идеи fix_intersections из solidification.py.

    Идея оригинала:
      * для каждой вершины хранится нормаль смещения (n) и позиция;
      * если вектор смещения вершины A и вектор смещения вершины B
        направлены навстречу (dot < 0) — значит смещённые позиции
        «прошли сквозь» друг друга -> пересечение -> вершины сливаются;
      * после слияния позиция уточняется итеративно: ищем максимальное
        расстояние r до плоскостей, заданных нормалями всех слитых
        вершин, и сдвигаем точку на r по соответствующей нормали
        (проекция в «карман» пересечения). При расходимости — сброс.

    Для 2D-линии нормаль смещения — это нормаль сегмента (или
    биссектриса в miter-угле). Слияние применяем к соседним вершинам
    цепочки и к самопересечениям «через край» (для замкнутых).

    Возвращает новый список смещённых 2D-точек Vector.
    """
    n = len(orig_pts)
    if n < 2 or len(off_pts) != n:
        return [Vector((p.x, p.y)) for p in off_pts]

    # нормали смещения (в 2D): направление original -> offset
    normals = []
    positions = []
    for i in range(n):
        d = off_pts[i] - orig_pts[i]
        if d.length < 1e-12:
            normals.append(Vector((0.0, 0.0)))
        else:
            normals.append(d.normalized())
        positions.append(off_pts[i].copy())

    # --- 1) попарная проверка «навстречу» --------------------------------
    # В original-коде это делалось для вершин, связанных общим ребром.
    # В линии — то же самое: соседние вершины цепочки (и замыкание).
    def neighbors(i):
        res = []
        if closed:
            res.append((i - 1) % n)
            res.append((i + 1) % n)
        else:
            if i > 0:
                res.append(i - 1)
            if i < n - 1:
                res.append(i + 1)
        return res

    # union-find для слияния
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
            return True
        return False

    merged_any = False
    for i in range(n):
        for j in neighbors(i):
            if j <= i:
                continue
            # условие из original: dot(v_i - o_i, p_j - p_i) < 0
            # (вектор смещения i против вектора от смещённой i к смещённой j)
            if normals[i].length == 0 or normals[j].length == 0:
                continue
            vi = off_pts[i] - orig_pts[i]
            pj_pi = off_pts[j] - off_pts[i]
            if vi.dot(pj_pi) < 0:
                # возможно, ещё проверим, что j действительно «за» i
                if union(i, j):
                    merged_any = True

    # --- 2) итеративная коррекция позиций слитых групп ------------------
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    result = [p.copy() for p in positions]

    for root, idxs in groups.items():
        if len(idxs) < 2:
            continue
        # средняя позиция
        v_co = Vector((0.0, 0.0))
        for k in idxs:
            v_co += positions[k]
        v_co /= len(idxs)

        # итеративная коррекция (порт из solidification.py)
        reset_co = v_co.copy()
        last_max_r = float('inf')
        for _ in range(iterations):
            max_r = 0.0
            for k in idxs:
                nk = normals[k]
                if nk.length == 0:
                    continue
                r = nk.dot(positions[k] - v_co)
                if r > 0:
                    if r > max_r:
                        max_r = r
                        v_co += nk * r
            if max_r < tol:
                break
            if max_r > last_max_r * 0.99:
                v_co = reset_co
                break
            last_max_r = max_r

        for k in idxs:
            result[k] = v_co.copy()

    # --- 3) «склейка» совсем близких точек (merge_tol) ------------------
    # на случай, если после коррекции точки всё ещё почти совпали
    if closed:
        for i in range(n):
            j = (i + 1) % n
            d = (result[i] - result[j]).length
            if d < merge_tol:
                mid = (result[i] + result[j]) * 0.5
                result[i] = mid
                result[j] = mid
    else:
        for i in range(n - 1):
            d = (result[i] - result[i + 1]).length
            if d < merge_tol:
                mid = (result[i] + result[i + 1]) * 0.5
                result[i] = mid
                result[i + 1] = mid

    return result


# ---------------------------------------------------------------------------
#  chains_from_edges — с поддержкой замкнутых цепочек
# ---------------------------------------------------------------------------

def chains_from_edges(edges):
    """
    Разбивает рёбра на связные цепочки. Возвращает список
    (indices, closed_flag).
    Замкнутые цепочки (циклы) корректно определяются.
    """
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    used = set()

    def edge_key(a, b):
        return (min(a, b), max(a, b))

    def walk(start, first):
        chain = [start, first]
        used.add(edge_key(start, first))
        cur = first
        while True:
            nxt = [w for w in adj[cur] if edge_key(cur, w) not in used]
            if len(nxt) != 1:
                break
            w = nxt[0]
            used.add(edge_key(cur, w))
            chain.append(w)
            cur = w
        return chain

    chains = []

    # 1) сначала цепочки, начинающиеся с концевых вершин
    for s in [v for v in adj if len(adj[v]) == 1]:
        for w in adj[s]:
            if edge_key(s, w) not in used:
                c = walk(s, w)
                chains.append((c, False))

    # 2) остатки — циклы или Y-разветвления
    for a, b in edges:
        if edge_key(a, b) not in used:
            c = walk(a, b)
            closed = False
            if len(c) >= 3:
                # цикл, если первая и последняя вершины соединены ребром
                closed = edge_key(c[0], c[-1]) in {
                    edge_key(x, y) for x, y in edges
                } and c[0] == c[-1] or False
                # walk не возвращается в начало, поэтому проверяем по adj:
                if not closed:
                    # если у c[0] и c[-1] есть ребро между собой
                    closed = c[-1] in adj[c[0]] and c[0] in adj[c[-1]]
            chains.append((c, closed))

    return chains


# ---------------------------------------------------------------------------
#  Нода
# ---------------------------------------------------------------------------

class SvOffsetLineLiteNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Offset Line 2D Lite
    Tooltip: Offsetting a Line into 2D space lite mod
    """
    bl_idname = 'SvOffsetLineLiteNodeMK2'
    bl_label = 'Offset Line 2D Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OFFSET_LINE'

    offset: FloatProperty(
        name='offset',
        description='Distance of offset (greater than zero. Zero will be replaced by 0.001)',
        default=0.1, update=updateNode)

    matrix_mode_auto: BoolProperty(
        default=True,
        name='Auto',
        description='True: Calc matrix automatically with first face/polygon '
                    'to get horizontal plane to work with Offset Line\n'
                    'False - use World XY plane for matrix',
        update=updateNode,
    )

    plane_types = [
        ('XY', "XY plane", "X and Y plane with Z up", 0),
        ('XZ', "XZ plane", "X and Z plane with Y up", 1),
        ('YZ', "YZ plane", "Y and Z plane with X up", 2),
    ]

    plane_type: EnumProperty(
        name="Plane",
        items=plane_types,
        default='XY',
        update=updateNode)

    # --- НОВЫЕ флаги ------------------------------------------------------
    closed: BoolProperty(
        name='Closed',
        description='Treat every input chain as closed loop '
                    '(offset also first/last point, segments n -> n)',
        default=False,
        update=updateNode)

    fix_intersections: BoolProperty(
        name='Fix intersections',
        description='Collapse offset vertices whose displacement vectors '
                    'point toward each other (ported from solidification)',
        default=True,
        update=updateNode)

    even_offset: BoolProperty(
        name='Even offset',
        description='Iteratively correct merged positions to keep constant '
                    'thickness at self-intersections',
        default=True,
        update=updateNode)

    miter_limit: FloatProperty(
        name='Miter limit',
        description='Max spike length multiplier at sharp angles',
        default=4.0, min=1.0, update=updateNode)

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'plane_type', expand=True)
        col.prop(self, 'closed')
        col.prop(self, 'fix_intersections')
        col.prop(self, 'even_offset')
        col.prop(self, 'miter_limit')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vers')
        self.inputs.new('SvStringsSocket', "Edgs")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'

        self.outputs.new('SvVerticesSocket', 'Vers')
        self.outputs.new('SvStringsSocket', "Edgs")

    def process(self):
        if not any(socket.is_linked for socket in list(self.outputs) + list(self.inputs)):
            return
        if not all(socket.is_linked for socket in self.inputs[:2]):
            raise SvNotFullyConnected(self, sockets=["Vers", "Edgs"])
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vers'].sv_get()
        edges_in = self.inputs['Edgs'].sv_get()
        shifter = self.inputs['Offset'].sv_get()[0]

        match self.plane_type:
            case "XY": plane = (0, 1)
            case "XZ": plane = (0, 2)
            case "YZ": plane = (1, 2)

        offset_lines = []
        all_edges = []

        for vobj, eobj in zip(verts_in, edges_in):
            chains = chains_from_edges(eobj)
            for shift in shifter:
                for c, chain_closed in chains:
                    if len(c) < 2:
                        continue

                    # флаг closed: пользовательский ИЛИ автоопределение
                    is_closed = self.closed or chain_closed

                    # исходная линия
                    line = [vobj[i] for i in c]

                    # офсет
                    off3d, _ = offset_polyline(
                        line, shift, plane=plane,
                        miter_limit=self.miter_limit,
                        closed=is_closed)

                    # fix_intersections (порт из solidification)
                    if self.fix_intersections:
                        orig2d = [_v2(p, plane) for p in line]
                        off2d = [_v2(p, plane) for p in off3d]
                        fixed2d = fix_offset_intersections(
                            orig2d, off2d, is_closed, plane=plane,
                            iterations=100 if self.even_offset else 1,
                            tol=0.01)
                        # записываем обратно в 3D
                        for i, p in enumerate(line):
                            off3d[i][plane[0]] = fixed2d[i].x
                            off3d[i][plane[1]] = fixed2d[i].y

                    offset_lines.append(off3d)

                    # рёбра
                    m = len(off3d)
                    if is_closed:
                        ed = [[i, (i + 1) % m] for i in range(m)]
                    else:
                        ed = [[i, i + 1] for i in range(m - 1)]
                    all_edges.append(ed)

        if not offset_lines:
            return

        self.outputs['Vers'].sv_set(offset_lines)
        self.outputs['Edgs'].sv_set(all_edges)


def register():
    bpy.utils.register_class(SvOffsetLineLiteNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvOffsetLineLiteNodeMK2)


if __name__ == '__main__':
    register()