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

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)


class SvCircleNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Circle '''
    bl_idname = 'SvCircleNode'
    bl_label = 'Circle'
    bl_icon = 'MESH_CIRCLE'

    rad_: FloatProperty(name='Radius', description='Radius', default=1.0, update=updateNode)
    vert_: IntProperty(name='num Verts', description='Vertices', default=24, min=3, update=updateNode)
    mode_: BoolProperty(name='mode_', description='Mode', default=0,  update=updateNode)
    degr_: FloatProperty(name='Degrees', description='Degrees', default=360.0, min=0, max=360.0,  update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('SvStringsSocket', "num Verts").prop_name = 'vert_'
        self.inputs.new('SvStringsSocket', "Degrees").prop_name = 'degr_'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
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

        points = list((x,y,0) for x,y in zip(listVertX, listVertY) )
        return points

    def make_edges(self, Angle, Vertices):
        listEdg = [(i, i+1) for i in range(Vertices-1)]

        if Angle < 360 and self.mode_ == 1:
            listEdg.append((0, Vertices))
            listEdg.append((Vertices-1, Vertices))
        else:
            listEdg.append((Vertices-1, 0))
        return listEdg

    def make_faces(self, Angle, Vertices):
        listPlg = list(range(Vertices))

        if Angle < 360 and self.mode_ == 1:
            listPlg.insert(0, Vertices)
        return [listPlg]

    def process(self):
        
        # inputs
        
        input_socket_names = ['Radius', 'num Verts', 'Degrees']
        radius_input, n_vert_input, angle_input = [self.inputs[n] for n in input_socket_names]

        radius = radius_input.sv_get(deepcopy=False)[0]

        n_verts = [self.vert_]
        if n_vert_input.is_linked:
            n_verts = n_vert_input.sv_get(deepcopy=False)[0]
            n_verts = list(map(lambda x: max(3, int(x)), n_verts))

        angle = angle_input.sv_get(deepcopy=False)[0]
        if angle_input.is_linked:
            angle = list(map(lambda x: min(360, max(0, x)), angle))

        parameters = match_long_repeat([angle, n_verts, radius])

        # outputs

        output_socket_names = ['Vertices', 'Edges', 'Polygons']
        verts_output, edges_output, faces_output = [self.outputs[n] for n in output_socket_names]

        # Node should calculated all its data for all output sockets at this stage
        points = [self.make_verts(a, v, r) for a, v, r in zip(*parameters)]
        verts_output.sv_set(points)

        edg = [self.make_edges(a, v) for a, v, r in zip(*parameters)]
        edges_output.sv_set(edg)

        plg = [self.make_faces(a, v) for a, v, r in zip(*parameters)]
        faces_output.sv_set(plg)


def register():
    bpy.utils.register_class(SvCircleNode)


def unregister():
    bpy.utils.unregister_class(SvCircleNode)
