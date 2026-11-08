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

def _seg_normal(p0, p1):
    """Левая единичная нормаль сегмента p0->p1 (2D)."""
    d = p1 - p0
    l = d.length
    if l < 1e-12:
        return Vector((0.0, 0.0)), d
    u = d / l
    return Vector((-u.y, u.x)), u

def _v2(p, plane):
    return Vector((float(p[plane[0]]), float(p[plane[1]])))


# ---------------------------------------------------------------------------
#  Офсет (только смещение по нормалям + miter с clamp)
# ---------------------------------------------------------------------------

def offset_polyline(pts, dist, plane=(0, 1), miter_limit=4.0, closed=False):
    """
    Офсет полилинии. pts — список [x,y,z] (или [x,y]).
    dist>0 — влево от направления обхода, dist<0 — вправо.
    closed=True — замкнутый контур: ровно n сегментов, miter для всех n
    вершин, включая i=0 (по нормалям n-1 и 0).
    """
    if len(pts) < 2:
        return [list(p) for p in pts]

    P = [_v2(p, plane) for p in pts]
    n = len(P)

    # --- сегменты ---------------------------------------------------------
    if closed:
        seg_pairs = [(P[i], P[(i + 1) % n]) for i in range(n)]   # ровно n
    else:
        seg_pairs = [(P[i], P[i + 1]) for i in range(n - 1)]

    normals = []
    for a, b in seg_pairs:
        nr, _ = _seg_normal(a, b)
        normals.append(nr)

    def _miter(n0, n1, pivot):
        m = n0 + n1
        lm = m.length
        if lm < 1e-9:
            return pivot + n0 * dist
        m = m / lm
        cos_half = max(m.dot(n0), 1.0 / miter_limit)
        if cos_half <= 1e-9:
            cos_half = 1.0 / miter_limit
        ml = dist / cos_half
        max_ml = abs(dist) * miter_limit
        if abs(ml) > max_ml:
            ml = math.copysign(max_ml, ml)
        return pivot + m * ml

    out = [None] * n

    if closed:
        for i in range(n):
            n0 = normals[(i - 1) % n]
            n1 = normals[i]
            out[i] = _miter(n0, n1, P[i])
    else:
        out[0] = P[0] + normals[0] * dist
        out[-1] = P[-1] + normals[-1] * dist
        for i in range(1, n - 1):
            out[i] = _miter(normals[i - 1], normals[i], P[i])

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

    return res


# ---------------------------------------------------------------------------
#  fix_intersections для 2D-линии
# ---------------------------------------------------------------------------


def fix_offset_intersections(orig_pts, off_pts, closed, plane=(0, 1),
                             merge_eps=1e-4):
    n = len(orig_pts)
    if n < 2:
        return ([Vector((p.x, p.y)) for p in off_pts],
                ([[i, (i + 1) % n] for i in range(n)] if closed
                 else [[i, i + 1] for i in range(n - 1)]),
                [[i] for i in range(n)])

    P = [Vector((p.x, p.y)) for p in orig_pts]
    O = [Vector((p.x, p.y)) for p in off_pts]

    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    seg_range = range(n) if closed else range(n - 1)
    for i in seg_range:
        j = (i + 1) % n
        d_off = O[j] - O[i]
        d_orig = P[j] - P[i]
        L_orig = d_orig.length

        # 1) точное совпадение
        if d_off.length < merge_eps:
            union(i, j)
            continue

        # 2) переворот / схлопывание: проекция на исходное направление
        if L_orig > 1e-12:
            u = d_orig / L_orig
            proj = d_off.dot(u)
            if proj <= merge_eps:        # <-- ключевой фикс
                union(i, j)

    # --- сжатие ---
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    order = []
    seen = set()
    for i in range(n):
        r = find(i)
        if r not in seen:
            seen.add(r)
            order.append(r)

    new_pts = []
    index_map = []
    for r in order:
        idxs = groups[r]
        acc = Vector((0.0, 0.0))
        for k in idxs:
            acc += O[k]
        new_pts.append(acc / len(idxs))
        index_map.append(sorted(idxs))

    m = len(new_pts)
    if closed:
        edges = ([] if m < 3
                 else [[i, (i + 1) % m] for i in range(m)])
    else:
        edges = ([] if m < 2
                 else [[i, i + 1] for i in range(m - 1)])

    return new_pts, edges, index_map


