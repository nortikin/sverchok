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
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


def get_bevel_edges(bm, bevel_edges):
    if bevel_edges:
        b_edges = []
        for edge in bevel_edges:
            b_edge = [e for e in bm.edges if set([v.index for v in e.verts]) == set(edge)]
            if b_edge:
                b_edges.append(b_edge[0])
    else:
        b_edges = bm.edges

    return b_edges


def get_bevel_verts(bm, mask):
    if mask:
        b_verts_list = list(bm.verts)
        b_verts = [bv for bv, m in zip(b_verts_list, mask) if m]
    else:
        b_verts = list(bm.verts)

    return b_verts


class SvBevelNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bevel, Round, Smooth
    Tooltip: Bevel vertices, edges and faces. Create rounded corners.
    """
    bl_idname = 'SvBevelNode'
    bl_label = 'Bevel'
    bl_icon = 'MOD_BEVEL'

    def mode_change(self, context):
        self.inputs[5].name = 'BevelEdges' if not self.vertexOnly else 'VerticesMask'
        updateNode(self, [])

    offset_: FloatProperty(
        name='Amount', description='Amount to offset beveled edge',
        default=0.0, min=0.0, update=updateNode)

    offset_modes = [
        ("OFFSET", "Offset", "Amount is offset of new edges from original", 1),
        ("WIDTH", "Width", "Amount is width of new face", 2),
        ("DEPTH", "Depth", "Amount is perpendicular distance from original edge to bevel face", 3),
        ("PERCENT", "Percent", "Amount is percent of adjacent edge length", 4)
    ]

    offsetType: EnumProperty(
        name='Amount Type', description="What distance Amount measures",
        items=offset_modes, default='OFFSET', update=updateNode)

    segments_: IntProperty(
        name="Segments", description="Number of segments in bevel",
        default=1, min=1, update=updateNode)

    profile_: FloatProperty(
        name="Profile", description="Profile shape; 0.5 - round",
        default=0.5, min=0.0, max=1.0, update=updateNode)

    vertexOnly: BoolProperty(
        name="Vertex mode", description="Only bevel edges, not edges",
        default=False, update=mode_change)

    clamp_overlap : BoolProperty(
        name = "Clamp Overlap",
        description = "do not allow beveled edges/vertices to overlap each other",
        default = False,
        update = updateNode)

    loop_slide : BoolProperty(
        name = "Loop Slide",
        description = "prefer to slide along edges to having even widths",
        default = True,
        update = updateNode)

    miter_types = [
        ('SHARP', "Sharp", "Sharp", 0),
        ('PATCH', "Patch", "Patch", 1),
        ('ARC', "Arc", "Arc", 2)
    ]

    miter_outer : EnumProperty(
        name = "Outer",
        description = "Outer mitter type",
        items = miter_types,
        default = 'SHARP',
        update = updateNode)

    miter_inner : EnumProperty(
        name = "Inner",
        description = "Inner mitter type",
        items = miter_types,
        default = 'SHARP',
        update = updateNode)
    
    spread : FloatProperty(
        name = "Spread",
        description = "Amount to offset beveled edge",
        default = 0.0,
        update = updateNode)

    def sv_init(self, context):
        si, so = self.inputs.new, self.outputs.new
        si('SvVerticesSocket', "Vertices")
        si('SvStringsSocket', 'Edges')
        si('SvStringsSocket', 'Polygons')
        si('SvStringsSocket', 'FaceData')
        si('SvStringsSocket', 'BevelFaceData')
        si('SvStringsSocket', 'BevelEdges')

        si('SvStringsSocket', "Offset").prop_name = "offset_"
        si('SvStringsSocket', "Segments").prop_name = "segments_"
        si('SvStringsSocket', "Profile").prop_name = "profile_"
        si('SvStringsSocket', "Spread").prop_name = "spread"

        so('SvVerticesSocket', 'Vertices')
        so('SvStringsSocket', 'Edges')
        so('SvStringsSocket', 'Polygons')
        so('SvStringsSocket', 'FaceData')
        so('SvStringsSocket', 'NewPolys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "vertexOnly")
        layout.prop(self, "clamp_overlap")
        layout.label(text="Amount type:")
        layout.prop(self, "offsetType", expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "loop_slide")
        layout.label(text="Miter type:")
        layout.prop(self, 'miter_inner')
        layout.prop(self, 'miter_outer')

    def get_socket_data(self):
        vertices = self.inputs['Vertices'].sv_get(default=[[]])
        edges = self.inputs['Edges'].sv_get(default=[[]])
        faces = self.inputs['Polygons'].sv_get(default=[[]])
        if 'FaceData' in self.inputs:
            face_data = self.inputs['FaceData'].sv_get(default=[[]])
        else:
            face_data = [[]]
        if 'BevelFaceData' in self.inputs:
            bevel_face_data = self.inputs['BevelFaceData'].sv_get(default=[[]])
        else:
            bevel_face_data = [[]]
        if self.vertexOnly:
            mask = self.inputs['VerticesMask'].sv_get(default=[[]])
        else:
            mask = self.inputs['BevelEdges'].sv_get(default=[[]])
        offsets = self.inputs['Offset'].sv_get()[0]
        segments = self.inputs['Segments'].sv_get()[0]
        profiles = self.inputs['Profile'].sv_get()[0]
        if 'Spread' in self.inputs:
            spreads = self.inputs['Spread'].sv_get()[0]
        else:
            spreads = [0.0]
        return vertices, edges, faces, face_data, mask, offsets, segments, profiles, bevel_face_data, spreads

    def create_geom(self, bm, mask):
        if not self.vertexOnly:
            b_edges = get_bevel_edges(bm, mask)
            geom = list(bm.verts) + list(b_edges) + list(bm.faces)
        else:
            b_verts = get_bevel_verts(bm, mask)
            geom = b_verts + list(bm.edges) + list(bm.faces)
        return geom

    def process(self):

        if not (self.inputs[0].is_linked and (self.inputs[2].is_linked or self.inputs[1].is_linked)):
            return
        if not any(self.outputs[name].is_linked for name in ['Vertices', 'Edges', 'Polygons', 'NewPolys']):
            return

        verts_out = []
        edges_out = []
        faces_out = []
        face_data_out = []
        result_bevel_faces = []

        meshes = match_long_repeat(self.get_socket_data())

        for vertices, edges, faces, face_data, mask, offset, segments, profile, bevel_face_data, spread in zip(*meshes):
            if face_data:
                fullList(face_data, len(faces))
            if bevel_face_data and isinstance(bevel_face_data, (list, tuple)):
                bevel_face_data = bevel_face_data[0]
            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, normal_update=True)
            geom = self.create_geom(bm, mask)

            try:
                bevel_faces = bmesh.ops.bevel(bm,
                    geom=geom,
                    offset=offset,
                    offset_type=self.offsetType,
                    segments=segments,
                    profile=profile,
                    vertex_only=self.vertexOnly,
                    clamp_overlap = self.clamp_overlap,
                    loop_slide = self.loop_slide,
                    spread = spread,
                    miter_inner = self.miter_inner,
                    miter_outer = self.miter_outer,
                    # strength= (float)
                    # hnmode= (enum in ['NONE', 'FACE', 'ADJACENT', 'FIXED_NORMAL_SHADING'], default 'NONE')
                    material=-1)['faces']
            except Exception as e:
                self.exception(e)

            new_bevel_faces = [[v.index for v in face.verts] for face in bevel_faces]
            if not face_data:
                verts, edges, faces = pydata_from_bmesh(bm)
                verts_out.append(verts)
                edges_out.append(edges)
                faces_out.append(faces)
                if bevel_face_data != []:
                    new_face_data = []
                    for face in faces:
                        if set(face) in map(set, new_bevel_faces):
                            new_face_data.append(bevel_face_data)
                        else:
                            new_face_data.append(None)
                    face_data_out.append(new_face_data)
                else:
                    face_data_out.append([])
            else:
                verts, edges, faces, new_face_data = pydata_from_bmesh(bm, face_data)
                verts_out.append(verts)
                edges_out.append(edges)
                faces_out.append(faces)
                if bevel_face_data != []:
                    new_face_data_m = []
                    for data, face in zip(new_face_data, faces):
                        if set(face) in map(set, new_bevel_faces):
                            new_face_data_m.append(bevel_face_data)
                        else:
                            new_face_data_m.append(data)
                    face_data_out.append(new_face_data_m)
                else:
                    face_data_out.append(new_face_data)
            bm.free()
            result_bevel_faces.append(new_bevel_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Polygons'].sv_set(faces_out)
        if 'FaceData' in self.outputs:
            self.outputs['FaceData'].sv_set(face_data_out)
        self.outputs['NewPolys'].sv_set(result_bevel_faces)


def register():
    bpy.utils.register_class(SvBevelNode)


def unregister():
    bpy.utils.unregister_class(SvBevelNode)
