# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.modules import sv_bmesh
from math import sin, cos, radians, pi, tan, atan2, sqrt, asin
from mathutils import Vector, Euler
def triang_A_B_b_Alpha(A, B, b, Alpha):
    # B =[A[0] + a, A[1], A[2]]
    ang = atan2(B[1]-A[1],B[0]-A[0])
    C =[A[0] + b*cos(Alpha + ang), A[1]+ b*sin(Alpha + ang), A[2]]
    return [A, B, C]

def triang_A_a_b_Alpha(A, a, b, Alpha):
    B =[A[0] + a, A[1], A[2]]
    C =[A[0] + b*cos(Alpha), A[1]+ b*sin(Alpha), A[2]]
    return [A, B, C]

def triang_A_a_b_c(A, a, b, c):
    B =[A[0] + a, A[1], A[2]]
    return triang_A_B_b_c(A, B, b, c)

def triang_A_B_b_c(A, B, b, c):
    # Adapted from circle interections function in Contour2D node
    ang = atan2(B[1]-A[1],B[0]-A[0])
    d = sqrt((B[0]-A[0])*(B[0]-A[0])+(B[1]-A[1])*(B[1]-A[1]))
    sum_rad = b + c
    dif_rad = abs(b - c)
    dist = d

    mask = sum_rad > dist
    mask *= dif_rad < dist
    mask *= 0 < dist

    if mask:
        ang_base = ang
        k = b*b - c*c + dist*dist
        k /= 2*dist
        h = sqrt(b*b - k*k)
        angK = asin(h / b)
        p1 = ang_base - angK - pi
        x = B[0]+ b*cos(p1)
        y = B[1]+ b*sin(p1)
    else:
        x = A[0]+(B[0]-A[0])*b/c
        y = A[1]+(B[1]-A[1])*b/c

    V = [A, B, [x, y, A[2]]]
    return V

class SvTriangleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: triangle
    Tooltip:  lowpoly cricket model

    """

    bl_idname = "SvTriangleNode"
    bl_label = "Triangle"
    bl_icon = "GHOST_ENABLED"
    sv_icon = "SV_TRIANGLE"
    triangle_modes =[("A_as_Alpha_Beta","A_a_alpha_beta","",0),
                     ("A_Bv_Alpha_Beta","A_B_alpha_beta","",1),
                     ("A_as_b_Alpha","A_a_b_alpha","",2),
                     ("A_Bv_b_Alpha","A_B_b_alpha","",3),
                     ("A_as_b_c", "A_a_b_c", "", 4),
                     ("A_Bv_b_c", "A_B_b_c", "", 5),
                     ("A_Bv_C", "A_B_C", "", 6)]

    def update_sokets(self,context):
        si = self.inputs
        inputs = ['A', 'Bv', 'C', 'as', 'b', 'c', 'Alpha', 'Beta']
        for idx, i in enumerate(inputs):
            if  i in self.mode:
                if si[idx].hide_safe:
                    si[idx].hide_safe = False
            else:
                si[idx].hide_safe = True
        updateNode(self, context)

    mode : EnumProperty(
        name="Mode", items=triangle_modes,
        default="A_Bv_C", update=update_sokets)
    v3_input_0 : FloatVectorProperty(
        name='A', description='Starting point',
        size=3, default=(0, 0, 0),
        update=updateNode)

    v3_input_1 : FloatVectorProperty(
        name='B', description='End point',
        size=3, default=(0.5, 0.5, 0.5),
        update=updateNode)

    v3_input_2 : FloatVectorProperty(
        name='C', description='Origin of line',
        size=3, default=(0, 0, 0),
        update=updateNode)
    size_a : FloatProperty(
        name='a', description='Size of line',
        default=10.0, update=updateNode)
    size_b : FloatProperty(
        name='b', description='Size of line',
        default=10.0, update=updateNode)
    size_c : FloatProperty(
        name='c', description='Size of line',
        default=10.0, update=updateNode)
    alpha : FloatProperty(
        name='alpha', description='Size of line',
        default=10.0, update=updateNode)
    beta : FloatProperty(
        name='beta', description='Size of line',
        default=10.0, update=updateNode)
    def draw_buttons(self, context, layout):

        layout.prop(self, "mode", expand=False)
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

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        out_verts = []
        out_faces = []


        params = [si.sv_get(default=[[]])[0] for si in self.inputs]
        for A, B, C, a, b, c, alpha, beta in zip(*params):
            if self.mode == 'A_Bv_C':
                V = [A,B,C]
            if self.mode == 'A_as_Alpha_Beta':
        	    # https://math.stackexchange.com/a/1081735
                a = a
                beta = beta
                j = -tan(beta)*a /(-tan(alpha)-tan(beta))
                k = - tan(alpha) * j
                V = [A,[a+A[0],A[1],A[2]],[j+A[0],k+ A[1],A[2]]]
            elif self.mode == 'A_Bv_Alpha_Beta':
                # https://math.stackexchange.com/a/145299
                ang = atan2(B[1]-A[1],B[0]-A[0])
                d = sqrt((B[0]-A[0])*(B[0]-A[0])+(B[1]-A[1])*(B[1]-A[1]))
                alpha = alpha + ang
                beta = 2*pi-beta+ang
                # y = tan(alpha)*x + A[1]−tan(alpha)*A[0]
                x = (tan(alpha)*A[0] - tan(beta)*B[0]+B[1] - A[1])/(tan(alpha)-tan(beta))
                y = tan(alpha)*x + A[1] - tan(alpha)*A[0]
                V = [A,B,[x,y,0]]

            elif self.mode == 'A_Bv_b_c':
                V = triang_A_B_b_c(A, B, b, c)
            elif self.mode == 'A_as_b_c':
                V = triang_A_a_b_c(A, a, b, c)

            elif self.mode == 'A_as_b_Alpha':
                V = triang_A_a_b_Alpha(A, a, b, alpha)
            elif self.mode == 'A_Bv_b_Alpha':
                V = triang_A_B_b_Alpha(A, B, b, alpha)

                # Adapted from circle interections function in Contour2D node
                # ang = atan2(B[1]-A[1],B[0]-A[0])
                # d = sqrt((B[0]-A[0])*(B[0]-A[0])+(B[1]-A[1])*(B[1]-A[1]))
                # sum_rad = b + c
                # dif_rad = abs(b - c)
                # dist = d
                #
                # mask = sum_rad > dist
                # mask *= dif_rad < dist
                # mask *= 0 < dist
                # print(dist,mask)
                # if mask:
                #     ang_base = ang
                #     k = b*b - c*c + dist*dist
                #     k /= 2*dist
                #     h = sqrt(b*b - k*k)
                #     angK = asin(h / b)
                #     p1 = ang_base - angK - pi
                #     x = B[0]+ b*cos(p1)
                #     y = B[1]+ b*sin(p1)
                # else:
                #     x = A[0]+(B[0]-A[0])*b/c
                #     y = A[1]+(B[1]-A[1])*b/c
                #
                # V = [A,B,[x,y,0]]
            out_verts.append(V)
            out_faces.append([[0,1,2]])

        #out_verts.append(verts)
        #out_faces.append(faces)

        self.outputs['Vertices'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)


classes = [SvTriangleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
