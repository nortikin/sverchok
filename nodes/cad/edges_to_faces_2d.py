# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import edges_to_faces


class SvEdgesToFaces2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: create polygons from given edges
    Tooltip: can generate holes in mesh

    Only X and Y dimensions of input points will be taken for work.
    """
    bl_idname = 'SvEdgesToFaces2D'
    bl_label = 'Edges to faces 2D'
    bl_icon = 'MESH_GRID'
    sv_icon = 'SV_PLANAR_EDGES_TO_POLY'

    do_intersect: bpy.props.BoolProperty(name="Self intersect", default=False, update=updateNode,
                                         description="Activate an algorithm of finding self intersections")
    fill_holes: bpy.props.BoolProperty(name="Fill holes", default=True, update=updateNode,
                                       description="Fills faces which are within another face and "
                                                   "does not intersect with one")
    accuracy: bpy.props.IntProperty(name='Accuracy', update=updateNode, default=5, min=3, max=12,
                                    description='Some errors of the node can be fixed by changing this value')

    def draw_buttons(self, context, layout):
        pass
        row = layout.column(align=True)
        row.prop(self, 'do_intersect', icon='SORTBYEXT', toggle=1)
        if self.fill_holes:
            row.prop(self, 'fill_holes', icon='PROP_ON', toggle=1)
        else:
            row.prop(self, 'fill_holes', icon='PROP_CON', toggle=1)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not all([soc.is_linked for soc in self.inputs]):
            return
        out = []
        for vs, es in zip(self.inputs['Verts'].sv_get(), self.inputs['Edges'].sv_get()):
            out.append(edges_to_faces(vs, es, self.do_intersect, self.fill_holes, self.accuracy))
        sv_verts, sv_faces = zip(*out)
        self.outputs['Verts'].sv_set(sv_verts)
        self.outputs['Faces'].sv_set(sv_faces)


def register():
    bpy.utils.register_class(SvEdgesToFaces2D)


def unregister():
    bpy.utils.unregister_class(SvEdgesToFaces2D)
