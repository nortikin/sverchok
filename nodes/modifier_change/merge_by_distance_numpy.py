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
from sverchok.utils.mesh.sv_mesh_core.nesting import map_mesh_tree
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode


OUTPUT_NAMES = ('Vertices', 'Edges', 'Polygons', 'FaceData', 'Doubles', 'Mask')
NUMPY_FLAGS = (
    ('numpy_vertices', 'Vertices'),
    ('numpy_edges', 'Edges'),
    ('numpy_face_data', 'FaceData'),
    ('numpy_doubles', 'Doubles'),
    ('numpy_mask', 'Mask'),
)


def _as_numpy(value, index):
    if index in (0, 4):
        return np.asarray(value, dtype=np.float32).reshape(-1, 3)
    if index == 1:
        return np.asarray(value, dtype=np.intp).reshape(-1, 2)
    if index == 3:
        try:
            return np.asarray(value)
        except ValueError:
            # FaceData may be a sequence of variable-length payloads.
            output = np.empty(len(value), dtype=object)
            output[:] = list(value)
            return output
    if index == 5:
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
    Tooltip: Merge nearby vertices using independent GRID clustering.

    Distance is one scalar per mesh; distance arrays match meshes, not vertices.
    """
    bl_idname = 'SvMergeByDistanceNumpyNode'
    bl_label = 'Merge by Distance'
    bl_icon = 'AUTOMERGE_ON'
    sv_icon = 'SV_REMOVE_DOUBLES'

    distance: FloatProperty(name='Distance', default=0.001, min=0,
                            update=updateNode)
    # Preserve stored enum identifiers from experimental v8 .blend files.
    # VERIFY is intentionally removed. Visible choices are GRID and BMesh.
    mode: EnumProperty(name='Implementation', default='FAST', update=updateNode,
                       items=[('FAST', 'GRID', 'Portable, fast; default'),
                              ('REFERENCE', 'BMesh (Legacy)', 'Original Blender behavior')])
    list_match: EnumProperty(name='List Match',
                             description='Match lists of meshes and per-mesh inputs',
                             default='REPEAT', items=numpy_list_match_modes,
                             update=updateNode)

    numpy_vertices: BoolProperty(name='Vertices as NumPy', default=False, update=updateNode)
    numpy_edges: BoolProperty(name='Edges as NumPy', default=False, update=updateNode)
    numpy_face_data: BoolProperty(name='FaceData as NumPy', default=False, update=updateNode)
    numpy_doubles: BoolProperty(name='Doubles as NumPy', default=False, update=updateNode)
    numpy_mask: BoolProperty(name='Mask as NumPy', default=False, update=updateNode)

    # Development-only compatibility for v8 benchmark scripts. Not user-visible.
    neighbor_backend: EnumProperty(name='GRID accelerator override', default='AUTO',
        items=[(name,name.title(), '') for name in
               ('AUTO','GRID','GRID_SCIPY','GRID_PY','NUMPY','NUMBA','SCIPY')],
        options={'HIDDEN'}, update=updateNode)
    use_numba: BoolProperty(name='Enable Numba accelerator', default=True,
                            options={'HIDDEN'}, update=updateNode)

    @property
    def sv_internal_links(self):
        return [
            (self.inputs['Vertices'], self.outputs['Vertices']),
            (self.inputs['PolyEdge'], self.outputs['Polygons']),
            (self.inputs['FaceData'], self.outputs['FaceData']),
            (self.inputs['Mask'], self.outputs['Mask']),
        ]

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        for name in ('PolyEdge','FaceData','Mask'):
            self.inputs.new('SvStringsSocket', name)
        self.inputs.new('SvStringsSocket','Distance').prop_name = 'distance'
        for socket_type, name in (
            ('SvVerticesSocket','Vertices'), ('SvStringsSocket','Edges'),
            ('SvStringsSocket','Polygons'), ('SvStringsSocket','FaceData'),
            ('SvVerticesSocket','Doubles'), ('SvStringsSocket','Mask')):
            self.outputs.new(socket_type, name)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'mode')
        layout.prop(self, 'list_match')
        layout.separator()
        layout.label(text='NumPy output per socket')
        for name, label in NUMPY_FLAGS:
            layout.prop(self, name, text=label)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, 'mode', text='Implementation')
        layout.prop_menu_enum(self, 'list_match', text='List Match')
        layout.menu(SV_MT_MergeByDistanceNumpyOutputs.bl_idname, text='NumPy outputs')

    def process(self):
        if not self.inputs['Vertices'].is_linked or not any(s.is_linked for s in self.outputs):
            return
        linked = {socket.name for socket in self.outputs if socket.is_linked}
        numpy_flags = (self.numpy_vertices, self.numpy_edges, False,
                       self.numpy_face_data, self.numpy_doubles, self.numpy_mask)
        source = [self.inputs['Vertices'].sv_get(default=[[]], deepcopy=False)]
        for name in ('PolyEdge', 'FaceData', 'Mask'):
            socket = self.inputs[name]
            # Unconnected optional sockets are broadcast defaults, not a
            # one-item object collection that truncates SHORT list matching.
            source.append(socket.sv_get(default=[[]], deepcopy=False)
                          if socket.is_linked else [])
        distance_values = (_distance_socket_data(
            self.inputs['Distance'].sv_get(default=[[self.distance]], deepcopy=False))
            if self.inputs['Distance'].is_linked else self.distance)
        reference = self.mode == 'REFERENCE'
        version = '4.3' if bpy.app.version[:2] == (4,3) else '5.1'

        def evaluate(vertices, poly, data, mask, distance):
            if reference:
                # Only an explicitly selected legacy mode may import BMesh.
                from sverchok.old_nodes.merge_by_distance import remove_doubles
                if isinstance(poly, RaggedArray):
                    poly = poly.to_list()
                elif isinstance(poly, np.ndarray):
                    poly = poly.tolist()
                if isinstance(data, np.ndarray):
                    data = data.tolist()
                if isinstance(mask, np.ndarray):
                    mask = mask.tolist()
                result = remove_doubles(vertices, poly, distance,
                    face_data=data, find_doubles='Doubles' in linked,
                    mask=mask, output_mask='Mask' in linked)
            else:
                result = merge_by_distance(vertices, poly, distance,
                    face_data=data, mask=mask, use_numba=self.use_numba,
                    backend=self.neighbor_backend, reference_version=version,
                    output_doubles='Doubles' in linked,
                    output_mask='Mask' in linked,
                    output_edges='Edges' in linked,
                    output_polygons='Polygons' in linked,
                    output_face_data='FaceData' in linked,
                    output_numpy=True)
            return tuple(_as_numpy(value, i) if numpy_flags[i] else _as_lists(value)
                         for i, value in enumerate(result))

        out = map_mesh_tree(*source, distance_values, evaluate, matching=self.list_match)
        for socket, data in zip(self.outputs, out):
            if socket.is_linked:
                socket.sv_set(data)


classes = (SV_MT_MergeByDistanceNumpyOutputs, SvMergeByDistanceNumpyNode)
register, unregister = bpy.utils.register_classes_factory(classes)
