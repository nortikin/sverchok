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

from math import pi, degrees
from mathutils import Vector, Matrix
import numpy as np

import bpy
from bpy.props import IntProperty

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

def duplicate_vertices(v1, v2, vertices, edges, faces, count):
    direction = v2 - v1
    edge_length = direction.length
    one_item_length = edge_length / count
    actual_length = diameter(vertices, 0)
    x_scale = one_item_length / actual_length
    x = Vector((1.0, 0.0, 0.0))
    origins = [v1 + direction*x for x in np.linspace(0.0, 1.0, count+1)][:-1]
    scale = Matrix.Scale(x_scale, 4, x)
    rot = autorotate(x, direction).inverted()
    result_vertices = []
    for o in origins:
        for vertex in vertices:
            v = scale * vertex
            v = rot * v
            v = v + o
            result_vertices.append(v)
    return result_vertices

def duplicate_edg_polys(n_vertices, tuples, offset, count):
    result = []
    for i in range(count):
        r = [tuple(v + i*n_vertices + offset for v in t) for t in tuples]
        result.extend(r)
    return result

class SvDuplicateAlongEdgeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Duplicate meshes along edge '''
    bl_idname = 'SvDuplicateAlongEdgeNode'
    bl_label = 'DuplicateAlongEdge'
    bl_icon = 'OUTLINER_OB_EMPTY'

    count_ = IntProperty(name='Count', description='Number of copies',
                        default=3, min=1,
                        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')
        self.inputs.new('VerticesSocket', "Vertex1")
        self.inputs.new('VerticesSocket', "Vertex2")
        self.inputs.new('StringsSocket', "Count").prop_name = "count_"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polygons')
  
    def process(self):
        # inputs
        if not self.inputs['Vertices'].is_linked:
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        vertices_s = Vector_generate(vertices_s)
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        vertices1_s = self.inputs['Vertex1'].sv_get()
        vertices1_s = Vector_generate(vertices1_s)[0]
        vertices2_s = self.inputs['Vertex2'].sv_get()
        vertices2_s = Vector_generate(vertices2_s)[0]
        counts = self.inputs['Count'].sv_get()[0]

        if self.outputs['Vertices'].is_linked:

            result_vertices = []
            result_edges = []
            result_faces = []

            meshes = match_long_repeat([vertices_s, edges_s, faces_s, vertices1_s, vertices2_s, counts])

            offset = 0
            for vertices, edges, faces, vertex1, vertex2, count in zip(*meshes):
                new_vertices = duplicate_vertices(vertex1, vertex2, vertices, edges, faces, count)
                n = len(vertices)
                offset += n
                result_edges.extend(edges)
                result_edges.extend( duplicate_edg_polys(n, edges, offset, count) )
                result_faces.extend(faces)
                result_faces.extend( duplicate_edg_polys(n, faces, offset, count) )

                result_vertices.extend(new_vertices)

            result_vertices = Vector_degenerate([result_vertices])
            self.outputs['Vertices'].sv_set(result_vertices)
            if self.outputs['Edges'].is_linked:
                self.outputs['Edges'].sv_set([result_edges])
            if self.outputs['Polygons'].is_linked:
                self.outputs['Polygons'].sv_set([result_faces])

def register():
    bpy.utils.register_class(SvDuplicateAlongEdgeNode)


def unregister():
    bpy.utils.unregister_class(SvDuplicateAlongEdgeNode)

if __name__ == '__main__':
    register()

