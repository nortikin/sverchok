# ##### BEGIN GPL LICENSE BLOCK #####
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# ##### END GPL LICENSE BLOCK #####

"""
SvDimensionDraw
---------------
CAD-style dimensions for masked edges (aligned: extension lines, dim line,
arrows) and face areas (centroid labels). Text always faces the viewer.
"""

from types import SimpleNamespace
import numpy as np

import bpy
import blf
import gpu
from bpy.props import (
    BoolProperty, FloatProperty, IntProperty, FloatVectorProperty,
    StringProperty, EnumProperty,
)
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

from sverchok.data_structure import updateNode, node_id, match_long_repeat
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable

# ---------------------------------------------------------------------------
# line shader (screen-space width)
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
    m = len(A)
    if m == 0:
        return None
    pos = np.stack([A, A, B, B], axis=1).reshape(-1, 3).astype(np.float32)
    other = np.stack([B, B, A, A], axis=1).reshape(-1, 3).astype(np.float32)
    corner = np.tile(
        np.array([[1, 0], [-1, 0], [1, 1], [-1, 1]], np.float32), (m, 1)
    )
    color = np.repeat(np.asarray(colors, dtype=np.float32), 4, axis=0)
    idx = (
        np.arange(m, dtype=np.uint32)[:, None] * 4
        + np.array([0, 1, 2, 2, 1, 3], np.uint32)
    ).reshape(-1)
    return SimpleNamespace(pos=pos, other=other, corner=corner, color=color, idx=idx)

# ---------------------------------------------------------------------------
# dimension geometry
# ---------------------------------------------------------------------------

def face_centroid_area(V, poly):
    pts = V[np.asarray(poly, dtype=np.int64)]
    n = len(pts)
    if n < 3:
        return pts.mean(axis=0), 0.0
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

def _offset_dir(edge_dir, style, view_dir):
    """Unit offset direction for the dimension line."""
    d = edge_dir.normalized()
    if style == 'HORIZONTAL':
        # dim line horizontal in XY; offset along Z or view-up
        n = Vector((0, 0, 1))
        if abs(d.dot(n)) > 0.95:
            n = Vector((0, 1, 0))
        return n.normalized()
    if style == 'VERTICAL':
        n = Vector((1, 0, 0))
        if abs(d.dot(n)) > 0.95:
            n = Vector((0, 1, 0))
        return n.normalized()
    # ALIGNED: perpendicular to edge, facing camera
    n = d.cross(view_dir)
    if n.length < 1e-6:
        n = d.cross(Vector((0, 0, 1)))
    if n.length < 1e-6:
        n = d.cross(Vector((0, 1, 0)))
    return n.normalized()

def build_aligned_dim(pa, pb, offset, extension, arrow, style, view_dir):
    """
    Returns (segments list of (Vector, Vector), text_pos Vector, length float)
    """
    pa, pb = Vector(pa), Vector(pb)
    edge = pb - pa
    length = edge.length
    if length < 1e-9:
        return [], None, 0.0

    d = edge.normalized()
    n = _offset_dir(d, style, view_dir)

    # For HORIZONTAL / VERTICAL, project endpoints so dim line is axis-aligned
    if style == 'HORIZONTAL':
        # measure along X (or longest horizontal component)
        # keep full 3D length but place dim parallel to XY projection of edge
        horiz = Vector((edge.x, edge.y, 0.0))
        if horiz.length > 1e-9:
            d = horiz.normalized()
            # re-place pb relative to pa along horizontal measure of true length
            # actually CAD horizontal dim measures delta-X; use true length still
            n = _offset_dir(d, 'ALIGNED', view_dir)
    elif style == 'VERTICAL':
        vert = Vector((0.0, 0.0, edge.z)) if abs(edge.z) > 1e-9 else Vector((0, edge.y, 0))
        if vert.length > 1e-9:
            d = vert.normalized()
            n = _offset_dir(d, 'ALIGNED', view_dir)

    a0 = pa + n * offset
    b0 = pb + n * offset

    # extension lines (from near geometry out past dim line)
    gap = min(offset * 0.2, offset * 0.5)
    segs = [
        (pa + n * gap, pa + n * (offset + extension)),
        (pb + n * gap, pb + n * (offset + extension)),
        (a0, b0),
    ]

    # arrowheads (inward)
    ah = max(arrow, 1e-6)
    wing = ah * 0.35
    segs += [
        (a0, a0 + d * ah + n * wing),
        (a0, a0 + d * ah - n * wing),
        (b0, b0 - d * ah + n * wing),
        (b0, b0 - d * ah - n * wing),
    ]

    text_pos = (a0 + b0) * 0.5 + n * (arrow * 0.15)
    return segs, text_pos, length

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

def build_dimension_data(
    verts_s, edges_s, faces_s, edge_masks, face_masks, mats,
    scale, offset, extension, arrow, style, view_dir,
    line_color, face_text_only,
):
    labels = []
    seg_A, seg_B, seg_C = [], [], []
    col = np.array(line_color, dtype=np.float32)

    for i, verts in enumerate(verts_s):
        V = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        if len(V) == 0:
            continue
        if mats:
            M = np.array(mats[i % len(mats)], dtype=np.float64)
            V = V @ M[:3, :3].T + M[:3, 3]

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
                    segs, tpos, length = build_aligned_dim(
                        pa, pb, offset, extension, arrow, style, view_dir
                    )
                    if tpos is None:
                        continue
                    for s, e in segs:
                        seg_A.append(s)
                        seg_B.append(e)
                        seg_C.append(col)
                    labels.append({
                        'pos': tpos,
                        'value': length * scale,
                        'kind': 'edge',
                    })
                except Exception:
                    continue

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
                        'value': area * (scale ** 2),
                        'kind': 'face',
                    })
                except Exception:
                    continue

    ticks = None
    if seg_A:
        ticks = expand_segments(
            np.array(seg_A, dtype=np.float64),
            np.array(seg_B, dtype=np.float64),
            np.array(seg_C, dtype=np.float32),
        )
    return labels, ticks

