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

from math import pi
import bpy
import bmesh
from bmesh.ops import transform, extrude_discrete_faces
from mathutils import Matrix, Vector
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


class SvExtrudeSeparateLiteNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Inset like behaviour but way different '''
    bl_idname = 'SvExtrudeSeparateLiteNode'
    bl_label = 'Extrude Separate Faces Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EXTRUDE_FACE'

    replacement_nodes = [
        ('SvExtrudeSeparateNode', None, None),
        ('SvInsetSpecial',
            dict(Vertices='vertices', Polygons='polygons'),
            dict(Vertices='vertices', Polygons='polygons')),
        ('SvInsetFaces',
            dict(Vertices='Verts', Polygons='Faces'),
            dict(Vertices='Verts', Polygons='Faces'))
    ]

    def sv_init(self, context):
        inew = self.inputs.new
        onew = self.outputs.new
        inew('SvVerticesSocket', "Vertices")
        inew('SvStringsSocket', 'Polygons')
        inew('SvStringsSocket', 'Mask')
        inew('SvMatrixSocket', 'Matrix')
        onew('SvVerticesSocket', 'Vertices')
        onew('SvStringsSocket', 'Edges')
        onew('SvStringsSocket', 'Polygons')
        onew('SvStringsSocket', 'ExtrudedPolys')
        onew('SvStringsSocket', 'OtherPolys')

    def process(self):
        outputs = self.outputs
        if not outputs['Vertices'].is_linked:
            return
        IVerts, IFaces, IMask, Imatr = self.inputs
        vertices_s = IVerts.sv_get()
        faces_s = IFaces.sv_get()
        linked_extruded_polygons = outputs['ExtrudedPolys'].is_linked
        linked_other_polygons = outputs['OtherPolys'].is_linked
        result_vertices = []
        result_edges = []
        result_faces = []
        result_extruded_faces = []
        result_other_faces = []
        bmlist = [bmesh_from_pydata(verts, [], faces) for verts, faces in zip(vertices_s, faces_s)]
        trans = Imatr.sv_get()
        if IMask.is_linked:
            flist = [np.extract(mask, bm.faces[:]) for bm, mask in zip(bmlist, IMask.sv_get())]
        else:
            flist = [bm.faces for bm in bmlist]
        for bm, selfaces in zip(bmlist, flist):
            extrfaces = extrude_discrete_faces(bm, faces=selfaces)['faces']
            fullList(trans, len(extrfaces))
            new_extruded_faces = []
            for face, ma in zip(extrfaces, trans):
                normal = face.normal
                if normal[0] == 0 and normal[1] == 0:
                    m_r = Matrix() if normal[2] >= 0 else Matrix.Rotation(pi, 4, 'X')
                else:
                    z_axis = normal
                    x_axis = Vector((z_axis[1] * -1, z_axis[0], 0)).normalized()
                    y_axis = z_axis.cross(x_axis).normalized()
                    m_r = Matrix(list([*zip(x_axis[:], y_axis[:], z_axis[:])])).to_4x4()
                m = (Matrix.Translation(face.calc_center_median()) @ m_r).inverted()
                transform(bm, matrix=ma, space=m, verts=face.verts)
                if linked_extruded_polygons or linked_other_polygons:
                    new_extruded_faces.append([v.index for v in face.verts])
            new_vertices, new_edges, new_faces = pydata_from_bmesh(bm)
            bm.free()
            new_other_faces = [f for f in new_faces if f not in new_extruded_faces] if linked_other_polygons else []
            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_extruded_faces.append(new_extruded_faces)
            result_other_faces.append(new_other_faces)
        outputs['Vertices'].sv_set(result_vertices)
        outputs['Edges'].sv_set(result_edges)
        outputs['Polygons'].sv_set(result_faces)
        outputs['ExtrudedPolys'].sv_set(result_extruded_faces)
        outputs['OtherPolys'].sv_set(result_other_faces)


def register():
    bpy.utils.register_class(SvExtrudeSeparateLiteNode)


def unregister():
    bpy.utils.unregister_class(SvExtrudeSeparateLiteNode)
