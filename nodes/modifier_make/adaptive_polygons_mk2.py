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

from math import sin, cos, pi, sqrt

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty
import bmesh
from mathutils import Vector
from mathutils.geometry import barycentric_transform

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_generate,
                                     Vector_degenerate, match_long_repeat, fullList)

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.geom import diameter, LineEquation2D
from sverchok.utils.logging import info, debug
# "coauthor": "Alessandro Zomparelli (sketchesofcode)"

cos_pi_6 = cos(pi/6)
sin_pi_6 = sin(pi/6)
sqrt_3 = sqrt(3)
sqrt_3_6 = sqrt_3/6
sqrt_3_3 = sqrt_3/3
sqrt_3_2 = sqrt_3/2

class SvAdaptivePolygonsNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvAdaptivePolygonsNodeMk2'
    bl_label = 'Adaptive Polygons Mk2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ADAPTATIVE_POLS'

    axes = [
            ("X", "X", "Orient donor's X axis along normal", 0),
            ("Y", "Y", "Orient donor's Y axis along normal", 1),
            ("Z", "Z", "Orient donor's Z axis along normal", 2)
        ]

    normal_axis: EnumProperty(
        name = "Normal axis",
        description = "Donor object axis to be oriented along recipient face normal",
        items = axes,
        default = 'Z',
        update = updateNode)

    width_coef: FloatProperty(
        name='Width coeff', description='with coefficient for sverchok adaptivepols donors size',
        default=1.0, max=3.0, min=0.5, update=updateNode)
    
    z_coef: FloatProperty(
        name='Z coeff',
        default=1.0, max=3.0, min=0.0, update=updateNode)

    z_offset: FloatProperty(
        name = "Z offet",
        default = 0.0,
        update = updateNode)

    normal_interp_modes = [
            ("LINEAR", "Linear", "Exact / linear normals interpolation", 0),
            ("SMOOTH", "Unit length", "Use normals of unit length", 1)
        ]

    normal_interp_mode : EnumProperty(
        name = "Interpolate normals",
        description = "Normals interpolation mode",
        items = normal_interp_modes, default = "LINEAR",
        update = updateNode)

    normal_modes = [
            ("MAP", "Map", "Interpolate from donor vertex normals", 0),
            ("FACE", "Face", "Use donor face normals", 1)
        ]

    normal_mode : EnumProperty(
        name = "Use normals",
        description = "Normals mapping mode",
        items = normal_modes, default = "MAP",
        update = updateNode)
    
    z_scale_modes = [
            ("PROP", "Proportional", "Scale along normal proportionally with the donor object", 0),
            ("CONST", "Constant", "Constant scale along normal", 1)
        ]

    z_scale : EnumProperty(
        name = "Z Scale",
        description = "Mode of scaling along the normals",
        items = z_scale_modes, default = "PROP",
        update = updateNode)

    xy_modes = [
            ("BOUNDS", "Bounds", "Map donor object bounds to recipient face", 0),
            ("PLAIN", "As Is", "Map donor object's coordinate space to recipient face as-is", 1)
        ]

    xy_mode : EnumProperty(
        name = "Coordinates",
        description = "Donor object coordinates mapping",
        items = xy_modes, default = "BOUNDS",
        update = updateNode)

    map_modes = [
            ("QUADTRI", "Quads / Tris Auto", "Use Quads or Tris mapping automatically", 0),
            ("QUADS", "Quads Always", "Use Quads mapping even for the Tris", 1)
        ]

    map_mode : EnumProperty(
        name = "Faces mode",
        description = "Donor object mapping mode",
        items = map_modes, default = "QUADTRI",
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        description = "Output one joined mesh",
        default = False,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "VersR")
        self.inputs.new('SvStringsSocket', "PolsR")
        self.inputs.new('SvVerticesSocket', "VersD")
        self.inputs.new('SvStringsSocket', "PolsD")
        self.inputs.new('SvStringsSocket', "W_Coef").prop_name = 'width_coef'
        self.inputs.new('SvStringsSocket', "Z_Coef").prop_name = 'z_coef'
        self.inputs.new('SvStringsSocket', "Z_Offset").prop_name = 'z_offset'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "normal_axis", expand=True)
        layout.prop(self, "z_scale")
        layout.prop(self, "normal_mode")
        if self.normal_mode == 'MAP':
            layout.prop(self, "normal_interp_mode")
        layout.prop(self, "xy_mode")
        layout.prop(self, "map_mode")
        layout.prop(self, "join")

    def get_triangle_directions(self):
        triangle_direction_1 = Vector((cos_pi_6, sin_pi_6, 0))
        triangle_direction_2 = Vector((-cos_pi_6, sin_pi_6, 0))
        triangle_direction_3 = Vector((0, -1, 0))

        if self.normal_axis == 'X':
            return triangle_direction_1.zxy, triangle_direction_2.zxy, triangle_direction_3.zxy
        elif self.normal_axis == 'Y':
            return triangle_direction_1.xzy, triangle_direction_2.xzy, triangle_direction_3.xzy
        else:
            return triangle_direction_1, triangle_direction_2, triangle_direction_3

    def to2d(self, v):
        if self.normal_axis == 'X':
            return v.yz
        elif self.normal_axis == 'Y':
            return v.xz
        else:
            return v.xy

    def from2d(self, x, y):
        if self.normal_axis == 'X':
            return Vector((0, x, y))
        elif self.normal_axis == 'Y':
            return Vector((x, 0, y))
        else:
            return Vector((x, y, 0))

    def remap3d(self, x, y, z):
        if self.normal_axis == 'X':
            return Vector((z, x, y))
        elif self.normal_axis == 'Y':
            return Vector((x, z, y))
        else:
            return Vector((x, y, z))

    def bounding_triangle(self, vertices):
        X, Y = self.get_other_axes()

        triangle_direction_1, triangle_direction_2, triangle_direction_3 = self.get_triangle_directions()
        max_1 = self.to2d(max(vertices, key = lambda vertex: triangle_direction_1.dot(vertex)))
        max_2 = self.to2d(max(vertices, key = lambda vertex: triangle_direction_2.dot(vertex)))
        max_3 = self.to2d(min(vertices, key = lambda vertex: vertex[Y]))

        side_1 = LineEquation2D.from_normal_and_point(self.to2d(triangle_direction_1), max_1)
        side_2 = LineEquation2D.from_normal_and_point(self.to2d(triangle_direction_2), max_2)
        side_3 = LineEquation2D.from_normal_and_point(self.to2d(triangle_direction_3), max_3)

        p1 = side_1.intersect_with_line(side_2)
        p2 = side_2.intersect_with_line(side_3)
        p3 = side_3.intersect_with_line(side_1)

        p1 = self.from2d(p1[0], p1[1])
        p2 = self.from2d(p2[0], p2[1])
        p3 = self.from2d(p3[0], p3[1])

        return p1, p2, p3

    def interpolate_quad_2d(self, v1, v2, v3, v4, v, x_coef, y_coef):
        X, Y = self.get_other_axes()
        v12 = v1 + (v2-v1)*v[X]*x_coef + ((v2-v1)/2)
        v43 = v4 + (v3-v4)*v[X]*x_coef + ((v3-v4)/2)
        return v12 + (v43-v12)*v[Y]*y_coef + ((v43-v12)/2)

    def interpolate_quad_3d(self, v1, v2, v3, v4, face_normal, v, x_coef, y_coef, z_coef, z_offset):
        loc = self.interpolate_quad_2d(v1.co, v2.co, v3.co, v4.co, v, x_coef, y_coef)
        if self.normal_mode == 'MAP':
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_quad_2d(v1.normal, v2.normal, v3.normal, v4.normal, v, x_coef, y_coef)
                normal.normalize()
            else:
                normal = self.interpolate_quad_2d(v1.co + v1.normal, v2.co + v2.normal,
                                             v3.co + v3.normal, v4.co + v4.normal,
                                             v, x_coef, y_coef)
                normal = normal - loc
        else:
            #normal = (v1.normal + v2.normal + v3.normal + v4.normal) * 0.25
            normal = face_normal
        Z = self.normal_axis_idx()
        return loc + normal*(v[Z]*z_coef + z_offset)

    def interpolate_tri_2d(self, dst_vert_1, dst_vert_2, dst_vert_3, src_vert_1, src_vert_2, src_vert_3, v):
        v = self.from2d(v.x, v.y)
        return barycentric_transform(v, src_vert_1, src_vert_2, src_vert_3,
                                        dst_vert_1, dst_vert_2, dst_vert_3)

    def interpolate_tri_3d(self, dst_vert_1, dst_vert_2, dst_vert_3, src_vert_1, src_vert_2, src_vert_3, face_normal, v, z_coef, z_offset):
        v_at_triangle = interpolate_tri_2d(dst_vert_1.co, dst_vert_2.co, dst_vert_3.co,
                                            src_vert_1, src_vert_2, src_vert_3, v)
        if self.normal_mode == 'MAP':
            if self.normal_interp_mode == 'SMOOTH':
                normal = interpolate_tri_2d(dst_vert_1.normal, dst_vert_2.normal, dst_vert_3.normal,
                                             src_vert_1, src_vert_2, src_vert_3, v)
                normal.normalize()
            else:
                normal = interpolate_tri_2d(dst_vert_1.co + dst_vert_1.normal, dst_vert_2.co + dst_vert_2.normal,
                                            dst_vert_3.co + dst_vert_3.normal,
                                            src_vert_1, src_vert_2, src_vert_3, v)
                normal = normal - v_at_triangle
        else:
            #normal = (dst_vert_1.normal + dst_vert_2.normal + dst_vert_3.normal) * 0.333333333
            normal = face_normal
        Z = self.normal_axis_idx()
        return v_at_triangle + normal * (v[Z] * z_coef + z_offset)

    def get_other_axes(self):
        if self.normal_axis == 'X':
            return 1, 2
        elif self.normal_axis == 'Y':
            return 0, 2
        else:
            return 0, 1

    def normal_axis_idx(self):
        return "XYZ".index(self.normal_axis)

    def map_bounds(self, min, max, x):
        c = (min + max) / 2.0
        k = 1.0 / (max - min)
        return (x - c) * k

    def _process(self, verts_recpt, faces_recpt, verts_donor, faces_donor, zcoefs, zoffsets, wcoefs):
        bm = bmesh_from_pydata(verts_recpt, None, faces_recpt, normal_update=True)
        bm.verts.ensure_lookup_table()
        donor_verts_v = [Vector(v) for v in verts_donor]

        X, Y = self.get_other_axes()
        Z = self.normal_axis_idx()

        if self.xy_mode == 'BOUNDS':
            max_x = max(v[X] for v in verts_donor)
            min_x = min(v[X] for v in verts_donor)
            max_y = max(v[Y] for v in verts_donor)
            min_y = min(v[Y] for v in verts_donor)

            tri_vert_1, tri_vert_2, tri_vert_3 = self.bounding_triangle(donor_verts_v)
        else:
            tri_vert_1 = self.from2d(0, sqrt_3_3)
            tri_vert_2 = self.from2d(0.5, -sqrt_3_6)
            tri_vert_3 = self.from2d(-0.5, -sqrt_3_6)

        z_size = diameter(verts_donor, Z)

        verts_out = []
        faces_out = []

        for recpt_face, recpt_face_bm, zcoef, zoffset, wcoef in zip(faces_recpt, bm.faces, zcoefs, zoffsets, wcoefs):
            recpt_face_vertices_bm = [bm.verts[i] for i in recpt_face]
            if self.z_scale == 'CONST':
                if abs(z_size) < 1e-6:
                    zcoef = 0
                else:
                    zcoef = zcoef / z_size

            if self.map_mode == 'QUADTRI':
                if len(recpt_face) == 3:
                    map_mode = 'TRI'
                else:
                    map_mode = 'QUAD'
            else:
                map_mode = 'QUAD'

            if map_mode == 'TRI':
                new_verts = []
                for v in verts_donor:
                    new_verts.append(self.interpolate_tri_3d(
                                        recpt_face_vertices_bm[0],
                                        recpt_face_vertices_bm[1],
                                        recpt_face_vertices_bm[2],
                                        tri_vert_1/wcoef, tri_vert_2/wcoef, tri_vert_3/wcoef,
                                        recpt_face_bm.normal,
                                        Vector(v), zcoef, zoffset))
                verts_out.append(new_verts)
            elif map_mode == 'QUAD':
                new_verts = []
                for v in verts_donor:
                    v = Vector(v)
                    if self.xy_mode == 'BOUNDS':
                        x = self.map_bounds(min_x, max_x, v[X])
                        y = self.map_bounds(min_y, max_y, v[Y])
                        z = v[Z]

                        v = Vector((0, 0, 0))
                        v[X] = x
                        v[Y] = y
                        v[Z] = z

                    new_verts.append(self.interpolate_quad_3d(
                                        recpt_face_vertices_bm[0],
                                        recpt_face_vertices_bm[1],
                                        recpt_face_vertices_bm[2],
                                        recpt_face_vertices_bm[-1],
                                        recpt_face_bm.normal,
                                        v,
                                        wcoef, wcoef,
                                        zcoef, zoffset))

                verts_out.append(new_verts)
            faces_out.append(faces_donor)

        bm.free()

        return verts_out, faces_out

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        verts_donor_s = self.inputs['VersR'].sv_get()
        faces_donor_s = self.inputs['PolsR'].sv_get()
        verts_recpt_s = self.inputs['VersD'].sv_get()
        faces_recpt_s = self.inputs['PolsD'].sv_get()
        zcoefs_s = self.inputs['Z_Coef'].sv_get()
        zoffsets_s = self.inputs['Z_Offset'].sv_get()
        wcoefs_s = self.inputs['W_Coef'].sv_get()

        verts_out = []
        faces_out = []

        objects = match_long_repeat([verts_recpt_s, faces_recpt_s, verts_donor_s, faces_donor_s, zcoefs_s, zoffsets_s, wcoefs_s])
        for verts_donor, faces_donor, verts_recpt, faces_recpt, zcoefs, zoffsets, wcoefs, in zip(*objects):
            fullList(zcoefs, len(faces_recpt))
            fullList(zoffsets, len(faces_recpt))
            fullList(wcoefs, len(faces_recpt))

            new_verts, new_faces = self._process(verts_recpt, faces_recpt,
                                                 verts_donor, faces_donor,
                                                 zcoefs, zoffsets, wcoefs)
            verts_out.extend(new_verts)
            faces_out.extend(new_faces)

            verts_out = Vector_degenerate(verts_out)
            if self.join:
                verts_out, _, faces_out = mesh_join(verts_out, [], faces_out)
                verts_out = [verts_out]
                faces_out = [faces_out]

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Polygons'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvAdaptivePolygonsNodeMk2)

def unregister():
    bpy.utils.unregister_class(SvAdaptivePolygonsNodeMk2)