# ---------------------------------------------------------------------------
# draw callback (POST_PIXEL)
# ---------------------------------------------------------------------------

def draw_dimensions(context, args):
    labels, ticks, cfg = args
    region = context.region
    rd = context.region_data
    if region is None or rd is None:
        return

    # GPU dimension lines
    if ticks is not None:
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

    # text
    font_id = 0
    blf.size(font_id, int(cfg.text_height))
    r, g, b, a = cfg.text_color
    blf.color(font_id, r, g, b, a)
    try:
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.85)
        blf.shadow_offset(font_id, 1, -1)
    except Exception:
        pass

    edge_fmt = f"{{:.{cfg.decimals}f}}{cfg.units}"
    face_fmt = f"{{:.{cfg.decimals}f}}{cfg.units}" + ("²" if cfg.units else " area")

    for lab in labels:
        co_2d = location_3d_to_region_2d(region, rd, lab['pos'])
        if co_2d is None:
            continue
        fmt = face_fmt if lab['kind'] == 'face' else edge_fmt
        text = fmt.format(lab['value'])
        tw, th = blf.dimensions(font_id, text)
        blf.position(font_id, co_2d.x - tw * 0.5, co_2d.y - th * 0.5, 0)
        blf.draw(font_id, text)

    try:
        blf.disable(font_id, blf.SHADOW)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# node
# ---------------------------------------------------------------------------

class SvDimensionDraw(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: dimension length area mask CAD
    Tooltip: CAD-style edge dimensions + face areas for masked indices
    """
    bl_idname = 'SvDimensionDraw'
    bl_label = 'Dimension Draw'
    bl_icon = 'DRIVER_DISTANCE'

    activate: BoolProperty(
        name='Show', default=True, update=updateNode)

    text_height: IntProperty(
        name='Text Height', default=14, min=6, max=72, update=updateNode)

    decimals: IntProperty(
        name='Decimals', default=2, min=0, max=8, update=updateNode)

    units: StringProperty(
        name='Units', default='', update=updateNode)

    scale: FloatProperty(
        name='Scale', default=1.0, min=0.0, update=updateNode)

    text_color: FloatVectorProperty(
        name='Text Color', subtype='COLOR', size=4,
        default=(0.05, 0.05, 0.05, 1.0), min=0.0, max=1.0, update=updateNode)

    line_color: FloatVectorProperty(
        name='Line Color', subtype='COLOR', size=4,
        default=(0.1, 0.1, 0.1, 1.0), min=0.0, max=1.0, update=updateNode)

    line_width: FloatProperty(
        name='Line Width', default=1.25, min=0.5, max=10.0, update=updateNode)

    dim_offset: FloatProperty(
        name='Offset', description='Distance of dim line from edge',
        default=0.25, min=0.0, update=updateNode)

    dim_extension: FloatProperty(
        name='Extension', description='Extension line past dim line',
        default=0.08, min=0.0, update=updateNode)

    arrow_size: FloatProperty(
        name='Arrow', default=0.06, min=0.0, update=updateNode)

    dim_style: EnumProperty(
        name='Style',
        items=[
            ('ALIGNED', 'Aligned', 'Dimension line parallel to the edge'),
            ('HORIZONTAL', 'Horizontal', 'Prefer horizontal layout'),
            ('VERTICAL', 'Vertical', 'Prefer vertical layout'),
        ],
        default='ALIGNED',
        update=updateNode,
    )

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
        row.prop(self, 'dim_style', text='')
        row = layout.row(align=True)
        row.prop(self, 'dim_offset')
        row.prop(self, 'dim_extension')
        row = layout.row(align=True)
        row.prop(self, 'arrow_size')
        row.prop(self, 'line_width')
        row = layout.row(align=True)
        row.prop(self, 'text_height')
        row.prop(self, 'decimals')
        row = layout.row(align=True)
        row.prop(self, 'scale')
        row.prop(self, 'units', text='')
        split = layout.split(factor=0.5)
        split.prop(self, 'text_color', text='')
        split.prop(self, 'line_color', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

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

        edge_masks = [flatten_mask(m) for m in edge_masks] or [[]]
        face_masks = [flatten_mask(m) for m in face_masks] or [[]]

        # view direction for aligned offset (approx; refined in draw if needed)
        view_dir = Vector((0, 0, -1))
        try:
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        space = area.spaces.active
                        if space and space.region_3d:
                            view_dir = space.region_3d.view_rotation @ Vector((0, 0, -1))
                            break
        except Exception:
            pass

        labels, ticks = build_dimension_data(
            verts_s, edges_s, faces_s, edge_masks, face_masks, mats,
            self.scale, self.dim_offset, self.dim_extension, self.arrow_size,
            self.dim_style, view_dir, self.line_color, True,
        )
        if not labels and ticks is None:
            return

        cfg = SimpleNamespace(
            text_height=self.text_height,
            decimals=self.decimals,
            units=self.units,
            text_color=tuple(self.text_color),
            line_width=self.line_width,
        )

        callback_enable(n_id, {
            'tree_name': self.id_data.name[:],
            'custom_function': draw_dimensions,
            'args': (labels, ticks, cfg),
        }, overlay='POST_PIXEL')

    def sv_free(self):
        callback_disable(node_id(self))

    def sv_copy(self, node):
        self.n_id = ''

classes = [SvDimensionDraw]
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()