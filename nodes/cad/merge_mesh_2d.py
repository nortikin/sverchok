# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import crop_mesh


class SvMergeMesh2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Merge two 2d meshes

    Each mesh can have disjoint parts
    Only X and Y coordinate takes in account
    """
    bl_idname = 'SvMergeMesh2D'
    bl_label = 'Merge mesh 2D'
    bl_icon = 'AUTOMERGE_ON'

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
        [[self.id_data.links.new(sock, link) for link in links[sock.name]] for sock in new_socks if sock.name in links]
        updateNode(self, context)

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
        pass


def register():
    bpy.utils.register_class(SvMergeMesh2D)


def unregister():
    bpy.utils.unregister_class(SvMergeMesh2D)
