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
from itertools import chain, repeat
import bpy
from bpy.props import FloatProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_generate, repeat_last, zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, face_data_from_bmesh_faces, vert_data_from_bmesh_verts
from sverchok.utils.logging import info, debug
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

def remove_doubles(vertices, faces, distance, face_data=None, find_doubles=False, mask=[], output_mask=False):
    if faces:
        edge_mode = (len(faces[0]) == 2)
    else:
        edge_mode = False
    if face_data:
        mark_face_data = True
    else:
        mark_face_data = False

    bm = bmesh_from_pydata(
        vertices,
        faces if edge_mode else [],
        [] if edge_mode else faces,
        markup_face_data=mark_face_data,
        markup_vert_data=output_mask)
    bm_verts = bm.verts

    if mask:
        mask_full = chain(mask, repeat(mask[-1]))
        bm_verts = [v for v, m in zip(bm_verts, mask_full) if m]

    if find_doubles:
        res = bmesh.ops.find_doubles(bm, verts=bm_verts, dist=distance)
        doubles = [vert.co[:] for vert in res['targetmap'].keys()]
    else:
        doubles = []

    bmesh.ops.remove_doubles(bm, verts=bm_verts, dist=distance)
    edges = []
    faces = []
    face_data_out = []
    bm.verts.index_update()
    verts = [vert.co[:] for vert in bm.verts[:]]

    bm.edges.index_update()
    bm.faces.index_update()
    for edge in bm.edges[:]:
        edges.append([v.index for v in edge.verts[:]])
    for face in bm.faces:
        faces.append([v.index for v in face.verts[:]])
    if face_data:
        face_data_out = face_data_from_bmesh_faces(bm, face_data)
    if mask and output_mask:
        mask_out = vert_data_from_bmesh_verts(bm, mask)
    else:
        mask_out = []

    bm.clear()
    bm.free()
    return (verts, edges, faces, face_data_out, doubles, mask_out)


class SvMergeByDistanceNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    """
    Triggers: Remove Doubles
    Tooltip: Merge Vertices that are closer than a distance.
    """
    bl_idname = 'SvMergeByDistanceNode'
    bl_label = 'Merge by Distance'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REMOVE_DOUBLES'

    distance: FloatProperty(
        name='Distance', description='Remove distance',
        default=0.001, precision=3, min=0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'PolyEdge')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvStringsSocket', 'Mask')
        self.inputs.new('SvStringsSocket', 'Distance').prop_name = 'distance'



        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')
        self.outputs.new('SvStringsSocket', 'FaceData')
        self.outputs.new('SvVerticesSocket', 'Doubles')
        self.outputs.new('SvStringsSocket', 'Mask')

    def draw_buttons(self, context, layout):
        #layout.prop(self, 'distance', text="Distance")
        pass

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def pre_setup(self):
        verts = self.inputs['Vertices']
        verts.is_mandatory = True
        verts.nesting_level = 3
        verts.default_mode = 'NONE'

        poly_edge = self.inputs['PolyEdge']
        poly_edge.nesting_level = 3
        poly_edge.default_mode = 'EMPTY_LIST'

        face_data = self.inputs['FaceData']
        face_data.nesting_level = 2
        face_data.default_mode = 'EMPTY_LIST'

        mask = self.inputs['Mask']
        mask.nesting_level = 2
        mask.default_mode = 'EMPTY_LIST'

        distance = self.inputs['Distance']
        distance.nesting_level = 1
        distance.default_mode = 'EMPTY_LIST'
        distance.pre_processing = 'ONE_ITEM'

    def process_data(self, params):
        vertices, faces, face_data, mask, distance = params
        has_mask_out = self.inputs['Mask'].is_linked and self.outputs['Mask'].is_linked
        has_double_out = self.outputs['Doubles'].is_linked
        result = [[] for s in self.outputs]
        for vertices, faces, face_data, mask, distance in zip(*params):
            res = remove_doubles(vertices, faces, distance,
                                 face_data=face_data,
                                 find_doubles=has_double_out,
                                 mask=mask,
                                 output_mask=has_mask_out)
            [r.append(rl) for r, rl in zip(result, res)]

        return result



def register():
    bpy.utils.register_class(SvMergeByDistanceNode)


def unregister():
    bpy.utils.unregister_class(SvMergeByDistanceNode)
