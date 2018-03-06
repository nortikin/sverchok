# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode)
from sverchok.ui.sv_icons import custom_icon

from math import sin, cos, pi, sqrt

centeringItems = [("F1", "F1", ""), ("C", "C", ""), ("F2", "F2", "")]
modeItems = [("AB", "a b", ""), ("AE", "a e", ""), ("AC", "a c", "")]


class SvEllipseNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Ellipse '''
    bl_idname = 'SvEllipseNode'
    bl_label = 'Ellipse'
    sv_icon = 'SV_ELLIPSE'

    def update_mode(self, context):
        ''' Update the ellipse parameters of the new mode based on previous mode ones'''
        self.updating = True

        if self.mode == "AB":
            if self.lastMode == "AE":  # ae => ab
                a = self.major_radius
                e = self.eccentricity
                self.minor_radius = a * sqrt(1 - e * e)
            elif self.lastMode == "AC":  # ac => ab
                a = self.major_radius
                c = min(a, self.focal_length)
                self.minor_radius = sqrt(a * a - c * c)

        elif self.mode == "AE":
            if self.lastMode == "AB":  # ab => ae
                a = self.major_radius
                b = min(a, self.minor_radius)
                self.eccentricity = sqrt(1 - (b * b) / (a * a))
            if self.lastMode == "AC":  # ac => ae
                a = self.major_radius
                c = self.focal_length
                self.eccentricity = c / a

        elif self.mode == "AC":
            if self.lastMode == "AB":  # ab => ac
                a = self.major_radius
                b = min(a, self.minor_radius)
                self.focal_length = sqrt(a * a - b * b)
            if self.lastMode == "AE":  # ae => ac
                a = self.major_radius
                e = self.eccentricity
                self.focal_length = a * e

        self.updating = False

        if self.mode != self.lastMode:
            self.lastMode = self.mode
            self.update_sockets()
            updateNode(self, context)

    def update_ellipse(self, context):
        if self.updating:
            return

        updateNode(self, context)

    centering = EnumProperty(
        name="Centering", items=centeringItems,
        description="Center the ellipse around F1, C or F2",
        default="C", update=updateNode)

    mode = EnumProperty(
        name="Mode", items=modeItems,
        description="Ellipse definition mode",
        default="AB", update=update_mode)

    lastMode = EnumProperty(
        name="Mode", items=modeItems,
        description="Ellipse definition last mode",
        default="AB")

    major_radius = FloatProperty(
        name='Major Radius', description='Ellipse major radius',
        default=1.0, min=0.0, update=update_ellipse)

    minor_radius = FloatProperty(
        name='Minor Radius', description='Ellipse minor radius',
        default=0.8, min=0.0, update=update_ellipse)

    eccentricity = FloatProperty(
        name='Eccentricity', description='Ellipse eccentricity',
        default=0.6, min=0.0, max=1.0, update=update_ellipse)

    focal_length = FloatProperty(
        name='Focal Length', description='Ellipse focal length',
        default=0.6, min=0.0, update=update_ellipse)

    num_verts = IntProperty(
        name='Num Verts', description='Number of vertices in the ellipse',
        default=36, min=3, update=updateNode)

    phase = FloatProperty(
        name='Phase', description='Phase ellipse vertices around the center by this radians amount',
        default=0.0, update=updateNode)

    rotation = FloatProperty(
        name='Rotation', description='Rotate ellipse vertices around the centering point by this radians amount',
        default=0.0, update=updateNode)

    scale = FloatProperty(
        name='Scale', description='Scale ellipse radii by this amount',
        default=1.0, min=0.0, update=updateNode)

    updating = BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('StringsSocket', "Major Radius").prop_name = "major_radius"
        self.inputs.new('StringsSocket', "Minor Radius").prop_name = "minor_radius"
        self.inputs.new('StringsSocket', "Num Verts").prop_name = "num_verts"
        self.inputs.new('StringsSocket', "Phase").prop_name = "phase"
        self.inputs.new('StringsSocket', "Rotation").prop_name = "rotation"
        self.inputs.new('StringsSocket', "Scale").prop_name = "scale"

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polys", "Polys")

        self.outputs.new('VerticesSocket', "F1", "F1")
        self.outputs.new('VerticesSocket', "F2", "F2")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        layout.prop(self, "centering", expand=True)

    def update_sockets(self):
        if self.mode == "AB":
            socket2 = self.inputs[1]
            socket2.replace_socket("StringsSocket", "Minor Radius").prop_name = "minor_radius"
        elif self.mode == "AE":
            socket2 = self.inputs[1]
            socket2.replace_socket("StringsSocket", "Eccentricity").prop_name = "eccentricity"
        else:  # AC
            socket2 = self.inputs[1]
            socket2.replace_socket("StringsSocket", "Focal Length").prop_name = "focal_length"

    def make_ellipse(self, a, b, N, phase, rotation, scale):
        verts = []
        edges = []
        polys = []

        a = a * scale
        b = b * scale

        if a > b:
            dx = sqrt(a * a - b * b)
            dy = 0
        else:
            dx = 0
            dy = sqrt(b * b - a * a)

        if self.centering == "F1":
            cx = -dx
            cy = -dy
        elif self.centering == "F2":
            cx = +dx
            cy = +dy
        else:  # "C"
            cx = 0
            cy = 0

        sins = sin(rotation)  # cached for performance
        coss = cos(rotation)  # cached for performance

        f1x = -cx - dx
        f1y = -cy - dy
        f2x = -cx + dx
        f2y = -cy + dy
        f1xx = f1x * coss - f1y * sins
        f1yy = f1x * sins + f1y * coss
        f2xx = f2x * coss - f2y * sins
        f2yy = f2x * sins + f2y * coss

        f1 = [f1xx, f1yy, 0]
        f2 = [f2xx, f2yy, 0]

        for n in range(N):
            theta = 2 * pi * n / N + phase
            x = -cx + a * cos(theta)
            y = -cy + b * sin(theta)
            xx = x * coss - y * sins
            yy = x * sins + y * coss
            verts.append((xx, yy, 0))

        edges = list((i, (i + 1) % N) for i in range(N + 1))
        polys = [list(range(N))]

        return verts, edges, polys, f1, f2

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        # input values lists (single or multi value)
        inputs = self.inputs
        input_v1 = inputs[0].sv_get()[0] # major radius
        input_v2 = inputs[1].sv_get()[0] # minor radius, eccentricity or focal length
        input_N = inputs["Num Verts"].sv_get()[0]
        input_p = inputs["Phase"].sv_get()[0]
        input_r = inputs["Rotation"].sv_get()[0]
        input_s = inputs["Scale"].sv_get()[0]

        # convert main input parameters to major/minor radii (and sanitize inputs)
        if self.mode == "AB":
            input_a, input_b = match_long_repeat([input_v1, input_v2])
            input_a = list(map(lambda a: max(0.0, a), input_a))
            input_b = list(map(lambda a, b: max(0.0, min(a, b)), input_a, input_b))
        elif self.mode == "AE":
            input_a, input_e = match_long_repeat([input_v1, input_v2])
            input_a = list(map(lambda a: max(0.0, a), input_a))
            input_e = list(map(lambda e: max(0.0, min(1.0, e)), input_e))
            input_b = list(map(lambda a, e: a * sqrt(1 - e * e), input_a, input_e))
        else:  # "AC"
            input_a, input_c = match_long_repeat([input_v1, input_v2])
            input_a = list(map(lambda a: max(0.0, a), input_a))
            input_c = list(map(lambda a, c: max(0.0, min(a, c)), input_a, input_c))
            input_b = list(map(lambda a, c: sqrt(a * a - c * c), input_a, input_c))

        # sanitize the input
        input_N = list(map(lambda n: max(3, int(n)), input_N))

        parameters = match_long_repeat([input_a, input_b, input_N, input_p, input_r, input_s])

        vertList = []
        edgeList = []
        polyList = []
        f1List = []
        f2List = []
        for a, b, N, p, r, s in zip(*parameters):
            verts, edges, polys, f1, f2 = self.make_ellipse(a, b, N, p, r, s)
            vertList.append(verts)
            edgeList.append(edges)
            polyList.append(polys)
            f1List.append(f1)
            f2List.append(f2)

        outputs["Verts"].sv_set(vertList)
        outputs["Edges"].sv_set(edgeList)
        outputs["Polys"].sv_set(polyList)

        outputs["F1"].sv_set([f1List])
        outputs["F2"].sv_set([f2List])


def register():
    bpy.utils.register_class(SvEllipseNode)


def unregister():
    bpy.utils.unregister_class(SvEllipseNode)
