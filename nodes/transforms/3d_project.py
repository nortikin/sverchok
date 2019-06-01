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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

modeItems = [
    ("PLANE",  "PLANE",  "Project onto a plane", 0),
    ("SPHERE", "SPHERE", "Project onto a sphere", 1),
    ("CYLINDER", "CYLINDER", "Project onto a cylinder", 2)]


projectionItems = [
    ("PERSPECTIVE",  "PERSPECTIVE",  "Perspective projection", 0),
    ("ORTHOGRAPHIC", "ORTHOGRAPHIC", "Orthographic projection", 1)]


def project_2d(vert3D, m, d):
    """
    Project a 3D vector onto 2D space given the projection distance
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection plane origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection plane normal

    o = [ox, oy, oz]
    n = [nx, ny, nz]

    x, y, z = vert3D

    x = x - ox
    y = y - oy
    z = z - oz

    an = x * nx + y * ny + z * nz

    s = d / (d + an)

    xa = s * (x - an * nx)
    ya = s * (y - an * ny)
    za = s * (z - an * nz)

    px = ox + xa
    py = oy + ya
    pz = oz + za

    return [px, py, pz]


def project_3d_verts(verts3D, m, d):
    """
    Project the 3D verts onto 2D space given the projection distance
    """
    verts2D = [project_2d(verts3D[i], m, d) for i in range(len(verts3D))]
    return verts2D


class Sv3DProjectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 3D Projection
    Tooltips: Perspective projection from 3D space to 2D space
    """
    bl_idname = 'Sv3DProjectNode'
    bl_label = '3D Project'

    def update_mode(self, context):
        # if self.mode == self.last_mode:
        #     return

        # self.last_mode = self.mode
        # self.update_sockets(context)
        updateNode(self, context)

    mode = EnumProperty(
        name="Mode", items=modeItems, default="PLANE", update=update_mode)

    distance = FloatProperty(
        name="Distance", description="Projection Distance",
        default=2.0, min=0.0,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Verts")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polys")
        # projection screen location
        self.inputs.new('MatrixSocket', "Matrix")

        self.inputs.new('StringsSocket', "D").prop_name = 'distance'

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polys")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs

        if inputs["Verts"].is_linked:
            input_v = inputs["Verts"].sv_get()
        else:
            return

        if inputs["Edges"].is_linked:
            input_e = inputs["Edges"].sv_get()
        else:
            input_e = [[]]

        if inputs["Polys"].is_linked:
            input_p = inputs["Polys"].sv_get()
        else:
            input_p = [[]]

        input_m = inputs["Matrix"].sv_get()

        input_d = inputs["D"].sv_get()[0]

        params = match_long_repeat([input_v, input_e, input_p, input_m, input_d])

        vertList = []
        edgeList = []
        polyList = []
        for v, e, p, m, d in zip(*params):
            verts = project_3d_verts(v, m, d)
            vertList.append(verts)
            edgeList.append(e)
            polyList.append(p)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vertList)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edgeList)
        if outputs["Polys"].is_linked:
            outputs["Polys"].sv_set(polyList)


def register():
    bpy.utils.register_class(Sv3DProjectNode)


def unregister():
    bpy.utils.unregister_class(Sv3DProjectNode)
