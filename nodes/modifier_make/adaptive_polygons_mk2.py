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

from math import sin, cos, pi, sqrt, pow
from functools import reduce

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import barycentric_transform

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_generate,
                                     Vector_degenerate, match_long_repeat, fullList, cycle_for_length,
                                     describe_data_shape, get_data_nesting_level,
                                     rotate_list)

from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.geom import diameter, LineEquation2D, center
from sverchok.utils.logging import info, debug
# "coauthor": "Alessandro Zomparelli (sketchesofcode)"

cos_pi_6 = cos(pi/6)
sin_pi_6 = sin(pi/6)
sqrt_3 = sqrt(3)
sqrt_3_6 = sqrt_3/6
sqrt_3_3 = sqrt_3/3
sqrt_3_2 = sqrt_3/2

class OutputData(object):
    def __init__(self):
        self.verts_out = []
        self.faces_out = []
        self.face_data_out = []

class RecptFaceData(object):
    def __init__(self):
        self.vertices_co = []
        self.vertices_normal = []
        self.vertices_idxs = []
        self.normal = None
        self.center = None
        self.frame_width = None

    def copy(self):
        r = RecptFaceData()
        r.vertices_co = self.vertices_co[:]
        r.vertices_normal = self.vertices_normal[:]
        r.vertices_idxs = self.vertices_idxs[:]
        r.normal = self.normal
        r.center = self.center
        r.frame_width = self.frame_width
        return r

class DonorData(object):
    def __init__(self):
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None
        self.tri_vert_1 = None
        self.tri_vert_2 = None
        self.tri_vert_3 = None
        self.verts_v = []
        self.faces_i = []
        self.face_data_i = []

class SvAdaptivePolygonsNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Adaptive Polygons Tessellate Tissue
    Tooltip: Generate an adapted copy of donor object along each face of recipient object.
    """
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
        name='Width coeff',
        description = "Donor object width coefficient",
        default=1.0, max=3.0, min=0.5, update=updateNode)
    
    frame_width: FloatProperty(
        name='Frame width',
        description = "Frame width coefficient for Frame / Fan mode",
        default=0.5, max=1.0, min=0.0, update=updateNode)
    
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
            ("CONST", "Constant", "Constant scale along normal", 1),
            ("AUTO", "Auto", "Try to calculate the correct scale automatically", 2)
        ]

    z_scale : EnumProperty(
        name = "Z Scale",
        description = "Mode of scaling along the normals",
        items = z_scale_modes, default = "PROP",
        update = updateNode)

    z_rotation: FloatProperty(
        name = "Z Rotation",
        description = "Rotate donor object around recipient's face normal",
        min = 0, max = 2*pi, default = 0,
        update = updateNode)
    
    poly_rotation: IntProperty(
        name = "Polygons rotation",
        description = "Rotate indexes in polygons definition",
        min = 0, default = 0,
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

    tri_bound_modes = [
            ("EQUILATERAL", "Equilateral", "Use unit-sided equilateral triangle as a base area",
                custom_icon("SV_EQUILATERAL_TRIANGLE"), 0),
            ("RECTANGULAR", "Rectangular", "Use rectangular triangle with hypotenuse of 2 as a base area",
                custom_icon("SV_RECTANGULAR_TRIANGLE"), 1)
        ]

    tri_bound_mode : EnumProperty(
        name = "Bounding triangle",
        description = "Type of triangle to use as a bounding triangle",
        items = tri_bound_modes,
        default = "EQUILATERAL",
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

    skip_modes = [
            ("SKIP", "Skip", "Do not output anything", 0),
            ("ASIS", "As Is", "Output these faces as is", 1)
        ]

    mask_mode: EnumProperty(
        name = "Mask mode",
        description = "What to do with masked out faces",
        items = skip_modes, default = "SKIP",
        update = updateNode)

    ngon_modes = [
            ("QUADS", "As Quads", "Try to process as Quads", 0),
            ("SKIP", "Skip", "Do not output anything", 1),
            ("ASIS", "As Is", "Output these faces as is", 2)
        ]

    ngon_mode: EnumProperty(
        name = "NGons",
        description = "What to do with NGons",
        items = ngon_modes, default = "QUADS",
        update = updateNode)

    def update_frame_mode(self, context):
        show_width = self.frame_mode != 'NEVER'
        if 'FrameWidth' in self.inputs:
            self.inputs['FrameWidth'].hide_safe = not show_width
        updateNode(self, context)

    frame_modes = [
            ("NEVER", "Do not use", "Do not use Frame / Fan mode", 0),
            ("NGONS", "NGons only", "Use Frame / Fan mode for NGons (n > 4) only", 1),
            ("NGONQUAD", "NGons and Quads", "Use Frame / Fan mode for NGons and Quads (n >= 4)", 2),
            ("ALWAYS", "Always", "Use Frame / Fan mode for all faces", 3)
        ]
    
    frame_mode: EnumProperty(
        name = "Frame mode",
        description = "When to use Frame / Fan mode",
        items = frame_modes, default = 'NEVER',
        update = update_frame_mode)

    matching_modes = [
            ("LONG", "Match longest", "Make an iteration for each donor or recipient object - depending on which list is longer", 0),
            ("PERFACE", "Donor per face", "If there are many donor objects, match each donor object with corresponding recipient object face", 1)
        ]

    matching_mode: EnumProperty(
        name = "Matching",
        description = "How to match list of recipient objects with list of donor objects",
        items = matching_modes, default = "LONG",
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        description = "Output one joined mesh",
        default = False,
        update = updateNode)

    tri_vert_idxs = [0, 1, 2]
    quad_vert_idxs = [0, 1, 2, -1]

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "VersR")
        self.inputs.new('SvStringsSocket', "PolsR")
        self.inputs.new('SvVerticesSocket', "VersD")
        self.inputs.new('SvStringsSocket', "PolsD")
        self.inputs.new('SvStringsSocket', "FaceDataD")
        self.inputs.new('SvStringsSocket', "W_Coef").prop_name = 'width_coef'
        self.inputs.new('SvStringsSocket', "FrameWidth").prop_name = 'frame_width'
        self.inputs.new('SvStringsSocket', "Z_Coef").prop_name = 'z_coef'
        self.inputs.new('SvStringsSocket', "Z_Offset").prop_name = 'z_offset'
        self.inputs.new('SvStringsSocket', "Z_Rotation").prop_name = 'z_rotation'
        self.inputs.new('SvStringsSocket', "PolyRotation").prop_name = 'poly_rotation'
        self.inputs.new('SvStringsSocket', "PolyMask")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Polygons")
        self.outputs.new('SvStringsSocket', "FaceData")

        self.update_frame_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "join")
        layout.prop(self, "matching_mode")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

        layout.label(text = "Normal axis:")
        layout.prop(self, "normal_axis", expand=True)
        layout.prop(self, "z_scale")
        layout.prop(self, "normal_mode")
        if self.normal_mode == 'MAP':
            layout.prop(self, "normal_interp_mode")
        layout.prop(self, "xy_mode")
        layout.label(text="Bounding triangle:")
        layout.prop(self, "tri_bound_mode", expand=True)
        layout.prop(self, "frame_mode")
        layout.prop(self, "map_mode")
        layout.prop(self, "mask_mode")
        layout.prop(self, "ngon_mode")

    def get_triangle_directions(self):
        """
        Three normal of unit triangle's edges.
        This is not constant just because the normal can be X or Y or Z.
        """
        if self.tri_bound_mode == 'EQUILATERAL':
            triangle_direction_1 = Vector((cos_pi_6, sin_pi_6, 0))
            triangle_direction_2 = Vector((-cos_pi_6, sin_pi_6, 0))
            triangle_direction_3 = Vector((0, -1, 0))
        else:
            triangle_direction_1 = Vector((1, 1, 0))
            triangle_direction_2 = Vector((-1, 1, 0))
            triangle_direction_3 = Vector((0, -1, 0))

        if self.normal_axis == 'X':
            return triangle_direction_1.zxy, triangle_direction_2.zxy, triangle_direction_3.zxy
        elif self.normal_axis == 'Y':
            return triangle_direction_1.xzy, triangle_direction_2.xzy, triangle_direction_3.xzy
        else:
            return triangle_direction_1, triangle_direction_2, triangle_direction_3

    def to2d(self, v):
        """
        Convert vector to 2D.
        Remove the coordinate which is responsible for normal axis.
        """
        if self.normal_axis == 'X':
            return v.yz
        elif self.normal_axis == 'Y':
            return v.xz
        else:
            return v.xy

    def from2d(self, x, y):
        """
        Make 3D vector from X and Y.
        Add zero for the coordinate which is responsible for normal axis.
        """
        if self.normal_axis == 'X':
            return Vector((0, x, y))
        elif self.normal_axis == 'Y':
            return Vector((x, 0, y))
        else:
            return Vector((x, y, 0))

    def bounding_triangle(self, vertices):
        """
        Return three vertices of a triangle with equal sides / rectangular triangle,
        which contains all provided vertices.
        """
        X, Y = self.get_other_axes()

        triangle_direction_1, triangle_direction_2, triangle_direction_3 = self.get_triangle_directions()
        max_1 = self.to2d(max(vertices, key = lambda vertex: triangle_direction_1.dot(vertex)))
        max_2 = self.to2d(max(vertices, key = lambda vertex: triangle_direction_2.dot(vertex)))
        max_3 = self.to2d(min(vertices, key = lambda vertex: vertex[Y]))

        side_1 = LineEquation2D.from_normal_and_point(self.to2d(triangle_direction_1), max_1)
        side_2 = LineEquation2D.from_normal_and_point(self.to2d(triangle_direction_2), max_2)
        side_3 = LineEquation2D.from_normal_and_point(self.to2d(triangle_direction_3), max_3)

        p1 = side_2.intersect_with_line(side_3)
        p2 = side_1.intersect_with_line(side_3)
        p3 = side_1.intersect_with_line(side_2)

        p1 = self.from2d(p1[0], p1[1])
        p2 = self.from2d(p2[0], p2[1])
        p3 = self.from2d(p3[0], p3[1])

        return p1, p2, p3

    def interpolate_quad_2d(self, dst_vert_1, dst_vert_2, dst_vert_3, dst_vert_4, v, x_coef, y_coef):
        """
        Map the provided `v` vertex, considering only two of it's coordinates,
        from the [-1/2; 1/2] x [-1/2; 1/2] square to the face defined by
        four `dst_vert_n` vertices.
        """
        X, Y = self.get_other_axes()
        v12 = dst_vert_1 + (dst_vert_2-dst_vert_1)*v[X]*x_coef + ((dst_vert_2-dst_vert_1)/2)
        v43 = dst_vert_4 + (dst_vert_3-dst_vert_4)*v[X]*x_coef + ((dst_vert_3-dst_vert_4)/2)
        return v12 + (v43-v12)*v[Y]*y_coef + ((v43-v12)/2)

    def interpolate_quad_3d(self, dst_vert_1, dst_vert_2, dst_vert_3, dst_vert_4, dst_normal_1, dst_normal_2, dst_normal_3, dst_normal_4, face_normal, v, x_coef, y_coef, z_coef, z_offset):
        """
        Map the provided `v` vertex from the source
        [-1/2; 1/2] x [-1/2; 1/2] x [-1/2; 1/2] cube
        to the space defined by `dst_vert_n` vertices.
        """
        loc = self.interpolate_quad_2d(dst_vert_1, dst_vert_2, dst_vert_3, dst_vert_4, v, x_coef, y_coef)
        if self.normal_mode == 'MAP':
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_quad_2d(dst_normal_1, dst_normal_2, dst_normal_3, dst_normal_4, v, x_coef, y_coef)
                normal.normalize()
            else:
                normal = self.interpolate_quad_2d(dst_vert_1 + dst_normal_1, dst_vert_2 + dst_normal_2,
                                             dst_vert_3 + dst_normal_3, dst_vert_4 + dst_normal_4,
                                             v, x_coef, y_coef)
                normal = normal - loc
        else:
            #normal = (dst_vert_1.normal + dst_vert_2.normal + dst_vert_3.normal + dst_vert_4.normal) * 0.25
            normal = face_normal
        Z = self.normal_axis_idx()
        return loc + normal*(v[Z]*z_coef + z_offset)

    def interpolate_tri_2d(self, dst_vert_1, dst_vert_2, dst_vert_3, src_vert_1, src_vert_2, src_vert_3, v):
        """
        Map the provided `v` vertex, considering only two of it's coordinates,
        from the source triangle (defined by `src_vert_n` vertices) to the face defined by
        three `dst_vert_n` vertices.
        """
        X, Y = self.get_other_axes()
        v = self.from2d(v[X], v[Y])
        return barycentric_transform(v, src_vert_1, src_vert_2, src_vert_3,
                                        dst_vert_1, dst_vert_2, dst_vert_3)

    def interpolate_tri_3d(self, dst_vert_1, dst_vert_2, dst_vert_3, dst_normal_1, dst_normal_2, dst_normal_3, src_vert_1, src_vert_2, src_vert_3, face_normal, v, z_coef, z_offset):
        """
        Map the provided `v` vertex from the source triangle
        to the space defined by `dst_vert_n` vertices.
        """
        v_at_triangle = self.interpolate_tri_2d(dst_vert_1, dst_vert_2, dst_vert_3,
                                            src_vert_1, src_vert_2, src_vert_3, v)
        if self.normal_mode == 'MAP':
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_tri_2d(dst_normal_1, dst_normal_2, dst_normal_3,
                                             src_vert_1, src_vert_2, src_vert_3, v)
                normal.normalize()
            else:
                normal = self.interpolate_tri_2d(dst_vert_1 + dst_normal_1, dst_vert_2 + dst_normal_2,
                                            dst_vert_3 + dst_normal_3,
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

    def rotate_z(self, verts, angle):
        if abs(angle) < 1e-6:
            return verts
        projection = [self.to2d(v) for v in verts]
        x0, y0 = center(projection)
        c = self.from2d(x0, y0)
        rot = Matrix.Rotation(angle, 4, self.normal_axis)
        result = [(rot @ (v - c)) + c for v in verts]
        return result

    def calc_z_scale(self, dst_verts, src_verts):
        src_lens = []
        for v1, v2 in zip(src_verts, src_verts[1:]):
            src_lens.append((v1 - v2).length)
        src_lens.append((src_verts[-1] - src_verts[0]).length)

        dst_lens = []
        for v1, v2 in zip(dst_verts, dst_verts[1:]):
            dst_lens.append((v1 - v2).length)
        dst_lens.append((dst_verts[-1] - dst_verts[0]).length)

        scales = [dst_len / src_len for src_len,dst_len in zip(src_lens, dst_lens) if abs(src_len) > 1e-6 and abs(dst_len) > 1e-6]
        n = len(scales)
        prod = reduce(lambda x,y: x*y, scales, 1.0)
        return pow(prod, 1.0/n)

    def _process_face(self, map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot):

        X, Y = self.get_other_axes()
        Z = self.normal_axis_idx()
        #self.info(f"Face: {len(recpt_face_data.vertices_co)}, mode: {map_mode}")

        if map_mode == 'ASIS':
            # Leave this recipient's face as it was - as a single face.
            verts = recpt_face_data.vertices_co[:]
            n = len(verts)
            output.verts_out.append(verts)
            output.faces_out.append([list(range(n))])

        elif map_mode == 'TRI':
            # Tris processing mode.
            #
            # As interpolate_tri_3d is based on barycentric_transform,
            # here we do not have to manually map donor vertices to the
            # unit triangle.

            i0, i1, i2 = rotate_list(self.tri_vert_idxs, facerot)
            if self.z_scale == 'AUTO':
                zcoef = self.calc_z_scale(
                                    [recpt_face_data.vertices_co[i0],
                                     recpt_face_data.vertices_co[i1],
                                     recpt_face_data.vertices_co[i2]],
                                    [donor.tri_vert_1/wcoef, donor.tri_vert_2/wcoef, donor.tri_vert_3/wcoef]
                                ) * zcoef
            new_verts = []
            for v in donor.verts_v:
                new_verts.append(self.interpolate_tri_3d(
                                    recpt_face_data.vertices_co[i0],
                                    recpt_face_data.vertices_co[i1],
                                    recpt_face_data.vertices_co[i2],
                                    recpt_face_data.vertices_normal[i0],
                                    recpt_face_data.vertices_normal[i1],
                                    recpt_face_data.vertices_normal[i2],
                                    donor.tri_vert_1/wcoef, donor.tri_vert_2/wcoef, donor.tri_vert_3/wcoef,
                                    recpt_face_data.normal,
                                    v, zcoef, zoffset))
            output.verts_out.append(new_verts)
            output.faces_out.append(donor.faces_i)
            output.face_data_out.append(donor.face_data_i)

        elif map_mode == 'QUAD':
            # Quads processing mode.
            #
            # It can process Tris, but it will look strange:
            # triangle will be processed as degenerated Quad,
            # where third and fourth vertices coincide.
            # In Tissue addon, this is the only mode possible for Quads.
            # Someone may like that behaivour, so we allow it with setting...
            #
            # This can process NGons in even worse way:
            # it will take first three vertices and the last one
            # and consider that as a Quad.

            i0, i1, i2, i3 = rotate_list(self.quad_vert_idxs, facerot)
            if self.z_scale == 'AUTO':
                corner1 = self.from2d(donor.min_x, donor.min_y)
                corner2 = self.from2d(donor.min_x, donor.max_y)
                corner3 = self.from2d(donor.max_x, donor.max_y)
                corner4 = self.from2d(donor.max_x, donor.min_y)

                zcoef = self.calc_z_scale(
                                [recpt_face_data.vertices_co[i0],
                                 recpt_face_data.vertices_co[i1],
                                 recpt_face_data.vertices_co[i2],
                                 recpt_face_data.vertices_co[i3]],
                                [corner1, corner2, corner3, corner4]
                            ) * zcoef

            new_verts = []
            #self.info("Donor: %s", len(donor.verts_v))
            for v in donor.verts_v:
                if self.xy_mode == 'BOUNDS':
                    # Map the `v` vertex's X, Y coordinates
                    # from it's bounding square to
                    # [-1/2; 1/2] square.
                    # Leave Z coordinate as it was.
                    x = self.map_bounds(donor.min_x, donor.max_x, v[X])
                    y = self.map_bounds(donor.min_y, donor.max_y, v[Y])
                    z = v[Z]

                    v = Vector((0, 0, 0))
                    v[X] = x
                    v[Y] = y
                    v[Z] = z

                new_verts.append(self.interpolate_quad_3d(
                                    recpt_face_data.vertices_co[i0],
                                    recpt_face_data.vertices_co[i1],
                                    recpt_face_data.vertices_co[i2],
                                    recpt_face_data.vertices_co[i3],
                                    recpt_face_data.vertices_normal[i0],
                                    recpt_face_data.vertices_normal[i1],
                                    recpt_face_data.vertices_normal[i2],
                                    recpt_face_data.vertices_normal[i3],
                                    recpt_face_data.normal,
                                    v,
                                    wcoef, wcoef,
                                    zcoef, zoffset))

            output.verts_out.append(new_verts)
            output.faces_out.append(donor.faces_i)
            output.face_data_out.append(donor.face_data_i)

        elif map_mode == 'FRAME':
            is_fan = abs(recpt_face_data.frame_width - 1.0) < 1e-6
            n = len(recpt_face_data.vertices_co)
            if self.map_mode == 'QUADS':
                sub_map_mode = 'QUAD'
            else:
                if is_fan:
                    sub_map_mode = 'TRI'
                else:
                    sub_map_mode = 'QUAD'

            if is_fan:
                tri_faces = [(recpt_face_data.vertices_co[i],
                                recpt_face_data.vertices_co[i+1],
                                recpt_face_data.center) for i in range(n-1)]
                tri_faces.append((recpt_face_data.vertices_co[-1],
                                    recpt_face_data.vertices_co[0],
                                    recpt_face_data.center))

                tri_normals = [(recpt_face_data.vertices_normal[i],
                                recpt_face_data.vertices_normal[i+1],
                                recpt_face_data.normal) for i in range(n-1)]
                tri_normals.append((recpt_face_data.vertices_normal[-1],
                                    recpt_face_data.vertices_normal[0],
                                    recpt_face_data.normal))

                for tri_face, tri_normal in zip(tri_faces, tri_normals):
                    sub_recpt = recpt_face_data.copy()
                    sub_recpt.vertices_co = tri_face
                    sub_recpt.vertices_normal = tri_normal
                    sub_recpt.vertices_idxs = [0, 1, 2]
                    self._process_face(sub_map_mode, output, sub_recpt, donor, zcoef, zoffset, angle, wcoef, facerot)
            else:
                inner_verts = [vert.lerp(recpt_face_data.center, recpt_face_data.frame_width)
                                    for vert in recpt_face_data.vertices_co]
                inner_normals = [normal.lerp(recpt_face_data.normal, recpt_face_data.frame_width)
                                    for normal in recpt_face_data.vertices_normal]

                quad_faces = [(recpt_face_data.vertices_co[i],
                                recpt_face_data.vertices_co[i+1],
                                inner_verts[i+1], inner_verts[i])
                                    for i in range(n-1)]
                quad_faces.append((recpt_face_data.vertices_co[-1],
                                    recpt_face_data.vertices_co[0],
                                    inner_verts[0], inner_verts[-1]))
                quad_normals = [(recpt_face_data.vertices_normal[i],
                                recpt_face_data.vertices_normal[i+1],
                                inner_normals[i+1], inner_normals[i])
                                    for i in range(n-1)]
                quad_normals.append((recpt_face_data.vertices_normal[-1],
                                    recpt_face_data.vertices_normal[0],
                                    inner_normals[0], inner_normals[-1]))

                for quad_face, quad_normal in zip(quad_faces, quad_normals):
                    sub_recpt = recpt_face_data.copy()
                    sub_recpt.vertices_co = quad_face
                    sub_recpt.vertices_normal = quad_normal
                    sub_recpt.vertices_idxs = [0, 1, 2, 3]
                    self._process_face(sub_map_mode, output, sub_recpt, donor, zcoef, zoffset, angle, wcoef, facerot)

    def _process(self, verts_recpt, faces_recpt, verts_donor, faces_donor, face_data_donor, frame_widths, zcoefs, zoffsets, zrotations, wcoefs, facerots, mask):
        bm = bmesh_from_pydata(verts_recpt, None, faces_recpt, normal_update=True)
        bm.verts.ensure_lookup_table()
        single_donor = self.matching_mode == 'LONG'
        frame_level = get_data_nesting_level(frame_widths)
        if single_donor:
            # Original (unrotated) donor vertices
            donor_verts_o = [Vector(v) for v in verts_donor]

            verts_donor = [verts_donor]
            faces_donor = [faces_donor]
            face_data_donor = [face_data_donor]
            if frame_level == 0:
                frame_widths = [frame_widths]

        n_faces_recpt = len(faces_recpt)
        fullList(verts_donor, n_faces_recpt)
        fullList(faces_donor, n_faces_recpt)
        fullList(face_data_donor, n_faces_recpt)
        fullList(frame_widths, n_faces_recpt)

        X, Y = self.get_other_axes()
        Z = self.normal_axis_idx()

        donor = DonorData()

        # Vertices of the unit triangle.
        # In case xy_mode != BOUNDS, we will never
        # have to recalculate these.
        if self.tri_bound_mode == 'EQUILATERAL':
            donor.tri_vert_1 = self.from2d(-0.5, -sqrt_3_6)
            donor.tri_vert_2 = self.from2d(0.5, -sqrt_3_6)
            donor.tri_vert_3 = self.from2d(0, sqrt_3_3)
        else:
            donor.tri_vert_1 = self.from2d(-1, 0)
            donor.tri_vert_2 = self.from2d(1, 0)
            donor.tri_vert_3 = self.from2d(0, 1)

        if single_donor:
            # We will be rotating the donor object around Z axis,
            # so it's size along Z is not going to change.
            z_size = diameter(donor_verts_o, Z)

        output = OutputData()

        prev_angle = None
        face_data = zip(faces_recpt, bm.faces, frame_widths, verts_donor, faces_donor, face_data_donor, zcoefs, zoffsets, zrotations, wcoefs, facerots, mask)
        for recpt_face, recpt_face_bm, frame_width, donor_verts_i, donor_faces_i, donor_face_data_i, zcoef, zoffset, angle, wcoef, facerot, m in face_data:

            recpt_face_data = RecptFaceData()
            recpt_face_data.normal = recpt_face_bm.normal
            recpt_face_data.center = recpt_face_bm.calc_center_median()
            recpt_face_data.vertices_co = [bm.verts[i].co for i in recpt_face]
            recpt_face_data.vertices_normal = [bm.verts[i].normal for i in recpt_face]
            recpt_face_data.vertices_idxs = recpt_face[:]
            if not isinstance(frame_width, (int, float)):
                raise Exception(f"Unexpected data type for frame_width: {frame_width}")
            recpt_face_data.frame_width = frame_width

            donor.faces_i = donor_faces_i
            donor.face_data_i = donor_face_data_i

            if not single_donor:
                # Original (unrotated) donor vertices
                donor_verts_o = [Vector(v) for v in donor_verts_i]
                z_size = diameter(donor_verts_o, Z)

            # We have to recalculate rotated vertices only if
            # the rotation angle have changed.
            if prev_angle is None or angle != prev_angle or not single_donor:
                donor.verts_v = self.rotate_z(donor_verts_o, angle)

                if self.xy_mode == 'BOUNDS' or self.z_scale == 'AUTO' :
                    donor.max_x = max(v[X] for v in donor.verts_v)
                    donor.min_x = min(v[X] for v in donor.verts_v)
                    donor.max_y = max(v[Y] for v in donor.verts_v)
                    donor.min_y = min(v[Y] for v in donor.verts_v)

                if self.xy_mode == 'BOUNDS':
                    donor.tri_vert_1, donor.tri_vert_2, donor.tri_vert_3 = self.bounding_triangle(donor.verts_v)

            prev_angle = angle

            if self.z_scale == 'CONST':
                if abs(z_size) < 1e-6:
                    zcoef = 0
                else:
                    zcoef = zcoef / z_size

            # Define TRI/QUAD mode based on node settings.
            n = len(recpt_face)
            if not m:
                map_mode = self.mask_mode
            else:
                if n == 3:
                    if self.frame_mode == 'ALWAYS':
                        map_mode = 'FRAME'
                    else:
                        if self.map_mode == 'QUADTRI':
                            map_mode = 'TRI'
                        else: # self.map_mode == 'QUADS':
                            map_mode = 'QUAD'
                elif n == 4:
                    if self.frame_mode in ['ALWAYS', 'NGONQUAD']:
                        map_mode = 'FRAME'
                    else:
                        map_mode = 'QUAD'
                else:
                    if self.frame_mode in ['ALWAYS', 'NGONQUAD', 'NGONS']:
                        map_mode = 'FRAME'
                    else:
                        if self.ngon_mode == 'QUADS':
                            map_mode = 'QUAD'
                        elif self.ngon_mode == 'ASIS':
                            map_mode = 'ASIS'
                        else:
                            map_mode = 'SKIP'

            if map_mode == 'SKIP':
                # Skip this recipient's face - do not produce any vertices/faces for it
                continue

            self._process_face(map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)

        bm.free()

        return output

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        verts_recpt_s = self.inputs['VersR'].sv_get(deepcopy=False)
        faces_recpt_s = self.inputs['PolsR'].sv_get(default=[[]], deepcopy=False)
        verts_donor_s = self.inputs['VersD'].sv_get()
        faces_donor_s = self.inputs['PolsD'].sv_get()
        if 'FaceDataD' in self.inputs:
            face_data_donor_s = self.inputs['FaceDataD'].sv_get(default=[[]])
        else:
            face_data_donor_s = [[]]
        zcoefs_s = self.inputs['Z_Coef'].sv_get(deepcopy=False)
        zoffsets_s = self.inputs['Z_Offset'].sv_get(deepcopy=False)
        zrotations_s = self.inputs['Z_Rotation'].sv_get(deepcopy=False)
        wcoefs_s = self.inputs['W_Coef'].sv_get(deepcopy=False)
        if 'FrameWidth' in self.inputs:
            frame_widths_s = self.inputs['FrameWidth'].sv_get(deepcopy=True)
        else:
            frame_widths_s = [[0.5]]
        if 'PolyRotation' in self.inputs:
            facerots_s = self.inputs['PolyRotation'].sv_get(default = [[0]], deepcopy=False)
        else:
            facerots_s = [[0]]
        mask_s = self.inputs['PolyMask'].sv_get(default = [[1]], deepcopy=False)

        output = OutputData()

        if self.matching_mode == 'PERFACE':
            verts_donor_s = [verts_donor_s]
            faces_donor_s = [faces_donor_s]
            face_data_donor_s = [face_data_donor_s]
            #self.info("FW: %s", frame_widths_s)
            #frame_widths_s = [frame_widths_s]
        objects = match_long_repeat([verts_recpt_s, faces_recpt_s, verts_donor_s, faces_donor_s, face_data_donor_s, frame_widths_s, zcoefs_s, zoffsets_s, zrotations_s, wcoefs_s, facerots_s, mask_s])
        #self.info("N objects: %s", len(list(zip(*objects))))
        for verts_recpt, faces_recpt, verts_donor, faces_donor, face_data_donor, frame_widths, zcoefs, zoffsets, zrotations, wcoefs, facerots, mask in zip(*objects):
            n_faces_recpt = len(faces_recpt)
            fullList(zcoefs, n_faces_recpt)
            fullList(zoffsets, n_faces_recpt)
            fullList(zrotations, n_faces_recpt)
            if get_data_nesting_level(frame_widths) < 1:
                frame_widths = [frame_widths]
            fullList(frame_widths, n_faces_recpt)
            fullList(wcoefs, n_faces_recpt)
            fullList(facerots, n_faces_recpt)
            mask = cycle_for_length(mask, n_faces_recpt)

            new = self._process(verts_recpt, faces_recpt,
                                 verts_donor, faces_donor,
                                 face_data_donor,
                                 frame_widths,
                                 zcoefs, zoffsets, zrotations,
                                 wcoefs, facerots, mask)

            output.verts_out.extend(new.verts_out)
            output.faces_out.extend(new.faces_out)
            output.face_data_out.extend(new.face_data_out)

            output.verts_out = Vector_degenerate(output.verts_out)
            if self.join:
                output.verts_out, _, output.faces_out = mesh_join(output.verts_out, [], output.faces_out)
                output.verts_out = [output.verts_out]
                output.faces_out = [output.faces_out]
                output.face_data_out = [sum(output.face_data_out, [])]

            self.outputs['Vertices'].sv_set(output.verts_out)
            self.outputs['Polygons'].sv_set(output.faces_out)
            if 'FaceData' in self.outputs:
                self.outputs['FaceData'].sv_set(output.face_data_out)

def register():
    bpy.utils.register_class(SvAdaptivePolygonsNodeMk2)

def unregister():
    bpy.utils.unregister_class(SvAdaptivePolygonsNodeMk2)

