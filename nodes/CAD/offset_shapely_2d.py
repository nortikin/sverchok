# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import math

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.sv_custom_exceptions import SvNotFullyConnected

try:
    from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False


# ---------------------------------------------------------------------------
#  Соответствие Enum -> Shapely
# ---------------------------------------------------------------------------

JOIN_STYLE = {
    'Miter': 2,   # mitre
    'Round': 1,   # round
    'Bevel': 3,   # bevel (ближайший аналог Clipper SQUARE)
}

CAP_STYLE = {
    'OpenButt':   2,  # flat
    'OpenSquare': 3,  # square
    'OpenRound':  1,  # round
}

CLOSED_TYPES = ('Polygon', 'ClosedLine')


# ---------------------------------------------------------------------------
#  Геометрические хелперы
# ---------------------------------------------------------------------------

def _arc_tol_to_quad_segs(arc_tol, distance):
    """Перевод абсолютного допуска дуги в quad_segs (как у shapely)."""
    d = max(abs(distance), 1e-9)
    ratio = max(-1.0, min(1.0, 1.0 - arc_tol / d))
    theta = 2.0 * math.acos(ratio)
    if theta <= 1e-9:
        return 64
    qs = int(math.ceil(math.pi / theta))
    return max(1, min(qs, 512))


def _iter_polygons(geom):
    """Разворачиваем Multi/Collection в плоский список Polygon."""
    if geom is None or geom.is_empty:
        return
    if isinstance(geom, Polygon):
        yield geom
    elif isinstance(geom, (MultiPolygon, GeometryCollection)):
        for g in geom.geoms:
            yield from _iter_polygons(g)


def _polygon_to_rings(poly):
    """Список колец полигона: внешнее + дыры. Каждое — список (x, y)."""
    rings = [list(poly.exterior.coords)]
    for interior in poly.interiors:
        rings.append(list(interior.coords))
    return rings


def _dedup_closing(ring):
    """Shapely замыкает кольца повтором первой точки — убираем дубль."""
    if len(ring) >= 2 and ring[0] == ring[-1]:
        return ring[:-1]
    return ring


def _ring_to_edges(n, offset, closed):
    if closed:
        return [[offset + i, offset + (i + 1) % n] for i in range(n)]
    return [[offset + i, offset + i + 1] for i in range(n - 1)]


# ---------------------------------------------------------------------------
#  Основная функция офсета
# ---------------------------------------------------------------------------

def offset_shapely(verts2d, dist, end_type, join_type, miter_limit,
                   quad_segs, arc_tol):
    """
    verts2d     : список (x, y)
    dist        : расстояние (может быть < 0 для внутрь)
    end_type    : 'Polygon' | 'ClosedLine' | 'OpenButt' | 'OpenSquare' | 'OpenRound'
    join_type   : 'Miter' | 'Round' | 'Bevel'
    miter_limit : отношение miter_length / dist
    quad_segs   : >0 — использовать как есть; <=0 — вычислить из arc_tol
    arc_tol     : абсолютный допуск дуги (fallback)

    Возвращает (verts_out, edges_out):
      verts_out — список [x, y, 0.0]
      edges_out — список [i, j]
    """
    if not HAS_SHAPELY:
        return [], []
    if not verts2d or len(verts2d) < 2:
        return [], []

    js = JOIN_STYLE.get(join_type, 2)
    d_val = float(dist)

    # quad_segs
    if quad_segs and quad_segs > 0:
        q_segs = int(quad_segs)
    else:
        q_segs = _arc_tol_to_quad_segs(float(arc_tol), d_val)

    pts = [(float(p[0]), float(p[1])) for p in verts2d]

    try:
        if end_type in CLOSED_TYPES:
            ring = list(pts)
            if ring[0] != ring[-1]:
                ring.append(ring[0])

            if end_type == 'Polygon':
                base = Polygon(ring)
                if not base.is_valid:
                    base = base.buffer(0)
                if base.is_empty:
                    return [], []
                geom = base.buffer(
                    d_val,
                    quad_segs=q_segs,
                    join_style=js,
                    mitre_limit=float(miter_limit),
                )
            else:
                # ClosedLine
                base = LineString(ring)
                geom = base.buffer(
                    d_val,
                    quad_segs=q_segs,
                    cap_style=1,
                    join_style=js,
                    mitre_limit=float(miter_limit),
                )
        else:
            base = LineString(pts)
            cap = CAP_STYLE.get(end_type, 2)
            geom = base.buffer(
                d_val,
                quad_segs=q_segs,
                cap_style=cap,
                join_style=js,
                mitre_limit=float(miter_limit),
            )
    except Exception as e:
        print(f"[OffsetShapely] buffer error: {e}")
        return [], []

    if geom is None or geom.is_empty:
        return [], []

    is_closed_output = end_type in CLOSED_TYPES

    final_v = []
    final_e = []
    v_off = 0

    for poly in _iter_polygons(geom):
        for ring in _polygon_to_rings(poly):
            ring = _dedup_closing(ring)
            n = len(ring)
            if n < 2:
                continue
            final_v.extend([[x, y, 0.0] for (x, y) in ring])
            final_e.extend(_ring_to_edges(n, v_off, is_closed_output))
            v_off += n

    return final_v, final_e


# ---------------------------------------------------------------------------
#  Нода
# ---------------------------------------------------------------------------

class SvOffsetLineShapelyNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Offset Line 2D Shapely
    Tooltip: Offsetting a Line into 2D space using Shapely buffer
    """
    bl_idname = 'SvOffsetLineShapelyNode'
    bl_label = 'Offset Line 2D Shapely'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OFFSET_LINE'
    sv_dependencies = {'shapely'}

    offset: FloatProperty(
        name='offset',
        description='Distance of offset; negative goes inward for closed paths',
        default=0.1, update=updateNode)

    miter_limit: FloatProperty(
        name='Miter limit',
        description='Ratio of miter length to offset distance',
        default=2.0, min=1.0, update=updateNode)

    arc_tol: FloatProperty(
        name='Arc tol',
        description='Absolute arc tolerance (used when Quad segs <= 0)',
        default=0.1, min=0.0, precision=6, update=updateNode)

    quad_segs: IntProperty(
        name='Quad segs',
        description='Segments per quarter circle. If > 0, overrides Arc tol',
        default=8, min=0, max=512, update=updateNode)

    join_types = [
        ('Miter', "Miter", "Mitre join", 0),
        ('Round', "Round", "Round join", 1),
        ('Bevel', "Bevel", "Bevel join (closest to Clipper Square)", 2),
    ]
    join_type: EnumProperty(
        name="Join Type",
        items=join_types,
        default='Miter',
        update=updateNode)

    end_types = [
        ('Polygon', "Polygon", "Closed polygon offset (in/out)", 0),
        ('ClosedLine', "ClosedLine", "Closed line with round caps at the seam", 1),
        #('OpenButt', "OpenButt", "Open line, flat caps", 2),
        #('OpenSquare', "OpenSquare", "Open line, square caps", 3),
        #('OpenRound', "OpenRound", "Open line, round caps", 4),
    ]
    end_type: EnumProperty(
        name="End Type",
        items=end_types,
        default='Polygon',
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Join Type:", icon='MOD_BEVEL')
        row = layout.row(align=True)
        row.prop_enum(self, "join_type", "Miter")
        row.prop_enum(self, "join_type", "Round")
        row.prop_enum(self, "join_type", "Bevel")

        layout.label(text="End Type:", icon='GP_SELECT_POINTS')
        col = layout.column(align=True)
        row2 = col.row(align=True)
        row2.prop_enum(self, "end_type", "Polygon")
        row2.prop_enum(self, "end_type", "ClosedLine")

        row3 = col.row(align=True)
        row3.prop_enum(self, "end_type", "OpenButt")
        row3.prop_enum(self, "end_type", "OpenSquare")
        row3.prop_enum(self, "end_type", "OpenRound")

        box = layout.box()
        if not HAS_SHAPELY:
            box.label(text="shapely is not installed", icon='ERROR')
        else:
            box.label(text=f"Mode: {self.join_type} / {self.end_type}",
                      icon='TOOL_SETTINGS')

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'miter_limit')
        col.prop(self, 'quad_segs')
        col.prop(self, 'arc_tol')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        self.inputs.new('SvStringsSocket', "Miter_limit").prop_name = 'miter_limit'
        self.inputs.new('SvStringsSocket', "Quad_segs").prop_name = 'quad_segs'
        self.inputs.new('SvStringsSocket', "Arc_tol").prop_name = 'arc_tol'

        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Edges")

    def process(self):
        if not any(socket.is_linked for socket in list(self.outputs) + list(self.inputs)):
            return
        if not self.inputs['Verts'].is_linked:
            raise SvNotFullyConnected(self, sockets=["Verts"])
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not HAS_SHAPELY:
            return

        verts_in = self.inputs['Verts'].sv_get()
        dist_in = self.inputs['Offset'].sv_get(deepcopy=False) if self.inputs['Offset'].is_linked else [[self.offset]]
        mlim_in = self.inputs['Miter_limit'].sv_get(deepcopy=False) if self.inputs['Miter_limit'].is_linked else [[self.miter_limit]]
        qseg_in = self.inputs['Quad_segs'].sv_get(deepcopy=False) if self.inputs['Quad_segs'].is_linked else [[self.quad_segs]]
        atol_in = self.inputs['Arc_tol'].sv_get(deepcopy=False) if self.inputs['Arc_tol'].is_linked else [[self.arc_tol]]

        out_v = []
        out_e = []

        for i, vobj in enumerate(verts_in):
            # параметры: берём i-й элемент, если есть, иначе 0-й
            def _pick(lst, idx):
                try:
                    return lst[idx][0]
                except Exception:
                    try:
                        return lst[0][0]
                    except Exception:
                        return None

            d_val = _pick(dist_in, i)
            m_val = _pick(mlim_in, i)
            q_val = _pick(qseg_in, i)
            a_val = _pick(atol_in, i)

            if d_val is None:
                continue
            d_val = -float(d_val)
            m_val = float(m_val) if m_val is not None else 2.0
            q_val = int(q_val) if q_val is not None else 8
            a_val = float(a_val) if a_val is not None else 0.1

            v_out, e_out = offset_shapely(
                vobj, d_val, self.end_type, self.join_type,
                m_val, q_val, a_val)

            if v_out:
                out_v.append(v_out)
                out_e.append(e_out)

        if not out_v:
            self.outputs['Verts'].sv_set([])
            self.outputs['Edges'].sv_set([])
            return

        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)


def register():
    bpy.utils.register_class(SvOffsetLineShapelyNode)


def unregister():
    bpy.utils.unregister_class(SvOffsetLineShapelyNode)


if __name__ == '__main__':
    register()