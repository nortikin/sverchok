# ##### BEGIN GPL LICENSE BLOCK #####
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# ##### END GPL LICENSE BLOCK #####

"""
SvDimensionDraw
---------------
Draw real-world edge lengths and face areas for masked indices.
Text always faces the viewer (screen-space blf). Optional GPU ticks.
"""

from types import SimpleNamespace
import numpy as np

import bpy
import blf
import gpu
from bpy.props import (
    BoolProperty, FloatProperty, IntProperty, FloatVectorProperty, StringProperty
)
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

from sverchok.data_structure import updateNode, node_id, match_long_repeat
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.geom import multiply_vectors_deep

# ---------------------------------------------------------------------------
# simple line shader (screen-space width, same style as Viewer Draw Mk5)
# ---------------------------------------------------------------------------

LINE_VS = '''
void main()
{
    vColor = color;
    vec4 p = viewProjectionMatrix * vec4(pos, 1.0);
    vec4 q = viewProjectionMatrix * vec4(other, 1.0);
    vec2 half_vp = viewportSize * 0.5;
    vec2 sp = p.xy / p.w * half_vp;
    vec2 sq = q.xy / q.w * half_vp;
    vec2 d = (corner.y < 0.5) ? (sq - sp) : (sp - sq);
    float len = length(d);
    d = (len > 1e-6) ? d / len : vec2(1.0, 0.0);
    vec2 n = vec2(-d.y, d.x);
    float hw = lineWidth * 0.5 + 1.0;
    p.xy += n * (corner.x * hw) / half_vp * p.w;
    gl_Position = p;
    vDist = corner.x * hw;
}
'''

LINE_FS = '''
void main()
{
    float a = clamp(lineWidth * 0.5 + 0.5 - abs(vDist), 0.0, 1.0);
    if (a <= 0.0) discard;
    FragColor = vec4(vColor.rgb, vColor.a * a);
}
'''

_LINE_SHADER = None

def get_line_shader():
    global _LINE_SHADER
    if _LINE_SHADER is None:
        iface = gpu.types.GPUStageInterfaceInfo("sv_dim_line_iface")
        iface.smooth('VEC4', "vColor")
        iface.no_perspective('FLOAT', "vDist")
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant('MAT4', "viewProjectionMatrix")
        info.push_constant('VEC2', "viewportSize")
        info.push_constant('FLOAT', "lineWidth")
        info.vertex_in(0, 'VEC3', "pos")
        info.vertex_in(1, 'VEC3', "other")
        info.vertex_in(2, 'VEC2', "corner")
        info.vertex_in(3, 'VEC4', "color")
        info.vertex_out(iface)
        info.fragment_out(0, 'VEC4', "FragColor")
        info.vertex_source(LINE_VS)
        info.fragment_source(LINE_FS)
        _LINE_SHADER = gpu.shader.create_from_info(info)
    return _LINE_SHADER

def expand_segments(A, B, colors):
    """Each segment → screen-space quad (4 verts, 2 tris)."""
    m = len(A)
    if m == 0:
        return None
    pos = np.stack([A, A, B, B], axis=1).reshape(-1, 3).astype(np.float32)
    other = np.stack([B, B, A, A], axis=1).reshape(-1, 3).astype(np.float32)
    corner = np.tile(
        np.array([[1, 0], [-1, 0], [1, 1], [-1, 1]], np.float32), (m, 1)
    )
    color = np.repeat(colors, 4, axis=0).astype(np.float32)
    idx = (
        np.arange(m, dtype=np.uint32)[:, None] * 4
        + np.array([0, 1, 2, 2, 1, 3], np.uint32)
    ).reshape(-1)
    return SimpleNamespace(pos=pos, other=other, corner=corner, color=color, idx=idx)

# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def face_centroid_area(V, poly):
    """Return (centroid, area) for a polygon given vertex array V and index list."""
    pts = V[np.asarray(poly, dtype=np.int64)]
    n = len(pts)
    if n < 3:
        return pts.mean(axis=0), 0.0
    # fan triangulation from first vertex
    area = 0.0
    c = np.zeros(3, dtype=np.float64)
    for i in range(1, n - 1):
        a, b, c_ = pts[0], pts[i], pts[i + 1]
        cross = np.cross(b - a, c_ - a)
        tri_area = 0.5 * np.linalg.norm(cross)
        area += tri_area
        c += (a + b + c_) * (tri_area / 3.0)
    if area > 1e-12:
        c /= area
    else:
        c = pts.mean(axis=0)
    return c, float(area)

