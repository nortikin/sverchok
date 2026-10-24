# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.hatch_module import (
    parse_pat, hatch_region, chain_segments, order_strokes, describe, RegionError, HatchTooDense)


# parsed patterns per text block, re-parsed only when the text changes
_parse_cache = {}
# enum items must stay referenced while Blender shows them
_enum_items = {}


def patterns_from_text(text):
    if text is None:
        return []
    source = text.as_string()
    cached = _parse_cache.get(text.name)
    if cached is None or cached[0] != source:
        patterns, _ = parse_pat(source)
        cached = _parse_cache[text.name] = (source, patterns)
    return cached[1]


def pattern_items(self, context):
    patterns = patterns_from_text(self.pattern_text)
    if not patterns:
        items = [('NONE', 'No patterns', 'Pick a text block holding .pat data', 0)]
    else:
        items = [(p.name, p.name, p.description or p.name, i) for i, p in enumerate(patterns)]
    _enum_items[self.node_id] = items
    return items


def _depth(data):
    """nesting depth of lists / tuples / numpy arrays"""
    d = 0
    while True:
        if hasattr(data, 'ndim'):
            return d + data.ndim
        if isinstance(data, (list, tuple)) and len(data):
            d += 1
            data = data[0]
        else:
            return d + (1 if isinstance(data, (list, tuple)) else 0)


def as_objects(data, level):
    """wrap a single object's data so the outer level is always the object list"""
    if data is None:
        return None
    while _depth(data) < level:
        data = [data]
    return data


def per_object_value(values):
    """number sockets: [[v, ...], ...] -> first value per object"""
    out = []
    for obj in as_objects(values, 2):
        obj = list(obj) if hasattr(obj, '__len__') else [obj]
        out.append(float(obj[0]) if len(obj) else 0.0)
    return [[v] for v in out]


class SvHatchPatternNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: hatch pat autocad revit fill pattern plot
    Tooltip: Fill planar regions (holes allowed) with an AutoCAD / Revit .pat hatch pattern
    """
    bl_idname = 'SvHatchPatternNode'
    bl_label = 'Hatch Pattern'
    bl_icon = 'TEXTURE'

    pattern_text: PointerProperty(
        type=bpy.types.Text, name="Pattern file",
        description="Text block holding .pat data (Text Editor > Open a .pat file, or paste one)",
        update=updateNode)

    pattern_name: StringProperty(default="", update=updateNode)

    def _get_pattern(self):
        names = [p.name for p in patterns_from_text(self.pattern_text)]
        return names.index(self.pattern_name) if self.pattern_name in names else 0

    def _set_pattern(self, index):
        names = [p.name for p in patterns_from_text(self.pattern_text)]
        if 0 <= index < len(names):
            self.pattern_name = names[index]

    pattern: EnumProperty(
        name="Pattern", description="Pattern from the text block",
        items=pattern_items, get=_get_pattern, set=_set_pattern)

    scale: FloatProperty(
        name="Scale", default=1.0, min=1e-9, precision=4,
        description="Pattern scale, .pat values are multiplied by this", update=updateNode)
    offset_x: FloatProperty(
        name="Offset X", default=0.0, precision=4,
        description="Shift the pattern along the plane's X axis", update=updateNode)
    offset_y: FloatProperty(
        name="Offset Y", default=0.0, precision=4,
        description="Shift the pattern along the plane's Y axis", update=updateNode)

    min_length: FloatProperty(
        name="Min Length", default=0.0, min=0.0, precision=5,
        description="Drop dashes shorter than this (e.g. the pen width), clipping leaves slivers",
        update=updateNode)
    order_strokes: BoolProperty(
        name="Order Strokes", default=True,
        description="Sort strokes nearest-first to cut pen travel when plotting", update=updateNode)
    status: StringProperty(default="")
    status_level: StringProperty(default="INFO")

    max_segments: IntProperty(
        name="Max Segments", default=1_000_000, min=1000,
        description="Stop with an error instead of generating more dashes than this per region",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Polygons")
        self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('SvStringsSocket', "Offset X").prop_name = 'offset_x'
        self.inputs.new('SvStringsSocket', "Offset Y").prop_name = 'offset_y'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvVerticesSocket', "Dots")
        self.outputs.new('SvVerticesSocket', "Stroke Vertices")
        self.outputs.new('SvStringsSocket', "Stroke Edges")
        self.outputs.new('SvMatrixSocket', "Plane")

    def draw_buttons(self, context, layout):
        layout.prop_search(self, 'pattern_text', bpy.data, 'texts', text='', icon='TEXT')
        layout.prop(self, 'pattern', text='')
        if self.status:
            layout.label(text=self.status, icon='ERROR' if self.status_level == 'WARNING' else 'INFO')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'min_length')
        layout.prop(self, 'order_strokes')
        layout.prop(self, 'max_segments')

    def current_pattern(self):
        patterns = patterns_from_text(self.pattern_text)
        if not patterns:
            return None
        for p in patterns:
            if p.name == self.pattern_name:
                return p
        return patterns[0]

    def process(self):
        if not any(s.is_linked for s in self.outputs) or not self.inputs['Vertices'].is_linked:
            return

        pattern = self.current_pattern()
        if pattern is None:
            self.set_status("pick a text block holding .pat data", "WARNING")
            raise ValueError("Pick a text block holding .pat data")
        if not pattern.families:
            self.set_status(f"{pattern.name} has no line families", "WARNING")
            raise ValueError(f"Pattern '{pattern.name}' has no line families")

        inputs = self.inputs
        verts_in = as_objects(inputs['Vertices'].sv_get(), 3)
        polys_in = as_objects(inputs['Polygons'].sv_get(), 3) if inputs['Polygons'].is_linked else [None]
        edges_in = as_objects(inputs['Edges'].sv_get(), 3) if inputs['Edges'].is_linked else [None]
        scale_in = per_object_value(inputs['Scale'].sv_get())
        offx_in = per_object_value(inputs['Offset X'].sv_get())
        offy_in = per_object_value(inputs['Offset Y'].sv_get())

        want_strokes = self.outputs['Stroke Vertices'].is_linked or self.outputs['Stroke Edges'].is_linked
        verts_out, edges_out, dots_out, stroke_verts, stroke_edges, planes = [], [], [], [], [], []
        n_dashes = n_dots = 0
        largest_extent, first_scale = 0.0, None

        for idx, (verts, polys, edges, scale, offx, offy) in enumerate(zip(*match_long_repeat(
                [verts_in, polys_in, edges_in, scale_in, offx_in, offy_in]))):
            try:
                result = hatch_region(
                    verts, pattern,
                    loops=polys if polys is not None and len(polys) else None,
                    edges=edges if edges is not None and len(edges) else None,
                    scale=scale[0], offset=(offx[0], offy[0]),
                    min_length=self.min_length, max_segments=self.max_segments)
            except (RegionError, HatchTooDense) as err:
                self.set_status(f"object {idx}: {err}", "WARNING")
                raise type(err)(f"object {idx}: {err}") from None
            n_dashes += len(result.segments)
            n_dots += len(result.dots)
            largest_extent = max(largest_extent, result.extent)
            if first_scale is None:
                first_scale = scale[0]

            seg = result.segments
            verts_out.append(seg.reshape(-1, 3).tolist())
            edges_out.append([[2 * i, 2 * i + 1] for i in range(len(seg))])
            dots_out.append(result.dots.tolist())
            planes.append(_matrix(result.frame))

            if want_strokes:
                strokes = chain_segments(seg, tol=_tolerance(seg))
                if self.order_strokes:
                    strokes = order_strokes(strokes)
                for s in strokes:
                    stroke_verts.append(s.tolist())
                    stroke_edges.append([[i, i + 1] for i in range(len(s) - 1)])

        self.set_status(*describe(pattern, first_scale or 1.0, len(verts_out), n_dashes, n_dots,
                                  largest_extent, self.max_segments))
        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Dots'].sv_set(dots_out)
        self.outputs['Stroke Vertices'].sv_set(stroke_verts)
        self.outputs['Stroke Edges'].sv_set(stroke_edges)
        self.outputs['Plane'].sv_set(planes)


def _set_status(node, text, level="INFO"):
    # plain StringProperties without update callbacks: setting them does not re-trigger process()
    if node.status != text:
        node.status = text
    if node.status_level != level:
        node.status_level = level


SvHatchPatternNode.set_status = _set_status


def _tolerance(segments):
    """endpoint matching tolerance relative to the size of the hatch"""
    if not len(segments):
        return 1e-6
    span = float(np.ptp(segments.reshape(-1, 3), axis=0).max())
    return max(span * 1e-9, 1e-9)


def _matrix(frame):
    from mathutils import Matrix
    origin, x, y, n = frame
    m = Matrix.Identity(4)
    for row in range(3):
        m[row][0], m[row][1], m[row][2], m[row][3] = x[row], y[row], n[row], origin[row]
    return m


def register():
    bpy.utils.register_class(SvHatchPatternNode)


def unregister():
    bpy.utils.unregister_class(SvHatchPatternNode)
