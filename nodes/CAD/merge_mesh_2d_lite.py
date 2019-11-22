# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode, throttle_tree_update
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import merge_mesh_light


class SvMergeMesh2DLite(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Merge 2D mesh into one
    Tooltip: Takes in account intersections and holes

    Has hidden output socket, look N panel
    """
    bl_idname = 'SvMergeMesh2DLite'
    bl_label = 'Merge mesh 2D lite'
    bl_icon = 'AUTOMERGE_ON'

    def update_sockets(self, context):
        with throttle_tree_update(self):
            links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
            [self.outputs.remove(sock) for sock in self.outputs[2:]]
            new_socks = []
            if self.face_index:
                new_socks.append(self.outputs.new('SvStringsSocket', 'Face index'))
            if self.overlap_number:
                new_socks.append(self.outputs.new('SvStringsSocket', 'Overlap number'))
            [[self.id_data.links.new(sock, link) for link in links[sock.name]]
                                                 for sock in new_socks if sock.name in links]
        updateNode(self, context)

    face_index: bpy.props.BoolProperty(name="Show face mask", update=update_sockets,
                                       description="Show output socket of index face mask")
    overlap_number: bpy.props.BoolProperty(name="Show number of overlapping", update=update_sockets,
                                           description="Show socket with information about number "
                                                       "of overlapping of polygon with other polygons")
    accuracy: bpy.props.IntProperty(name='Accuracy', update=updateNode, default=5, min=3, max=12,
                                    description='Some errors of the node can be fixed by changing this value')

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'face_index', toggle=True)
        col.prop(self, 'overlap_number', toggle=True)
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        out = []
        for sv_verts, sv_faces in zip(self.inputs['Verts'].sv_get(), self.inputs['Faces'].sv_get()):
            out.append(merge_mesh_light(sv_verts, sv_faces, self.face_index, self.overlap_number, self.accuracy))
        out_verts, out_faces, face_index, overlap_number = zip(*out)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)
        if self.face_index:
            self.outputs['Face index'].sv_set(face_index)
        if self.overlap_number:
            self.outputs['Overlap number'].sv_set(overlap_number)


def register():
    bpy.utils.register_class(SvMergeMesh2DLite)


def unregister():
    bpy.utils.unregister_class(SvMergeMesh2DLite)
