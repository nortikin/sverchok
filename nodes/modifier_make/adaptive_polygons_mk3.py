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
from itertools import cycle
from numpy import (array as np_array,
                   newaxis as np_newaxis,
                   cross as np_cross,
                   zeros as np_zeros,
                   sqrt as np_sqrt,
                   float64 as np_float64,
                   dot as np_dot,
                   max as np_max,
                   min as np_min)
from numpy.linalg import (norm as np_norm,
                          inv as np_inv)
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector, Matrix
from mathutils.geometry import barycentric_transform

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, throttle_and_update_node,
                                     match_long_repeat,
                                     numpy_list_match_modes,
                                     cycle_for_length, make_repeaters, make_cyclers,
                                     get_data_nesting_level,
                                     rotate_list)

from sverchok.ui.sv_icons import custom_icon
from sverchok.ui.utils import enum_split
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, remove_doubles
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.geom import diameter, LineEquation2D, center
from sverchok.utils.math import np_normalize_vectors

# "coauthor": "Alessandro Zomparelli (sketchesofcode)"

cos_pi_6 = cos(pi/6)
sin_pi_6 = sin(pi/6)
sqrt_3 = sqrt(3)
sqrt_3_6 = sqrt_3/6
sqrt_3_3 = sqrt_3/3
sqrt_3_2 = sqrt_3/2

def matrix_def(triangle):
    '''Creation of Transform matrix from triangle'''
    tri0, tri1, tri2 = triangle[0, :], triangle[1, :], triangle[2, :]
    tri_normal = np_cross(tri1 - tri0, tri2 - tri0)
    magnitude = np_norm(tri_normal)
    tri_area = 0.5 * magnitude
    tri3 = tri0+ (tri_normal / magnitude)* np_sqrt(tri_area)

    transform_matrix = np_zeros([3, 3], dtype=np_float64)
    transform_matrix[0, :] = tri0 - tri3
    transform_matrix[1, :] = tri1 - tri3
    transform_matrix[2, :] = tri2 - tri3

    return transform_matrix, tri3

def prepare_source_data(src_verts):
    '''Create the inverted Transformation Matrix and 4th point of the tetrahedron'''
    matrix_trasform_s, tri3_src = matrix_def(src_verts)
    inverted_matrix_s = np_inv(matrix_trasform_s).T

    return inverted_matrix_s, tri3_src


def prepare_dest_data(dst_verts):
    '''Create Transformation Matrix and 4th point of the tetrahedron'''
    matrix_trasform, tri3_dest = matrix_def(dst_verts)

    return matrix_trasform, tri3_dest

def barycentric_transform_np(verts, src_verts, dst_verts):
    '''NumPy Implementation of a barycentric transform'''

    inverted_matrix_s, tri3_src = prepare_source_data(src_verts)
    matrix_transform_d, tri3_dest = prepare_dest_data(dst_verts)


    barycentric_co = np_dot(inverted_matrix_s, (verts - tri3_src).T)
    cartesian_co = np_dot(barycentric_co.T, matrix_transform_d) + tri3_dest

    return cartesian_co


class OutputData():
    def __init__(self):
        self.verts_out = []
        self.faces_out = []
        self.face_data_out = []
        self.vert_recpt_idx_out = []
        self.face_recpt_idx_out = []

class RecptFaceData():
    def __init__(self):
        self.vertices_co = []
        self.vertices_normal = []
        self.vertices_idxs = []
        self.index = 0
        self.normal = None
        self.normal_mode = None
        self.center = None
        self.frame_width = None

    def copy(self):
        r = RecptFaceData()
        r.vertices_co = self.vertices_co[:]
        r.vertices_normal = self.vertices_normal[:]
        r.vertices_idxs = self.vertices_idxs[:]
        r.normal = self.normal
        r.normal_mode = self.normal_mode
        r.center = self.center
        r.frame_width = self.frame_width
        r.index = self.index
        return r

class DonorData():
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


