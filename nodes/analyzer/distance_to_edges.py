# This file is part of Sverchok (GPL-3.0-or-later).
# SPDX-License-Identifier: GPL-3.0-or-later
"""Find the nearest point on an indexed edge network."""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, numpy_list_match_modes
from sverchok.utils.edge_distance import (
    HAS_NUMBA, recursive_distance_to_edges,
)


class SvDistanceToEdgesNode(SverchCustomTreeNode, bpy.types.Node):
    """Triggers: Distance to edges
    Tooltip: Find the nearest point on target edges or loose vertices
    """

    bl_idname = 'SvDistanceToEdgesNode'
    bl_label = 'Nearest Point on Edges'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def ensure_control_sockets(self):
        # Also upgrade nodes created with v5 when an old .blend is opened.
        if 'Distance' not in self.inputs:
            self.inputs.new('SvStringsSocket', 'Distance')
        if 'Count' not in self.inputs:
            self.inputs.new('SvStringsSocket', 'Count')
        dist_socket = self.inputs['Distance']
        count_socket = self.inputs['Count']
        if dist_socket.prop_name != 'max_distance':
            dist_socket.prop_name = 'max_distance'
        if count_socket.prop_name != 'nearest_count':
            count_socket.prop_name = 'nearest_count'
        # 'enabled' hides a socket without disconnecting its existing links.
        if dist_socket.enabled != (self.mode == 'RANGE'):
            dist_socket.enabled = self.mode == 'RANGE'
        if count_socket.enabled != (self.mode == 'NEAREST_N'):
            count_socket.enabled = self.mode == 'NEAREST_N'

    def update_mode(self, context):
        self.ensure_control_sockets()
        updateNode(self, context)

    mode: EnumProperty(
        name='Mode',
        description='How many points to return for each query point',
        items=[
            ('NEAREST', 'Nearest', 'Return only the closest point'),
            ('RANGE', 'Nearest in Range', 'All edges within the maximum distance'),
            ('NEAREST_N', 'Nearest N', 'The N nearest edges, if available'),
        ],
        default='NEAREST', update=update_mode)

    max_distance: FloatProperty(
        name='Max Distance',
        description='Include each edge whose closest point is within this distance',
        default=1.0, min=0.0, update=updateNode)

    nearest_count: IntProperty(
        name='Count',
        description='Maximum number of closest edges per query point',
        default=3, min=0, soft_max=50, update=updateNode)

    engine: EnumProperty(
        name='Engine',
        description='Algorithm used for the exhaustive exact search',
        items=[
            ('AUTO', 'Auto', 'Use Numba whenever installed, otherwise NumPy'),
            ('NUMPY', 'NumPy', 'Vectorized calculation with bounded block memory'),
            ('NUMBA', 'Numba', 'Compiled, parallel exhaustive search (requires Numba)'),
        ],
        default='AUTO', update=updateNode)

    list_match: EnumProperty(
        name='List Match',
        description='Match complete point sets and edge networks at every group level',
        items=numpy_list_match_modes, default='REPEAT', update=updateNode)

    include_loose: BoolProperty(
        name='Include Loose Vertices',
        description='Also search vertices not referenced by any target edge',
        default=True, update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Keep result arrays as NumPy arrays at the object level',
        default=False, update=updateNode)

    pair_budget: IntProperty(
        name='NumPy Block Pairs',
        description='Maximum point/edge pairs in a NumPy tile',
        default=65536, min=256, max=4_194_304, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Points').is_mandatory = True
        self.inputs.new('SvVerticesSocket', 'Target Verts').is_mandatory = True
        self.inputs.new('SvStringsSocket', 'Target Edges')
        # Append after the v5 inputs so existing .blend links keep their indices.
        self.ensure_control_sockets()

        self.outputs.new('SvStringsSocket', 'Distance')
        self.outputs.new('SvVerticesSocket', 'Closest Point')
        self.outputs.new('SvStringsSocket', 'Edge Index')
        self.outputs.new('SvStringsSocket', 'Factor')

    def sv_update(self):
        self.ensure_control_sockets()

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'mode', text='')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'engine', text='Engine')
        layout.label(text='Numba: available' if HAS_NUMBA else 'Numba: not installed')
        layout.prop(self, 'list_match')
        layout.prop(self, 'include_loose')
        layout.prop(self, 'output_numpy')
        row = layout.row()
        row.enabled = self.engine == 'NUMPY' or (self.engine == 'AUTO' and not HAS_NUMBA)
        row.prop(self, 'pair_budget')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, 'list_match', text='List Match')

    def process(self):
        self.ensure_control_sockets()
        if not any(s.is_linked for s in self.outputs):
            return
        if not self.inputs['Points'].is_linked or not self.inputs['Target Verts'].is_linked:
            for s in self.outputs:
                s.sv_set([])
            return

        points = self.inputs['Points'].sv_get(deepcopy=False)
        vertices = self.inputs['Target Verts'].sv_get(deepcopy=False)
        edges = (self.inputs['Target Edges'].sv_get(deepcopy=False)
                 if self.inputs['Target Edges'].is_linked else [[]])

        # Read only the active socket; defaults are exposed in its unlinked UI.
        max_distance = (self.inputs['Distance'].sv_get(deepcopy=False)
                        if self.mode == 'RANGE' and self.inputs['Distance'].is_linked
                        else self.max_distance)
        count = (self.inputs['Count'].sv_get(deepcopy=False)
                 if self.mode == 'NEAREST_N' and self.inputs['Count'].is_linked
                 else self.nearest_count)

        result = recursive_distance_to_edges(
            points, vertices, edges,
            engine=self.engine, list_match=self.list_match,
            include_loose=self.include_loose,
            output_numpy=self.output_numpy, pair_budget=self.pair_budget,
            mode=self.mode, max_distance=max_distance,
            count=count)
        for socket, value in zip(self.outputs, result):
            if socket.is_linked:
                socket.sv_set(value)


def register():
    bpy.utils.register_class(SvDistanceToEdgesNode)


def unregister():
    bpy.utils.unregister_class(SvDistanceToEdgesNode)