def build_dimension_data(verts_s, edges_s, faces_s, edge_masks, face_masks, mats, scale):
    """
    Returns list of dicts:
        { 'pos': Vector, 'text': str, 'kind': 'edge'|'face' }
    and optional tick segments (A, B, color).
    """
    labels = []
    tick_A, tick_B, tick_C = [], [], []

    edge_color = np.array([1.0, 0.85, 0.2, 1.0], dtype=np.float32)
    face_color = np.array([0.3, 0.85, 1.0, 1.0], dtype=np.float32)

    for i, verts in enumerate(verts_s):
        V = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        if len(V) == 0:
            continue
        if mats:
            M = np.array(mats[i % len(mats)], dtype=np.float64)
            V = V @ M[:3, :3].T + M[:3, 3]

        # ---- edges ----
        emask = edge_masks[i % len(edge_masks)] if edge_masks else []
        edges = edges_s[i % len(edges_s)] if edges_s else []
        if emask and edges:
            E = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
            for ei in emask:
                try:
                    ei = int(ei)
                    if ei < 0 or ei >= len(E):
                        continue
                    a, b = E[ei]
                    pa, pb = V[a], V[b]
                    length = float(np.linalg.norm(pb - pa)) * scale
                    mid = (pa + pb) * 0.5
                    labels.append({
                        'pos': Vector(mid),
                        'text': None,  # filled later with formatting
                        'value': length,
                        'kind': 'edge',
                    })
                    # short perpendicular tick (optional visual cue)
                    d = pb - pa
                    ln = np.linalg.norm(d)
                    if ln > 1e-9:
                        d = d / ln
                        # arbitrary perpendicular in world space
                        n = np.cross(d, [0, 0, 1])
                        if np.linalg.norm(n) < 1e-6:
                            n = np.cross(d, [0, 1, 0])
                        n = n / (np.linalg.norm(n) + 1e-12) * 0.05  # small world size
                        tick_A.append(mid - n)
                        tick_B.append(mid + n)
                        tick_C.append(edge_color)
                except Exception:
                    continue

        # ---- faces ----
        fmask = face_masks[i % len(face_masks)] if face_masks else []
        faces = faces_s[i % len(faces_s)] if faces_s else []
        if fmask and faces:
            for fi in fmask:
                try:
                    fi = int(fi)
                    if fi < 0 or fi >= len(faces):
                        continue
                    poly = faces[fi]
                    if len(poly) < 3:
                        continue
                    cent, area = face_centroid_area(V, poly)
                    labels.append({
                        'pos': Vector(cent),
                        'text': None,
                        'value': area * (scale ** 2),
                        'kind': 'face',
                    })
                except Exception:
                    continue

    ticks = None
    if tick_A:
        ticks = expand_segments(
            np.array(tick_A, dtype=np.float64),
            np.array(tick_B, dtype=np.float64),
            np.array(tick_C, dtype=np.float32),
        )
    return labels, ticks

# ---------------------------------------------------------------------------
# draw callback
# ---------------------------------------------------------------------------

def draw_dimensions(context, args):
    labels, ticks, cfg = args
    region = context.region
    rd = context.region_data
    if region is None or rd is None:
        return

    # --- GPU ticks ---
    if ticks is not None and cfg.draw_ticks:
        shader = get_line_shader()
        batch = batch_for_shader(
            shader, 'TRIS',
            {
                "pos": ticks.pos,
                "other": ticks.other,
                "corner": ticks.corner,
                "color": ticks.color,
            },
            indices=ticks.idx,
        )
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS_EQUAL')
        shader.bind()
        shader.uniform_float("viewProjectionMatrix", rd.perspective_matrix)
        shader.uniform_float("viewportSize", (float(region.width), float(region.height)))
        shader.uniform_float("lineWidth", float(cfg.line_width))
        batch.draw(shader)
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')

    # --- text (always camera-facing because it is screen-space) ---
    font_id = 0
    blf.size(font_id, cfg.text_height)
    # try a monospace font if available
    try:
        # Blender ships with some fonts; fallback is fine
        blf.size(font_id, cfg.text_height)
    except Exception:
        pass

    r, g, b, a = cfg.text_color
    blf.color(font_id, r, g, b, a)

    fmt = f"{{:.{cfg.decimals}f}}{cfg.units}"
    for lab in labels:
        # project 3d → 2d
        co_2d = location_3d_to_region_2d(region, rd, lab['pos'])
        if co_2d is None:
            continue
        text = fmt.format(lab['value'])
        # centre the text roughly
        tw, th = blf.dimensions(font_id, text)
        x = co_2d.x - tw * 0.5
        y = co_2d.y - th * 0.5
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, text)

