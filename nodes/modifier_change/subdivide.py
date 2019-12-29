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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
import bmesh.ops

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList, Matrix_generate
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvSubdivideNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: subdivide
    Tooltip: Subdivide edges and faces
    '''

    bl_idname = 'SvSubdivideNode'
    bl_label = 'Subdivide'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SUBDIVIDE'

    falloff_types = [
        ("SMOOTH", "Smooth", "", 'SMOOTHCURVE', 0),
        ("SPHERE", "Sphere", "", 'SPHERECURVE', 1),
        ("ROOT", "Root", "", 'ROOTCURVE', 2),
        ("SHARP", "Sharp", "", 'SHARPCURVE', 3),
        ("LINEAR", "Linear", "", 'LINCURVE', 4),
        ("INVERSE_SQUARE", "Inverse Square", "", 'ROOTCURVE', 7)
    ]

    corner_types = [
        ("INNER_VERT", "Inner Vertices", "", 0),
        ("PATH", "Path", "", 1),
        ("FAN", "Fan", "", 2),
        ("STRAIGHT_CUT", "Straight Cut", "", 3)
    ]

    def update_mode(self, context):
        self.outputs['NewVertices'].hide_safe = not self.show_new
        self.outputs['NewEdges'].hide_safe = not self.show_new
        self.outputs['NewFaces'].hide_safe = not self.show_new

        self.outputs['OldVertices'].hide_safe = not self.show_old
        self.outputs['OldEdges'].hide_safe = not self.show_old
        self.outputs['OldFaces'].hide_safe = not self.show_old

        updateNode(self, context)

    falloff_type: EnumProperty(name="Falloff", items=falloff_types, default="LINEAR", update=updateNode)
    corner_type: EnumProperty(name="Corner Cut Type", items=corner_types, default="INNER_VERT", update=updateNode)

    cuts: IntProperty(
        description="Specifies the number of cuts per edge to make",
        name="Number of Cuts", min=1, default=1, update=updateNode)

    smooth: FloatProperty(
        description="Displaces subdivisions to maintain approximate curvature",
        name="Smooth", min=0.0, max=1.0, default=0.0, update=updateNode)

    fractal: FloatProperty(
        description="Displaces the vertices in random directions after the mesh is subdivided",
        name="Fractal", min=0.0, max=1.0, default=0.0, update=updateNode)

    along_normal: FloatProperty(
        description="Causes the vertices to move along the their normals, instead of random directions",
        name="Along normal", min=0.0, max=1.0, default=0.0, update=updateNode)

    seed: IntProperty(
        description="Random seed",
        name="Seed", default=0, update=updateNode)

    grid_fill: BoolProperty(
        description="fill in fully-selected faces with a grid",
        name="Grid fill", default=True, update=updateNode)

    single_edge: BoolProperty(
        description="tessellate the case of one edge selected in a quad or triangle",
        name="Single edge", default=False, update=updateNode)

    only_quads: BoolProperty(
        description="only subdivide quads (for loopcut)",
        name="Only Quads", default=False, update=updateNode)

    smooth_even: BoolProperty(
        description="maintain even offset when smoothing",
        name="Even smooth", default=False, update=updateNode)

    show_new: BoolProperty(
        description="Show outputs with new geometry",
        name="Show New", default=False, update=update_mode)

    show_old: BoolProperty(
        description="Show outputs with old geometry",
        name="Show Old", default=False, update=update_mode)

    show_options: BoolProperty(
        description="Show options on the node",
        name="Show Options", default=False, update=updateNode)

    def draw_common(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "show_old", toggle=True)
        row.prop(self, "show_new", toggle=True)
        col.prop(self, "show_options", toggle=True)

    def draw_options(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "falloff_type")
        col.prop(self, "corner_type")

        row = layout.row(align=True)
        col = row.column(align=True)
        col.prop(self, "grid_fill", toggle=True)
        col.prop(self, "single_edge", toggle=True)

        col = row.column(align=True)
        col.prop(self, "only_quads", toggle=True)
        col.prop(self, "smooth_even", toggle=True)

    def draw_buttons(self, context, layout):
        self.draw_common(context, layout)
        if self.show_options:
            self.draw_options(context, layout)

    def draw_buttons_ext(self, context, layout):
        self.draw_common(context, layout)
        self.draw_options(context, layout)


    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', "Vertices")
        inew('SvStringsSocket', 'Edges')
        inew('SvStringsSocket', 'Faces')
        inew('SvStringsSocket', 'FaceData')
        inew('SvStringsSocket', 'EdgeMask')

        inew('SvStringsSocket', 'Cuts').prop_name = "cuts"
        inew('SvStringsSocket', 'Smooth').prop_name = "smooth"
        inew('SvStringsSocket', 'Fractal').prop_name = "fractal"
        inew('SvStringsSocket', 'AlongNormal').prop_name = "along_normal"
        inew('SvStringsSocket', 'Seed').prop_name = "seed"

        onew = self.outputs.new
        onew('SvVerticesSocket', 'Vertices')
        onew('SvStringsSocket', 'Edges')
        onew('SvStringsSocket', 'Faces')
        onew('SvStringsSocket', 'FaceData')

        onew('SvVerticesSocket', 'NewVertices')
        onew('SvStringsSocket', 'NewEdges')
        onew('SvStringsSocket', 'NewFaces')

        onew('SvVerticesSocket', 'OldVertices')
        onew('SvStringsSocket', 'OldEdges')
        onew('SvStringsSocket', 'OldFaces')

        self.update_mode(context)

    def get_result_pydata(self, geom):
        new_verts = [v for v in geom if isinstance(v, bmesh.types.BMVert)]
        new_edges = [e for e in geom if isinstance(e, bmesh.types.BMEdge)]
        new_faces = [f for f in geom if isinstance(f, bmesh.types.BMFace)]

        new_verts = [tuple(v.co) for v in new_verts]
        new_edges = [[v.index for v in edge.verts] for edge in new_edges]
        new_faces = [[v.index for v in face.verts] for face in new_faces]

        return new_verts, new_edges, new_faces

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['EdgeMask'].sv_get(default=[[1]])
        if 'FaceData' in self.inputs:
            face_data_s = self.inputs['FaceData'].sv_get(default=[[]])
        else:
            face_data_s = [[]]

        cuts_s = self.inputs['Cuts'].sv_get()[0]
        smooth_s = self.inputs['Smooth'].sv_get()[0]
        fractal_s = self.inputs['Fractal'].sv_get()[0]
        along_normal_s = self.inputs['AlongNormal'].sv_get()[0]
        seed_s = self.inputs['Seed'].sv_get()[0]

        result_vertices = []
        result_edges = []
        result_faces = []
        result_face_data = []

        r_inner_vertices = []
        r_inner_edges = []
        r_inner_faces = []

        r_split_vertices = []
        r_split_edges = []
        r_split_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, face_data_s, masks_s, cuts_s, smooth_s, fractal_s, along_normal_s, seed_s])
        for vertices, edges, faces, face_data, masks, cuts, smooth, fractal, along_normal, seed in zip(*meshes):
            fullList(masks,  len(edges))
            if face_data:
                fullList(face_data, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, normal_update=True)

            selected_edges = []
            for m, edge in zip(masks, edges):
                if not m:
                    continue
                found = False
                for bmesh_edge in bm.edges:
                    if set(v.index for v in bmesh_edge.verts) == set(edge):
                        found = True
                        break
                if found:
                    selected_edges.append(bmesh_edge)
                else:
                    self.debug("Cant find edge: " + str(edge))

            geom = bmesh.ops.subdivide_edges(bm, edges = selected_edges,
                    smooth = smooth,
                    smooth_falloff = self.falloff_type,
                    fractal = fractal, along_normal = along_normal,
                    cuts = cuts, seed = seed,
                    quad_corner_type = self.corner_type,
                    use_grid_fill = self.grid_fill,
                    use_single_edge = self.single_edge,
                    use_only_quads = self.only_quads,
                    use_smooth_even = self.smooth_even)

            if face_data:
                new_verts, new_edges, new_faces, new_face_data = pydata_from_bmesh(bm, face_data)
            else:
                new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
                new_face_data = []

            inner_verts, inner_edges, inner_faces = self.get_result_pydata(geom['geom_inner'])
            split_verts, split_edges, split_faces = self.get_result_pydata(geom['geom_split'])

            bm.free()

            result_vertices.append(new_verts)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_face_data.append(new_face_data)

            r_inner_vertices.append(inner_verts)
            r_inner_edges.append(inner_edges)
            r_inner_faces.append(inner_faces)

            r_split_vertices.append(split_verts)
            r_split_edges.append(split_edges)
            r_split_faces.append(split_faces)

        self.outputs['Vertices'].sv_set(result_vertices)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Faces'].sv_set(result_faces)
        if 'FaceData' in self.outputs:
            self.outputs['FaceData'].sv_set(result_face_data)

        self.outputs['NewVertices'].sv_set(r_inner_vertices)
        self.outputs['NewEdges'].sv_set(r_inner_edges)
        self.outputs['NewFaces'].sv_set(r_inner_faces)

        self.outputs['OldVertices'].sv_set(r_split_vertices)
        self.outputs['OldEdges'].sv_set(r_split_edges)
        self.outputs['OldFaces'].sv_set(r_split_faces)


def register():
    bpy.utils.register_class(SvSubdivideNode)


def unregister():
    bpy.utils.unregister_class(SvSubdivideNode)
