# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

maximum_spec_vd_dict = dict(
    vector_light="light direction (3f)",
    vert_color="points rgba (4f)",
    edge_color="edge rgba (4f)",
    face_color="face rgba (4f)",
    display_verts="display verts (b)",
    display_edges="display edges (b)",
    display_faces="display faces (b)",
    selected_draw_mode="shade mode (enum)",
    draw_gl_wireframe="wireframe (b)",
    draw_gl_polygonoffset="fix zfighting (b)",
    point_size="point size (i)",
    line_width="line width (i)",
    extended_matrix="extended matrix (b)"
)

class SvVDAttrsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' a SvVDAttrsNode f '''
    bl_idname = 'SvVDAttrsNode'
    bl_label = 'VD Attributes'
    bl_icon = 'GREASEPENCIL'

    def sv_init(self, context):
        self.outputs.new("SvStringsSocket", name="attrs dict")
        inew = self.inputs.new
        inew("SvVerticesSocket", "light direction (3f)")
        inew("SvColorSocket", "points rgba (4f)")
        inew("SvStringsSocket", "edge rgba (4f)")
        inew("SvStringsSocket", "face rgba (4f)")
        inew("SvStringsSocket", "display verts (b)")
        inew("SvStringsSocket", "display edges (b)")
        inew("SvStringsSocket", "display faces (b)")
        inew("SvStringsSocket", "shade mode (enum)")
        inew("SvStringsSocket", "wireframe (b)")
        inew("SvStringsSocket", "fix zfighting (b)")
        inew("SvStringsSocket", "point size (i)")
        inew("SvStringsSocket", "line width (i)")
        inew("SvStringsSocket", "extended matrix (b)")
        for input_socket in self.inputs:
            input_socket.hide = True

    def draw_buttons(self, context, layout):
        ...

    def process(self):
        ...

        self.outputs['attrs'].sv_set([{'activate': True, 'display_verts': False}])


classes = [SvVDAttrsNode]
register, unregister = bpy.utils.register_classes_factory(classes)