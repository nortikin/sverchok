# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Viewer Draw Mk5

Changes relative to Mk4:

- all shaders use GPUShaderCreateInfo (works on OpenGL, Metal and Vulkan),
  are compiled once per session and cached at module level
- batches are built once per node update (lazily, on the first redraw)
  instead of on every viewport redraw
- edges are drawn as screen-space quads: real line width on every backend,
  antialiased, optional dashes in pixels, near-plane clipped
- vertices are drawn as round antialiased screen-space quads
- edges/points get a depth offset applied in clip space that equals a fixed
  fraction of the view distance (no gl_FragDepth writes, so early-z stays on,
  and no break-up at distance)
- facet / smooth lighting in the shaders, with Viewer Draw Mk4's formula and colours: facet
  normals come from dFdx/dFdy and the polygon winding (gl_FrontFacing), so faces no longer need
  to be split per triangle; smooth shading is worked out per vertex like Mk4. Lighting uses the
  matrix-transformed geometry (Mk4 lit the untransformed vertices)
- colours are converted for Blender's sRGB overlay framebuffer like the built-in shaders do
- 'fragment' mode (geometry shader, unsupported on Metal/Vulkan) is replaced
  by 'normals' (built-in normal view) and 'custom' (text-block shader)
- geometry is built with numpy

Custom shader text block (mode 'custom'), the text is exec'd and may define:

    build_shader()          -> returns a gpu shader              (preferred)
    shader_info             -> a gpu.types.GPUShaderCreateInfo
    vertex_shader, fragment_shader  -> legacy GLSL strings (Mk4 compatible)
    draw_fragment(context, shader, geom)  -> optional, called after bind,
                                            use it to set extra uniforms

Available vertex attributes (supplied when the shader declares them):
    position / pos (vec3, world space), color (vec4), normal / nrm (vec3)
