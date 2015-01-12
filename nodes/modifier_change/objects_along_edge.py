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

from math import pi, degrees, floor, ceil
from mathutils import Vector, Matrix
import numpy as np

import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, Matrix_generate, Vector_generate, Vector_degenerate

def householder(u):
    x,y,z = u[0], u[1], u[2]
    m = Matrix([[x*x, x*y, x*z, 0], [x*y, y*y, y*z, 0], [x*z, y*z, z*z, 0], [0,0,0,0]])
    h = Matrix() - 2*m
    return h

def autorotate(e1, xx):
    alpha = xx.length
#     e1 = Vector((1.0, 0.0, 0.0))
    u = xx - alpha*e1
    v = u.normalized()
    q = householder(v)
    return q

def diameter(vertices, axis):
    xs = [vertex[axis] for vertex in vertices]
    M = max(xs)
    m = min(xs)
    return (M-m)

all_axes = [
        Vector((1.0, 0.0, 0.0)),
        Vector((0.0, 1.0, 0.0)),
        Vector((0.0, 0.0, 1.0))
    ]

class SvDuplicateAlongEdgeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Duplicate meshes along edge '''
    bl_idname = 'SvDuplicateAlongEdgeNode'
    bl_label = 'DuplicateAlongEdge'
    bl_icon = 'OUTLINER_OB_EMPTY'

    count_modes = [
            ("count", "Count", "Specify number of donor objects per edge", 1),
            ("up", "Up", "Calculate count of objects automatically, scaling them only up", 2),
            ("down", "Down", "Calculate count of objects automatically, scaling them only down", 3),
            ("off", "Off", "Calculate count of objects automatically, do not scale them", 4),
        ]

    def count_const(self, v1, v2, vertices, count):
        return count

    def count_up(self, v1, v2, vertices, count):
        distance = (v1-v2).length
        donor_size = diameter(vertices, self.orient_axis)
        return floor( distance / donor_size )

    def count_down(self, v1, v2, vertices, count):
        distance = (v1-v2).length
        donor_size = diameter(vertices, self.orient_axis)
        return ceil( distance / donor_size )

    count_funcs = {"count": count_const,
                   "up": count_up,
                   "down": count_down,
                   "off": count_up}

    def count_mode_change(self, context):
        self.inputs["Count"].hide = self.count_mode != "count"
        updateNode(self, context)

    count_mode = EnumProperty(items = count_modes, default="count", update=count_mode_change)

    axes = [
            ("X", "X", "X axis", 1),
            ("Y", "Y", "Y axis", 2),
            ("Z", "Z", "Z axis", 3)
        ]

    def orient_axis_change(self, context):
        updateNode(self, context)

    orient_axis_ = EnumProperty(items = axes, default="X", update=orient_axis_change)

    def get_axis_idx(self):
        if self.orient_axis_ == "X":
            return 0
        elif self.orient_axis_ == "Y":
            return 1
        elif self.orient_axis_ == "Z":
            return 2

    orient_axis = property(get_axis_idx)

    count_ = IntProperty(name='Count', description='Number of copies',
                        default=3, min=1,
                        update=updateNode)

    scale_all = BoolProperty(name="Scale all axes", description="Scale donor objects along all axes or only along orientation axis",
                             default=False,
                        update=updateNode)

    def get_count(self, v1, v2, vertices, count):
        func = self.count_funcs[self.count_mode]
        return func(self, v1, v2, vertices, count)

    def get_scale_off(self):
        return self.count_mode == "off"

    scale_off = property(get_scale_off)

    input_modes = [
            ("edge", "Edges", "Define recipient edges from set of vertices and set of edges", 1),
            ("fixed", "Fixed", "Use two specified vertices to define recipient edge", 2),
        ]

    def input_mode_change(self, context):
        self.inputs["Vertex1"].hide = self.input_mode != "fixed" 
        self.inputs["Vertex2"].hide = self.input_mode != "fixed" 
        self.inputs["VerticesR"].hide = self.input_mode != "edge"
        self.inputs["EdgesR"].hide = self.input_mode != "edge"

    input_mode = EnumProperty(items = input_modes, default="edge", update=input_mode_change)

    def get_recipient_vertices(self, vs1, vs2, vertices, edges):
        if self.input_mode == "fixed":
            return vs1, vs2
        elif self.input_mode == "edge":
            rs1 = [vertices[i] for (i,j) in edges]
            rs2 = [vertices[j] for (i,j) in edges]
            return rs1, rs2

    def duplicate_vertices(self, v1, v2, vertices, edges, faces, count):
        count = max(count,1)
        direction = v2 - v1
        edge_length = direction.length
        one_item_length = edge_length / count
        actual_length = diameter(vertices, self.orient_axis)
        x_scale = one_item_length / actual_length
        x = all_axes[self.orient_axis]
        # for actual_length = 1.0 and edge_length = 3.0, let origins be [0.5, 1.5, 2.5]
        u = direction.normalized()
        origins = [v1 + direction*x + 0.5*one_item_length*u for x in np.linspace(0.0, 1.0, count+1)][:-1]
        if self.scale_off:
            scale = None
        else:
            if self.scale_all:
                scale = Matrix.Scale(x_scale, 4)
            else:
                scale = Matrix.Scale(x_scale, 4, x)
        rot = autorotate(x, direction).inverted()
        result_vertices = []
        for o in origins:
            new_vertices = []
            for vertex in vertices:
                if scale is None:
                    v = vertex
                else:
                    v = scale * vertex
                v = rot * v
                v = v + o
                new_vertices.append(v)
            result_vertices.append(new_vertices)
        return result_vertices

    def duplicate_edges(self, n_vertices, tuples, count):
        result = []
        for i in range(count):
            r = [tuple(v + i*n_vertices for v in t) for t in tuples]
            result.extend(r)
        return result

    def duplicate_faces(self, n_vertices, tuples, count):
        result = []
        for i in range(count):
            r = [[v + i*n_vertices for v in t] for t in tuples]
            result.extend(r)
        return result

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')
        self.inputs.new('VerticesSocket', "Vertex1")
        self.inputs.new('VerticesSocket', "Vertex2")
        self.inputs.new('VerticesSocket', "VerticesR")
        self.inputs.new('StringsSocket', 'EdgesR')
        self.inputs.new('StringsSocket', "Count").prop_name = "count_"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polygons')

        self.input_mode_change(context)
  
    def draw_buttons(self, context, layout):
        layout.prop(self, "count_mode", expand=True)
        layout.prop(self, "orient_axis_", expand=True)
        layout.prop(self, "input_mode", expand=True)
        if not self.scale_off:
            layout.prop(self, "scale_all")

    def process(self):
        # inputs
        if not self.inputs['Vertices'].is_linked:
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        vertices_s = Vector_generate(vertices_s)
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        inp_vertices1_s = self.inputs['Vertex1'].sv_get(default=[[]])
        inp_vertices1_s = Vector_generate(inp_vertices1_s)[0]
        inp_vertices2_s = self.inputs['Vertex2'].sv_get(default=[[]])
        inp_vertices2_s = Vector_generate(inp_vertices2_s)[0]
        vertices_r = self.inputs['VerticesR'].sv_get(default=[[]])
        vertices_r = Vector_generate(vertices_r)[0]
        edges_r = self.inputs['EdgesR'].sv_get(default=[[]])[0]
        counts = self.inputs['Count'].sv_get()[0]

        vertices1_s, vertices2_s = self.get_recipient_vertices(inp_vertices1_s, inp_vertices2_s, vertices_r, edges_r)

        if self.outputs['Vertices'].is_linked:

            result_vertices = []
            result_edges = []
            result_faces = []
            meshes = match_long_repeat([vertices_s, edges_s, faces_s, vertices1_s, vertices2_s, counts])

            for vertices, edges, faces, vertex1, vertex2, inp_count in zip(*meshes):
                count = self.get_count(vertex1, vertex2, vertices, inp_count)
                new_vertices = self.duplicate_vertices(vertex1, vertex2, vertices, edges, faces, count)
                result_edges.extend( [edges] * count )
                result_faces.extend( [faces] * count )
                result_vertices.extend( Vector_degenerate(new_vertices) )

            #result_vertices = Vector_degenerate(result_vertices)
            print("R1:", len(result_vertices))
            print("E:", result_edges)
            print("F:", result_faces)
            self.outputs['Vertices'].sv_set(result_vertices)
            if self.outputs['Edges'].is_linked:
                self.outputs['Edges'].sv_set(result_edges)
            if self.outputs['Polygons'].is_linked:
                self.outputs['Polygons'].sv_set(result_faces)

def register():
    bpy.utils.register_class(SvDuplicateAlongEdgeNode)


def unregister():
    bpy.utils.unregister_class(SvDuplicateAlongEdgeNode)

if __name__ == '__main__':
    register()

