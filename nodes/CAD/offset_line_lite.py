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

import bpy
from bpy.props import FloatProperty,  EnumProperty
import math
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from collections import defaultdict

def offset_polyline(pts, dist, plane=(0, 1), miter_limit=4.0):
    """Офсет открытой полилинии. pts — список [x,y,z] (или [x,y]).
    dist>0 — влево от направления обхода, dist<0 — вправо.
    plane: (0,1)=XY, (0,2)=XZ, (1,2)=YZ — плоскость, в которой офсетим.
    miter_limit: во сколько раз шип на угле может превышать dist."""
    if len(pts) < 2:
        return [list(p) for p in pts]
    P = [[float(p[plane[0]]), float(p[plane[1]])] for p in pts]
    n = len(P)
    seg = [[P[i+1][0]-P[i][0], P[i+1][1]-P[i][1]] for i in range(n-1)]
    ln = [math.hypot(a, b) for a, b in seg]
    u = [[a/l, b/l] for (a, b), l in zip(seg, ln)]       # направления сегментов
    nr = [[-b, a] for a, b in u]                          # левые нормали
    out = [None] * n
    print(dist,nr[0])
    out[0]  = [P[0][0] + dist*nr[0][0],  P[0][1] + dist*nr[0][1]]
    out[-1] = [P[-1][0] + dist*nr[-1][0], P[-1][1] + dist*nr[-1][1]]
    for i in range(1, n-1):
        m = [nr[i-1][0]+nr[i][0], nr[i-1][1]+nr[i][1]]    # сумма нормалей = биссектриса
        lm = math.hypot(*m)
        if lm < 1e-9:                                     # разворот на 180°
            out[i] = [P[i][0] + dist*nr[i-1][0], P[i][1] + dist*nr[i-1][1]]
            continue
        m = [m[0]/lm, m[1]/lm]
        cos_half = max(m[0]*nr[i-1][0] + m[1]*nr[i-1][1], 1.0/miter_limit)
        ml = dist / cos_half                              # длина шипа
        out[i] = [P[i][0] + m[0]*ml, P[i][1] + m[1]*ml]
    if len(pts[0]) == 3:                                  # вернуть в 3D
        res = []
        for i, p in enumerate(pts):
            q = list(p); q[plane[0]], q[plane[1]] = out[i]; res.append(q)
        return res
    return out

def chains_from_edges(edges):
    """Разбивает рёбра на связные цепочки. Возвращает списки индексов вершин."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b); adj[b].append(a)
    used = set()
    chains = []
    def walk(start, first):
        """ Сортируем """
        chain = [start, first]
        used.add((min(start, first), max(start, first)))
        cur = first
        while True:
            nxt = [w for w in adj[cur] if (min(cur, w), max(cur, w)) not in used]
            if len(nxt) != 1:
                break
            w = nxt[0]
            used.add((min(cur, w), max(cur, w)))
            chain.append(w); cur = w
        return chain
    for s in [v for v in adj if len(adj[v]) == 1]:          # сначала концевые вершины
        w = adj[s][0]
        if (min(s, w), max(s, w)) not in used:
            chains.append(walk(s, w))
    for a, b in edges:                                       # остатки (замкнутые и Y-разветвления)
        if (min(a, b), max(a, b)) not in used:
            chains.append(walk(a, b))
    return chains


class SvOffsetLineLiteNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Offset Line 2D Lite
    Tooltip: Offsetting a Line into 2D space lite mod

    Only X and Y dimensions of input points will be taken for work.
    """
    bl_idname = 'SvOffsetLineLiteNode'
    bl_label = 'Offset Line 2D Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OFFSET_LINE'

    offset: FloatProperty(
        name='offset', description='Distance of offset (greater than zero. Zero will be replaced by 0.001)',
        default=0.1, update=updateNode)
    
    matrix_mode_auto: bpy.props.BoolProperty(
        default=True,
        name='Auto',
        description='True: Calc matrix automatically with first face/polygon to get horizontal plane to work with Offset Line\nFalse - use World XY plane for matrix',
        update=updateNode,
    )

    plane_types = [
            ('XY', "XY plane", "X and Y plane with Z up", 0),
            ('XZ' , "XZ plane", "X and Z plane with Y up", 1),
            ('YZ' , "YZ plane", "Y and Z plane with X up", 2),
        ]

    plane_type : EnumProperty(
        name = "Plane",
        items = plane_types,
        default = 'XY',
        update = updateNode) # type: ignore

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'plane_type', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vers')
        self.inputs.new('SvStringsSocket', "Edgs")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'

        self.outputs.new('SvVerticesSocket', 'Vers')
        self.outputs.new('SvStringsSocket', "Edgs")

    def process(self):

        if not any(socket.is_linked for socket in list(self.outputs)+list(self.inputs)):
            return

        if not all(socket.is_linked for socket in self.inputs[:2]):
            raise SvNotFullyConnected(self, sockets=["Vers", "Edgs"])

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vers'].sv_get()
        edges_in = self.inputs['Edgs'].sv_get()
        shifter = self.inputs['Offset'].sv_get()[0]

        # Main circuit
        offset_line = []
        for vobj, eobj in zip(verts_in, edges_in):
            for shift in shifter:
                chains = chains_from_edges(eobj)
                match self.plane_type:
                    case "XY": plane = (0,1)
                    case "XZ": plane = (0,2)
                    case "YZ": plane = (1,2)
                for c in chains:
                    line = [vobj[i] for i in c]
                    offset_line.append(offset_polyline(line, shift, plane=plane))

        # nothing done
        if not len(offset_line[0]):
            return

        edgs = [[[i-1,i] for i in range(len(offs)) if i!=0] for offs in offset_line]

        self.outputs['Vers'].sv_set(offset_line)
        self.outputs['Edgs'].sv_set(edgs)

def register():
    bpy.utils.register_class(SvOffsetLineLiteNode)


def unregister():
    bpy.utils.unregister_class(SvOffsetLineLiteNode)

if __name__ == '__main__': register()