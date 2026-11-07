# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import math

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode


def split_edges_at_intersections(verts, edges, angle_threshold=180.0, close_loops=True):
    """
    Разбивает цепочки линий в точках пересечения (где соединяется >2 линий)
    и в точках, где угол между сегментами превышает angle_threshold.

    Parameters:
    verts: список вершин [[x,y,z], ...]
    edges: список рёбер [[i,j], ...]
    angle_threshold: порог угла в градусах (180.0 - только узлы со степенью != 2)
    close_loops: замыкать ли контуры

    Returns:
    out_verts: список подсписков вершин (каждый подсписок - отдельная линия)
    out_edges: список подсписков рёбер (локальные индексы)
    cyclic: список флагов замкнутости
    lengths: список длин каждой линии
    total_length: суммарная длина всех линий
    """

    out_verts = []
    out_edges = []
    cyclic = []
    lengths = []
    total_length = 0.0

    if not edges:
        return out_verts, out_edges, cyclic, lengths, total_length

    def dist3(p, q):
        dx = p[0] - q[0]
        dy = p[1] - q[1]
        dz = (p[2] - q[2]) if (len(p) > 2 and len(q) > 2) else 0.0
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    # Считаем степень каждой вершины
    degree = {}
    for e in edges:
        a, b = int(e[0]), int(e[1])
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1

    # Строим граф смежности (нужен и для углов)
    adj = {}
    for e in edges:
        a, b = int(e[0]), int(e[1])
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    # Узлы - вершины со степенью != 2
    nodes = set(v for v, d in degree.items() if d != 2)

    # Дополнительно: вершины degree == 2 с изломом больше порога
    if angle_threshold < 180.0:
        for v, d in degree.items():
            if d == 2 and len(adj.get(v, [])) == 2:
                n1, n2 = adj[v][0], adj[v][1]
                p0, p1, p2 = verts[v], verts[n1], verts[n2]

                dx1 = p0[0] - p1[0]
                dy1 = p0[1] - p1[1]
                dz1 = (p0[2] - p1[2]) if (len(p0) > 2 and len(p1) > 2) else 0.0
                dx2 = p2[0] - p0[0]
                dy2 = p2[1] - p0[1]
                dz2 = (p2[2] - p0[2]) if (len(p2) > 2 and len(p0) > 2) else 0.0

                len1 = math.sqrt(dx1 * dx1 + dy1 * dy1 + dz1 * dz1)
                len2 = math.sqrt(dx2 * dx2 + dy2 * dy2 + dz2 * dz2)

                if len1 > 1e-9 and len2 > 1e-9:
                    dot = dx1 * dx2 + dy1 * dy2 + dz1 * dz2
                    cos_angle = max(-1.0, min(1.0, dot / (len1 * len2)))
                    angle_deg = math.degrees(math.acos(cos_angle))
                    if angle_deg > angle_threshold:
                        nodes.add(v)

    # Если все вершины degree==2 и нет узлов - замкнутый контур
    if not nodes:
        start = int(edges[0][0])
        nodes = {start}

    visited_edges = set()

    def edge_key(a, b):
        return (min(a, b), max(a, b))

    result_lines = []

    # Обход цепочек от узлов
    for start_node in sorted(nodes):
        for neighbor in adj.get(start_node, []):
            ek = edge_key(start_node, neighbor)
            if ek in visited_edges:
                continue

            chain = [start_node, neighbor]
            visited_edges.add(ek)
            prev, curr = start_node, neighbor

            while curr not in nodes:
                next_verts = [n for n in adj[curr] if n != prev]
                if not next_verts:
                    break
                nxt = next_verts[0]
                ek2 = edge_key(curr, nxt)
                if ek2 in visited_edges:
                    break
                visited_edges.add(ek2)
                chain.append(nxt)
                prev, curr = curr, nxt

            result_lines.append((chain, False))

    # Оставшиеся непосещённые рёбра (замкнутые контуры без узлов)
    for e in edges:
        a, b = int(e[0]), int(e[1])
        ek = edge_key(a, b)
        if ek in visited_edges:
            continue

        chain = [a, b]
        visited_edges.add(ek)
        prev, curr = a, b

        while True:
            next_verts = [n for n in adj[curr] if n != prev]
            if not next_verts:
                break
            nxt = next_verts[0]
            ek2 = edge_key(curr, nxt)
            if ek2 in visited_edges:
                break
            visited_edges.add(ek2)
            chain.append(nxt)
            prev, curr = curr, nxt

        is_cyclic = len(chain) > 2 and chain[0] == chain[-1]
        if is_cyclic:
            chain = chain[:-1]
        result_lines.append((chain, is_cyclic))

    # Формируем выходные данные + считаем длины
    for chain, is_cyclic in result_lines:
        if len(chain) < 2:
            continue
        line_coords = []
        for idx in chain:
            if 0 <= idx < len(verts):
                line_coords.append(list(verts[idx]))
            else:
                line_coords.append([0.0, 0.0, 0.0])

        line_edges = [[i, i + 1] for i in range(len(chain) - 1)]
        if is_cyclic and close_loops and len(chain) > 2:
            line_edges.append([len(chain) - 1, 0])
            line_coords_closed = line_coords + [line_coords[0]]
        else:
            line_coords_closed = line_coords

        # Длина линии
        line_len = 0.0
        for i in range(len(line_coords_closed) - 1):
            line_len += dist3(line_coords_closed[i], line_coords_closed[i + 1])

        out_verts.append(line_coords)
        out_edges.append(line_edges)
        cyclic.append(is_cyclic)
        lengths.append(line_len)
        total_length += line_len

    return out_verts, out_edges, cyclic, lengths, total_length


