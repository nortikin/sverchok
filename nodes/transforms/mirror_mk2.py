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

from math import radians

from mathutils import Vector, Matrix

import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, zip_long_repeat

def mirror_vertex(vertices, vert_as):
    vert = []
    for i, vert_a in zip_long_repeat(vertices, vert_as):
        v = Vector(i)
        a = Vector(vert_a)
        vert.append((v + 2 * (a - v))[:])
    return vert

def mirror_axis_two_points(vertices, vert_as, vert_bs):
    vert = []
    for i, vert_a, vert_b in zip_long_repeat(vertices, vert_as, vert_bs):
        a = Vector(vert_a)
        b = Vector(vert_b)
        c = b - a
        v = Vector(i)
        #  Intersection point in vector A-B from point V
        pq = v - a
        w2 = pq - ((pq.dot(c) / c.length_squared) * c)
        x = v - w2

        mat = Matrix.Translation(2 * (v - w2 - v))
        mat_rot = Matrix.Rotation(radians(360), 4, c)
        vert.append(((mat @ mat_rot) @ v)[:])
    return vert

def mirror_axis_point_and_direction(vertices, verts, directions):
    vert_bs = [Vector(vert) + Vector(direction) for vert, direction in zip_long_repeat(verts, directions)]
    return mirror_axis_two_points(vertices, verts, vert_bs)

def mirror_plane_matrix(vertices, matrixes):
    vert = []
    if isinstance(matrixes, Matrix):
        matrixes = [matrixes]
    for i, matrix in zip_long_repeat(vertices, matrixes):
        eul = matrix.to_euler()
        normal = Vector((0.0, 0.0, 1.0))
        normal.rotate(eul)
        trans = Matrix.Translation(2 * matrix.to_translation())
        v = Vector(i)
        r = v.reflect(normal)
        vert.append((trans @ r)[:])
    return vert

def mirror_plane_point_and_normal(vertices, points, normals):
    vert = []
    for i, point, normal in zip_long_repeat(vertices, points, normals):
        center = Vector(point)
        n = Vector(normal)
        v = Vector(i)
        r = (v - center).reflect(n) + center
        vert.append(r)
    return vert

def mirror_axis_coordinate(vertex, axis):
    x,y,z = vertex
    if axis == 'X':
        return x, -y, -z
    elif axis == 'Y':
        return -x, y, -z
    elif axis == 'Z':
        return -x, -y, z

def mirror_plane_coordinate(vertex, plane):
    x, y, z = vertex
    if plane == 'XY':
        return x, y, -z
    elif plane == 'XZ':
        return x, -y, z
    elif plane == 'YZ':
        return -x, y, z

class SvMirrorNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    ''' Mirroring, Symmetry'''
    bl_idname = 'SvMirrorNodeMk2'
    bl_label = 'Mirror Mk2'
    bl_icon = 'MOD_MIRROR'

    def mode_change(self, context):
        mode = self.mode

        self.inputs['Vert A'].hide_safe = (mode not in ['VERTEX', 'AXIS2P', 'AXISPD', 'PLANE_N'])
        self.inputs['Vert B'].hide_safe = (mode != 'AXIS2P')
        self.inputs['Plane'].hide_safe = (mode != 'PLANE_M')
        self.inputs['Normal'].hide_safe = (mode != 'PLANE_N')
        self.inputs['Direction'].hide_safe = (mode != 'AXISPD')

        updateNode(self, context)

    modes = [
        ("VERTEX", "Vertex", "Mirror aroung vertex", 1),
        ("AXIS2P", "Axis by 2 points", "Mirror around axis defined by two points", 2),
        ("COORDINATE_AXIS", "Coordinate Axis", "Mirror around coordinate axis (X, Y, Z)", 3),
        ("AXISPD", "Axis by point and direction", "Mirror around axis defined by a point and a direction", 4),
        ("PLANE_M", "Plane by matrix", "Mirror around a plane defined by a matrix", 5),
        ("PLANE_N", "Plane by normal and point", "Mirror around a plane defined by a normal and a point", 6),
        ("COORDINATE_PLANE", "Coordinate plane", "Mirror around coordinate plane (XY, YZ, XZ)", 7)
    ]

    mode : EnumProperty(name="Mode", description="mode",
                          default='VERTEX', items=modes,
                          update=mode_change)

    axes = [
            ("X", "X", "X axis", 0),
            ("Y", "Y", "Y axis", 1),
            ("Z", "Z", "Z axis", 2)
        ]

    axis : EnumProperty(name = "Axis", description = "Coordinate axis to mirror around",
                        default = 'Z', items = axes,
                        update = updateNode)

    planes = [
            ("XY", "XY", "XY plane", 0),
            ("YZ", "YZ", "YZ plane", 1),
            ("XZ", "XZ", "XZ plane", 2)
        ]

    plane : EnumProperty(name = "Plane", description = "Coordinate plane to mirror around",
                        default = 'XY', items = planes,
                        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvVerticesSocket', "Vert A")
        self.inputs.new('SvVerticesSocket', "Vert B")
        self.inputs.new('SvMatrixSocket', "Plane")
        self.inputs.new('SvVerticesSocket', "Normal")
        self.inputs.new('SvVerticesSocket', "Direction")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.mode_change(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')
        if self.mode == 'COORDINATE_AXIS':
            layout.prop(self, "axis", expand=True)
        elif self.mode == 'COORDINATE_PLANE':
            layout.prop(self, "plane", expand=True)

    def process(self):
        if not self.outputs['Vertices'].is_linked:
            return

        vertices = self.inputs['Vertices'].sv_get(default=[])
        vert_A = self.inputs['Vert A'].sv_get(default=[[[0.0, 0.0, 0.0]]])
        vert_B = self.inputs['Vert B'].sv_get(default=[[[1.0, 0.0, 0.0]]])
        plane = self.inputs['Plane'].sv_get(default=[[Matrix()]])
        normal = self.inputs['Normal'].sv_get(default=[[[0.0, 0.0, 1.0]]])
        direction = self.inputs['Direction'].sv_get(default=[[[0.0, 0.0, 1.0]]])

        if self.mode == 'VERTEX':
            parameters = match_long_repeat([vertices, vert_A])
            points = [mirror_vertex(v, a) for v, a in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'AXIS2P':
            parameters = match_long_repeat([vertices, vert_A, vert_B])
            points = [mirror_axis_two_points(v, a, b) for v, a, b in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'AXISPD':
            parameters = match_long_repeat([vertices, vert_A, direction])
            points = [mirror_axis_point_and_direction(v, a, d) for v, a, d in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'PLANE_M':
            parameters = match_long_repeat([vertices, plane])
            points = [mirror_plane_matrix(v, p) for v, p in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'PLANE_N':
            parameters = match_long_repeat([vertices, vert_A, normal])
            points = [mirror_plane_point_and_normal(v, a, n) for v, a, n in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'COORDINATE_AXIS':
            points = [[mirror_axis_coordinate(v, self.axis) for v in verts] for verts in vertices]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'COORDINATE_PLANE':
            points = [[mirror_plane_coordinate(v, self.plane) for v in verts] for verts in vertices]
            self.outputs['Vertices'].sv_set(points)

def register():
    bpy.utils.register_class(SvMirrorNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvMirrorNodeMk2)

