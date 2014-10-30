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

import bpy
from bpy.props import FloatProperty, BoolProperty
import bmesh

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode, Vector_generate, repeat_last,
                            SvSetSocketAnyType, SvGetSocketAnyType)


def wireframe(vertices, faces, t, o, replace, boundary, even_offset, relative_offset):

    if not faces or not vertices:
        return False

    if len(faces[0]) == 2:
        return False

    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in vertices]
    for face in faces:
        bm.faces.new([bm_verts[i] for i in face])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    res = bmesh.ops.wireframe(bm, faces=bm.faces[:], thickness=t, offset=o, use_replace=replace,
                              use_boundary=boundary, use_even_offset=even_offset,
                              use_relative_offset=relative_offset)
    #bmesh.ops.wireframe(bm, faces, thickness, offset, use_replace,
    #    use_boundary, use_even_offset, use_crease, crease_weight, thickness, use_relative_offset, material_offset)
    edges = []
    faces = []
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    for edge in bm.edges[:]:
        edges.append([v.index for v in edge.verts[:]])
    verts = [vert.co[:] for vert in bm.verts[:]]
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    bm.clear()
    bm.free()
    return (verts, edges, faces)


class SvWireframeNode(bpy.types.Node, SverchCustomTreeNode):
    '''Wireframe'''
    bl_idname = 'SvWireframeNode'
    bl_label = 'Wireframe'
    bl_icon = 'OUTLINER_OB_EMPTY'

    thickness = FloatProperty(name='thickness', description='thickness',
                              default=0.01, min=0.0,
                              update=updateNode)
    offset = FloatProperty(name='offset', description='offset',
                           default=0.01, min=0.0,
                           update=updateNode)
    replace = BoolProperty(name='replace', description='replace',
                           default=True,
                           update=updateNode)
    even_offset = BoolProperty(name='even_offset', description='even_offset',
                               default=True,
                               update=updateNode)
    relative_offset = BoolProperty(name='relative_offset', description='even_offset',
                                   default=False,
                                   update=updateNode)
    boundary = BoolProperty(name='boundary', description='boundry',
                            default=True,
                            update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', 'thickness').prop_name = 'thickness'
        self.inputs.new('StringsSocket', 'Offset').prop_name = 'offset'
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'polygons', 'polygons')

        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
        self.outputs.new('StringsSocket', 'polygons', 'polygons')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'boundary', text="Boundary")
        layout.prop(self, 'even_offset', text="Offset even")
        layout.prop(self, 'relative_offset', text="Offset relative")
        layout.prop(self, 'replace', text="Replace")

    def update(self):
        if not ('vertices' in self.outputs and self.outputs['vertices'].links or
                'edges' in self.outputs and self.outputs['edges'].links or
                'polygons' in self.outputs and self.outputs['polygons'].links):
            return

        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
           'polygons' in self.inputs and self.inputs['polygons'].links:

            verts = Vector_generate(SvGetSocketAnyType(self, self.inputs['vertices']))
            polys = SvGetSocketAnyType(self, self.inputs['polygons'])
            if 'thickness' in self.inputs:
                thickness = self.inputs['thickness'].sv_get()[0]
            else:
                thickness = [self.thickness]
            verts_out = []
            edges_out = []
            polys_out = []
            for v, p, t in zip(verts, polys, repeat_last(thickness)):
                res = wireframe(v, p, t, self.offset,
                                self.replace, self.boundary, self.even_offset, self.relative_offset)

                if not res:
                    return
                verts_out.append(res[0])
                edges_out.append(res[1])
                polys_out.append(res[2])

            if 'vertices' in self.outputs and self.outputs['vertices'].links:
                SvSetSocketAnyType(self, 'vertices', verts_out)

            if 'edges' in self.outputs and self.outputs['edges'].links:
                SvSetSocketAnyType(self, 'edges', edges_out)

            if 'polygons' in self.outputs and self.outputs['polygons'].links:
                SvSetSocketAnyType(self, 'polygons', polys_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvWireframeNode)


def unregister():
    bpy.utils.unregister_class(SvWireframeNode)
