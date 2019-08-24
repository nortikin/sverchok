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
from mathutils import Matrix
from math import sqrt

from sverchok.utils.profile import profile

projection_type_items = [
    ("PLANAR",  "Planar",  "Project onto a plane", 0),
    ("SPHERICAL", "Spherical", "Project onto a sphere", 1),
    ("CYLINDRICAL", "Cylindrical", "Project onto a cylinder", 2)]


projectionItems = [
    ("PERSPECTIVE",  "Perspective",  "Perspective projection", 0),
    ("ORTHOGRAPHIC", "Orthographic", "Orthographic projection", 1)]

idMat = [[tuple(v) for v in Matrix()]]  # identity matrix

EPSILON = 1e-10

@profile
def projection_cylindrical(verts3D, m, d):
    """

    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection cylinder origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection cylinder axis

    vertList = []
    focusList = []
    for vert in verts3D:
        x, y, z = vert
        # vector relative to the center of the cylinder (V-O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the vector projected parallel to the cylinder normal
        vn = dx * nx + dy * ny + dz * nz
        # vector projected perpendicular to the cylinder normal
        xn = dx - vn * nx
        yn = dy - vn * ny
        zn = dz - vn * nz
        # magnitude of the perpendicular projection
        r = sqrt(xn * xn + yn * yn + zn * zn) + EPSILON
        # factor to scale the vector to touch the cylinder
        s = d / r
        # extended vector touching the cylinder
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vertList.append([xx, yy, zz])

    focusList = [[ox, oy, oz]]

    return vertList, focusList


def projection_spherical(verts3D, m, d):
    """

    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection sphere origin

    vertList = []
    focusList = []
    for vert in verts3D:
        x, y, z = vert
        dx = x - ox
        dy = y - oy
        dz = z - oz

        r = sqrt(dx*dx + dy*dy + dz*dz) + EPSILON

        xx = ox + dx * d/r
        yy = oy + dy * d/r
        zz = oz + dz * d/r

        vertList.append([xx, yy, zz])

    focusList = [[ox, oy, oz]]

    return vertList, focusList


def projection_planar2D(vert3D, m, d):
    """
    Project a 3D vector onto 2D space given the projection distance
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection screen origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection screen normal

    x, y, z = vert3D

    x = x - ox
    y = y - oy
    z = z - oz

    an = x * nx + y * ny + z * nz  # v projection along the plane normal

    s = d / (d + an)  # perspective factor

    xa = s * (x - an * nx)
    ya = s * (y - an * ny)
    za = s * (z - an * nz)

    px = ox + xa
    py = oy + ya
    pz = oz + za

    return [px, py, pz]


def projection_planar(verts3D, m, d):
    """
    Project the 3D verts onto 2D space given the projection distance
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection screen origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection screen normal

    vertList = []
    focusList = []
    for vert in verts3D:
        x, y, z = vert

        # Focus location
        # Xx Yx Zx Tx        0     Tx - d * Zx
        # Xy Yy Zy Ty   *    0  =  Ty - d * Zy
        # Xz Yz Zz Tz      - d     Tz - d * Zz
        # 0  0  0  1         1     1

        dx = x - ox
        dy = y - oy
        dz = z - oz

        an = dx * nx + dy * ny + dz * nz  # v projection along the plane normal

        s = d / (d + an)  # perspective factor

        xa = s * (dx - an * nx)
        ya = s * (dy - an * ny)
        za = s * (dz - an * nz)

        px = ox + xa
        py = oy + ya
        pz = oz + za

        vertList.append([px, py, pz])

    focusList = [[ox - d*nx, oy - d*ny, oz - d * nz]]

    return vertList, focusList


def projection_planar2(verts3D, m, d):
    """
    Project the 3D verts onto 2D space given the projection distance
    """
    verts2D = [projection_planar2D(verts3D[i], m, d) for i in range(len(verts3D))]

    # Focus location
    # Xx Yx Zx Tx        0     Tx - d * Zx
    # Xy Yy Zy Ty   *    0  =  Ty - d * Zy
    # Xz Yz Zz Tz      - d     Tz - d * Zz
    # 0  0  0  1         1     1

    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection plane origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection plane normal

    focus = [[ox - d*nx, oy - d*ny, oz - d * nz]]

    return verts2D, focus


class Sv3DProjectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 3D Projection, Perspective, Orthogonal
    Tooltips: Projection from 3D space to 2D space
    """
    bl_idname = 'Sv3DProjectNode'
    bl_label = '3D Projection'

    projection_type = EnumProperty(
        name="Type", items=projection_type_items, default="PLANAR", update=updateNode)

    distance = FloatProperty(
        name="Distance", description="Projection Distance",
        default=2.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Verts")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polys")
        # projection screen location and orientation
        self.inputs.new('MatrixSocket', "Matrix")
        # distance from the projection point to the projection screen
        self.inputs.new('StringsSocket', "D").prop_name = 'distance'

        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polys")
        self.outputs.new('VerticesSocket', "Focus")

    def draw_buttons(self, context, layout):
        layout.prop(self, "projection_type", text="")

    @profile
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

        input_m = inputs["Matrix"].sv_get(default=idMat)

        input_d = inputs["D"].sv_get()[0]

        params = match_long_repeat([input_v, input_e, input_p, input_m, input_d])

        if self.projection_type == "PLANAR":
            projector = projection_planar
        elif self.projection_type == "CYLINDRICAL":
            projector = projection_cylindrical
        elif self.projection_type == "SPHERICAL":
            projector = projection_spherical

        vertList = []
        edgeList = []
        polyList = []
        focusList = []
        for v, e, p, m, d in zip(*params):
            verts, focus = projector(v, m, d)
            vertList.append(verts)
            edgeList.append(e)
            polyList.append(p)
            focusList.append(focus)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vertList)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edgeList)
        if outputs["Polys"].is_linked:
            outputs["Polys"].sv_set(polyList)
        if outputs["Focus"].is_linked:
            outputs["Focus"].sv_set(focusList)


def register():
    bpy.utils.register_class(Sv3DProjectNode)


def unregister():
    bpy.utils.unregister_class(Sv3DProjectNode)
