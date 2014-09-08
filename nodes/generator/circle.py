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

from math import sin, cos, pi, degrees, radians

from mathutils import Vector

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import (fullList, match_long_repeat, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class CircleNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Circle '''
    bl_idname = 'CircleNode'
    bl_label = 'Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'

    rad_ = FloatProperty(name='rad_', description='Radius',
                         default=1.0, options={'ANIMATABLE'},
                         update=updateNode)
    vert_ = IntProperty(name='vert_', description='Vertices',
                        default=24, min=3, options={'ANIMATABLE'},
                        update=updateNode)
    degr_ = FloatProperty(name='degr_', description='Degrees',
                          default=360, min=0, max=360,
                          options={'ANIMATABLE'}, update=updateNode)
    mode_ = BoolProperty(name='mode_', description='Mode',
                         default=0, options={'ANIMATABLE'},
                         update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Radius", "Radius")
        self.inputs.new('StringsSocket', "Nº Vertices", "Nº Vertices")
        self.inputs.new('StringsSocket', "Degrees", "Degrees")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "rad_", text="Radius")
        layout.prop(self, "vert_", text="Nº Vert")
        layout.prop(self, "degr_", text="Degrees")
        layout.prop(self, "mode_", text="Mode")

    def make_verts(self, Angle, Vertices, Radius):
        if Angle < 360:
            theta = Angle/(Vertices-1)
        else:
            theta = Angle/Vertices
        listVertX = []
        listVertY = []
        for i in range(Vertices):
            listVertX.append(Radius*cos(radians(theta*i)))
            listVertY.append(Radius*sin(radians(theta*i)))

        if Angle < 360 and self.mode_ == 0:
            sigma = radians(Angle)
            listVertX[-1] = Radius*cos(sigma)
            listVertY[-1] = Radius*sin(sigma)
        elif Angle < 360 and self.mode_ == 1:
            listVertX.append(0.0)
            listVertY.append(0.0)

        X = listVertX
        Y = listVertY
        Z = [0.0]

        max_num = max(len(X), len(Y), len(Z))

        fullList(X, max_num)
        fullList(Y, max_num)
        fullList(Z, max_num)

        points = list(zip(X, Y, Z))
        return points

    def make_edges(self, Vertices, Angle):
        listEdg = [(i, i+1) for i in range(Vertices-1)]

        if Angle < 360 and self.mode_ == 1:
            listEdg.append((0, Vertices))
            listEdg.append((Vertices-1, Vertices))
        else:
            listEdg.append((0, Vertices-1))
        return listEdg

    def make_faces(self, Angle, Vertices):
        listPlg = list(range(Vertices))

        if Angle < 360 and self.mode_ == 1:
            listPlg.insert(0, Vertices)
        return [listPlg]

    def update(self):
        # inputs
        if 'Radius' in self.inputs and self.inputs['Radius'].links:
            Radius = SvGetSocketAnyType(self, self.inputs['Radius'])[0]
        else:
            Radius = [self.rad_]

        if 'Nº Vertices' in self.inputs and self.inputs['Nº Vertices'].links:
            Vertices = SvGetSocketAnyType(self, self.inputs['Nº Vertices'])[0]
            Vertices = list(map(lambda x: max(3, int(x)), Vertices))
        else:
            Vertices = [self.vert_]

        if 'Degrees' in self.inputs and self.inputs['Degrees'].links:
            Angle = SvGetSocketAnyType(self, self.inputs['Degrees'])[0]
            Angle = list(map(lambda x: min(360, max(0, x)), Angle))
        else:
            Angle = [self.degr_]

        parameters = match_long_repeat([Angle, Vertices, Radius])

        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            points = [self.make_verts(a, v, r) for a, v, r in zip(*parameters)]
            SvSetSocketAnyType(self, 'Vertices', points)

        if 'Edges' in self.outputs and self.outputs['Edges'].links:
            edg = [self.make_edges(v, a) for a, v, r in zip(*parameters)]
            SvSetSocketAnyType(self, 'Edges', edg)

        if 'Polygons' in self.outputs and self.outputs['Polygons'].links:
            plg = [self.make_faces(a, v) for a, v, r in zip(*parameters)]
            SvSetSocketAnyType(self, 'Polygons', plg)

    def update_socket(self, context):
        self.update()

def make_circle(Angle, Vertices, Radius, mode):        
        Vertices = [int(Vertices) if type(Vertices) is not list else int(Vertices[0])]
        Radius = [Radius if type(Radius) is not list else Radius[0]]
        Angle = [Angle if type(Angle) is not list else Angle[0]]

        Angle = Angle[0]
        Vertices = Vertices[0]
        Radius = Radius[0]
        if Angle < 360:
            theta = Angle/(Vertices-1)
        else:
            theta = Angle/Vertices
        listVert = []

        for i in range(Vertices):
            listVert.append((Radius*cos(radians(theta*i)), Radius*sin(radians(theta*i)), 0.0))

        if Angle < 360 and mode == 0:
            sigma = radians(Angle)
            listVert[-1] = (Radius*cos(sigma), Radius*sin(sigma), 0.0)
        elif Angle < 360 and mode == 1:
            listVert.append((0.0, 0.0, 0.0))

        listEdg = [(i, i+1) for i in range(Vertices-1)]

        if Angle < 360 and mode == 1:
            listEdg.append((0, Vertices))
            listEdg.append((Vertices-1, Vertices))
        else:
            listEdg.append((0, Vertices-1))

        listPlg = list(range(Vertices))

        if Angle < 360 and mode == 1:
            listPlg.insert(0, Vertices)
            print("prueba", listPlg)

        return listVert, listEdg, [listPlg]

class SvCircleNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Circle '''
    bl_idname = 'SvCircleNode'
    bl_label = 'Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'

    rad_ = FloatProperty(name='Radius', description='Radius',
                         default=1.0,
                         update=updateNode)
    vert_ = IntProperty(name='N Vertices', description='Vertices',
                        default=24, min=3,
                        update=updateNode)
    degr_ = FloatProperty(name='Degrees', description='Degrees',
                          default=360, min=0, max=360,
                          options={'ANIMATABLE'}, update=updateNode)
    mode_ = BoolProperty(name='mode_', description='Mode',
                         default=0,  update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'vert_'
        self.inputs.new('StringsSocket', "Degrees").prop_name = 'degr_'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode_", text="Mode")

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        if not 'Polygons' in outputs:
            return

        Radius = inputs["Radius"].sv_get()
        Vertices = inputs["Nº Vertices"].sv_get()
        Angle = inputs["Degrees"].sv_get()

        params = match_long_repeat([Angle, Vertices, Radius, [self.mode_]])
        out = [a for a in (zip(*[make_circle(a, v, r, m) for a, v, r, m in zip(*params)]))]

        # outputs
        if outputs['Vertices'].links:
            outputs['Vertices'].sv_set(out[0])

        if outputs['Edges'].links:
            outputs['Edges'].sv_set(out[1])

        if outputs['Polygons'].links:
            outputs['Polygons'].sv_set(out[2])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvCircleNode)
    bpy.utils.register_class(CircleNode)


def unregister():
    bpy.utils.unregister_class(SvCircleNode)
    bpy.utils.unregister_class(CircleNode)