# ---------------------------------------------------------------------------
# node
# ---------------------------------------------------------------------------

class SvDimensionDraw(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: dimension length area mask
    Tooltip: Draw real-world edge lengths and face areas for masked indices.\n
             Text always faces the viewer.
    """
    bl_idname = 'SvDimensionDraw'
    bl_label = 'Dimension Draw'
    bl_icon = 'DRIVER_DISTANCE'
    sv_icon = 'SV_NUMBER'

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode)

    text_height: IntProperty(
        name='Text Height', description='Font size in pixels',
        default=14, min=6, max=72, update=updateNode)

    decimals: IntProperty(
        name='Decimals', default=2, min=0, max=8, update=updateNode)

    units: StringProperty(
        name='Units', description='Suffix after the number',
        default='', update=updateNode)

    scale: FloatProperty(
        name='Scale', description='Multiply displayed values (e.g. 1000 for mm)',
        default=1.0, min=0.0, update=updateNode)

    text_color: FloatVectorProperty(
        name='Text Color', subtype='COLOR', size=4,
        default=(1.0, 1.0, 1.0, 1.0), min=0.0, max=1.0, update=updateNode)

    draw_ticks: BoolProperty(
        name='Draw Ticks', description='Small GPU ticks at edge midpoints',
        default=True, update=updateNode)

    line_width: FloatProperty(
        name='Tick Width', default=1.5, min=0.5, max=10.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Edge Mask')
        self.inputs.new('SvStringsSocket', 'Face Mask')
        self.inputs.new('SvMatrixSocket', 'Matrix')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'activate', text='', icon='HIDE_' + ('OFF' if self.activate else 'ON'))
        row.prop(self, 'text_height')
        row = layout.row(align=True)
        row.prop(self, 'decimals')
        row.prop(self, 'scale')
        layout.prop(self, 'units')
        layout.prop(self, 'text_color', text='')
        layout.prop(self, 'draw_ticks')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'line_width')

    def process(self):
        if bpy.app.background:
            return

        n_id = node_id(self)
        callback_disable(n_id)

        if not (self.id_data.sv_show and self.activate):
            return

        inputs = self.inputs
        if not inputs['Vertices'].is_linked:
            return

        verts_s = inputs['Vertices'].sv_get(deepcopy=False, default=[[]])
        if not any(len(v) for v in verts_s):
            return

        edges_s = inputs['Edges'].sv_get(deepcopy=False, default=[[]]) if inputs['Edges'].is_linked else [[]]
        faces_s = inputs['Faces'].sv_get(deepcopy=False, default=[[]]) if inputs['Faces'].is_linked else [[]]
        edge_masks = inputs['Edge Mask'].sv_get(deepcopy=False, default=[[]]) if inputs['Edge Mask'].is_linked else [[]]
        face_masks = inputs['Face Mask'].sv_get(deepcopy=False, default=[[]]) if inputs['Face Mask'].is_linked else [[]]

        mats = []
        if inputs['Matrix'].is_linked:
            mats = inputs['Matrix'].sv_get(deepcopy=False, default=[])
            if mats:
                verts_s, mats = match_long_repeat([verts_s, mats])

        # flatten masks if they come nested
        def flatten_mask(m):
            out = []
            for item in m:
                if isinstance(item, (list, tuple)):
                    out.extend(int(x) for x in item)
                else:
                    try:
                        out.append(int(item))
                    except Exception:
                        pass
            return out

        edge_masks = [flatten_mask(m) for m in edge_masks] or [[]]
        face_masks = [flatten_mask(m) for m in face_masks] or [[]]

        labels, ticks = build_dimension_data(
            verts_s, edges_s, faces_s, edge_masks, face_masks, mats, self.scale
        )
        if not labels and ticks is None:
            return

        cfg = SimpleNamespace(
            text_height=self.text_height,
            decimals=self.decimals,
            units=self.units,
            text_color=tuple(self.text_color),
            draw_ticks=self.draw_ticks,
            line_width=self.line_width,
        )

        callback_enable(n_id, {
            'tree_name': self.id_data.name[:],
            'custom_function': draw_dimensions,
            'args': (labels, ticks, cfg),
        })

    def sv_free(self):
        callback_disable(node_id(self))

    def sv_copy(self, node):
        # new node_id on copy
        self.n_id = ''

classes = [SvDimensionDraw]
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()