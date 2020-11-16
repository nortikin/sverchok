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

projection_screen_items = [
    ("PLANAR",  "Planar",  "Project onto a plane", 0),
    ("CYLINDRICAL", "Cylindrical", "Project onto a cylinder", 1),
    ("SPHERICAL", "Spherical", "Project onto a sphere", 2)]

id_mat = [[tuple(v) for v in Matrix()]]  # identity matrix

EPSILON = 1e-10


def projection_cylindrical(verts_3D, m, d):
    """
    Project the 3D verts onto a CYLINDRICAL screen
     verts_3D : vertices to project
            m : transformation matrix of the projection cylinder (location & rotation)
            d : distance between the projection point and the projection cylinder (cylinder radius)
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection cylinder origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection cylinder axis (Z)

    vert_list = []
    for vert in verts_3D:
        x, y, z = vert
        # vertex vector relative to the center of the cylinder (OV = V - O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the OV vector projected PARALLEL to the cylinder axis
        vn = dx * nx + dy * ny + dz * nz
        # vector OV projected PERPENDICULAR to the cylinder axis
        xn = dx - vn * nx
        yn = dy - vn * ny
        zn = dz - vn * nz
        # magnitude of the PERPENDICULAR projection
        r = sqrt(xn * xn + yn * yn + zn * zn) + EPSILON
        # factor to scale the OV vector to touch the cylinder
        s = d / r
        # extended vector touching the cylinder
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vert_list.append([xx, yy, zz])

    return vert_list


def projection_spherical(verts_3D, m, d):
    """
    Project the 3D verts onto a SPHERICAL screen
     verts_3D : vertices to project
            m : transformation matrix of the projection sphere (location & rotation)
            d : distance between the projection point and the projection sphere (sphere radius)
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection sphere origin

    vert_list = []
    for vert in verts_3D:
        x, y, z = vert
        # vertex vector relative to the sphere origin (OV = V - O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the OV vector
        r = sqrt(dx*dx + dy*dy + dz*dz) + EPSILON
        # factor to scale the OV vector to touch the sphere
        s = d / r
        # extended vector touching the sphere
        xx = ox + dx * s
        yy = oy + dy * s
        zz = oz + dz * s

        vert_list.append([xx, yy, zz])

    return vert_list


def projection_planar(verts_3D, m, d):
    """
    Project the 3D verts onto a PLANAR screen
     verts_3D : vertices to project
            m : transformation matrix of the projection plane (location & rotation)
            d : distance between the projector point and the projection plane

    Projection point location is given by m * D:
        Xx Yx Zx Tx        0     Tx - d * Zx
        Xy Yy Zy Ty   *    0  =  Ty - d * Zy
        Xz Yz Zz Tz      - d     Tz - d * Zz
        0  0  0  1         1     1
    """
    ox, oy, oz = [m[0][3], m[1][3], m[2][3]]  # projection plane origin
    nx, ny, nz = [m[0][2], m[1][2], m[2][2]]  # projection plane normal

    vert_list = []
    for vert in verts_3D:
        x, y, z = vert
        # vertex vector relative to the projection point (OV = V - O)
        dx = x - ox
        dy = y - oy
        dz = z - oz
        # magnitude of the OV vector projected PARALLEL to the plane normal (OV * N)
        l = dx * nx + dy * ny + dz * nz + EPSILON
        # factor to scale the OV vector to touch the plane
        s = d / l
        # extended vector touching the plane
        px = ox + dx * s
        py = oy + dy * s
        pz = oz + dz * s

        vert_list.append([px, py, pz])

    return vert_list


class Sv3DProjectNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 3D Projection, Perspective
    Tooltips: Projection from 3D space to 2D space
    """
    bl_idname = 'Sv3DProjectNode'
    bl_label = '3D Projection'

    projection_screen: EnumProperty(
        name="Screen", items=projection_screen_items, default="PLANAR", update=updateNode)

    distance: FloatProperty(
        name="Distance", description="Projection Distance", default=2.0, update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('SvVerticesSocket', "Verts")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        # projection screen location and orientation
        self.inputs.new('SvMatrixSocket', "Matrix")
        # distance from the projection point to the projection screen
        self.inputs.new('SvStringsSocket', "D").prop_name = 'distance'

        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        # self.outputs.new('SvVerticesSocket', "Projector")

    def draw_buttons(self, context, layout):
        layout.prop(self, "projection_screen", text="")

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

        input_e = inputs["Edges"].sv_get(default=[[]])
        input_p = inputs["Faces"].sv_get(default=[[]])
        input_m = inputs["Matrix"].sv_get(default=id_mat)
        input_d = inputs["D"].sv_get()[0]

        params = match_long_repeat([input_v, input_e, input_p, input_m, input_d])

        if self.projection_screen == "PLANAR":
            projector = projection_planar
        elif self.projection_screen == "CYLINDRICAL":
            projector = projection_cylindrical
        elif self.projection_screen == "SPHERICAL":
            projector = projection_spherical

        vert_list = []
        edge_list = []
        face_list = []
        for v, e, p, m, d in zip(*params):
            verts = projector(v, m, d)
            vert_list.append(verts)
            edge_list.append(e)
            face_list.append(p)

        if outputs["Verts"].is_linked:
            outputs["Verts"].sv_set(vert_list)
        if outputs["Edges"].is_linked:
            outputs["Edges"].sv_set(edge_list)
        if outputs["Faces"].is_linked:
            outputs["Faces"].sv_set(face_list)
        # if outputs["Projector"].is_linked:
        #     outputs["Projector"].sv_set(focus_list)


def register():
    bpy.utils.register_class(Sv3DProjectNode)


def unregister():
    bpy.utils.unregister_class(Sv3DProjectNode)
