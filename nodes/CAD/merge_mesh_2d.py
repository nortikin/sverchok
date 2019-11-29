# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import merge_mesh

class SvMergeMesh2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Merge two 2d meshes

    Each mesh can have disjoint parts
    Only X and Y coordinate takes in account
    """
    bl_idname = 'SvMergeMesh2D'
    bl_label = 'Merge mesh 2D'
    bl_icon = 'AUTOMERGE_ON'

    @throttled
    def update_sockets(self, context):
        links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
        [self.outputs.remove(sock) for sock in self.outputs[2:]]
        new_socks = []
        if self.simple_mask:
            new_socks.append(self.outputs.new('SvStringsSocket', 'Mask A'))
            new_socks.append(self.outputs.new('SvStringsSocket', 'Mask B'))
        if self.index_mask:
            new_socks.append(self.outputs.new('SvStringsSocket', 'Face index A'))
            new_socks.append(self.outputs.new('SvStringsSocket', 'Face index B'))
        [[self.id_data.links.new(sock, link) for link in links[sock.name]]
                                             for sock in new_socks if sock.name in links]


    simple_mask: bpy.props.BoolProperty(name='Simple mask', update=update_sockets, default=True,
                                        description='Switching between two type of masks')
    index_mask: bpy.props.BoolProperty(name="Index mask", update=update_sockets,
                                       description="Mask of output mesh represented indexes"
                                                    " of faces from mesh A and Mesh B")
    accuracy: bpy.props.IntProperty(name='Accuracy', update=updateNode, default=5, min=3, max=12,
                                    description='Some errors of the node can be fixed by changing this value')

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'simple_mask', toggle=True)
        col.prop(self, 'index_mask', toggle=True)
        col.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts A')
        self.inputs.new('SvStringsSocket', 'Faces A')
        self.inputs.new('SvVerticesSocket', 'Verts B')
        self.inputs.new('SvStringsSocket', 'Faces B')
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Mask A')
        self.outputs.new('SvStringsSocket', 'Mask B')

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        out = []
        for sv_verts_a, sv_faces_a, sv_verts_b, sv_faces_b in zip(self.inputs['Verts A'].sv_get(),
                                                                  self.inputs['Faces A'].sv_get(),
                                                                  self.inputs['Verts B'].sv_get(),
                                                                  self.inputs['Faces B'].sv_get()):
            out.append(merge_mesh(sv_verts_a, sv_faces_a, sv_verts_b, sv_faces_b, self.simple_mask, self.index_mask,
                                  self.accuracy))
        if self.simple_mask and self.index_mask:
            out_verts, out_faces, mask_a, mask_b, face_index_a, face_index_b = zip(*out)
            self.outputs['Mask A'].sv_set(mask_a)
            self.outputs['Mask B'].sv_set(mask_b)
            self.outputs['Face index A'].sv_set(face_index_a)
            self.outputs['Face index B'].sv_set(face_index_b)
        elif self.simple_mask:
            out_verts, out_faces, mask_a, mask_b = zip(*out)
            self.outputs['Mask A'].sv_set(mask_a)
            self.outputs['Mask B'].sv_set(mask_b)
        elif self.index_mask:
            out_verts, out_faces, face_index_a, face_index_b = zip(*out)
            self.outputs['Face index A'].sv_set(face_index_a)
            self.outputs['Face index B'].sv_set(face_index_b)
        else:
            out_verts, out_faces = zip(*out)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)


def register():
    bpy.utils.register_class(SvMergeMesh2D)


def unregister():
    bpy.utils.unregister_class(SvMergeMesh2D)
