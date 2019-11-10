# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.dissolve_mesh import dissolve_faces


class SvDissolveFaces2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: dissolve selected by mask input faces
    Tooltip: cant produce disjoint parts

    It has extra outputs on N panel
    """
    bl_idname = 'SvDissolveFaces2D'
    bl_label = 'Dissolve Faces 2D'
    bl_icon = 'MESH_PLANE'

    def update_sockets(self, context):
        self.id_data.freeze()
        # is not great, another solution should be find
        # for protection from update node each time when new socket is created
        links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
        [self.outputs.remove(sock) for sock in self.outputs[2:]]
        new_socks = []
        if self.face_mask:
            new_socks.append(self.outputs.new('SvStringsSocket', 'Face mask'))
        if self.index_mask:
            new_socks.append(self.outputs.new('SvStringsSocket', 'Index mask'))
        [[self.id_data.links.new(sock, link) for link in links[sock.name]] for sock in new_socks if sock.name in links]
        self.id_data.unfreeze()
        self.id_data.process()  # is not great, another solution should be find

    face_mask: bpy.props.BoolProperty(name='Face mask', update=update_sockets,
                                        description='Show new selecting mak after dissolving faces')
    index_mask: bpy.props.BoolProperty(name="Index mask", update=update_sockets,
                                       description="Show output mask of indexes of old faces per new face")

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'face_mask', toggle=True)
        col.prop(self, 'index_mask', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Face mask')
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        out = []
        out_mask = []
        out_index = []
        for vs, fs, mf in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get(),
                              self.inputs['Face mask'].sv_get()):
            if self.face_mask and self.index_mask:
                v, f, m, i = dissolve_faces(vs, fs, mf, self.face_mask, self.index_mask)
                out_mask.append(m)
                out_index.append(i)
            elif self.face_mask:
                v, f, m = dissolve_faces(vs, fs, mf, self.face_mask, self.index_mask)
                out_mask.append(m)
            elif self.index_mask:
                v, f, i = dissolve_faces(vs, fs, mf, self.face_mask, self.index_mask)
                out_index.append(i)
            else:
                v, f = dissolve_faces(vs, fs, mf, self.face_mask, self.index_mask)
            out.append([v, f])
        out_v, out_f = zip(*out)
        self.outputs['Verts'].sv_set(out_v)
        self.outputs['Faces'].sv_set(out_f)
        if self.face_mask:
            self.outputs['Face mask'].sv_set(out_mask)
        if self.index_mask:
            self.outputs['Index mask'].sv_set(out_index)


def register():
    bpy.utils.register_class(SvDissolveFaces2D)


def unregister():
    bpy.utils.unregister_class(SvDissolveFaces2D)
