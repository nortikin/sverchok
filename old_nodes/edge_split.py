# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat, fixed_iter


class SvSplitEdgesNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Split Edges '''
    bl_idname = 'SvSplitEdgesNode'
    bl_label = 'Split Edges'
    sv_icon = 'SV_SPLIT_EDGES'
    # sv_icon = 'SV_EDGE_SPLIT'

    replacement_nodes = [('SvSplitEdgesMk3Node', None, None)]

    factor: bpy.props.FloatProperty(
        name="Factor", description="Split Factor",
        default=0.5, min=0.0, soft_min=0.0, max=1.0,
        update=lambda s, c: s.process_node(c))
    mirror: bpy.props.BoolProperty(
        name="Mirror", description="Mirror split",
        default=False, update=lambda s, c: s.process_node(c))

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = 'factor'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mirror')

    def process(self):
        verts = self.inputs['Vertices'].sv_get(default=[])
        edges = self.inputs['Edges'].sv_get(default=[])
        factor = self.inputs['Factor'].sv_get(deepcopy=False)

        obj_n = max(len(verts), len(factor))
        out_v = []
        out_e = []

        def vec(arr):
            return fixed_iter(arr, obj_n, [])

        for v, e, f in zip(vec(verts), vec(edges), vec(factor)):
            if not all((v, e)):
                break

            # sanitize the input
            input_f = list(map(lambda _f: min(1, max(0, _f)), f))

            params = match_long_repeat([e, input_f])

            offset = len(v)
            new_verts = list(v)
            new_edges = []
            i = 0
            for edge, f in zip(*params):
                i0 = edge[0]
                i1 = edge[1]
                v0 = v[i0]
                v1 = v[i1]

                if self.mirror:
                    f = f / 2

                    vx = v0[0] * (1 - f) + v1[0] * f
                    vy = v0[1] * (1 - f) + v1[1] * f
                    vz = v0[2] * (1 - f) + v1[2] * f
                    va = [vx, vy, vz]
                    new_verts.append(va)

                    vx = v0[0] * f + v1[0] * (1 - f)
                    vy = v0[1] * f + v1[1] * (1 - f)
                    vz = v0[2] * f + v1[2] * (1 - f)
                    vb = [vx, vy, vz]
                    new_verts.append(vb)

                    new_edges.append([i0, offset + i])  # v0 - va
                    new_edges.append([offset + i, offset + i + 1])  # va - vb
                    new_edges.append([offset + i + 1, i1])  # vb - v1
                    i = i + 2

                else:
                    vx = v0[0] * (1 - f) + v1[0] * f
                    vy = v0[1] * (1 - f) + v1[1] * f
                    vz = v0[2] * (1 - f) + v1[2] * f
                    va = [vx, vy, vz]
                    new_verts.append(va)

                    new_edges.append([i0, offset + i])  # v0 - va
                    new_edges.append([offset + i, i1])  # va - v1
                    i = i + 1

            out_v.append(new_verts)
            out_e.append(new_edges)

        self.outputs['Vertices'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)


register, unregister = bpy.utils.register_classes_factory([SvSplitEdgesNode])
