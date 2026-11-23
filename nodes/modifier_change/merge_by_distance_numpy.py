# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Merge by Distance: portable GRID default; explicit legacy BMesh option.

Does not inherit from an already registered Blender node class.
The separate old_nodes/SvMergeByDistanceNode retains the historical tree ID.
"""
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
import numpy as np

from sverchok.data_structure import updateNode, numpy_list_match_modes
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.mesh.merge_numpy import merge_by_distance
from sverchok.utils.mesh.sv_mesh_core.buffers import RaggedArray
from sverchok.utils.mesh.sv_mesh_core.data_nesting import map_mesh_tree_data
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode


OUTPUT_NAMES = ('Vertices', 'Edges', 'Polygons', 'Doubles', 'Mask',
                'VertData', 'EdgeData', 'FaceData',
                'Vert Init Index', 'Edge Init Index', 'Face Init Index')
INPUT_NAMES = ('Vertices', 'Edges', 'Polygons', 'Verts Mask', 'Distance',
               'VertData', 'EdgeData', 'FaceData')
MESH_DATA_INPUTS = ('VertData', 'EdgeData', 'FaceData')
MESH_DATA_OUTPUTS = ('VertData', 'EdgeData', 'FaceData',
                     'Vert Init Index', 'Edge Init Index', 'Face Init Index')
NUMPY_FLAGS = (
    ('numpy_vertices', 'Vertices'),
    ('numpy_edges', 'Edges'),
    ('numpy_doubles', 'Doubles'),
    ('numpy_mask', 'Mask'),
    ('numpy_vert_data', 'VertData'),
    ('numpy_edge_data', 'EdgeData'),
    ('numpy_face_data', 'FaceData'),
)


def _as_numpy(value, index):
    if index in (0, 3):
        return np.asarray(value, dtype=np.float32).reshape(-1, 3)
    if index == 1:
        return np.asarray(value, dtype=np.intp).reshape(-1, 2)
    if index in (5, 6, 7):
        try:
            return np.asarray(value)
        except ValueError:
            # FaceData may be a sequence of variable-length payloads.
            output = np.empty(len(value), dtype=object)
            output[:] = list(value)
            return output
    if index == 4:
        return np.asarray(value)
    return value


def _as_lists(value):
    if isinstance(value, RaggedArray):
        return value.to_list()
    return value.tolist() if isinstance(value, np.ndarray) else value


def _distance_socket_data(value):
    """Unwrap Sverchok's outer numerical socket level, not mesh-level nesting."""
    if isinstance(value, np.ndarray) and value.ndim >= 2 and len(value) == 1:
        return value[0]
    if isinstance(value, (list, tuple)) and len(value) == 1 and isinstance(value[0], (list, tuple, np.ndarray)):
        return value[0]
    return value


def _set_mesh_data_socket_visibility(node):
    """Update visibility without modifying linked sockets or triggering evaluation."""
    for sockets, names in ((node.inputs, MESH_DATA_INPUTS),
                           (node.outputs, MESH_DATA_OUTPUTS)):
        for name in names:
            socket = sockets.get(name)
            if socket is not None:
                socket.hide = not node.mesh_data and not socket.is_linked


def _update_mesh_data(node, context):
    """Hide unlinked data sockets only; never drop an existing connection.

    Sverchok's ``hide_safe`` *removes links* when hiding a connected socket.
    Therefore connected data sockets remain visible even with Mesh Data off.
    """
    _set_mesh_data_socket_visibility(node)
    updateNode(node, context)


class SV_MT_MergeByDistanceNumpyOutputs(bpy.types.Menu):
    bl_idname = 'SV_MT_merge_by_distance_numpy_outputs'
    bl_label = 'NumPy outputs'

    def draw(self, context):
        space = context.space_data
        tree = getattr(space, 'edit_tree', None)
        node = tree.nodes.active if tree else None
        if node is None or node.bl_idname != 'SvMergeByDistanceNumpyNode':
            self.layout.label(text='Select a Merge by Distance node')
            return
        for name, label in NUMPY_FLAGS:
            self.layout.prop(node, name, text=label)


