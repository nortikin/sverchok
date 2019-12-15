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
from sverchok.data_structure import updateNode, match_long_repeat

def mirrorPoint(vertex, vert_a):
    vert = []
    a = Vector(vert_a)
    for i in vertex:
        v = Vector(i)
        vert.append((v + 2 * (a - v))[:])
    return vert

def mirrorAxis(vertex, vert_a, vert_b):
    vert = []
    a = Vector(vert_a)
    b = Vector(vert_b)
    c = b - a
    for i in vertex:
        v = Vector(i)
        #  Intersection point in vector A-B from point V
        pq = v - a
        w2 = pq - ((pq.dot(c) / c.length_squared) * c)
        x = v - w2

        mat = Matrix.Translation(2 * (v - w2 - v))
        mat_rot = Matrix.Rotation(radians(360), 4, c)
        vert.append(((mat @ mat_rot) @ v)[:])
    return vert

def mirrorPlane(vertex, matrix):
    vert = []
    eul = matrix.to_euler()
    normal = Vector((0.0, 0.0, 1.0))
    normal.rotate(eul)
    trans = Matrix.Translation(2 * matrix.to_translation())
    for i in vertex:
        v = Vector(i)
        r = v.reflect(normal)
        vert.append((trans @ r)[:])
    return vert

def mirrorCoordinateAxis(vertex, axis):
    x,y,z = vertex
    if axis == 'X':
        return x, -y, -z
    elif axis == 'Y':
        return -x, y, -z
    elif axis == 'Z':
        return -x, -y, z

def mirrorCoordinatePlane(vertex, plane):
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

        self.inputs['Vert A'].hide_safe = (mode != 'VERTEX' and mode != 'AXIS')
        self.inputs['Vert B'].hide_safe = (mode != 'AXIS')
        self.inputs['Plane'].hide_safe = (mode != 'PLANE')

        updateNode(self, context)

    modes = [
        ("VERTEX", "Vertex", "Mirror aroung vertex", 1),
        ("AXIS", "Axis", "Mirror around axis", 2),
        ("COORDINATE_AXIS", "Coordinate Axis", "Mirror around coordinate axis (X, Y, Z)", 3),
        ("PLANE", "Plane", "Mirror around plane", 4),
        ("COORDINATE_PLANE", "Coordinate Plane", "Mirror around coordinate plane (XY, YZ, XZ)", 5)
    ]

    mode = EnumProperty(name="Mode", description="mode",
                          default='VERTEX', items=modes,
                          update=mode_change)

    axes = [
            ("X", "X", "X axis", 0),
            ("Y", "Y", "Y axis", 1),
            ("Z", "Z", "Z axis", 2)
        ]

    axis = EnumProperty(name = "Axis", description = "Coordinate axis to mirror around",
                        default = 'Z', items = axes,
                        update = updateNode)

    planes = [
            ("XY", "XY", "XY plane", 0),
            ("YZ", "YZ", "YZ plane", 1),
            ("XZ", "XZ", "XZ plane", 2)
        ]

    plane = EnumProperty(name = "Plane", description = "Coordinate plane to mirror around",
                        default = 'XY', items = planes,
                        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvVerticesSocket', "Vert A")
        self.inputs.new('SvVerticesSocket', "Vert B")
        self.inputs.new('SvMatrixSocket', "Plane")
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
        vert_A = self.inputs['Vert A'].sv_get(default=[[[0.0, 0.0, 0.0]]])[0]
        vert_B = self.inputs['Vert B'].sv_get(default=[[[1.0, 0.0, 0.0]]])[0]
        plane = self.inputs['Plane'].sv_get(default=[Matrix()])

        # outputs
        if self.mode == 'VERTEX':
            parameters = match_long_repeat([vertices, vert_A])
            points = [mirrorPoint(v, a) for v, a in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'AXIS':
            parameters = match_long_repeat([vertices, vert_A, vert_B])
            points = [mirrorAxis(v, a, b) for v, a, b in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'PLANE':
            parameters = match_long_repeat([vertices, plane])
            points = [mirrorPlane(v, p) for v, p in zip(*parameters)]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'COORDINATE_AXIS':
            points = [[mirrorCoordinateAxis(v, self.axis) for v in verts] for verts in vertices]
            self.outputs['Vertices'].sv_set(points)
        elif self.mode == 'COORDINATE_PLANE':
            points = [[mirrorCoordinatePlane(v, self.plane) for v in verts] for verts in vertices]
            self.outputs['Vertices'].sv_set(points)

def register():
    bpy.utils.register_class(SvMirrorNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvMirrorNodeMk2)

