# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from collections import defaultdict

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat, rotate_list, repeat_last_for_length, fixed_iter
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from sverchok.utils.sv_mesh_utils import polygons_to_edges_np


split_modes = [
        ('SIMPLE', "Simple", "Split each edge in two parts, controlled by factor", 0),
        ('MIRROR', "Mirror", "Split each edge in two symmetrical parts, controlled by factor", 1),
        ('MULTI', "Multiple", "Split each edge in several parts, controlled by number of parts", 2)
    ]


class SvSplitEdgesMk3Node(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Split Edges
    Tooltip: Split each edge of a mesh in two
    """
    bl_idname = 'SvSplitEdgesMk3Node'
    bl_label = 'Split Edges'
    sv_icon = 'SV_SPLIT_EDGES'
    # sv_icon = 'SV_EDGE_SPLIT'

    def update_mode(self, context):
        self.inputs['Factor'].hide = False  # This can be True in old nodes
        self.inputs['Cuts'].hide = False  # This can be True in old nodes
        self.inputs['Factor'].hide_safe = self.mode == 'MULTI'
        self.inputs['Cuts'].hide_safe = self.mode != 'MULTI'
        self.process_node(context)

    factor: bpy.props.FloatProperty(
        name="Factor", description="Split Factor",
        default=0.5, min=0.0, soft_min=0.0, max=1.0,
        update=lambda s, c: s.process_node(c))
    count: bpy.props.IntProperty(
        name="Cuts",
        description="Number of cuts to make at each edge, i.e. number of new vertices at each edge",
        default=1, min=0, update=lambda s, c: s.process_node(c))
    mode: bpy.props.EnumProperty(
        name="Mode", description="Edge split mode",
        items=split_modes, default='SIMPLE', update=update_mode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'EdgeMask')
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = 'factor'
        s = self.inputs.new('SvStringsSocket', 'Cuts')
        s.prop_name = 'count'
        #s.enabled = False
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def process(self):
        verts = self.inputs['Vertices'].sv_get(default=[])
        edges = self.inputs['Edges'].sv_get(default=[])
        faces = self.inputs['Faces'].sv_get(default=[])
        e_mask = self.inputs['EdgeMask'].sv_get(deepcopy=False, default=[[True]])
        factor = self.inputs['Factor'].sv_get(deepcopy=False)
        cuts = self.inputs['Cuts'].sv_get(deepcopy=False)

        if faces and not edges:
            edges = polygons_to_edges_np(faces, True, False)

        obj_n = max(len(verts), len(e_mask), len(factor), len(cuts))
        out_v = []
        out_e = []
        out_f = []

        def vec(arr):
            return fixed_iter(arr, obj_n, [])

        for v, e, face, m, fact, c in zip(vec(verts), vec(edges), vec(faces), vec(e_mask), vec(factor), vec(cuts)):
            if not all((v, e)):
                break

            new_faces = list(face)
            faces_per_edge = defaultdict(list)
            for face_idx, f in enumerate(new_faces):
                for i, j in zip(f, rotate_list(f)):
                    faces_per_edge[(i, j)].append((i, False, face_idx))
                    faces_per_edge[(j, i)].append((j, True, face_idx))

            def insert_after(_face, _vert_idx, _new_vert_idx):
                idx = _face.index(_vert_idx)
                _face.insert(idx+1, _new_vert_idx)

            def insert_before(_face, _vert_idx, _new_vert_idx):
                idx = _face.index(_vert_idx)
                _face.insert(idx, _new_vert_idx)

            # sanitize the input
            input_f = list(map(lambda _f: min(1, max(0, _f)), fact))
            counts = repeat_last_for_length(c, len(e))

            mask = repeat_last_for_length(m, len(e))
            params = match_long_repeat([e, mask, input_f, counts])

            offset = len(v)
            new_verts = list(v)
            new_edges = []
            i = 0
            for edge, ok, factor, count in zip(*params):
                if not ok:
                    new_edges.append(edge)
                    continue

                i0 = edge[0]
                i1 = edge[1]
                v0 = v[i0]
                v1 = v[i1]

                if self.mode == 'MIRROR':
                    factor = factor / 2

                    vx = v0[0] * (1 - factor) + v1[0] * factor
                    vy = v0[1] * (1 - factor) + v1[1] * factor
                    vz = v0[2] * (1 - factor) + v1[2] * factor
                    va = [vx, vy, vz]
                    new_verts.append(va)

                    vx = v0[0] * factor + v1[0] * (1 - factor)
                    vy = v0[1] * factor + v1[1] * (1 - factor)
                    vz = v0[2] * factor + v1[2] * (1 - factor)
                    vb = [vx, vy, vz]
                    new_verts.append(vb)

                    new_edges.append([i0, offset + i])  # v0 - va
                    new_edges.append([offset + i, offset + i + 1])  # va - vb
                    new_edges.append([offset + i + 1, i1])  # vb - v1

                    for vert_idx, before, face_idx in faces_per_edge[tuple(edge)]:
                        if before:
                            insert_before(new_faces[face_idx], vert_idx, offset+i)
                            insert_before(new_faces[face_idx], offset+i, offset+i+1)
                        else:
                            insert_after(new_faces[face_idx], vert_idx, offset+i)
                            insert_after(new_faces[face_idx], offset+i, offset+i+1)

                    i = i + 2

                elif self.mode == 'SIMPLE':
                    vx = v0[0] * (1 - factor) + v1[0] * factor
                    vy = v0[1] * (1 - factor) + v1[1] * factor
                    vz = v0[2] * (1 - factor) + v1[2] * factor
                    va = [vx, vy, vz]
                    new_verts.append(va)

                    new_edges.append([i0, offset + i])  # v0 - va
                    new_edges.append([offset + i, i1])  # va - v1

                    for vert_idx, before, face_idx in faces_per_edge[tuple(edge)]:
                        if before:
                            insert_before(new_faces[face_idx], vert_idx, offset+i)
                        else:
                            insert_after(new_faces[face_idx], vert_idx, offset+i)

                    i = i + 1

                else:  # MULTI
                    if count > 0:
                        new_vert_idxs = []
                        j = offset + i
                        for p in np.linspace(0.0, 1.0, num=count+1, endpoint=False)[1:]:
                            vx = v0[0] * (1 - p) + v1[0] * p
                            vy = v0[1] * (1 - p) + v1[1] * p
                            vz = v0[2] * (1 - p) + v1[2] * p
                            va = [vx, vy, vz]
                            new_verts.append(va)
                            new_vert_idxs.append(j)
                            j += 1

                        if new_vert_idxs:
                            vert_idxs = [i0] + new_vert_idxs[:]
                            edges = list(zip(vert_idxs, vert_idxs[1:]))
                            edges.append((vert_idxs[-1], i1))
                            new_edges.extend(edges)

                            for vert_idx, before, face_idx in faces_per_edge[tuple(edge)]:
                                prev_vert_idx = vert_idx
                                for new_vert_idx in new_vert_idxs:
                                    if before:
                                        insert_before(new_faces[face_idx], prev_vert_idx, new_vert_idx)
                                    else:
                                        insert_after(new_faces[face_idx], prev_vert_idx, new_vert_idx)
                                    prev_vert_idx = new_vert_idx
                    else:
                        new_edges.append(edge)

                    i = i + count

            out_v.append(new_verts)
            out_e.append(new_edges)
            out_f.append(new_faces)

        self.outputs['Vertices'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)
        self.outputs['Faces'].sv_set(out_f)


register, unregister = bpy.utils.register_classes_factory([SvSplitEdgesMk3Node])