Uniform set automatically if declared: viewProjectionMatrix (mat4)
"""

from types import SimpleNamespace

import numpy as np

import bpy
import gpu
from bpy.props import (StringProperty, FloatProperty, IntProperty,
                       EnumProperty, BoolProperty, FloatVectorProperty)
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon as tessellate
from gpu_extras.batch import batch_for_shader

from sverchok.data_structure import updateNode, node_id, match_long_repeat, enum_item_5
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.utils.sv_mesh_utils import polygons_to_edges_np
from sverchok.utils.geom import multiply_vectors_deep
from sverchok.utils.sv_3dview_tools import Sv3DviewAlign
from sverchok.utils.sv_obj_baker import SvObjBakeMK3
from sverchok.utils.modules.vertex_utils import np_vertex_normals


# ---------------------------------------------------------------------------
# shaders
# ---------------------------------------------------------------------------

# Blender's viewport overlay framebuffer is sRGB. Built-in shaders convert their sRGB input to
# linear before writing (blender_srgb_to_framebuffer_space); custom shaders must do the same or
# every colour comes out lighter. Blender sets the srgbTarget push constant automatically.
SRGB_GLSL = '''
vec4 srgb_to_framebuffer(vec4 c)
{
    if (srgbTarget) {
        vec3 v = max(c.rgb, vec3(0.0));
        c.rgb = mix(v * (1.0 / 12.92), pow((v + 0.055) * (1.0 / 1.055), vec3(2.4)), step(vec3(0.04045), v));
    }
    return c;
}
'''

LINE_VS = '''
vec4 clip_toward(vec4 p, vec4 q)
{
    /* pull an endpoint that lies behind the eye onto the near side */
    const float eps = 1e-4;
    if (p.w < eps && q.w > eps) {
        return mix(p, q, (eps - p.w) / (q.w - p.w));
    }
    return p;
}

void main()
{
    vColor = color;
    vDist = 0.0;
    vArc = 0.0;

    vec4 p = clip_toward(viewProjectionMatrix * vec4(pos, 1.0),
                         viewProjectionMatrix * vec4(other, 1.0));
    vec4 q = clip_toward(viewProjectionMatrix * vec4(other, 1.0),
                         viewProjectionMatrix * vec4(pos, 1.0));

    if (p.w < 1e-5) {
        /* whole segment behind the eye: emit outside the clip volume */
        gl_Position = vec4(0.0, 0.0, 2.0, 1.0);
        return;
    }

    vec2 half_vp = viewportSize * 0.5;
    vec2 sp = p.xy / p.w * half_vp;
    vec2 sq = q.xy / q.w * half_vp;

    /* corner.x = side (+1/-1), corner.y = 0 at segment start, 1 at end.
       direction is always start->end so both ends agree on the side. */
    vec2 d = (corner.y < 0.5) ? (sq - sp) : (sp - sq);
    float len = length(d);
    d = (len > 1e-6) ? d / len : vec2(1.0, 0.0);
    vec2 n = vec2(-d.y, d.x);

    float hw = lineWidth * 0.5 + 1.0;   /* +1px for the AA fringe */
    p.xy += n * (corner.x * hw) / half_vp * p.w;
    p.z -= depthBias;

    gl_Position = p;
    vDist = corner.x * hw;
    vArc = corner.y * len;
}
'''

LINE_FS = '''
void main()
{
    if (dashPattern.x > 0.0) {
        if (mod(vArc, dashPattern.x + dashPattern.y) > dashPattern.x) {
            discard;
        }
    }
    float a = clamp(lineWidth * 0.5 + 0.5 - abs(vDist), 0.0, 1.0);
    if (a <= 0.0) {
        discard;
    }
    FragColor = srgb_to_framebuffer(vec4(vColor.rgb, vColor.a * a));
}
'''

POINT_VS = '''
void main()
{
    vColor = color;
    float r = pointSize * 0.5 + 1.0;    /* +1px for the AA fringe */
    vCorner = corner * r;
    vec4 p = viewProjectionMatrix * vec4(pos, 1.0);
    p.xy += corner * r / (viewportSize * 0.5) * p.w;
    p.z -= depthBias;
    gl_Position = p;
}
'''

POINT_FS = '''
void main()
{
    float a = clamp(pointSize * 0.5 + 0.5 - length(vCorner), 0.0, 1.0);
    if (a <= 0.0) {
        discard;
    }
    FragColor = srgb_to_framebuffer(vec4(vColor.rgb, vColor.a * a));
}
'''

# Lighting matches Viewer Draw Mk4:
#   light factor = ambient_occlusion(dot(normal, light) * 0.5 + 0.5), where values under 0.4 fold
#   back up (utils.math.np_ambient_occlusion) and the light vector is used as set, not normalised.
#   facet:  (colour * 0.8 + 0.2) * factor - red * 0.1, one factor per face from its winding normal
#   smooth: colour * factor, worked out per vertex from the vertex normals and interpolated
FACE_VS = '''
float ambient_occlusion(float x)
{
    return (x < 0.4) ? 0.8 - x : x;
}

void main()
{
    vPos = pos;
    vColor = color;
    if (shadeMode == 2) {
        float len = length(nrm);
        float factor = (len > 1e-12) ? ambient_occlusion(dot(nrm / len, lightDir.xyz) * 0.5 + 0.5) : 1.0;
        vColor = vec4(color.rgb * factor, color.a);
    }
    gl_Position = viewProjectionMatrix * vec4(pos, 1.0);
}
'''

FACE_FS = '''
float ambient_occlusion(float x)
{
    return (x < 0.4) ? 0.8 - x : x;
}

void main()
{
    vec4 c = vColor;
    if (shadeMode == 0 || shadeMode == 2) {
        FragColor = srgb_to_framebuffer(c);
        return;
    }

    /* face normal from screen derivatives, turned toward the viewer, then flipped for back
       faces so it follows the polygon's winding like Mk4's face normals */
    vec3 V = (viewInfo.w > 0.5) ? normalize(viewInfo.xyz - vPos) : normalize(viewInfo.xyz);
    vec3 N = normalize(cross(dFdx(vPos), dFdy(vPos)));
    if (dot(N, V) < 0.0) {
        N = -N;
    }

    if (shadeMode == 3) {
        /* normals view: two sided, colours the side you are looking at */
        FragColor = srgb_to_framebuffer(vec4(N * 0.5 + 0.5, c.a));
        return;
    }

    if (!gl_FrontFacing) {
        N = -N;
    }
    float factor = ambient_occlusion(dot(N, lightDir.xyz) * 0.5 + 0.5);
    vec3 rgb = (c.rgb * 0.8 + 0.2) * factor - c.r * 0.1;   /* Mk4 subtracts the red channel from all three */
    FragColor = srgb_to_framebuffer(vec4(rgb, c.a));
}
'''

SHADE_MODES = {'flat': 0, 'facet': 1, 'smooth': 2, 'normals': 3, 'custom': 3}

_SHADERS = {}


def _build_line_shader():
    iface = gpu.types.GPUStageInterfaceInfo("sv_vd5_line_iface")
    iface.smooth('VEC4', "vColor")
    iface.no_perspective('FLOAT', "vDist")
    iface.no_perspective('FLOAT', "vArc")

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant('BOOL', "srgbTarget")
    info.push_constant('MAT4', "viewProjectionMatrix")
    info.push_constant('VEC2', "viewportSize")
    info.push_constant('VEC2', "dashPattern")
    info.push_constant('FLOAT', "lineWidth")
    info.push_constant('FLOAT', "depthBias")
    info.vertex_in(0, 'VEC3', "pos")
    info.vertex_in(1, 'VEC3', "other")
    info.vertex_in(2, 'VEC2', "corner")
    info.vertex_in(3, 'VEC4', "color")
    info.vertex_out(iface)
    info.fragment_out(0, 'VEC4', "FragColor")
    info.vertex_source(LINE_VS)
    info.fragment_source(SRGB_GLSL + LINE_FS)
    return gpu.shader.create_from_info(info)


def _build_point_shader():
    iface = gpu.types.GPUStageInterfaceInfo("sv_vd5_point_iface")
    iface.smooth('VEC4', "vColor")
    iface.no_perspective('VEC2', "vCorner")

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant('BOOL', "srgbTarget")
    info.push_constant('MAT4', "viewProjectionMatrix")
    info.push_constant('VEC2', "viewportSize")
    info.push_constant('FLOAT', "pointSize")
    info.push_constant('FLOAT', "depthBias")
    info.vertex_in(0, 'VEC3', "pos")
    info.vertex_in(1, 'VEC2', "corner")
    info.vertex_in(2, 'VEC4', "color")
    info.vertex_out(iface)
    info.fragment_out(0, 'VEC4', "FragColor")
    info.vertex_source(POINT_VS)
    info.fragment_source(SRGB_GLSL + POINT_FS)
    return gpu.shader.create_from_info(info)


def _build_face_shader():
    iface = gpu.types.GPUStageInterfaceInfo("sv_vd5_face_iface")
    iface.smooth('VEC4', "vColor")
    iface.smooth('VEC3', "vPos")

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant('BOOL', "srgbTarget")
    info.push_constant('MAT4', "viewProjectionMatrix")
    info.push_constant('VEC4', "lightDir")
    info.push_constant('VEC4', "viewInfo")
    info.push_constant('INT', "shadeMode")
    info.vertex_in(0, 'VEC3', "pos")
    info.vertex_in(1, 'VEC3', "nrm")
    info.vertex_in(2, 'VEC4', "color")
    info.vertex_out(iface)
    info.fragment_out(0, 'VEC4', "FragColor")
    info.vertex_source(FACE_VS)
    info.fragment_source(SRGB_GLSL + FACE_FS)
    return gpu.shader.create_from_info(info)


_BUILDERS = {'line': _build_line_shader, 'point': _build_point_shader, 'face': _build_face_shader}


def get_shader(name):
    """compile once, needs a GPU context, so only call from the draw callback"""
    shader = _SHADERS.get(name)
    if shader is None:
        shader = _SHADERS[name] = _BUILDERS[name]()
    return shader


# ---------------------------------------------------------------------------
# geometry helpers (numpy)
# ---------------------------------------------------------------------------

def rgba(cols, n):
    """cycle a color or a list of colors to an (n, 4) float32 array"""
    try:
        a = np.asarray(cols, dtype=np.float32)
    except ValueError:
        # ragged list, e.g. a mix of rgb and rgba entries
        a = np.array([tuple(c)[:4] + (1.0,) * (4 - len(c)) for c in cols], dtype=np.float32)
    if a.ndim == 1:
        a = a[None, :]
    a = a.reshape(-1, a.shape[-1])
    if a.shape[1] == 3:
        a = np.hstack([a, np.ones((len(a), 1), np.float32)])
    if n == 0 or len(a) == 0:
        return np.zeros((n, 4), np.float32)
    return np.resize(a[:, :4], (n, 4))


def triangulate(V, polys, all_triangles, concave_quads):
    """returns (tris (T,3) int64, face_index (T,) int64)"""
    if all_triangles or (isinstance(polys, np.ndarray) and polys.ndim == 2 and polys.shape[1] == 3):
        tris = np.asarray(polys, dtype=np.int64).reshape(-1, 3)
        return tris, np.arange(len(tris))

    if isinstance(polys, np.ndarray) and polys.ndim == 2 and polys.shape[1] == 4 and not concave_quads:
        tris = polys[:, [0, 1, 2, 0, 2, 3]].astype(np.int64).reshape(-1, 3)
        return tris, np.repeat(np.arange(len(polys)), 2)

    tris, fidx = [], []
    tris_append, fidx_append = tris.append, fidx.append
    for i, p in enumerate(polys):
        n = len(p)
        if n == 3:
            tris_append((p[0], p[1], p[2]))
            fidx_append(i)
        elif n == 4 and not concave_quads:
            tris_append((p[0], p[1], p[2]))
            tris_append((p[0], p[2], p[3]))
            fidx_append(i)
            fidx_append(i)
        elif n > 3:
            sub = [Vector(V[j]) for j in p]
            pts = np.asarray(V[list(p)], dtype=np.float64)
            normal = np.cross(pts - pts.mean(axis=0), np.roll(pts, -1, axis=0) - pts.mean(axis=0)).sum(axis=0)
            for t in tessellate([sub]):
                a, b, c = t
                if np.dot(np.cross(pts[b] - pts[a], pts[c] - pts[a]), normal) < 0:
                    b, c = c, b
                tris_append((p[a], p[b], p[c]))
                fidx_append(i)
    return (np.array(tris, dtype=np.int64).reshape(-1, 3),
            np.array(fidx, dtype=np.int64))


def vertex_normals(V, tris):
    """area weighted vertex normals"""
    vn = np.zeros_like(V)
    if len(tris):
        a, b, c = V[tris[:, 0]], V[tris[:, 1]], V[tris[:, 2]]
        fn = np.cross(b - a, c - a)
        for k in range(3):
            np.add.at(vn, tris[:, k], fn)
    length = np.linalg.norm(vn, axis=1, keepdims=True)
    length[length == 0] = 1.0
    return vn / length


def smooth_normals(V, polys, tris):
    """vertex normals as Viewer Draw Mk4 computes them, falling back to area weighted ones"""
    try:
        n = np.asarray(np_vertex_normals(V, polys, output_numpy=True), dtype=np.float64).reshape(-1, 3)
        if n.shape == V.shape:
            return n
    except Exception:
        pass
    return vertex_normals(V, tris)


def expand_segments(A, B, cA, cB):
    """each segment becomes a screen-space quad (4 verts, 2 tris)"""
    m = len(A)
    pos = np.stack([A, A, B, B], axis=1).reshape(-1, 3)
    other = np.stack([B, B, A, A], axis=1).reshape(-1, 3)
    corner = np.tile(np.array([[1, 0], [-1, 0], [1, 1], [-1, 1]], np.float32), (m, 1))
    color = np.stack([cA, cA, cB, cB], axis=1).reshape(-1, 4)
    idx = (np.arange(m, dtype=np.uint32)[:, None] * 4 +
           np.array([0, 1, 2, 2, 1, 3], np.uint32)).reshape(-1, 3)
    return SimpleNamespace(pos=f32(pos), other=f32(other), corner=corner, color=f32(color), idx=idx)


def expand_points(P, C):
    m = len(P)
    pos = np.repeat(P, 4, axis=0)
    corner = np.tile(np.array([[-1, -1], [1, -1], [-1, 1], [1, 1]], np.float32), (m, 1))
    color = np.repeat(C, 4, axis=0)
    idx = (np.arange(m, dtype=np.uint32)[:, None] * 4 +
           np.array([0, 1, 2, 2, 1, 3], np.uint32)).reshape(-1, 3)
    return SimpleNamespace(pos=f32(pos), corner=corner, color=f32(color), idx=idx)


def f32(a):
    return np.ascontiguousarray(a, dtype=np.float32)


def _concat(parts, width, dtype=np.float32):
    return np.concatenate(parts) if parts else np.zeros((0, width), dtype)


def build_geom(cfg, vecs, edges_s, polys_s, mats, vcol, ecol, pcol, seed):
    rng = np.random.default_rng(seed)
    pts_p, pts_c = [], []
    seg_a, seg_b, seg_ca, seg_cb = [], [], [], []
    f_pos, f_nrm, f_col, f_idx = [], [], [], []
    f_off = 0
    need_normals = cfg.shade_mode in ('smooth', 'custom')

    for i, verts in enumerate(vecs):
        V = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        n = len(V)
        if not n:
            continue
        if mats:
            M = np.array(mats[i], dtype=np.float64)
            V = V @ M[:3, :3].T + M[:3, 3]

        # point colors
        if cfg.random_colors:
            if cfg.color_per_point:
                pc = rng.random((n, 4)).astype(np.float32)
            else:
                pc = np.tile(rng.random(4).astype(np.float32), (n, 1))
            pc[:, 3] = 1.0
        elif cfg.color_per_point:
            pc = rgba(vcol[i % len(vcol)], n)
        else:
            pc = rgba(vcol[0][i % len(vcol[0])], n)

        if cfg.draw_verts:
            pts_p.append(V)
            pts_c.append(pc)

        if cfg.draw_edges:
            edges = edges_s[i % len(edges_s)]
            if len(edges):
                E = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
                if cfg.edges_use_vertex_color:
                    ca, cb = pc[E[:, 0]], pc[E[:, 1]]
                elif cfg.color_per_edge:
                    ca = cb = rgba(ecol[i % len(ecol)], len(E))
                else:
                    ca = cb = rgba(ecol[0][i % len(ecol[0])], len(E))
                seg_a.append(V[E[:, 0]])
                seg_b.append(V[E[:, 1]])
                seg_ca.append(ca)
                seg_cb.append(cb)

        if cfg.draw_polys:
            polys = polys_s[i % len(polys_s)]
            if len(polys):
                tris, fidx = triangulate(V, polys, cfg.all_triangles, cfg.handle_concave_quads)
                if len(tris):
                    N = smooth_normals(V, polys, tris) if need_normals else np.zeros_like(V)
                    if cfg.polygon_use_vertex_color:
                        fp, fn, fc, fi = V, N, pc, tris
                    elif cfg.color_per_polygon:
                        face_cols = rgba(pcol[i % len(pcol)], len(polys))[fidx]
                        fp = V[tris].reshape(-1, 3)
                        fn = N[tris].reshape(-1, 3)
                        fc = np.repeat(face_cols, 3, axis=0)
                        fi = np.arange(len(fp)).reshape(-1, 3)
                    else:
                        fp, fn, fc, fi = V, N, rgba(pcol[0][i % len(pcol[0])], n), tris
                    f_pos.append(fp)
                    f_nrm.append(fn)
                    f_col.append(fc)
                    f_idx.append(fi + f_off)
                    f_off += len(fp)

    geom = SimpleNamespace(points=None, lines=None, faces=None, batches={}, custom_shader=None)

    if pts_p:
        geom.points = expand_points(_concat(pts_p, 3), _concat(pts_c, 4))
    if seg_a:
        geom.lines = expand_segments(_concat(seg_a, 3), _concat(seg_b, 3),
                                     _concat(seg_ca, 4), _concat(seg_cb, 4))
    if f_pos:
        geom.faces = SimpleNamespace(
            pos=f32(_concat(f_pos, 3)), nrm=f32(_concat(f_nrm, 3)), color=f32(_concat(f_col, 4)),
            idx=np.ascontiguousarray(_concat(f_idx, 3, np.int64), dtype=np.uint32))

    if not (geom.points or geom.lines or geom.faces):
        return None
    return geom


# ---------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------

def depth_bias(rd, amount):
    """
    clip-space z offset. In perspective, subtracting a constant c from clip z
    moves a fragment toward the eye by (c * (f-n) / 2fn) * distance, so
    c = amount * 2fn/(f-n) = amount * |P[2][3]| pulls by `amount` * distance.
    Orthographic depth is linear, so a small constant is enough there.
    """
    P = rd.window_matrix
    if abs(P[3][3]) < 0.5:
        return amount * abs(P[2][3])
    return amount * 0.02


def view_info(rd):
    inv = rd.view_matrix.inverted()
    if abs(rd.window_matrix[3][3]) < 0.5:
        t = inv.translation
        return (t.x, t.y, t.z, 1.0)
    z = inv.col[2]
    return (z[0], z[1], z[2], 0.0)


def _batch(geom, key, shader, content, indices):
    batch = geom.batches.get(key)
    if batch is None:
        batch = geom.batches[key] = batch_for_shader(shader, 'TRIS', content, indices=indices)
    return batch


def _custom_shader(geom, cfg):
    """None = not tried yet, False = failed / not defined"""
    if geom.custom_shader is None:
        geom.custom_shader = False
        ns = cfg.custom_ns
        if ns:
            try:
                shader = None
                if callable(ns.get('build_shader')):
                    shader = ns['build_shader']()
                elif ns.get('shader_info') is not None:
                    shader = gpu.shader.create_from_info(ns['shader_info'])
                elif ns.get('vertex_shader') and ns.get('fragment_shader'):
                    shader = gpu.types.GPUShader(ns['vertex_shader'], ns['fragment_shader'])
                if shader is not None:
                    geom.custom_shader = shader
            except Exception as err:
                print(f"Viewer Draw Mk5: custom shader failed: {err}")
    return geom.custom_shader or None


def _draw_custom_faces(context, geom, cfg, vp):
    shader = _custom_shader(geom, cfg)
    if shader is None:
        return False
    f = geom.faces
    batch = geom.batches.get('custom')
    if batch is None:
        try:
            names = [a[0] for a in shader.attrs_info_get()]
        except Exception:
            names = ['position']
        available = {'position': f.pos, 'pos': f.pos, 'color': f.color, 'normal': f.nrm, 'nrm': f.nrm}
        content = {k: available[k] for k in names if k in available}
        try:
            batch = geom.batches['custom'] = batch_for_shader(shader, 'TRIS', content, indices=f.idx)
        except Exception as err:
            print(f"Viewer Draw Mk5: custom shader batch failed: {err}")
            geom.custom_shader = False
            return False
    shader.bind()
    try:
        shader.uniform_float("viewProjectionMatrix", vp)
    except Exception:
        pass
    if callable(cfg.custom_ns.get('draw_fragment')):
        try:
            cfg.custom_ns['draw_fragment'](context, shader, geom)
        except Exception as err:
            print(f"Viewer Draw Mk5: draw_fragment failed: {err}")
    batch.draw(shader)
    return True


def view_3d_geom(context, args):
    geom, cfg = args
    rd = context.region_data
    region = context.region
    if rd is None or region is None:
        return

    vp = rd.perspective_matrix
    viewport = (float(region.width), float(region.height))
    bias = depth_bias(rd, cfg.depth_offset)

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(True)
    try:
        if geom.faces is not None:
            gpu.state.face_culling_set(cfg.face_culling)
            drawn = cfg.shade_mode == 'custom' and _draw_custom_faces(context, geom, cfg, vp)
            if not drawn:
                f = geom.faces
                shader = get_shader('face')
                batch = _batch(geom, 'faces', shader,
                               {"pos": f.pos, "nrm": f.nrm, "color": f.color}, f.idx)
                shader.bind()
                shader.uniform_float("viewProjectionMatrix", vp)
                shader.uniform_float("lightDir", (*cfg.light, 0.0))
                shader.uniform_float("viewInfo", view_info(rd))
                shader.uniform_int("shadeMode", SHADE_MODES[cfg.shade_mode])
                batch.draw(shader)
            gpu.state.face_culling_set('NONE')

        if geom.lines is not None:
            ln = geom.lines
            shader = get_shader('line')
            batch = _batch(geom, 'lines', shader,
                           {"pos": ln.pos, "other": ln.other, "corner": ln.corner, "color": ln.color}, ln.idx)
            shader.bind()
            shader.uniform_float("viewProjectionMatrix", vp)
            shader.uniform_float("viewportSize", viewport)
            shader.uniform_float("dashPattern", cfg.dash if cfg.dashed else (0.0, 0.0))
            shader.uniform_float("lineWidth", float(cfg.line_width))
            shader.uniform_float("depthBias", bias)
            batch.draw(shader)

        if geom.points is not None:
            pt = geom.points
            shader = get_shader('point')
            batch = _batch(geom, 'points', shader,
                           {"pos": pt.pos, "corner": pt.corner, "color": pt.color}, pt.idx)
            shader.bind()
            shader.uniform_float("viewProjectionMatrix", vp)
            shader.uniform_float("viewportSize", viewport)
            shader.uniform_float("pointSize", float(cfg.point_size))
            shader.uniform_float("depthBias", bias)
            batch.draw(shader)
    finally:
        gpu.state.face_culling_set('NONE')
        gpu.state.depth_mask_set(False)
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')


def draw_matrix(context, args):
    """ this takes one or more matrices packed into an iterable """
    matrices, scale = args
    mdraw = MatrixDraw28()
    for matrix in matrices:
        mdraw.draw_matrix(matrix, scale=scale)


# ---------------------------------------------------------------------------
# node
# ---------------------------------------------------------------------------

socket_dict = {
    'vector_color': ('display_verts', 'UV_VERTEXSEL', 'color_per_point', 'vector_random_colors', 'random_seed'),
    'edge_color': ('display_edges', 'UV_EDGESEL', 'color_per_edge', 'edges_use_vertex_color'),
    'polygon_color': ('display_faces', 'UV_FACESEL', 'color_per_polygon', 'polygon_use_vertex_color'),
}

MIGRATE_PROPS = (
    'activate', 'face_culling_set', 'vector_light', 'handle_concave_quads', 'point_size', 'line_width',
    'vector_color', 'display_verts', 'vector_random_colors', 'random_seed', 'color_per_point',
    'color_per_edge', 'color_per_polygon', 'polygon_use_vertex_color', 'edges_use_vertex_color',
    'edge_color', 'display_edges', 'polygon_color', 'display_faces', 'all_triangles',
    'matrix_draw_scale', 'use_dashed', 'custom_shader_location', 'node_ui_show_attrs_socket')


class SvViewerDrawMk5(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: vd geometry preview
    Tooltip: Drawing preview on 3d scene.\n\tIn: Vertices, Edges, Polygons, Matrix, Colors for vertices, edges, polygons\n\tParams: Vertices size, Edges width, Draw mode, Align 3DView\n\tExtra: Depth offset, dashes, custom shader (N-panel)
    """
    bl_idname = 'SvViewerDrawMk5'
    bl_label = 'Viewer Draw+'
    bl_icon = 'GREASEPENCIL'
    sv_icon = 'SV_DRAW_VIEWER'

    face_culling_set: EnumProperty(
        items=[
            ('NONE', 'None', 'none facets can be culled', 'SNAP_VOLUME', 0),
            ('FRONT', 'Front', 'front-facing facets can be culled', 'SNAP_FACE', 1),
            ('BACK', 'Back', 'back-facing facets can be culled', 'SELECT_SUBTRACT', 2),
        ],
        description="none, front-facing or back-facing facets can be culled. Viewport only",
        default="NONE", update=updateNode)

    selected_draw_mode: EnumProperty(
        items=enum_item_5(["flat", "facet", "smooth", "normals", "custom"],
                          ['SNAP_VOLUME', 'ALIASED', 'ANTIALIASED', 'NORMALS_FACE', 'SCRIPTPLUGINS']),
        description="pick how the node will draw faces",
        default="facet", update=updateNode)

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode)

    vector_light: FloatVectorProperty(
        name='vector light', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4), update=updateNode)

    handle_concave_quads: BoolProperty(
        name='Handle Concave Quads', default=False, update=updateNode,
        description='tessellate quads using geometry.tessellate_polygon, expect some speed impact')

    point_size: IntProperty(
        min=1, default=3, name='Verts Size',
        description='Point Size', update=updateNode)

    line_width: IntProperty(
        min=1, default=1, name='Edge Width',
        description='Edge Width', update=updateNode)

    depth_offset: FloatProperty(
        name='Depth Offset', default=0.002, min=0.0, max=0.05, precision=4, step=0.01,
        description='Pull edges and vertices toward the eye by this fraction of their view distance '
                    '(avoids z-fighting with faces)',
        update=updateNode)

    vector_color: FloatVectorProperty(
        update=updateNode, name='Vertices Color', default=(.9, .9, .95, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR')

    display_verts: BoolProperty(
        update=updateNode, name='Display Vertices', default=True)

    vector_random_colors: BoolProperty(
        update=updateNode, name='Random Vertices Color', default=False)

    random_seed: IntProperty(
        min=1, default=1, name='Random Seed',
        description='Seed of random colors', update=updateNode)

    color_per_point: BoolProperty(
        update=updateNode, name='Color per point', default=False,
        description='Toggle between color per point or per object')

    color_per_edge: BoolProperty(
        update=updateNode, name='Color per edge', default=False,
        description='Toggle between color per edge or per object')

    color_per_polygon: BoolProperty(
        update=updateNode, name='Color per polygon', default=False,
        description='Toggle between color per polygon or per object')

    polygon_use_vertex_color: BoolProperty(
        update=updateNode, name='Polys Vertex Color', default=False,
        description='Colorize polygons using vertices color')

    edges_use_vertex_color: BoolProperty(
        update=updateNode, name='Edges Vertex Color', default=False,
        description='Colorize edges using vertices color')

    edge_color: FloatVectorProperty(
        update=updateNode, name='Edges Color', default=(0.9, 0.7, 0.25, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR')

    display_edges: BoolProperty(
        update=updateNode, name='Display Edges', default=True)

    polygon_color: FloatVectorProperty(
        update=updateNode, name='Polygons Color', default=(0.14, 0.54, 0.81, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR')

    display_faces: BoolProperty(
        update=updateNode, name='Display Polygons', default=True)

    all_triangles: BoolProperty(
        update=updateNode, name='All Triangles', default=False,
        description='Enable if all the incoming faces are Tris (makes node faster)')

    matrix_draw_scale: FloatProperty(default=1, min=0.0001, name="Drawing matrix scale", update=updateNode)

    # dashes, in pixels
    use_dashed: BoolProperty(name='Dashed Edges', update=updateNode)
    dash_length: FloatProperty(default=8.0, min=0.5, name="Dash (px)", update=updateNode)
    gap_length: FloatProperty(default=5.0, min=0.5, name="Gap (px)", update=updateNode)

    custom_shader_location: StringProperty(update=updateNode, name='custom shader location')

    def configureAttrSocket(self, context):
        self.inputs['attrs'].hide_safe = not self.node_ui_show_attrs_socket

    node_ui_show_attrs_socket: BoolProperty(default=False, name='Show attributes socket', update=configureAttrSocket)

    # -- ui -----------------------------------------------------------------

    def draw_buttons(self, context, layout):
        r0 = layout.row()
        r0.prop(self, "activate", text="", icon="HIDE_" + ("OFF" if self.activate else "ON"))
        r0.separator()
        r0.prop(self, "selected_draw_mode", expand=True, text='')
        if self.selected_draw_mode == 'custom':
            layout.prop_search(self, "custom_shader_location", bpy.data, "texts", text='', icon='TEXT')

        row = layout.row(align=True)
        row.label(text=' ')
        row.prop(self, "face_culling_set", expand=True, text='')

        row = layout.row(align=True)
        row.scale_y = 4.0 if self.prefs_over_sized_buttons else 1
        self.wrapper_tracked_ui_draw_op(row, SvObjBakeMK3.bl_idname, icon='OUTLINER_OB_MESH', text="B A K E")
        row.separator()
        self.wrapper_tracked_ui_draw_op(row, Sv3DviewAlign.bl_idname, icon='CURSOR', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        row = layout.row(align=True)
        row.prop(self, "point_size")
        row.prop(self, "line_width")
        layout.label(text='Light Direction')
        layout.prop(self, 'vector_light', text='')
        layout.prop(self, 'depth_offset')
        self.draw_additional_props(context, layout)
        if self.use_dashed:
            row = layout.row(align=True)
            row.prop(self, "dash_length")
            row.prop(self, "gap_length")

    def draw_additional_props(self, context, layout):
        layout.prop(self, 'handle_concave_quads')
        layout.prop(self, 'node_ui_show_attrs_socket')
        layout.prop(self, 'matrix_draw_scale')
        layout.prop(self, "use_dashed")
        layout.prop(self, "all_triangles")

    def rclick_menu(self, context, layout):
        self.draw_additional_props(context, layout)

    def draw_property_socket(self, socket, context, layout):
        drawing_verts = socket.name == "Vertices"
        prop_to_show = "point_size" if drawing_verts else "line_width"
        layout.label(text=f"{socket.name}. {socket.objects_number}")
        layout.prop(self, prop_to_show, text="px")

    def draw_color_socket(self, socket, context, layout):
        socket_info = socket_dict[socket.prop_name]
        layout.prop(self, socket_info[0], text="", icon=socket_info[1])
        layout.prop(self, socket_info[2], text="", icon='COLOR')

        display_color = not socket.is_linked
        draw_name = True
        if len(socket_info) < 5:
            layout.prop(self, socket_info[3], text="", icon='VPAINT_HLT')
        else:
            layout.prop(self, socket_info[3], text="", icon='MOD_NOISE')
            if getattr(self, socket_info[3]):
                layout.prop(self, socket_info[4], text="Seed")
                draw_name = False

        display_color = display_color and not getattr(self, socket_info[3])

        if display_color:
            layout.prop(self, socket.prop_name, text="")
        elif draw_name:
            layout.label(text=f"{socket.name[:2]}. Col. {socket.objects_number}")

    # -- lifecycle ----------------------------------------------------------

    def sv_init(self, context):
        new_input = self.sv_new_input
        new_input('SvVerticesSocket', "Vertices", custom_draw="draw_property_socket")
        new_input('SvStringsSocket', "Edges", custom_draw="draw_property_socket")
        new_input('SvStringsSocket', "Polygons")
        new_input('SvMatrixSocket', 'Matrix')
        new_input('SvColorSocket', "Vector Color", custom_draw='draw_color_socket', prop_name='vector_color')
        new_input('SvColorSocket', "Edge Color", custom_draw='draw_color_socket', prop_name='edge_color')
        new_input('SvColorSocket', "Polygon Color", custom_draw='draw_color_socket', prop_name='polygon_color')
        new_input('SvStringsSocket', 'attrs', quick_link_to_node="SvVDAttrsNodeMk2", hide=True)

    def migrate_from(self, old_node):
        for name in MIGRATE_PROPS:
            if hasattr(old_node, name):
                try:
                    setattr(self, name, getattr(old_node, name))
                except Exception as err:
                    print(f"Viewer Draw Mk5 migrate {name}: {err}")
        mode = getattr(old_node, 'selected_draw_mode', 'facet')
        if mode == 'fragment':
            mode = 'custom' if getattr(old_node, 'custom_shader_location', '') else 'normals'
        try:
            self.selected_draw_mode = mode
        except Exception:
            pass
        if getattr(old_node, 'u_dash_size', None) is not None:
            pass  # old dash units were relative, keep the pixel defaults
        self.hot_update_ui()

    def hot_update_ui(self):
        for idx in range(2):
            if self.inputs and not self.inputs[idx].custom_draw:
                self.inputs[idx].custom_draw = "draw_property_socket"

    def load_custom_ns(self):
        text = bpy.data.texts.get(self.custom_shader_location)
        if text is None:
            return None
        ns = {'gpu': gpu, 'bpy': bpy, 'np': np}
        try:
            exec(text.as_string(), ns)
        except Exception as err:
            print(f"Viewer Draw Mk5: error in text '{text.name}': {err}")
            return None
        return ns

    def create_config(self):
        inputs = self.inputs
        cfg = SimpleNamespace(
            draw_verts=self.display_verts,
            draw_edges=self.display_edges,
            draw_polys=self.display_faces and inputs['Polygons'].is_linked,
            point_size=self.point_size,
            line_width=self.line_width,
            random_colors=self.vector_random_colors,
            color_per_point=self.color_per_point and (inputs['Vector Color'].is_linked or self.vector_random_colors),
            color_per_edge=self.color_per_edge and (inputs['Edge Color'].is_linked or self.edges_use_vertex_color),
            color_per_polygon=self.color_per_polygon and (inputs['Polygon Color'].is_linked or self.polygon_use_vertex_color),
            polygon_use_vertex_color=self.polygon_use_vertex_color,
            edges_use_vertex_color=self.edges_use_vertex_color,
            shade_mode=self.selected_draw_mode,
            light=tuple(self.vector_light),
            face_culling=self.face_culling_set,
            all_triangles=self.all_triangles,
            handle_concave_quads=self.handle_concave_quads,
            dashed=self.use_dashed,
            dash=(self.dash_length, self.gap_length),
            depth_offset=self.depth_offset,
            custom_ns=None,
        )
        if cfg.shade_mode == 'custom':
            cfg.custom_ns = self.load_custom_ns()
        return cfg

    def handle_attr_socket(self):
        """
        this socket expects input dictionary wrapped. once.
            [  {attr: attr_vale, attr2: attr2_value } ]
        """
        if self.node_ui_show_attrs_socket and not self.inputs['attrs'].hide and self.inputs['attrs'].is_linked:
            socket_acquired_attrs = self.inputs['attrs'].sv_get(default=[{'activate': False}])
            if socket_acquired_attrs:
                try:
                    for k, new_value in socket_acquired_attrs[0].items():
                        setattr(self, k, new_value)
                except Exception as err:
                    print('error inside socket_acquired_attrs: ', err)

    def get_data(self):
        """used by the baker"""
        verts_socket, edges_socket, faces_socket, matrix_socket = self.inputs[:4]
        edge_indices = [[]]
        face_indices = [[]]

        propv = verts_socket.sv_get(deepcopy=False, default=[[]])
        coords = propv

        if edges_socket.is_linked:
            edge_indices = edges_socket.sv_get(deepcopy=False, default=[[]])

        if faces_socket.is_linked:
            face_indices = faces_socket.sv_get(deepcopy=False, default=[[]])

        if matrix_socket.is_linked:
            m = matrix_socket.sv_get(deepcopy=False, default=[Matrix()])
            verts, matrix = match_long_repeat([propv, m])
            coords = [multiply_vectors_deep(mx, v) for mx, v in zip(matrix, verts)]
        else:
            matrix = [Matrix()]
            verts = coords
        return match_long_repeat([coords, edge_indices, face_indices, verts, matrix])

    def process(self):
        if bpy.app.background:
            return
        self.handle_attr_socket()
        n_id = node_id(self)
        callback_disable(n_id)
        if not (self.id_data.sv_show and self.activate):
            return

        inputs = self.inputs
        if inputs['Vertices'].is_linked:
            vecs = inputs['Vertices'].sv_get(deepcopy=False, default=[[]])
            if not any(len(v) for v in vecs):
                return

            cfg = self.create_config()

            polys_s = inputs['Polygons'].sv_get(deepcopy=False, default=[[]]) if inputs['Polygons'].is_linked else [[]]
            if not len(polys_s):
                polys_s = [[]]

            edges_s = inputs['Edges'].sv_get(deepcopy=False, default=[[]]) if inputs['Edges'].is_linked else [[]]
            if not len(edges_s):
                edges_s = [[]]
            has_edges = inputs['Edges'].is_linked and any(len(e) for e in edges_s)
            has_polys = inputs['Polygons'].is_linked and any(len(p) for p in polys_s)
            if cfg.draw_edges and not has_edges and has_polys:
                edges_s = polygons_to_edges_np(polys_s, unique_edges=True)

            mats = []
            if inputs['Matrix'].is_linked:
                mats = inputs['Matrix'].sv_get(deepcopy=False, default=[])
                if mats:
                    vecs, mats = match_long_repeat([vecs, mats])

            vcol = inputs['Vector Color'].sv_get(deepcopy=False, default=[[self.vector_color[:]]])
            ecol = inputs['Edge Color'].sv_get(deepcopy=False, default=[[self.edge_color[:]]])
            pcol = inputs['Polygon Color'].sv_get(deepcopy=False, default=[[self.polygon_color[:]]])

            geom = build_geom(cfg, vecs, edges_s, polys_s, mats, vcol, ecol, pcol, self.random_seed)
            if geom is None:
                return

            callback_enable(n_id, {
                'tree_name': self.id_data.name[:],
                'custom_function': view_3d_geom,
                'args': (geom, cfg)})

        elif inputs['Matrix'].is_linked:
            matrices = inputs['Matrix'].sv_get(deepcopy=False, default=[Matrix()])
            callback_enable(n_id, {
                'tree_name': self.id_data.name[:],
                'custom_function': draw_matrix,
                'args': (matrices, self.matrix_draw_scale)})

    def sv_free(self):
        callback_disable(node_id(self))

    def toggle_viewer(self, context):
        self.activate = not self.activate

    def show_viewport(self, is_show: bool):
        """It should be called by node tree to show/hide objects"""
        if not self.activate:
            return
        if is_show:
            self.process()
        else:
            callback_disable(node_id(self))


classes = [SvViewerDrawMk5]
register, unregister = bpy.utils.register_classes_factory(classes)