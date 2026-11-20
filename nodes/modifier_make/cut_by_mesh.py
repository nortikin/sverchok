# SPDX-License-Identifier: GPL-3.0-or-later
"""Sverchok Cut by Mesh: cut, split (disconnect), or separate into objects.

The Blender-independent core lives in utils/mesh/mesh_cut*.py.
"""

import bpy
from bpy.props import BoolProperty, BoolVectorProperty, EnumProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.mesh.mesh_cut_parts import cut_mesh_parts
from sverchok.utils.mesh.mesh_cut import HAS_NUMBA, HAS_SCIPY


class SvCutByMeshNpNode(SverchCustomTreeNode, bpy.types.Node):
    """Triggers: Cut split separate mesh bisect knife; Tooltip: Cut mesh A with surface B; split seams or separate pieces"""
    bl_idname = 'SvCutByMeshNpNode'
    bl_label = 'Cut by Mesh'
    bl_icon = 'MOD_BOOLEAN'

    ADVANCED_OUTPUTS = (
        'Cut Vertices Mask',
        'Face Origins',
        'Intersection Vertices',
        'Intersection Edges',
    )

    def _rename_legacy_cutter_sockets(self):
        """Rename old .blend sockets *in place* to keep their existing links.

        We intentionally do not delete/recreate sockets and do not reorder them.
        Existing input data and NodeLink socket pointers remain unchanged.
        """
        if len(self.inputs) >= 4:
            for index, old_name, new_name in (
                (2, 'Vertices B', 'Vertices Cutter'),
                (3, 'Faces B', 'Faces Cutter'),
            ):
                socket = self.inputs[index]
                if socket.name == old_name:
                    socket.name = new_name

    def update_sockets(self, context):
        self._rename_legacy_cutter_sockets()
        for name in self.ADVANCED_OUTPUTS:
            if name in self.outputs:
                self.outputs[name].hide_safe = not self.advanced_outputs
        updateNode(self, context)

    advanced_outputs: BoolProperty(
        name='Advanced Outputs',
        description='Show origin indices, cut-vertex mask and intersection geometry',
        default=False, update=update_sockets,
    )
    mode: EnumProperty(
        name='Mode',
        description='Cut keeps one connected mesh; Split opens seam edges; Separate outputs one SV object per piece',
        items=[
            ('CUT', 'Cut', 'Insert intersection edges, preserve topology'),
            ('SPLIT', 'Split', 'Disconnect vertices along cut edges; output loose parts as one SV object'),
            ('SEPARATE', 'Separate', 'Return each disconnected region as an independent SV object'),
        ],
        default='CUT', update=updateNode,
    )
    keep: EnumProperty(
        name='Keep',
        description='Filter the regions after cutting; side choices need a planar or closed B',
        items=[
            ('ALL', 'All', 'Keep all parts (do not remove geometry)'),
            ('POSITIVE', 'Positive', 'Keep side pointed to by planar B face normals'),
            ('NEGATIVE', 'Negative', 'Keep opposite side of planar B face normals'),
            ('INSIDE', 'Inside', 'Keep regions inside a closed, oriented cutter B'),
            ('OUTSIDE', 'Outside', 'Keep regions outside a closed, oriented cutter B'),
            ('LARGEST', 'Largest', 'Keep largest part by surface area'),
            ('SMALLEST', 'Smallest', 'Keep smallest part by surface area'),
            ('INDEX', 'Index', 'Keep one region (sorted largest to smallest)'),
        ],
        default='ALL', update=updateNode,
    )
    piece_index: IntProperty(
        name='Piece Index', description='Piece index (sorted by decreasing surface area)',
        default=0, min=0, update=updateNode,
    )
    out_np: BoolVectorProperty(
        name='Output NumPy',
        description='Output Vertices and Edges as NumPy arrays instead of Python lists',
        size=2, default=(False, False), update=updateNode,
    )
    acceleration: EnumProperty(
        name='Search',
        description='Broad-phase backend; Auto prefers SciPy cKDTree',
        items=[
            ('AUTO', 'Auto', 'SciPy if installed, otherwise NumPy BVH'),
            ('SCIPY', 'SciPy', 'Force SciPy cKDTree'),
            ('BVH', 'NumPy', 'Force NumPy BVH'),
            ('BRUTE', 'Brute Force', 'Exhaustive AABB search, useful for comparison'),
        ],
        default='AUTO', update=updateNode,
    )
    tolerance: FloatProperty(
        name='Tolerance', description='Distance tolerance in mesh coordinate units',
        default=1e-6, min=1e-12, precision=6, update=updateNode,
    )
    preserve_polygons: BoolProperty(
        name='Preserve Polygons',
        description='Recombine internal triangles into original polygon regions without removing cut edges',
        default=True, update=updateNode,
    )
    include_coplanar: BoolProperty(
        name='Coplanar', description='Cut at rims of coplanar overlaps',
        default=True, update=updateNode,
    )

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices A')
        self.inputs.new('SvStringsSocket', 'Faces A')
        self.inputs.new('SvVerticesSocket', 'Vertices Cutter')
        self.inputs.new('SvStringsSocket', 'Faces Cutter')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Cut Edges Mask')
        self.outputs.new('SvStringsSocket', 'Cut Vertices Mask')
        self.outputs.new('SvStringsSocket', 'Face Origins')
        self.outputs.new('SvVerticesSocket', 'Intersection Vertices')
        self.outputs.new('SvStringsSocket', 'Intersection Edges')
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', text='Mode')
        if self.mode != 'CUT':
            layout.prop(self, 'keep', text='Keep')
            if self.keep == 'INDEX':
                layout.prop(self, 'piece_index', text='Index')
        layout.prop(self, 'advanced_outputs', toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'acceleration', text='Search')
        layout.prop(self, 'preserve_polygons')
        layout.prop(self, 'include_coplanar')
        layout.prop(self, 'tolerance')
        layout.label(text='Output NumPy:')
        row = layout.row(align=True)
        row.prop(self, 'out_np', index=0, text='Vertices', toggle=True)
        row.prop(self, 'out_np', index=1, text='Edges', toggle=True)
        layout.label(text=f'SciPy: {"available" if HAS_SCIPY else "unavailable"}')
        layout.label(text=f'Numba: {"enabled" if HAS_NUMBA else "unavailable"} (automatic)')
        layout.label(text='Separate: one object per region')

    def process(self):
        self._rename_legacy_cutter_sockets()
        if not any(sock.is_linked for sock in self.outputs):
            return
        outputs = [[] for _ in self.outputs]
        data = [sock.sv_get(default=[[]]) for sock in self.inputs]
        backend = {'AUTO': 'auto', 'SCIPY': 'scipy', 'BVH': 'bvh', 'BRUTE': 'brute'}[self.acceleration]

        for va, fa, vb, fb in zip_long_repeat(*data):
            result = cut_mesh_parts(
                va, fa, vb, fb,
                mode=self.mode,
                keep='ALL' if self.mode == 'CUT' else self.keep,
                piece_index=self.piece_index,
                tolerance=self.tolerance,
                acceleration=backend,
                use_numba=HAS_NUMBA,
                include_coplanar=self.include_coplanar,
                preserve_polygons=self.preserve_polygons,
            )
            # Separate mode appends one object per part. Never materialize
            # inactive outputs (or convert NumPy to Python lists needlessly).
            linked = [sock.is_linked for sock in self.outputs]
            int_verts = (result.intersection_vertices.tolist()
                         if linked[6] else None)
            int_edges = (result.intersection_edges.tolist()
                         if linked[7] else None)
            for piece in result.pieces:
                if linked[0]:
                    outputs[0].append(piece.vertices if self.out_np[0]
                                      else piece.vertices.tolist())
                if linked[1]:
                    outputs[1].append(piece.edges if self.out_np[1]
                                      else piece.edges.tolist())
                if linked[2]:
                    outputs[2].append(piece.faces)
                if linked[3]:
                    outputs[3].append(piece.cut_edge_mask.tolist())
                if linked[4]:
                    outputs[4].append(piece.cut_vertex_mask.tolist())
                if linked[5]:
                    outputs[5].append(piece.face_origins.tolist())
                if linked[6]:
                    outputs[6].append(int_verts)
                if linked[7]:
                    outputs[7].append(int_edges)
        for socket, values in zip(self.outputs, outputs):
            if socket.is_linked:
                socket.sv_set(values)


def register():
    bpy.utils.register_class(SvCutByMeshNpNode)


def unregister():
    bpy.utils.unregister_class(SvCutByMeshNpNode)
