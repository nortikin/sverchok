# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
import bmesh

from sverchok.data_structure import updateNode, fixed_iter
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_bmesh_utils import empty_bmesh, add_mesh_to_bmesh, mesh_indexes_from_bmesh
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode

modes = [(n, n, '', ic, i) for i, (n, ic) in
         enumerate(zip(('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]


class SvDissolveMeshElements(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: dissolve delete remove

    dissolve points edges or polygons of given mesh
    """
    bl_idname = 'SvDissolveMeshElements'
    bl_label = 'Dissolve Mesh Elements'
    bl_icon = 'EXPERIMENTAL'

    mask_mode: bpy.props.EnumProperty(items=modes, update=updateNode)
    use_face_split: bpy.props.BoolProperty(update=updateNode)
    use_boundary_tear: bpy.props.BoolProperty(update=updateNode)
    use_verts: bpy.props.BoolProperty(update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        s = self.inputs.new('SvStringsSocket', 'Mask')
        s.custom_draw = 'draw_mask_socket_modes'

        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Verts ind')
        self.outputs.new('SvStringsSocket', 'Edges ind')
        self.outputs.new('SvStringsSocket', 'Face ind')
        self.outputs.new('SvStringsSocket', 'Loop ind')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'use_face_split', toggle=1)
        layout.prop(self, 'use_boundary_tear', toggle=1)
        layout.prop(self, 'use_verts', toggle=1)

    def draw_mask_socket_modes(self, socket, context, layout):
        layout.label(text='Mask')
        layout.prop(self, 'mask_mode', expand=True, text='')

    def process(self):
        verts = self.inputs['Verts'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[])
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])
        masks = self.inputs['Mask'].sv_get(deepcopy=False, default=[])

        obj_n = max(len(verts), len(edges), len(faces), len(masks))

        out_v, out_e, out_f, out_vi, out_ei, out_fi, out_li = ([] for _ in range(7))
        if not masks:
            out_v, out_e, out_f = verts, edges, faces

        def vec(arr):
            return fixed_iter(arr, obj_n, [])

        for v, e, f, m in zip(vec(verts), vec(edges), vec(faces), vec(masks)):
            if not m:
                break
            with empty_bmesh() as bm:
                add_mesh_to_bmesh(bm, v, e, f, 'sv_index')
                if self.mask_mode == 'Verts':
                    bmesh.ops.dissolve_verts(bm,
                                             verts=[v for v, _m in zip(bm.verts, m) if _m],
                                             use_face_split=self.use_face_split,
                                             use_boundary_tear=self.use_boundary_tear)
                elif self.mask_mode == 'Edges':
                    bmesh.ops.dissolve_edges(bm,
                                             edges=[e for e, _m in zip(bm.edges, m) if _m],
                                             use_verts=self.use_verts,
                                             use_face_split=self.use_face_split)
                elif self.mask_mode == 'Faces':
                    bmesh.ops.dissolve_faces(bm,
                                             faces=[f for f, _m in zip(bm.faces, m) if _m],
                                             use_verts=self.use_verts)
                v, e, f, vi, ei, fi, li = mesh_indexes_from_bmesh(bm, 'sv_index')
                out_v.append(v)
                out_e.append(e)
                out_f.append(f)
                out_vi.append(vi)
                out_ei.append(ei)
                out_fi.append(fi)
                out_li.append(li)

        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Edges'].sv_set(out_e)
        self.outputs['Faces'].sv_set(out_f)
        self.outputs['Verts ind'].sv_set(out_vi)
        self.outputs['Edges ind'].sv_set(out_ei)
        self.outputs['Face ind'].sv_set(out_fi)
        self.outputs['Loop ind'].sv_set(out_li)


register, unregister = bpy.utils.register_classes_factory([SvDissolveMeshElements])
