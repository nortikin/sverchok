# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import radians
import bpy
from bpy.props import (FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.modules.triangle_utils import triang_A_c_Alpha_Beta, triang_A_B_Alpha_Beta, triang_A_B_b_Alpha, triang_A_b_c_Alpha, triang_A_a_b_c, triang_A_B_a_b
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.sv_bmesh_utils import remove_doubles
from sverchok.utils.listutils import lists_flat
from sverchok.ui.sv_icons import custom_icon


class SvTriangleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: from vertices, sides or angles
    Tooltip:  create triangle from various combinations of vertices, sides length and angles

    """

    bl_idname = "SvTriangleNode"
    bl_label = "Triangle"
    bl_icon = "GHOST_ENABLED"
    sv_icon = "SV_TRIANGLE_NODE"
    triangle_modes = [("A_c_Alpha_Beta", "A_c_alpha_beta", "", custom_icon("SV_TRIANGLE_ACALPHABETA"), 0),
                      ("A_Bv_Alpha_Beta", "A_B_alpha_beta", "", custom_icon("SV_TRIANGLE_ABALPHABETA"), 1),
                      ("A_b_c_Alpha", "A_b_c_alpha", "", custom_icon("SV_TRIANGLE_ABCALPHA"), 2),
                      ("A_Bv_b_Alpha", "A_B_b_alpha", "", custom_icon("SV_TRIANGLE_ABBALPHA"), 3),
                      ("A_as_b_c", "A_a_b_c", "", custom_icon("SV_TRIANGLE_AABC"), 4),
                      ("A_Bv_as_b", "A_B_a_b", "", custom_icon("SV_TRIANGLE_ABAB"), 5),
                      ("A_Bv_C", "A_B_C", "", custom_icon("SV_TRIANGLE_ABC"), 6)]
    angle_units = [("Degrees", "Degrees", "", 0),
                   ("Radians", "Radians", "", 1)]

    def update_sokets(self, context):
        si = self.inputs
        inputs = ['A', 'Bv', 'C', 'as', 'b', 'c', 'Alpha', 'Beta']
        for idx, i in enumerate(inputs):
            if  i in self.mode:
                if si[idx].hide_safe:
                    si[idx].hide_safe = False
            else:
                si[idx].hide_safe = True
        updateNode(self, context)

    mode: EnumProperty(
        name="Mode", items=triangle_modes,
        default="A_Bv_C", update=update_sokets)
    angle_mode: EnumProperty(
        name="Angle Mode", items=angle_units,
        default="Degrees", update=update_sokets)

    v3_input_0: FloatVectorProperty(
        name='A', description='Vertice A of triangle',
        size=3, default=(0, 0, 0),
        update=updateNode)
    v3_input_1: FloatVectorProperty(
        name='B', description='Vertice B of triangle',
        size=3, default=(0.5, 0.5, 0),
        update=updateNode)
    v3_input_2: FloatVectorProperty(
        name='C', description='Vertice C of triangle',
        size=3, default=(1, 0, 0),
        update=updateNode)

    size_a: FloatProperty(
        name='a', description='Size side a',
        default=10.0, update=updateNode)
    size_b: FloatProperty(
        name='b', description='Size side b',
        default=10.0, update=updateNode)
    size_c: FloatProperty(
        name='c', description='Size side c',
        default=10.0, update=updateNode)

    alpha: FloatProperty(
        name='Alpha', description='Angle at vertice A',
        default=30.0, update=updateNode)
    beta: FloatProperty(
        name='Beta', description='Angle at vertice B',
        default=30.0, update=updateNode)

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    join_level: BoolProperty(
        name="Join Last level",
        description="Join (mesh join) last level of triangles",
        default=False,
        update=updateNode)
    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)
    rm_doubles: BoolProperty(
        name="Remove Doubles",
        description="Remove doubles of the joined triangles",
        default=True,
        update=updateNode)
    epsilon: FloatProperty(
        name='Tolerance', description='Removing Doubles Tolerance',
        default=1e-6, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''

        layout.prop(self, "mode", expand=False)
        layout.prop(self, "angle_mode", expand=False)

        layout.separator()
        layout.prop(self, "join_level", text="Join Last Level", expand=False)
        if self.join_level:
            layout.prop(self, "rm_doubles", expand=False)
            if self.rm_doubles:
                layout.prop(self, "epsilon", text="Merge Distance", expand=False)
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)


    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "mode", text="Mode")
        layout.prop_menu_enum(self, "angle_mode", text="Angle Units")
        layout.separator()
        layout.prop(self, "join_level", text="Join Last Level", expand=False)
        if self.join_level:
            layout.prop(self, "rm_doubles", expand=False)
            if self.rm_doubles:
                layout.prop(self, "epsilon", text="Merge Distance", expand=False)
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")
    def sv_init(self, context):
        sinw = self.inputs.new
        sinw('SvVerticesSocket', "A").prop_name = "v3_input_0"
        sinw('SvVerticesSocket', "B").prop_name = "v3_input_1"
        sinw('SvVerticesSocket', "C").prop_name = "v3_input_2"
        sinw('SvStringsSocket', "a").prop_name = "size_a"
        sinw('SvStringsSocket', "b").prop_name = "size_b"
        sinw('SvStringsSocket', "c").prop_name = "size_c"

        sinw('SvStringsSocket', "Alpha").prop_name = "alpha"
        sinw('SvStringsSocket', "Beta").prop_name = "beta"



        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def main_func(self, params):
        out_verts, out_edges, out_faces = [], [], []
        for A, B, C, a, b, c, alpha, beta in zip(*params):
            if self.angle_mode == 'Degrees':
                alpha = radians(alpha)
                beta = radians(beta)
            if self.mode == 'A_Bv_C':
                verts = [A, B, C]
            if self.mode == 'A_c_Alpha_Beta':
                verts = triang_A_c_Alpha_Beta(A, c, alpha, beta)
            elif self.mode == 'A_Bv_Alpha_Beta':
                verts = triang_A_B_Alpha_Beta(A, B, alpha, beta)
            elif self.mode == 'A_Bv_as_b':
                verts = triang_A_B_a_b(A, B, a, b)
            elif self.mode == 'A_as_b_c':
                verts = triang_A_a_b_c(A, a, b, c)
            elif self.mode == 'A_b_c_Alpha':
                verts = triang_A_b_c_Alpha(A, b, c, alpha)
            elif self.mode == 'A_Bv_b_Alpha':
                verts = triang_A_B_b_Alpha(A, B, b, alpha)

            out_verts.append(verts)
            out_edges.append([[0, 1], [1, 2], [2, 0]])
            out_faces.append([[0, 1, 2]])

        if self.join_level:
            out_verts, out_edges, out_faces = mesh_join(out_verts, out_edges, out_faces)
            if self.rm_doubles:
                out_verts, out_edges, out_faces = remove_doubles(out_verts, out_edges, out_faces, self.epsilon)

            out_verts, out_edges, out_faces = [out_verts], [out_edges], [out_faces]
        return out_verts, out_edges, out_faces

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        out_verts = []
        out_edges = []
        out_faces = []

        match_func = list_match_func[self.list_match_global]
        family = match_func([si.sv_get(default=[[]]) for si in self.inputs])
        for params in zip(*family):
            match_func = list_match_func[self.list_match_local]
            params = match_func(params)
            verts, edges, faces = self.main_func(params)

            out_verts.append(verts)
            out_edges.append(edges)
            out_faces.append(faces)

        if self.flat_output:
            out_verts, out_edges, out_faces = lists_flat([out_verts, out_edges, out_faces])

        self.outputs['Vertices'].sv_set(out_verts)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)


classes = [SvTriangleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
