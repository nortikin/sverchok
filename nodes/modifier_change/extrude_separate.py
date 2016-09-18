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

from mathutils import Matrix, Vector
#from math import copysign

import bpy
from bpy.props import IntProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

def Matrix_degenerate(ms):
    return [[ j[:] for j in M ] for M in ms]

class SvExtrudeSeparateNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Extrude separate faces '''
    bl_idname = 'SvExtrudeSeparateNode'
    bl_label = 'Extrude Separate Faces'
    bl_icon = 'OUTLINER_OB_EMPTY'

    height_ = FloatProperty(name="Height", description="Extrusion amount",
                default=0.0,
                update=updateNode)
    scale_ = FloatProperty(name="Scale", description="Extruded faces scale",
                default=1.0, min=0.0,
                update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('StringsSocket', 'Polygons', 'Polygons')
        self.inputs.new('StringsSocket', 'Mask')
        self.inputs.new('StringsSocket', "Height").prop_name = "height_"
        self.inputs.new('StringsSocket', "Scale").prop_name = "scale_"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polygons')
        self.outputs.new('StringsSocket', 'ExtrudedPolys')
        self.outputs.new('StringsSocket', 'OtherPolys')
  
    def process(self):
        # inputs
        if not (self.inputs['Vertices'].is_linked and self.inputs['Polygons'].is_linked):
            return
        if not any(self.outputs[name].is_linked for name in ['Vertices', 'Edges', 'Polygons', 'ExtrudedPolys', 'OtherPolys']):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])
        masks_s = self.inputs['Mask'].sv_get(default=[[1]])
        heights_s = self.inputs['Height'].sv_get()
        scales_s  = self.inputs['Scale'].sv_get()

        result_vertices = []
        result_edges = []
        result_faces = []
        result_extruded_faces = []
        result_other_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, heights_s, scales_s])

        offset = 0
        for vertices, edges, faces, masks, heights, scales in zip(*meshes):
            fullList(heights, len(faces))
            fullList(scales,  len(faces))
            fullList(masks,  len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces)
            extruded_faces = bmesh.ops.extrude_discrete_faces(bm, faces=bm.faces)['faces']

            new_extruded_faces = []

            for face, mask, height, scale in zip(extruded_faces, masks, heights, scales):
                if not mask:
                    continue
                dr = face.normal * height
                center = face.calc_center_median()
                translation = Matrix.Translation(center)
                rotation = face.normal.rotation_difference((0,0,1)).to_matrix().to_4x4()
                #rotation = autorotate(z, face.normal).inverted()
                m = translation * rotation
                bmesh.ops.scale(bm, vec=(scale, scale, scale), space=m.inverted(), verts=face.verts)
                bmesh.ops.translate(bm, verts=face.verts, vec=dr)

                new_extruded_faces.append([v.index for v in face.verts])

            new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()
            new_other_faces = [f for f in new_faces if f not in new_extruded_faces]

            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_extruded_faces.append(new_extruded_faces)
            result_other_faces.append(new_other_faces)

        self.outputs['Vertices'].sv_set(result_vertices)
        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(result_edges)
        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(result_faces)
        if self.outputs['ExtrudedPolys'].is_linked:
            self.outputs['ExtrudedPolys'].sv_set(result_extruded_faces)
        if self.outputs['OtherPolys'].is_linked:
            self.outputs['OtherPolys'].sv_set(result_other_faces)

def register():
    bpy.utils.register_class(SvExtrudeSeparateNode)


def unregister():
    bpy.utils.unregister_class(SvExtrudeSeparateNode)

if __name__ == '__main__':
    register()

