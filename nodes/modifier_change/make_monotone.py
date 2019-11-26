# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import zip_longest

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.make_monotone import monotone_sv_face_with_holes


class SvMakeMonotone(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Split face into monotone pieces
    Can spilt face with holes
    One object - one polygon
    """
    bl_idname = 'SvMakeMonotone'
    bl_label = 'Make monotone'
    bl_icon = 'MOD_MESHDEFORM'

    accuracy: bpy.props.IntProperty(name='Accuracy', description='Some errors of the node '
                                                                 'can be fixed by changing this value',
                                     update=updateNode, default=5, min=3, max=12)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Polygon')
        self.inputs.new('SvVerticesSocket', 'Hole vectors')
        self.inputs.new('SvStringsSocket', 'Hole polygons')
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Polygons')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'accuracy')

    def process(self):
        verts = self.inputs['Polygon'].sv_get()
        mesh = []
        if self.inputs['Hole vectors'].is_linked and self.inputs['Hole polygons'].is_linked:
            hole_v = self.inputs['Hole vectors'].sv_get()
            hole_f = self.inputs['Hole polygons'].sv_get()
            for vs, hvs, hfs in zip_longest(verts, hole_v, hole_f, fillvalue=None):
                mesh.append(monotone_sv_face_with_holes(vs, hvs, hfs, self.accuracy))
        else:
            for vs in verts:
                mesh.append(monotone_sv_face_with_holes(vs, accuracy=self.accuracy))
        if mesh:
            v, f = zip(*mesh)
            self.outputs['Vertices'].sv_set(v)
            self.outputs['Polygons'].sv_set(f)


def register():
    bpy.utils.register_class(SvMakeMonotone)


def unregister():
    bpy.utils.unregister_class(SvMakeMonotone)