class SvAdaptivePolygonsNodeMk3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Tessellate Tissue
    Tooltip: Generate an adapted copy of donor object along each face of recipient object.
    """
    bl_idname = 'SvAdaptivePolygonsNodeMk3'
    bl_label = 'Adaptive Polygons'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ADAPTATIVE_POLS'

    axes = [
            ("X", "X", "Orient donor's X axis along normal", 0),
            ("Y", "Y", "Orient donor's Y axis along normal", 1),
            ("Z", "Z", "Orient donor's Z axis along normal", 2)
        ]

    normal_axis: EnumProperty(
        name="Normal axis",
        description="Donor object axis to be oriented along recipient face normal",
        items=axes,
        default='Z',
        update=updateNode)

    width_coef: FloatProperty(
        name='Width coeff',
        description="Donor object width coefficient",
        default=1.0, max=3.0, min=0.5, update=updateNode)

    frame_width: FloatProperty(
        name='Frame width',
        description="Frame width coefficient for Frame / Fan mode",
        default=0.5, max=1.0, min=0.0, update=updateNode)

    z_coef: FloatProperty(
        name='Z coeff',
        default=1.0, max=3.0, min=0.0, update=updateNode)

    z_offset: FloatProperty(
        name="Z offet",
        default=0.0,
        update=updateNode)

    normal_interp_modes = [
            ("LINEAR", "Linear", "Exact / linear normals interpolation", 0),
            ("SMOOTH", "Unit length", "Use normals of unit length", 1)
        ]

    normal_interp_mode: EnumProperty(
        name="Interpolate normals",
        description="Normals interpolation mode",
        items=normal_interp_modes, default="LINEAR",
        update=updateNode)

    normal_modes = [
            ("MAP", "Map", "Interpolate from donor vertex normals", 0),
            ("FACE", "Face", "Use donor face normals", 1)
        ]
    implementation_modes = [
            ("NumPy", "NumPy", "Faster when donor has more than 50 vertices for tris or 12 verts for quads", 0),
            ("Mathutils", "Mathutils", "Faster when donor has less than 50 vertices for tris or 12 verts for quads ", 1),
            ("Auto", "Auto", "Switched between Mathutils and NumPy implementation depending on donor vert count", 2)
        ]

    normal_mode: EnumProperty(
        name="Use normals",
        description="Normals mapping mode",
        items=normal_modes, default="MAP",
        update=updateNode)

    use_shell_factor: BoolProperty(
        name="Use shell factor",
        description="Use shell factor to make shell thickness constant",
        default=False,
        update=updateNode)

    implementation: EnumProperty(
        name="Implementation",
        description="Algorithm used for computation",
        items=implementation_modes, default="Auto",
        update=updateNode)

    z_scale_modes = [
            ("PROP", "Proportional", "Scale along normal proportionally with the donor object", 0),
            ("CONST", "Constant", "Constant scale along normal", 1),
            ("AUTO", "Auto", "Try to calculate the correct scale automatically", 2)
        ]

    z_scale: EnumProperty(
        name="Z Scale",
        description="Mode of scaling along the normals",
        items=z_scale_modes, default="PROP",
        update=updateNode)

    z_rotation: FloatProperty(
        name="Z Rotation",
        description="Rotate donor object around recipient's face normal",
        min=0, max=2*pi, default=0,
        update=updateNode)

    poly_rotation: IntProperty(
        name="Polygons rotation",
        description="Rotate indexes in polygons definition",
        min=0, default=0,
        update=updateNode)

    donor_index: IntProperty(
        name="Donor Index",
        description="Donor index to use",
        min=0, default=0,
        update=updateNode)

    xy_modes = [
            ("BOUNDS", "Bounds", "Map donor object bounds to recipient face", 0),
            ("PLAIN", "As Is", "Map donor object's coordinate space to recipient face as-is", 1)
        ]

    xy_mode: EnumProperty(
        name="Coordinates",
        description="Donor object coordinates mapping",
        items=xy_modes, default="BOUNDS",
        update=updateNode)

    tri_bound_modes = [
            ("EQUILATERAL", "Equilateral", "Use unit-sided equilateral triangle as a base area",
                custom_icon("SV_EQUILATERAL_TRIANGLE"), 0),
            ("RECTANGULAR", "Rectangular", "Use rectangular triangle with hypotenuse of 2 as a base area",
                custom_icon("SV_RECTANGULAR_TRIANGLE"), 1)
        ]

    tri_bound_mode: EnumProperty(
        name="Bounding triangle",
        description="Type of triangle to use as a bounding triangle",
        items=tri_bound_modes,
        default="EQUILATERAL",
        update=updateNode)

    transform_modes = [("SKIP", "Skip", "Don't Output Anything", 0),
                       ("ASIS", "As Is", "Output the receiver face", 1),
                       ("TRI", "Tris", "Perform Tris Transform", 2),
                       ("QUAD", "Quads", "Perform Quad Transform", 3),
                       ("FAN", "Fan", "Perform Fan Transform", 4),
                       ("SUB_QUADS", "SubQuads", "Divides the face in 4 + Quad Transform", 5),
                       ("FRAME", "Frame", "Perform Frame Transform", 6),
                       ("FRAME_FAN", "Auto Frame Fan", "Perform Frame transform if Frame With is lower than 1 otherwise perform Fan", 7),
                       ("FRAME_QUADS", "Auto Frame Sub Quads", "Frame transform if Frame With is lower than 1 otherwise perform Sub Quads transform", 8),
                       ("FAN_QUAD", "Fan (Quad)", "Fan Subdivision + Quad Transform", 9),
                       ("FRAME_TRI", "Frame (Tri)", "Frame Subdivision + Tri Transform", 10),
                       ("SUB_QUADS_TRI", "Sub Quads (Tri)", "Quads Subdivision + Tri Transform", 11),
                       ]

    transform_description = ''.join([f'{p[3]} = {p[1]} ({p[2]})\n' for p in transform_modes])
    transform_dict = {p[0]: p[3] for p in transform_modes}

    @throttle_and_update_node
    def update_sockets(self, context):
        show_width = self.mask_mode == 'TRANSFORM' or 'FRAME' in self.quads_as or 'FRAME'in self.tris_as or 'FRAME'in self.ngons_as
        self.inputs['FrameWidth'].hide_safe = not show_width
        self.inputs['Threshold'].hide_safe = not self.join or not self.remove_doubles
        self.inputs['Donor Index'].hide_safe = self.donor_matching_mode != "INDEX"
        if self.mask_mode == 'TRANSFORM':
            self.inputs['PolyMask'].prop_name = 'transform_mask'
            self.inputs['PolyMask'].label ='Transform Mode'
        else:
            self.inputs['PolyMask'].prop_name = ''
            self.inputs['PolyMask'].label ='Polygon Mask'

    skip_modes = [
            ("SKIP", "Skip", "Do not output anything", 0),
            ("ASIS", "As Is", "Output these faces as is", 1),
            ("TRANSFORM", "Transform Control", transform_description, 2)
        ]

    mask_mode: EnumProperty(
        name="Mask mode",
        description="What to do with masked out faces",
        items=skip_modes, default="SKIP",
        update=update_sockets)

    matching_modes = [
            ("LONG", "Match longest", "Make an iteration for each donor or recipient object - depending on which list is longer", 0),
            ("PERFACE", "Donor per face", "If there are many donor objects, match each donor object with corresponding recipient object face", 1)
        ]

    matching_mode: EnumProperty(
        name="Matching",
        description="How to match list of recipient objects with list of donor objects",
        items=matching_modes, default="LONG",
        update=update_sockets)

    donor_matching_modes = numpy_list_match_modes[1:] + [("INDEX", "By Index", "Specify donor index with input", 4)]

    donor_matching_mode: EnumProperty(
        name="Donor Matching",
        description="How to match list of recipient objects with list of donor objects",
        items=donor_matching_modes, default="REPEAT",
        update=update_sockets)

    tris_as: EnumProperty(
        name="Tris Transform",
        description="How to transform on triangular faces",
        items=transform_modes, default="TRI",
        update=update_sockets
    )
    quads_as: EnumProperty(
        name="Quad Transform",
        description="How to transform on triangular faces",
        items=transform_modes, default="QUAD",
        update=update_sockets
    )
    ngons_as: EnumProperty(
        name="Ngons Transform",
        description="How to transform on triangular faces",
        items=transform_modes, default="FRAME",
        update=update_sockets
    )

    transform_mask: EnumProperty(
        name="Transform",
        description="Transform method:\n"+ transform_description + 'Selected',
        items=transform_modes, default="QUAD",
        update=update_sockets
    )
    join: BoolProperty(
        name="Join",
        description="Output one joined mesh",
        default=False,
        update=updateNode)

    remove_doubles: BoolProperty(
        name="Remove doubles",
        description="Merge vertices at the same location",
        default=False,
        update=update_sockets)

    threshold: FloatProperty(
        name="Threshold",
        description="Threshold for vertices to be considered as identical",
        precision=4, min=0,
        default=1e-4,
        update=updateNode)

    output_numpy: BoolProperty(
        name="Output Numpy",
        description="Output Arrays",
        default=False,
        update=update_sockets)

    tri_vert_idxs = [0, 1, 2]
    quad_vert_idxs = [0, 1, 2, -1]

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvVerticesSocket', "Vertices Recipient")
        self.inputs.new('SvStringsSocket', "Polygons Recipient")
        self.inputs.new('SvVerticesSocket', "Vertices Donor")
        self.inputs.new('SvStringsSocket', "Polygons Donor")
        self.inputs.new('SvStringsSocket', "FaceData Donor")
        self.inputs.new('SvStringsSocket', "W_Coef").prop_name = 'width_coef'
        self.inputs.new('SvStringsSocket', "FrameWidth").prop_name = 'frame_width'
        self.inputs.new('SvStringsSocket', "Z_Coef").prop_name = 'z_coef'
        self.inputs.new('SvStringsSocket', "Z_Offset").prop_name = 'z_offset'
        self.inputs.new('SvStringsSocket', "Z_Rotation").prop_name = 'z_rotation'
        self.inputs.new('SvStringsSocket', "PolyRotation").prop_name = 'poly_rotation'
        mask = self.inputs.new('SvStringsSocket', "PolyMask")
        mask.label = 'Polygon Mask'
        mask.custom_draw = 'draw_enum_socket'
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "Donor Index").prop_name = 'donor_index'
        nm = self.inputs.new('SvStringsSocket', "Normal Mode")
        nm.prop_name = 'normal_mode'
        nm.label = 'Normal Mode'
        nm.custom_draw = 'draw_enum_socket'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Polygons")
        self.outputs.new('SvStringsSocket', "FaceData")
        self.outputs.new('SvStringsSocket', "VertRecptIdx")
        self.outputs.new('SvStringsSocket', "FaceRecptIdx")

        self.update_sockets(context)

    def draw_enum_socket(self, socket, context, layout):

        if socket.is_linked:
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        elif socket.prop_name:
            enum_split(layout, self, socket.prop_name, socket.label, 0.45)

        else:
            layout.label(text=socket.label)

    def draw_buttons(self, context, layout):
        join_row = layout.split(factor=0.45)
        join_row.prop(self, "join")
        if self.join:
            join_row.prop(self, "remove_doubles", text='Merge Doubles')
        enum_split(layout, self, 'matching_mode', 'Matching Mode', 0.45)
        # layout.prop(self, "matching_mode")
        if self.matching_mode == 'PERFACE':
            enum_split(layout, self, 'donor_matching_mode', 'Donor Matching', 0.45)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

        layout.label(text="Normal axis:")
        layout.prop(self, "normal_axis", expand=True)
        layout.prop(self, "z_scale")
        layout.prop(self, "normal_interp_mode")
        layout.prop(self, "use_shell_factor")
        layout.prop(self, "xy_mode")
        layout.label(text="Bounding triangle:")
        layout.prop(self, "tri_bound_mode", expand=True)
        layout.prop(self, "mask_mode")
        if self.mask_mode != 'TRANSFORM':
            b = layout.box()
            b.label(text="Transform:")
            b.prop(self, 'tris_as', text="Tris as")
            b.prop(self, 'quads_as', text="Quads as")
            b.prop(self, 'ngons_as', text="NGons as")
        layout.prop(self, "implementation")
        if not self.join:
            layout.prop(self, "output_numpy")

    def migrate_from(self, old_node):
        if old_node.map_mode == 'QUADTRI':
            self.tris_as = 'TRI'
            self.quads_as = 'QUAD'
        else:
            self.tris_as = 'QUAD'
            self.quads_as = 'QUAD'
        if old_node.frame_mode == 'ALWAYS':
            self.tris_as = 'FRAME'
            self.quads_as = 'FRAME'
            self.ngons_as = 'FRAME'
        elif old_node.frame_mode == 'NGONQUAD':
            self.quads_as = 'FRAME'
            self.ngons_as = 'FRAME'
        elif old_node.frame_mode == 'NGONS':
            self.ngons_as = 'FRAME'
        else:
            if old_node.ngon_mode == 'QUADS':
                self.ngons_as = 'QUAD'
            elif old_node.ngon_mode == 'ASIS':
                self.ngons_as = 'ASIS'
            else:
                self.ngons_as = 'SKIP'




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

        if self.normal_axis == 'Y':
            return triangle_direction_1.xzy, triangle_direction_2.xzy, triangle_direction_3.xzy

        return triangle_direction_1, triangle_direction_2, triangle_direction_3

    def to2d(self, vec):
        """
        Convert vector to 2D.
        Remove the coordinate which is responsible for normal axis.
        """
        if self.normal_axis == 'X':
            return vec.yz
        if self.normal_axis == 'Y':
            return vec.xz

        return vec.xy

    def from2d(self, x_co, y_co):
        """
        Make 3D vector from X and Y.
        Add zero for the coordinate which is responsible for normal axis.
        """
        if self.normal_axis == 'X':
            return Vector((0, x_co, y_co))
        if self.normal_axis == 'Y':
            return Vector((x_co, 0, y_co))

        return Vector((x_co, y_co, 0))

    def bounding_triangle(self, vertices):
        """
        Return three vertices of a triangle with equal sides / rectangular triangle,
        which contains all provided vertices.
        """
        X, Y = self.get_other_axes()

        triangle_direction_1, triangle_direction_2, triangle_direction_3 = self.get_triangle_directions()
        max_1 = self.to2d(max(vertices, key=lambda vertex: triangle_direction_1.dot(vertex)))
        max_2 = self.to2d(max(vertices, key=lambda vertex: triangle_direction_2.dot(vertex)))
        max_3 = self.to2d(min(vertices, key=lambda vertex: vertex[Y]))

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
        v12 = dst_vert_1 + (dst_vert_2 - dst_vert_1) * v[X] * x_coef + ((dst_vert_2 - dst_vert_1) / 2)
        v43 = dst_vert_4 + (dst_vert_3 - dst_vert_4) * v[X] * x_coef + ((dst_vert_3 - dst_vert_4) / 2)
        return v12 + (v43 - v12) * v[Y] * y_coef + ((v43 - v12) / 2)

    def interpolate_quad_3d(self, dst_vert_1, dst_vert_2, dst_vert_3, dst_vert_4,
                            dst_normal_1, dst_normal_2, dst_normal_3, dst_normal_4,
                            face_normal, normal_mode,
                            v,
                            x_coef, y_coef, z_coef, z_offset):
        """
        Map the provided `v` vertex from the source
        [-1/2; 1/2] x [-1/2; 1/2] x [-1/2; 1/2] cube
        to the space defined by `dst_vert_n` vertices.
        """
        loc = self.interpolate_quad_2d(dst_vert_1,
                                       dst_vert_2,
                                       dst_vert_3,
                                       dst_vert_4,
                                       v, x_coef, y_coef)
        if normal_mode:
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_quad_2d(dst_normal_1,
                                                  dst_normal_2,
                                                  dst_normal_3,
                                                  dst_normal_4,
                                                  v, x_coef, y_coef)
                normal.normalize()
            else:
                normal = self.interpolate_quad_2d(dst_vert_1 + dst_normal_1,
                                                  dst_vert_2 + dst_normal_2,
                                                  dst_vert_3 + dst_normal_3,
                                                  dst_vert_4 + dst_normal_4,
                                                  v, x_coef, y_coef)
                normal = normal - loc
        else:

            normal = face_normal
        Z = self.normal_axis_idx()
        return loc + normal * (v[Z] * z_coef + z_offset)

    def interpolate_quad_2d_np(self, dst_verts, verts, x_coef, y_coef):
        """
        Map the provided `v` vertex, considering only two of it's coordinates,
        from the [-1/2; 1/2] x [-1/2; 1/2] square to the face defined by
        four `dst_vert_n` vertices.
        """
        dst_vert_1, dst_vert_2, dst_vert_3, dst_vert_4 = dst_verts
        X, Y = self.get_other_axes()
        v10 = dst_vert_1 + ((dst_vert_2-dst_vert_1)/2)
        v02 = (dst_vert_2 - dst_vert_1)[np_newaxis] * (verts[:, X] * x_coef)[:, np_newaxis]
        v12 = v10 + v02


        v40 = dst_vert_4 + ((dst_vert_3-dst_vert_4)/2)
        v03 = (dst_vert_3 - dst_vert_4)[np_newaxis] * (verts[:, X] * x_coef)[:, np_newaxis]
        v43 = v40 + v03

        return v12  + ((v43-v12)/2) + (v43-v12) * (verts[:, Y] * y_coef)[:, np_newaxis]

    def interpolate_quad_3d_np(self, recpt_face_data, verts, w_coef, z_coef, z_offset, indexes):
        """
        Map the provided `v` vertex from the source
        [-1/2; 1/2] x [-1/2; 1/2] x [-1/2; 1/2] cube
        to the space defined by `dst_vert_n` vertices.
        """
        dst_verts = np_array(recpt_face_data.vertices_co)[indexes]
        dst_normals = np_array(recpt_face_data.vertices_normal)[indexes]
        face_normal = np_array(recpt_face_data.normal)
        x_coef = y_coef = w_coef
        loc = self.interpolate_quad_2d_np(dst_verts, verts, x_coef, y_coef)
        if recpt_face_data.normal_mode:
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_quad_2d_np(dst_normals, verts, x_coef, y_coef)
                np_normalize_vectors(normal)
            else:
                normal = self.interpolate_quad_2d_np(dst_verts + dst_normals, verts, x_coef, y_coef)
                normal = normal - loc
        else:

            normal = face_normal[np_newaxis, :]
        Z = self.normal_axis_idx()

        return loc + normal * (verts[:, Z] * z_coef + z_offset)[:, np_newaxis]

    def interpolate_tri_2d(self, dst_vert_1, dst_vert_2, dst_vert_3,
                           src_vert_1, src_vert_2, src_vert_3,
                           v):
        """
        Map the provided `v` vertex, considering only two of it's coordinates,
        from the source triangle (defined by `src_vert_n` vertices) to the face defined by
        three `dst_vert_n` vertices.
        """
        X, Y = self.get_other_axes()
        v = self.from2d(v[X], v[Y])
        return barycentric_transform(v, src_vert_1, src_vert_2, src_vert_3,
                                        dst_vert_1, dst_vert_2, dst_vert_3)

    def interpolate_tri_3d(self, dst_vert_1, dst_vert_2, dst_vert_3,
                           dst_normal_1, dst_normal_2, dst_normal_3,
                           src_vert_1, src_vert_2, src_vert_3,
                           face_normal, normal_mode,
                           v, z_coef, z_offset):
        """
        Map the provided `v` vertex from the source triangle
        to the space defined by `dst_vert_n` vertices.
        """
        v_at_triangle = self.interpolate_tri_2d(dst_vert_1, dst_vert_2, dst_vert_3,
                                                src_vert_1, src_vert_2, src_vert_3,
                                                v)
        if normal_mode:
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_tri_2d(dst_normal_1, dst_normal_2, dst_normal_3,
                                                 src_vert_1, src_vert_2, src_vert_3,
                                                 v)
                normal.normalize()
            else:
                normal = self.interpolate_tri_2d(dst_vert_1 + dst_normal_1,
                                                 dst_vert_2 + dst_normal_2,
                                                 dst_vert_3 + dst_normal_3,
                                                 src_vert_1, src_vert_2, src_vert_3,
                                                 v)
                normal = normal - v_at_triangle
        else:
            normal = face_normal
        Z = self.normal_axis_idx()
        return (v_at_triangle + normal * (v[Z] * z_coef + z_offset))[:]

    def interpolate_tri_2d_np(self, dst_verts, src_verts, verts):
        """
        Map the provided `v` vertex, considering only two of it's coordinates,
        from the source triangle (defined by `src_vert_n` vertices) to the face defined by
        three `dst_vert_n` vertices.
        """
        Z = self.normal_axis_idx()
        v2d = np_array(verts)
        v2d[:, Z] *= 0
        return barycentric_transform_np(v2d, src_verts, dst_verts)

    def interpolate_tri_3d_np(self, recpt_face_data, donor, wcoef, z_coef, z_offset, indexes):
        """
        Map the provided `vecs` vertex from the source triangle
        to the space defined by `dst_vert_n` vertices.
        """
        dst_verts = np_array(recpt_face_data.vertices_co)[indexes]
        src_verts = np_array([donor.tri_vert_1, donor.tri_vert_2, donor.tri_vert_3])/wcoef
        vecs = donor.verts_v
        v_at_triangle = self.interpolate_tri_2d_np(dst_verts,
                                                   src_verts,
                                                   vecs)
        if recpt_face_data.normal_mode:
            dst_normals = np_array(recpt_face_data.vertices_normal)[indexes]
            if self.normal_interp_mode == 'SMOOTH':
                normal = self.interpolate_tri_2d_np(dst_normals,
                                                    src_verts,
                                                    vecs)
                np_normalize_vectors(normal)
            else:
                normal = self.interpolate_tri_2d_np(dst_verts + dst_normals,
                                                    src_verts,
                                                    vecs)
                normal = normal - v_at_triangle
        else:
            normal = np_array(recpt_face_data.normal)

        Z = self.normal_axis_idx()
        return v_at_triangle + normal * (vecs[:, Z] * z_coef + z_offset)[:, np_newaxis]

    def get_other_axes(self):
        if self.normal_axis == 'X':
            return 1, 2
        if self.normal_axis == 'Y':
            return 0, 2

        return 0, 1

    def normal_axis_idx(self):
        return "XYZ".index(self.normal_axis)

    def map_bounds(self, min_v, max_v, x):
        c = (min_v + max_v) / 2.0
        k = 1.0 / (max_v - min_v)
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

    def interpolate_quads(self, recpt_face_data, donor, wcoef, zcoef, zoffset, X, Y, Z, i0, i1, i2, i3):
        new_verts=[]

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
                                recpt_face_data.normal_mode,
                                v,
                                wcoef, wcoef,
                                zcoef, zoffset)[:])
        return new_verts

    def interpolate_tris(self, recpt_face_data, donor, wcoef, zcoef, zoffset, i0, i1, i2):
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
                                recpt_face_data.normal, recpt_face_data.normal_mode,
                                v, zcoef, zoffset))
        return new_verts

    def verts_of_unit_triangle(self, donor):
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

    def process_as_fan(self, sub_map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot):
        n = len(recpt_face_data.vertices_co)
        tri_faces = [(recpt_face_data.vertices_co[i],
                      recpt_face_data.vertices_co[i+1],
                      recpt_face_data.center) for i in range(n-1)]
        tri_faces.append((recpt_face_data.vertices_co[-1],
                          recpt_face_data.vertices_co[0],
                          recpt_face_data.center))

        if self.use_shell_factor:
            face_normal = sum(recpt_face_data.vertices_normal, Vector()) / n
        else:
            face_normal = recpt_face_data.normal
        tri_normals = [(recpt_face_data.vertices_normal[i],
                        recpt_face_data.vertices_normal[i+1],
                        face_normal) for i in range(n-1)]
        tri_normals.append((recpt_face_data.vertices_normal[-1],
                            recpt_face_data.vertices_normal[0],
                            face_normal))

        for tri_face, tri_normal in zip(tri_faces, tri_normals):
            sub_recpt = recpt_face_data.copy()
            sub_recpt.vertices_co = tri_face
            sub_recpt.vertices_normal = tri_normal
            sub_recpt.vertices_idxs = [0, 1, 2]
            self._process_face(sub_map_mode, output, sub_recpt, donor, zcoef, zoffset, angle, wcoef, facerot)

    def process_as_sub_quads(self, sub_map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot):
        n = len(recpt_face_data.vertices_co)
        quad_faces = [(recpt_face_data.vertices_co[i],
                      (recpt_face_data.vertices_co[(i+1)%n] + recpt_face_data.vertices_co[i])/2,
                      recpt_face_data.center,
                      (recpt_face_data.vertices_co[(i+n-1)%n] + recpt_face_data.vertices_co[i])/2)
                      for i in range(n)]

        if self.use_shell_factor:
            face_normal = sum(recpt_face_data.vertices_normal, Vector()) / n
        else:
            face_normal = recpt_face_data.normal
        quad_normals = [(recpt_face_data.vertices_normal[i],
                        (recpt_face_data.vertices_normal[i]+recpt_face_data.vertices_normal[(i+1)%n])/2,
                        face_normal,
                        (recpt_face_data.vertices_normal[i]+recpt_face_data.vertices_normal[(i+n-1)%n])/2,
                        ) for i in range(n)]

        for quad_face, quad_normal in zip(quad_faces, quad_normals):
            sub_recpt = recpt_face_data.copy()
            sub_recpt.vertices_co = quad_face
            sub_recpt.vertices_normal = quad_normal
            sub_recpt.vertices_idxs = [0, 1, 2, 3]
            self._process_face(sub_map_mode, output, sub_recpt, donor, zcoef, zoffset, angle, wcoef, facerot)

    def process_as_frame_quads(self, sub_map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot):
        n = len(recpt_face_data.vertices_co)
        inner_verts = [vert.lerp(recpt_face_data.center, recpt_face_data.frame_width)
                       for vert in recpt_face_data.vertices_co]
        if self.use_shell_factor:
            inner_normals = [normal.lerp(recpt_face_data.normal, recpt_face_data.frame_width)
                             for normal in recpt_face_data.vertices_normal]
        else:
            face_normal = sum(recpt_face_data.vertices_normal, Vector()) / n
            inner_normals = [normal.lerp(face_normal, recpt_face_data.frame_width)
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

    def _process_face(self, map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot):

        X, Y = self.get_other_axes()
        Z = self.normal_axis_idx()

        output_numpy = self.output_numpy and not self.join


        if map_mode == 'TRI':
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

            if self.implementation == 'NumPy' or (self.implementation == 'Auto' and len(donor.verts_v) > 50):
                new_verts = self.interpolate_tri_3d_np(recpt_face_data, donor,
                                                       wcoef, zcoef, zoffset,
                                                       [i0, i1, i2])
                output.verts_out.append(new_verts if output_numpy else new_verts.tolist())
            else:
                new_verts = self.interpolate_tris(recpt_face_data, donor,
                                                  wcoef, zcoef, zoffset,
                                                  i0, i1, i2)
                output.verts_out.append(np_array(new_verts) if output_numpy else new_verts)
            output.faces_out.append(donor.faces_i)
            output.face_data_out.append(donor.face_data_i)
            output.vert_recpt_idx_out.append([recpt_face_data.index for i in new_verts])
            output.face_recpt_idx_out.append([recpt_face_data.index for i in donor.faces_i])

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

            if self.implementation == 'NumPy' or (self.implementation == 'Auto' and len(donor.verts_v) > 12):
                verts = donor.verts_v

                new_verts = self.interpolate_quad_3d_np(recpt_face_data, verts,
                                                        wcoef, zcoef, zoffset,
                                                        [i0, i1, i2, i3])

                output.verts_out.append(new_verts if output_numpy else new_verts.tolist())
            else:
                new_verts = self.interpolate_quads(recpt_face_data, donor,
                                                   wcoef, zcoef, zoffset,
                                                   X, Y, Z,
                                                   i0, i1, i2, i3)
                output.verts_out.append(np_array(new_verts) if output_numpy else new_verts)

            output.faces_out.append(donor.faces_i)
            output.face_data_out.append(donor.face_data_i)
            output.vert_recpt_idx_out.append([recpt_face_data.index for i in new_verts])
            output.face_recpt_idx_out.append([recpt_face_data.index for i in donor.faces_i])

        elif map_mode == 'FRAME':
            self.process_as_frame_quads('QUAD', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'FRAME_TRI':
            self.process_as_frame_quads('TRI', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'FAN':
            self.process_as_fan('TRI', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'FAN_QUAD':
            self.process_as_fan('QUAD', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'SUB_QUADS':
            self.process_as_sub_quads('QUAD', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'SUB_QUADS_TRI':
            self.process_as_sub_quads('TRI', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'FRAME_FAN':
            is_fan = abs(recpt_face_data.frame_width - 1.0) < 1e-6

            if is_fan:
                self.process_as_fan('TRI', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)

            else:
                self.process_as_frame_quads('QUAD', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
        elif map_mode == 'FRAME_QUADS':
            is_sub_quads = abs(recpt_face_data.frame_width - 1.0) < 1e-6

            if is_fan:
                self.process_as_sub_quads('QUAD', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)

            else:
                self.process_as_frame_quads('QUAD', output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)


    def get_map_mode(self, mask, sides_n):
        if self.mask_mode == 'TRANSFORM':
            return  self.transform_modes[mask][0]
        if not mask:
            return  self.mask_mode

        if sides_n == 3:
            return self.tris_as

        if sides_n == 4:
            return self.quads_as

        return self.ngons_as


    def _process(self, verts_recpt, faces_recpt, verts_donor, faces_donor, face_data_donor, frame_widths, zcoefs, zoffsets, zrotations, wcoefs, facerots, mask, single_donor, donor_index, normal_mode):
        bm = bmesh_from_pydata(verts_recpt, [], faces_recpt, normal_update=True)
        bm_verts = bm.verts
        bm_verts.ensure_lookup_table()

        if single_donor:
            # Original (unrotated) donor vertices
            donor_verts_o = [Vector(v) for v in verts_donor]

            verts_donor = [verts_donor]
            faces_donor = [faces_donor]
            face_data_donor = [face_data_donor]

        if self.matching_mode == 'LONG':
            verts_donor_match, faces_donor_match, face_data_match = make_repeaters([verts_donor, faces_donor, face_data_donor])
        else:
            if self.donor_matching_mode == 'REPEAT':
                verts_donor_match, faces_donor_match, face_data_match = make_repeaters([verts_donor, faces_donor, face_data_donor])
            elif  self.donor_matching_mode == 'CYCLE':
                verts_donor_match, faces_donor_match, face_data_match = make_cyclers([verts_donor, faces_donor, face_data_donor])
            else:
                verts_donor_match, faces_donor_match, face_data_match = [], [], []
                if not face_data_donor[0]:
                    face_data_match = cycle([[]])
                n_faces_recpt = len(faces_recpt)
                for i, idx in zip(range(n_faces_recpt), cycle(donor_index)):
                    idx_f = idx%(n_faces_recpt-1)
                    verts_donor_match.append(verts_donor[idx % len(verts_donor)])
                    faces_donor_match.append(faces_donor[idx % len(faces_donor)])
                    if face_data_donor[0]:
                        face_data_match.append(face_data_donor[idx % len(face_data_donor)])



        X, Y = self.get_other_axes()
        Z = self.normal_axis_idx()

        donor = DonorData()
        self.verts_of_unit_triangle(donor)

        if single_donor:
            # We will be rotating the donor object around Z axis,
            # so it's size along Z is not going to change.
            z_size = diameter(donor_verts_o, Z)

        output = OutputData()

        prev_angle = None
        face_data = zip(faces_recpt, bm.faces, frame_widths, verts_donor_match, faces_donor_match, face_data_match, zcoefs, zoffsets, zrotations, wcoefs, facerots, mask, normal_mode)
        recpt_face_idx = 0
        for recpt_face, recpt_face_bm, frame_width, donor_verts_i, donor_faces_i, donor_face_data_i, zcoef, zoffset, angle, wcoef, facerot, m, n_mode in face_data:
            sides_n = len(recpt_face)
            map_mode = self.get_map_mode(m, sides_n)

            if map_mode == 'SKIP':
                continue
            if map_mode == 'ASIS':
                # Leave this recipient's face as it was - as a single face.
                verts = [verts_recpt[i] for i in recpt_face]
                output.verts_out.append(verts)
                output.faces_out.append([list(range(sides_n))])
                output.vert_recpt_idx_out.append([recpt_face_idx for i in verts])
                output.face_recpt_idx_out.append([recpt_face_idx for i in range(sides_n)])
                continue

            recpt_face_data = RecptFaceData()
            recpt_face_data.index = recpt_face_idx
            recpt_face_data.normal = recpt_face_bm.normal
            recpt_face_data.normal_mode = n_mode
            recpt_face_data.center = recpt_face_bm.calc_center_median()
            recpt_face_data.vertices_co = [bm_verts[i].co for i in recpt_face]
            if self.use_shell_factor:
                recpt_face_data.vertices_normal = [bm_verts[i].normal * bm_verts[i].calc_shell_factor() for i in recpt_face]
            else:
                recpt_face_data.vertices_normal = [bm_verts[i].normal for i in recpt_face]
            recpt_face_data.vertices_idxs = recpt_face[:]
            if not isinstance(frame_width, (int, float)):
                raise Exception(f"Unexpected data type for frame_width: {frame_width}")
            recpt_face_data.frame_width = frame_width

            donor.faces_i = donor_faces_i
            donor.face_data_i = donor_face_data_i


            is_fan = abs(frame_width - 1.0) < 1e-6
            is_tri = map_mode in ['TRI', 'FAN', 'SUB_QUADS_TRI', 'FRAME_TRI'] or (map_mode == 'FRAME_FAN' and is_fan)
            if self.implementation == 'Auto':
                numpy_candidate = len(donor_verts_i) > (50 if is_tri else 12)
            else:
                numpy_candidate = False
            numpy_mode = self.implementation == 'NumPy' or (numpy_candidate)
            if not single_donor:
                # Original (unrotated) donor vertices
                donor_verts_o = [Vector(v) for v in donor_verts_i]
                z_size = diameter(donor_verts_o, Z)

            # We have to recalculate rotated vertices only if
            # the rotation angle have changed.
            if prev_angle is None or angle != prev_angle or not single_donor:
                verts_v = self.rotate_z(donor_verts_o, angle)
                np_verts = np_array(verts_v)
                if numpy_mode:
                    donor.verts_v = np_verts
                else:
                    donor.verts_v = verts_v

                if self.xy_mode == 'BOUNDS' or self.z_scale == 'AUTO' :
                    donor.max_x = np_max(np_verts[:, X])
                    donor.min_x = np_min(np_verts[:, X])

                    donor.max_y = np_max(np_verts[:, Y])
                    donor.min_y = np_min(np_verts[:, Y])

                if self.xy_mode == 'BOUNDS':
                    if single_donor:
                        donor.tri_vert_1, donor.tri_vert_2, donor.tri_vert_3 = self.bounding_triangle(verts_v)
                        if numpy_mode:
                            np_verts[:, X] = self.map_bounds(donor.min_x, donor.max_x, np_verts[:, X])
                            np_verts[:, Y] = self.map_bounds(donor.min_y, donor.max_y, np_verts[:, Y])
                    elif is_tri:
                        donor.tri_vert_1, donor.tri_vert_2, donor.tri_vert_3 = self.bounding_triangle(verts_v)
                    else:
                        if numpy_mode:
                            np_verts[:, X] = self.map_bounds(donor.min_x, donor.max_x, np_verts[:, X])
                            np_verts[:, Y] = self.map_bounds(donor.min_y, donor.max_y, np_verts[:, Y])
            prev_angle = angle

            if self.z_scale == 'CONST':
                if abs(z_size) < 1e-6:
                    zcoef = 0
                else:
                    zcoef = zcoef / z_size


            self._process_face(map_mode, output, recpt_face_data, donor, zcoef, zoffset, angle, wcoef, facerot)
            recpt_face_idx += 1

        bm.free()

        return output

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        verts_recpt_s = self.inputs['Vertices Recipient'].sv_get(deepcopy=False)
        faces_recpt_s = self.inputs['Polygons Recipient'].sv_get(default=[[]], deepcopy=False)
        verts_donor_s = self.inputs['Vertices Donor'].sv_get(deepcopy=False)
        faces_donor_s = self.inputs['Polygons Donor'].sv_get(deepcopy=False)
        face_data_donor_s = self.inputs['FaceData Donor'].sv_get(default=[[]], deepcopy=False)
        zcoefs_s = self.inputs['Z_Coef'].sv_get(deepcopy=False)
        zoffsets_s = self.inputs['Z_Offset'].sv_get(deepcopy=False)
        zrotations_s = self.inputs['Z_Rotation'].sv_get(deepcopy=False)
        wcoefs_s = self.inputs['W_Coef'].sv_get(deepcopy=False)
        frame_widths_s = self.inputs['FrameWidth'].sv_get(deepcopy=False)
        facerots_s = self.inputs['PolyRotation'].sv_get(default=[[0]], deepcopy=False)
        mask_s = self.inputs['PolyMask'].sv_get(default=[[1]], deepcopy=False)
        if isinstance(mask_s[0][0], str):
            mask_s = [[self.transform_dict[mask_s[0][0]]]]

        thresholds_s = self.inputs['Threshold'].sv_get(deepcopy=False)
        donor_index_s = self.inputs['Donor Index'].sv_get(deepcopy=False)
        normal_mode_s = self.inputs['Normal Mode'].sv_get(deepcopy=False, default=[[1 if self.normal_mode == 'MAP' else 0]])

        if isinstance(normal_mode_s[0][0], str):
            normal_mode_s=[[1 if self.normal_mode == 'MAP' else 0]]
        output = OutputData()
        print('normal_mode_s', normal_mode_s)

        single_donor = self.matching_mode == 'LONG' or len(verts_donor_s) < 2
        if not single_donor:
        # if self.matching_mode == 'PERFACE':
            verts_donor_s = [verts_donor_s]
            faces_donor_s = [faces_donor_s]
            face_data_donor_s = [face_data_donor_s]
            #self.info("FW: %s", frame_widths_s)
            #frame_widths_s = [frame_widths_s]
        objects = match_long_repeat([verts_recpt_s, faces_recpt_s,
                                     verts_donor_s, faces_donor_s, face_data_donor_s,
                                     frame_widths_s,
                                     zcoefs_s, zoffsets_s, zrotations_s,
                                     wcoefs_s, facerots_s, mask_s,
                                     thresholds_s,
                                     donor_index_s,
                                     normal_mode_s])
        #self.info("N objects: %s", len(list(zip(*objects))))
        for verts_recpt, faces_recpt, verts_donor,\
            faces_donor, face_data_donor,\
            frame_widths, zcoefs, zoffsets, zrotations, wcoefs, facerots, \
            mask, threshold, donor_index, normal_mode in zip(*objects):
            n_faces_recpt = len(faces_recpt)

            if get_data_nesting_level(frame_widths) < 1:
                frame_widths = [frame_widths]

            zcoefs, zoffsets, zrotations, frame_widths, wcoefs, facerots, normal_mode = make_repeaters([zcoefs, zoffsets, zrotations, frame_widths, wcoefs, facerots, normal_mode])
            mask = cycle_for_length(mask, n_faces_recpt)

            if isinstance(threshold, (list, tuple)):
                threshold = threshold[0]

            new = self._process(verts_recpt, faces_recpt,
                                verts_donor, faces_donor,
                                face_data_donor,
                                frame_widths,
                                zcoefs, zoffsets, zrotations,
                                wcoefs, facerots,
                                mask, single_donor,
                                donor_index,
                                normal_mode)

            output.verts_out.extend(new.verts_out)
            output.faces_out.extend(new.faces_out)
            output.face_data_out.extend(new.face_data_out)
            output.vert_recpt_idx_out.extend(new.vert_recpt_idx_out)
            output.face_recpt_idx_out.extend(new.face_recpt_idx_out)

            # output.verts_out = Vector_degenerate(output.verts_out)
            if self.join:
                output.verts_out, _, output.faces_out = mesh_join(output.verts_out, [], output.faces_out)
                output.face_data_out = sum(output.face_data_out, [])
                output.vert_recpt_idx_out = sum(output.vert_recpt_idx_out, [])
                output.face_recpt_idx_out = sum(output.face_recpt_idx_out, [])

                if self.remove_doubles:
                    doubles_res = remove_doubles(output.verts_out, [], output.faces_out, threshold, face_data=output.face_data_out, vert_data=output.vert_recpt_idx_out)
                    if len(doubles_res) == 4:
                        output.verts_out, _, output.faces_out, data_out = doubles_res
                    else:
                        output.verts_out, _, output.faces_out = doubles_res
                        data_out = dict()
                    output.vert_recpt_idx_out = data_out.get('verts', [])
                    if output.face_recpt_idx_out:
                        output.face_recpt_idx_out = [output.face_recpt_idx_out[idx] for idx in data_out['face_init_index']]

                output.verts_out = [output.verts_out]
                output.faces_out = [output.faces_out]
                output.face_data_out = [output.face_data_out]
                output.vert_recpt_idx_out = [output.vert_recpt_idx_out]
                output.face_recpt_idx_out = [output.face_recpt_idx_out]

            self.outputs['Vertices'].sv_set(output.verts_out)
            self.outputs['Polygons'].sv_set(output.faces_out)
            if 'FaceData' in self.outputs:
                self.outputs['FaceData'].sv_set(output.face_data_out)
            if 'VertRecptIdx' in self.outputs:
                self.outputs['VertRecptIdx'].sv_set(output.vert_recpt_idx_out)
            if 'FaceRecptIdx' in self.outputs:
                self.outputs['FaceRecptIdx'].sv_set(output.face_recpt_idx_out)

def register():
    bpy.utils.register_class(SvAdaptivePolygonsNodeMk3)

def unregister():
    bpy.utils.unregister_class(SvAdaptivePolygonsNodeMk3)