class SvEdgenetToSegmentsNode(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    '''
    Triggers: Split edges at intersections
    Tooltip: Split edge chains at intersection points and at sharp angles
    '''
    bl_idname = 'SvEdgenetToSegmentsNode'
    bl_label = 'Edgenet to Segments'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SEPARATE_LOOSE_PARTS'

    join: bpy.props.BoolProperty(
        name="Join",
        description="If checked, generate one flat list of segments for all input meshes; "
                    "otherwise, generate separate list of segments for each input mesh",
        default=True,
        update=updateNode)

    def update_sockets(self, context):
        self.outputs['Cyclic'].hide_safe = not self.cycle
        updateNode(self, context)

    cycle: bpy.props.BoolProperty(
        name="Close Loops",
        description="When checked, closed loops are detected and their first/last points merged",
        default=True,
        update=update_sockets)

    angle_threshold: bpy.props.FloatProperty(
        name="Angle Threshold",
        description="Split at vertices where the turn angle exceeds this value (degrees). "
                    "180.0 means split only at intersection points (degree != 2)",
        default=180.0,
        min=0.0,
        max=180.0,
        #subtype='ANGLE',
        update=updateNode)

    def draw_buttons(self, context, layout):
        #layout.prop(self, 'cycle')
        pass

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'join')
        #layout.prop(self, 'cycle')

    def rclick_menu(self, context, layout):
        self.draw_buttons_ext(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Angle Threshold').prop_name = 'angle_threshold'

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Cyclic')
        self.outputs.new('SvStringsSocket', 'Lengths')
        self.outputs.new('SvStringsSocket', 'Total Length')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        verts = self.inputs[0].sv_get(deepcopy=False)
        edges = self.inputs[1].sv_get(deepcopy=False)

        if self.inputs['Angle Threshold'].is_linked:
            angles = self.inputs['Angle Threshold'].sv_get(deepcopy=False)
        else:
            angles = [[self.angle_threshold]]

        verts_out = []
        edges_out = []
        cyclic_out = []
        lengths_out = []
        total_length_out = []

        if self.join:
            new_verts = verts_out.extend
            new_edges = edges_out.extend
            new_cyclic = cyclic_out.extend
            new_lengths = lengths_out.extend
        else:
            new_verts = verts_out.append
            new_edges = edges_out.append
            new_cyclic = cyclic_out.append
            new_lengths = lengths_out.append

        for vecs, edgs, ang in zip_long_repeat(verts, edges, angles):
            angle_val = ang[0] if isinstance(ang, (list, tuple)) else ang
            v_out, e_out, cyc, lens, total = split_edges_at_intersections(
                vecs, edgs, angle_threshold=angle_val, close_loops=self.cycle
            )
            new_verts(v_out)
            new_edges(e_out)
            new_cyclic(cyc)
            new_lengths(lens)
            total_length_out.append(total)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Cyclic'].sv_set(cyclic_out)
        self.outputs['Lengths'].sv_set([lengths_out])
        self.outputs['Total Length'].sv_set(total_length_out)


def register():
    bpy.utils.register_class(SvEdgenetToSegmentsNode)


def unregister():
    bpy.utils.unregister_class(SvEdgenetToSegmentsNode)

if __name__=='__main__': 
    register()
    #bpy.data.node_groups['Sverchok'].nodes.new('SvEdgenetToSegmentsNode')