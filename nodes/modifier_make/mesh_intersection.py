# SPDX-License-Identifier: GPL-3.0-or-later
"""Sverchok frontend for Blender-independent NumPy mesh intersection kernel.

Returns intersection geometry only: it does not split faces of either mesh.
The geometry kernel has no bpy, bmesh, or mathutils dependencies.
"""

import bpy
from bpy.props import BoolProperty, BoolVectorProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.mesh.mesh_intersections import (
    HAS_NUMBA,
    HAS_SCIPY,
    intersect_meshes,
)


class SvMeshIntersectionNpNode(SverchCustomTreeNode, bpy.types.Node):
    """Triggers: Mesh intersection numpy scipy numba; Tooltip: Extract intersections between two surface meshes without BMesh"""

    # Keep existing bl_idname to preserve saved Sverchok node trees.
    bl_idname = 'SvMeshIntersectionNpNode'
    bl_label = 'Mesh Intersection'
    bl_icon = 'MOD_BOOLEAN'

    BASIC_OUTPUTS = ('Vertices', 'Edges')
    ADVANCED_OUTPUTS = (
        'Point Indices',
        'Coplanar Polygons',
        'Edge Face Pairs',
        'Point Face Pairs',
        'Coplanar Face Pairs',
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
        """Use hide_safe so existing advanced links stay connected and visible."""
        for name in self.ADVANCED_OUTPUTS:
            if name in self.outputs:
                self.outputs[name].hide_safe = not self.advanced_outputs
        updateNode(self, context)

    advanced_outputs: BoolProperty(
        name='Advanced Outputs',
        description='Show contact, coplanar and original-face attribution outputs',
        default=False,
        update=update_sockets,
    )
    out_np: BoolVectorProperty(
        name='Output NumPy',
        description='Output Vertices and Edges as NumPy arrays instead of Python lists',
        size=2, default=(False, False), update=updateNode,
    )
    acceleration: EnumProperty(
        name='Search',
        description='Broad-phase candidate search; Auto uses SciPy when available',
        items=[
            ('AUTO', 'Auto', 'Use SciPy cKDTree if available, otherwise NumPy BVH'),
            # Preserve the old enum identifiers, including forced SciPy, so
            # pre-existing saved .blend nodes do not lose their settings.
            ('SCIPY', 'SciPy', 'Force SciPy cKDTree (requires SciPy)'),
            ('BVH', 'NumPy', 'Force NumPy AABB BVH (no SciPy)'),
            ('BRUTE', 'Brute Force', 'Exhaustive NumPy AABB scan; for diagnostics'),
        ],
        default='AUTO',
        update=updateNode,
    )
    tolerance: FloatProperty(
        name='Tolerance',
        description='Absolute tolerance in mesh coordinate units',
        default=1e-6,
        min=1e-12,
        precision=6,
        update=updateNode,
    )
    include_coplanar: BoolProperty(
        name='Coplanar',
        description='Include coplanar overlap polygons and 1D coplanar contacts',
        default=True,
        update=updateNode,
    )

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices A')
        self.inputs.new('SvStringsSocket', 'Faces A')
        self.inputs.new('SvVerticesSocket', 'Vertices Cutter')
        self.inputs.new('SvStringsSocket', 'Faces Cutter')

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        for name in self.ADVANCED_OUTPUTS:
            self.outputs.new('SvStringsSocket', name)
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'advanced_outputs', toggle=True)

    def draw_buttons_ext(self, context, layout):
        """Options in the N-panel rather than cluttering the node itself."""
        layout.prop(self, 'acceleration', text='Search')
        layout.prop(self, 'include_coplanar')
        layout.prop(self, 'tolerance')
        layout.label(text='Output NumPy:')
        row = layout.row(align=True)
        row.prop(self, 'out_np', index=0, text='Vertices', toggle=True)
        row.prop(self, 'out_np', index=1, text='Edges', toggle=True)
        layout.label(text=f'SciPy: {"available" if HAS_SCIPY else "unavailable"}')
        layout.label(text=f'Numba: {"enabled" if HAS_NUMBA else "unavailable"} (automatic)')
        layout.label(text='Intersections only; faces are not cut')

    def get_backend(self):
        """Select a backend without timing probes or a SciPy requirement."""
        if self.acceleration == 'AUTO':
            return 'scipy' if HAS_SCIPY else 'bvh'
        return {
            'SCIPY': 'scipy',
            'BVH': 'bvh',
            'BRUTE': 'brute',
        }[self.acceleration]

    def process(self):
        self._rename_legacy_cutter_sockets()
        if not any(sock.is_linked for sock in self.outputs):
            return

        inputs = [socket.sv_get(default=[[]]) for socket in self.inputs]
        acceleration = self.get_backend()
        result_data = [[] for _ in self.outputs]

        for vertices_a, faces_a, vertices_b, faces_b in zip_long_repeat(*inputs):
            result = intersect_meshes(
                vertices_a, faces_a, vertices_b, faces_b,
                tolerance=self.tolerance,
                acceleration=acceleration,
                # Use Numba whenever installed. No option or pair-count threshold.
                use_numba=HAS_NUMBA,
                include_coplanar=self.include_coplanar,
            )
            # Preserve arrays end-to-end when requested. Avoid converting
            # advanced outputs that are not actually connected.
            if self.outputs[0].is_linked:
                result_data[0].append(result.vertices if self.out_np[0]
                                      else result.vertices.tolist())
            if self.outputs[1].is_linked:
                result_data[1].append(result.edges if self.out_np[1]
                                      else result.edges.tolist())
            if self.outputs[2].is_linked:
                result_data[2].append(result.point_indices.tolist())
            if self.outputs[3].is_linked:
                result_data[3].append([poly.tolist() for poly in result.coplanar_polygons])
            if self.outputs[4].is_linked:
                result_data[4].append(result.edge_face_pairs.tolist())
            if self.outputs[5].is_linked:
                result_data[5].append(result.point_face_pairs.tolist())
            if self.outputs[6].is_linked:
                result_data[6].append(result.coplanar_face_pairs.tolist())

        for socket, values in zip(self.outputs, result_data):
            if socket.is_linked:
                socket.sv_set(values)


def register():
    bpy.utils.register_class(SvMeshIntersectionNpNode)


def unregister():
    bpy.utils.unregister_class(SvMeshIntersectionNpNode)