class SvMergeByDistanceNumpyNode(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Weld, Doubled Verts
    Tooltip: Merge vertices by distance with optional data provenance.

    Distance is one scalar per mesh, not a radius per vertex.
    """
    bl_idname = 'SvMergeByDistanceNumpyNode'
    bl_label = 'Merge by Distance'
    bl_icon = 'AUTOMERGE_ON'
    sv_icon = 'SV_REMOVE_DOUBLES'

    distance: FloatProperty(name='Distance', default=0.001, min=0,
                            update=updateNode)
    # Preserve saved enum identifiers from previous versions.
    mode: EnumProperty(name='Implementation', default='FAST', update=updateNode,
                       items=[('FAST', 'GRID', 'Portable fast implementation'),
                              ('REFERENCE', 'BMesh (Legacy)', 'Original Blender behavior')])
    list_match: EnumProperty(name='List Match',
                             description='Match lists of meshes and per-mesh inputs',
                             default='REPEAT', items=numpy_list_match_modes,
                             update=updateNode)
    mesh_data: BoolProperty(name='Mesh Data', default=False,
                            description='Show data and origin sockets (connected sockets are never hidden)',
                            update=_update_mesh_data)
    numpy_vertices: BoolProperty(name='Vertices as NumPy', default=False, update=updateNode)
    numpy_edges: BoolProperty(name='Edges as NumPy', default=False, update=updateNode)
    numpy_doubles: BoolProperty(name='Doubles as NumPy', default=False, update=updateNode)
    numpy_mask: BoolProperty(name='Mask as NumPy', default=False, update=updateNode)
    numpy_vert_data: BoolProperty(name='VertData as NumPy', default=False, update=updateNode)
    numpy_edge_data: BoolProperty(name='EdgeData as NumPy', default=False, update=updateNode)
    numpy_face_data: BoolProperty(name='FaceData as NumPy', default=False, update=updateNode)

    # Retain the hidden accelerator override for benchmarks; no VERIFY/strict.
    neighbor_backend: EnumProperty(name='GRID accelerator override', default='AUTO',
        items=[(name,name.title(), '') for name in
               ('AUTO','GRID','GRID_SCIPY','GRID_PY','NUMPY','NUMBA','SCIPY')],
        options={'HIDDEN'}, update=updateNode)
    use_numba: BoolProperty(name='Enable Numba accelerator', default=True,
                            options={'HIDDEN'}, update=updateNode)

    @property
    def sv_internal_links(self):
        pairs = [('Vertices', 'Vertices'), ('Edges', 'Edges'),
                 ('Polygons', 'Polygons'), ('Verts Mask', 'Mask'),
                 ('VertData', 'VertData'), ('EdgeData', 'EdgeData'),
                 ('FaceData', 'FaceData')]
        return [(self.inputs[a], self.outputs[b]) for a, b in pairs]

    def sv_init(self, context):
        # Geometry and mask first; arbitrary attributes last.
        for socket_type, name in (
            ('SvVerticesSocket', 'Vertices'),
            ('SvStringsSocket', 'Edges'),
            ('SvStringsSocket', 'Polygons'),
            ('SvStringsSocket', 'Verts Mask'),
            ('SvStringsSocket', 'Distance'),
            ('SvStringsSocket', 'VertData'),
            ('SvStringsSocket', 'EdgeData'),
            ('SvStringsSocket', 'FaceData')):
            socket = self.inputs.new(socket_type, name)
            if name == 'Distance':
                socket.prop_name = 'distance'
        for socket_type, name in (
            ('SvVerticesSocket', 'Vertices'), ('SvStringsSocket', 'Edges'),
            ('SvStringsSocket', 'Polygons'), ('SvVerticesSocket', 'Doubles'),
            ('SvStringsSocket', 'Mask'), ('SvStringsSocket', 'VertData'),
            ('SvStringsSocket', 'EdgeData'), ('SvStringsSocket', 'FaceData'),
            ('SvStringsSocket', 'Vert Init Index'),
            ('SvStringsSocket', 'Edge Init Index'),
            ('SvStringsSocket', 'Face Init Index')):
            self.outputs.new(socket_type, name)
        _set_mesh_data_socket_visibility(self)

    def sv_draw_buttons(self, context, layout):
        # The only control shown on the node itself.
        layout.prop(self, 'mesh_data', text='Mesh Data')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'mode')
        layout.prop(self, 'list_match')
        layout.prop(self, 'mesh_data')
        layout.separator()
        layout.label(text='NumPy output per socket')
        for name, label in NUMPY_FLAGS:
            layout.prop(self, name, text=label)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, 'mode', text='Implementation')
        layout.prop_menu_enum(self, 'list_match', text='List Match')
        layout.prop(self, 'mesh_data')
        layout.menu(SV_MT_MergeByDistanceNumpyOutputs.bl_idname, text='NumPy outputs')

    def process(self):
        if not self.inputs['Vertices'].is_linked or not any(s.is_linked for s in self.outputs):
            return
        linked = {socket.name for socket in self.outputs if socket.is_linked}
        numpy_flags = (self.numpy_vertices, self.numpy_edges, False,
                       self.numpy_doubles, self.numpy_mask,
                       self.numpy_vert_data, self.numpy_edge_data,
                       self.numpy_face_data, False, False, False)
        vertices = self.inputs['Vertices'].sv_get(default=[[]], deepcopy=False)
        polygons = (self.inputs['Polygons'].sv_get(default=[[]], deepcopy=False)
                    if self.inputs['Polygons'].is_linked else [])
        face_data = (self.inputs['FaceData'].sv_get(default=[[]], deepcopy=False)
                     if self.inputs['FaceData'].is_linked else [])
        mask = (self.inputs['Verts Mask'].sv_get(default=[[]], deepcopy=False)
                if self.inputs['Verts Mask'].is_linked else [])
        distance_values = (_distance_socket_data(
            self.inputs['Distance'].sv_get(default=[[self.distance]], deepcopy=False))
            if self.inputs['Distance'].is_linked else self.distance)
        edges = (self.inputs['Edges'].sv_get(default=[[]], deepcopy=False)
                 if self.inputs['Edges'].is_linked else [])
        vert_data = (self.inputs['VertData'].sv_get(default=[[]], deepcopy=False)
                     if self.inputs['VertData'].is_linked else [])
        edge_data = (self.inputs['EdgeData'].sv_get(default=[[]], deepcopy=False)
                     if self.inputs['EdgeData'].is_linked else [])
        # The portable tree mapper retains its original kernel argument order:
        # (vertices, polygons, face_data, mask, distance, edges, vert_data, edge_data).
        source = (vertices, polygons, face_data, mask, distance_values,
                  edges, vert_data, edge_data)
        reference = self.mode == 'REFERENCE'
        version = '4.3' if bpy.app.version[:2] == (4, 3) else '5.1'
        metadata_names = {'VertData', 'EdgeData', 'Vert Init Index',
                          'Edge Init Index', 'Face Init Index'}
        wants_metadata = bool(metadata_names & linked)
        extra_edges_linked = self.inputs['Edges'].is_linked
        if reference and (wants_metadata or extra_edges_linked):
            # No fabricated provenance for the legacy backend.
            raise NotImplementedError(
                'Mesh Data provenance and the separate Edges input require GRID. '
                'BMesh (Legacy) supports Polygons, Verts Mask, Distance and FaceData.')

        def evaluate(v, p, f, m, d, e, vd, ed):
            if reference:
                from sverchok.old_nodes.merge_by_distance import remove_doubles
                if isinstance(p, RaggedArray):
                    p = p.to_list()
                elif isinstance(p, np.ndarray):
                    p = p.tolist()
                if isinstance(f, np.ndarray):
                    f = f.tolist()
                if isinstance(m, np.ndarray):
                    m = m.tolist()
                result = remove_doubles(v, p, d,
                    face_data=f, find_doubles='Doubles' in linked,
                    mask=m, output_mask='Mask' in linked) + ([],)*5
            else:
                edge_mode = len(p) > 0 and len(p[0]) == 2
                result = merge_by_distance(v, p, d,
                    face_data=f, mask=m, use_numba=self.use_numba,
                    backend=self.neighbor_backend, reference_version=version,
                    output_doubles='Doubles' in linked,
                    output_mask='Mask' in linked,
                    output_edges='Edges' in linked,
                    output_polygons='Polygons' in linked,
                    output_face_data='FaceData' in linked,
                    output_numpy=True, edges=e, vert_data=vd, edge_data=ed,
                    output_mesh_data=wants_metadata,
                    edge_data_from_poly=(edge_mode and not extra_edges_linked))
                if not wants_metadata:
                    result = result + ([],)*5
            # Portable kernel returns: V E P FaceData Doubles Mask VertData
            # EdgeData VOrigin EOrigin FOrigin. Reorder for the requested UI.
            ordered = (result[0], result[1], result[2], result[4], result[5],
                       result[6], result[7], result[3],
                       result[8], result[9], result[10])
            return tuple(_as_numpy(value, i) if numpy_flags[i] else _as_lists(value)
                         for i, value in enumerate(ordered))

        out = map_mesh_tree_data(*source, evaluate, matching=self.list_match)
        for socket, data in zip(self.outputs, out):
            if socket.is_linked:
                socket.sv_set(data)


classes = (SV_MT_MergeByDistanceNumpyOutputs, SvMergeByDistanceNumpyNode)
register, unregister = bpy.utils.register_classes_factory(classes)
