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

from node_tree import SverchCustomTreeNode
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType, match_long_repeat

def mirrorPoint(vertex, vert_a):
    vert = []
    a = Vector(vert_a)
    for i in vertex:
        v = Vector(i)
        vert.append((v+2*(a-v))[:])
    return vert

def mirrorAxis(vertex, vert_a, vert_b):
    vert = []
    a = Vector(vert_a)
    b = Vector(vert_b)
    c = b - a
    for i in vertex:
        v = Vector(i)
        #Intersection point in vector A-B from point V
        pq = v - a
        w2 = pq - ((pq.dot(c) / c.length_squared) * c)
        x = v - w2

        mat = Matrix.Translation(2*(v - w2 - v))
        mat_rot = Matrix.Rotation(radians(360), 4, c)
        vert.append(((mat*mat_rot)*v)[:])
    return vert

def mirrorPlane(vertex, matrix):
    vert = []
    a = Matrix(matrix)
    eul = a.to_euler()
    normal = Vector((0.0, 0.0, 1.0))
    normal.rotate(eul)
    tras = Matrix.Translation(2*a.to_translation())
    for i in vertex:
        v = Vector(i)
        r = v.reflect(normal)
        vert.append((tras*r)[:])
    return vert

class SvMirrorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Mirroring  '''
    bl_idname = 'SvMirrorNode'
    bl_label = 'Mirror'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def mode_change(self, context):
        # just because click doesn't mean we need to change mode
        mode = self.mode
        if mode == self.current_mode:
            return

        if mode == 'VERTEX':
            n = 2 if "Vert A" in self.inputs else 1
            while len(self.inputs) > n:
                self.inputs.remove(self.inputs[-1])
            if n == 1:
                self.inputs.new('VerticesSocket', "Vert A", "Vert A")

        if mode == 'AXIS':
            n = 2 if "Vert A" in self.inputs else 1
            if n == 2:
                while len(self.inputs) > n:
                    self.inputs.remove(self.inputs[-1])
                self.inputs.new('VerticesSocket', "Vert B", "Vert B")
            else:
                while len(self.inputs) > n:
                    self.inputs.remove(self.inputs[-1])                
                self.inputs.new('VerticesSocket', "Vert A", "Vert A")
                self.inputs.new('VerticesSocket', "Vert B", "Vert B")

        if mode == 'PLANE':
            while len(self.inputs) > 1:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('MatrixSocket', "Plane", "Plane")

        self.current_mode = mode
        updateNode(self, context)

    modes = [
        ("VERTEX", "Vertex", "Mirror aroung vertex", 1),
        ("AXIS", "Axis", "Mirror around axis", 2),
        ("PLANE", "Plane", "Mirror around plane", 3),
    ]

    mode = EnumProperty(name="mode", description="mode",
                          default='VERTEX', items=modes,
                          update=mode_change)
    current_mode = StringProperty(default="VERTEX")

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('VerticesSocket', "Vert A", "Vert A")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

    def update(self):
        # inputs
        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
            Vertices = SvGetSocketAnyType(self, self.inputs['Vertices'])
        else:
            Vertices = []
        if 'Vert A' in self.inputs and self.inputs['Vert A'].links:
            Vert_A = SvGetSocketAnyType(self, self.inputs['Vert A'])[0]
        else:
            Vert_A = [[0.0, 0.0, 0.0]]
        if 'Vert B' in self.inputs and self.inputs['Vert B'].links:
            Vert_B = SvGetSocketAnyType(self, self.inputs['Vert B'])[0]
        else:
            Vert_B = [[1.0, 0.0, 0.0]]
        if 'Plane' in self.inputs and self.inputs['Plane'].links:
            Plane = SvGetSocketAnyType(self, self.inputs['Plane'])
        else:
            Plane = [Matrix()]

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            if self.mode == 'VERTEX':
                parameters = match_long_repeat([Vertices, Vert_A])
                points = [mirrorPoint(v, a) for v, a in zip(*parameters)]
                SvSetSocketAnyType(self, 'Vertices', points)
            elif self.mode == 'AXIS':
                parameters = match_long_repeat([Vertices, Vert_A, Vert_B])
                points = [mirrorAxis(v, a, b) for v, a, b in zip(*parameters)]
                SvSetSocketAnyType(self, 'Vertices', points)
            elif self.mode == 'PLANE':
                parameters = match_long_repeat([Vertices, Plane])
                points = [mirrorPlane(v, p) for v, p in zip(*parameters)]
                SvSetSocketAnyType(self, 'Vertices', points)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMirrorNode)


def unregister():
    bpy.utils.unregister_class(SvMirrorNode)