# ---------------------------------------------------------------------------
#  chains_from_edges — с корректным определением замкнутости
# ---------------------------------------------------------------------------

def chains_from_edges(edges):
    """
    Разбивает рёбра на связные цепочки.
    Возвращает список (indices, closed):
      indices — список индексов вершин цепочки;
      closed  — True, если цепочка образует цикл (indices[0] -> ... ->
                indices[-1] -> indices[0]).
    Для замкнутой цепочки start НЕ дублируется в конце.
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
        closed = False
        while True:
            nxt = [w for w in adj[cur] if edge_key(cur, w) not in used]
            if len(nxt) != 1:
                break
            w = nxt[0]
            used.add(edge_key(cur, w))
            if w == start:
                closed = True
                break                     # не добавляем start повторно
            chain.append(w)
            cur = w
        return chain, closed

    chains = []

    # 1) цепочки, начинающиеся с концевых вершин (степень 1)
    for s in [v for v in adj if len(adj[v]) == 1]:
        for w in adj[s]:
            if edge_key(s, w) not in used:
                c, cl = walk(s, w)
                chains.append((c, cl))

    # 2) остатки — циклы или Y-разветвления
    for a, b in edges:
        if edge_key(a, b) not in used:
            c, cl = walk(a, b)
            chains.append((c, cl))

    return chains


# ---------------------------------------------------------------------------
#  Нода
# ---------------------------------------------------------------------------

class SvOffsetLineLiteNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Offset Line 2D Lite
    Tooltip: Offsetting a Line into 2D space lite mod
    """
    bl_idname = 'SvOffsetLineLiteNode'
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

    merge_eps: FloatProperty(
        name='Merge eps',
        description='Min length of offset segment; shorter segments are '
                    'collapsed into a point',
        default=2e-3, min=0.0, precision=6,
        update=updateNode)

    plane_type: EnumProperty(
        name="Plane",
        items=plane_types,
        default='XY',
        update=updateNode)

    # fix_intersections и miter_limit оставляем; closed убран — только авто
    fix_intersections: BoolProperty(
        name='Fix intersections',
        description='Collapse offset vertices whose segments flip / '
                    'cross each other',
        default=False,
        update=updateNode)

    miter_limit: FloatProperty(
        name='Miter limit',
        description='Max spike length multiplier at sharp angles',
        default=4.0, min=1.0, update=updateNode)

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'plane_type', expand=True)
        col.prop(self, 'fix_intersections')
        col.prop(self, 'miter_limit')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'merge_eps')

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
                for c, is_closed in chains:
                    if len(c) < 2:
                        continue

                    line = [vobj[i] for i in c]

                    # офсет: closed — только из топологии цепочки
                    off3d = offset_polyline(
                        line, shift, plane=plane,
                        miter_limit=self.miter_limit,
                        closed=is_closed)

                    # fix_intersections
                    if self.fix_intersections and len(line) >= 2:
                        orig2d = [_v2(p, plane) for p in line]
                        off2d = [_v2(p, plane) for p in off3d]

                        new_pts, new_edges, index_map = fix_offset_intersections(
                            orig2d, off2d, is_closed, merge_eps=self.merge_eps)

                        # new_pts — короче, чем line. z берём из первой исходной точки группы.
                        off3d_final = []
                        for k, p2d in enumerate(new_pts):
                            src = line[index_map[k][0]]
                            q = list(src)
                            q[plane[0]] = p2d.x
                            q[plane[1]] = p2d.y
                            off3d_final.append(q)

                        offset_lines.append(off3d_final)
                        all_edges.append(new_edges)
                    else:
                        offset_lines.append(off3d)
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
    bpy.utils.register_class(SvOffsetLineLiteNode)


def unregister():
    bpy.utils.unregister_class(SvOffsetLineLiteNode)


if __name__ == '__main__':
    register()