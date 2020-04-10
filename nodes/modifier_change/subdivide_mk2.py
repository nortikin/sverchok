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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, BoolVectorProperty
from bmesh.ops import subdivide_edges

from numpy import ndarray
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList, Matrix_generate, numpy_full_list
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh, numpy_data_from_bmesh, get_partial_result_pydata

socket_names = ['Vertices', 'Edges', 'Faces', 'FaceData']
def get_selected_edges(use_mask, masks, bm_edges):
    if use_mask:
        if isinstance(masks, ndarray):
            masks = numpy_full_list(masks, len(bm_edges)).tolist()
        else:
            fullList(masks, len(bm_edges))
        edge_id = bm_edges.layers.int.get("initial_index")
        return  [edge for edge in bm_edges if masks[edge[edge_id]]]


    return bm_edges

class SvSubdivideNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: subdivide
    Tooltip: Subdivide edges and faces
    '''

    bl_idname = 'SvSubdivideNodeMK2'
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
        name="Number of Cuts", min=0, soft_max=10, default=1, update=updateNode)

    cuts_draft: IntProperty(
        description="Specifies the number of cuts per edge to make (draft mode)",
        name="[D] Number of Cuts", min=0, default=1, update=updateNode)

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

    out_np: BoolVectorProperty(
        name="Ouput Numpy",
        description="Output NumPy arrays slows this node but may improve performance of nodes it is connected to",
        default=(False, False, False, False),
        size=4, update=updateNode)

    draft_properties_mapping = dict(
            cuts = 'cuts_draft'

        )
    def does_support_draft_mode(self):
        return True

    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label
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
        layout.label(text="Ouput Numpy:")
        r = layout.row()
        for i in range(4):
            r.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "falloff_type")
        layout.prop_menu_enum(self, "corner_type")
        layout.prop(self, "grid_fill", toggle=True)
        layout.prop(self, "single_edge", toggle=True)


        layout.prop(self, "only_quads", toggle=True)
        layout.prop(self, "smooth_even", toggle=True)

        layout.label(text="Ouput Numpy:")

        for i in range(4):
            layout.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

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

    def mute_node(self):
        origin_socket = [0, 1, 2, 3, 0, 1, 2, 0, 1, 2]

        for i, s in zip(origin_socket, self.outputs):
            if self.inputs[i].is_linked:
                s.sv_set(self.inputs[i].sv_get(deepcopy=False))

    def freeze_node(self):
        if hash(self) in self.mem.keys():
            # for m, s in zip(self.mem[hash(self)], self.outputs):
                # s.sv_set(m)
            return True
        return False

    def get_data(self):
        inputs = self.inputs

        verts_s = inputs['Vertices'].sv_get(deepcopy=False)
        edges_s = inputs['Edges'].sv_get(default=[[]], deepcopy=False)
        faces_s = inputs['Faces'].sv_get(default=[[]], deepcopy=False)

        masks_s = inputs['EdgeMask'].sv_get(default=[[1]], deepcopy=True)
        face_data_s = inputs['FaceData'].sv_get(default=[[]], deepcopy=True)

        cuts_s = inputs['Cuts'].sv_get(deepcopy=False)[0]
        smooth_s = inputs['Smooth'].sv_get(deepcopy=False)[0]
        fractal_s = inputs['Fractal'].sv_get(deepcopy=False)[0]
        along_normal_s = inputs['AlongNormal'].sv_get(deepcopy=False)[0]
        seed_s = inputs['Seed'].sv_get(deepcopy=False)[0]

        return match_long_repeat([verts_s, edges_s, faces_s, face_data_s, masks_s, cuts_s, smooth_s, fractal_s, along_normal_s, seed_s])

    def dont_process(self):
        inputs, outputs = self.inputs, self.outputs
        return not (any(s.is_linked for s in outputs) and all(s.is_linked for s in inputs[:2]))

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if self.dont_process():
            return

        result_vertices, result_edges, result_faces, result_face_data = [], [], [], []
        r_inner_vertices, r_inner_edges, r_inner_faces = [], [], []
        r_split_vertices, r_split_edges, r_split_faces = [], [], []

        use_mask = inputs['EdgeMask'].is_linked
        show_new = self.show_new and any(s.is_linked for s in outputs[4:7])
        show_old = self.show_old and any(s.is_linked for s in outputs[7:])
        use_face_data = inputs['FaceData'].is_linked and outputs['FaceData'].is_linked
        output_numpy = any(self.out_np)

        meshes = self.get_data()

        for vertices, edges, faces, face_data, masks, cuts, smooth, fractal, along_normal, seed in zip(*meshes):
            if cuts < 1:
                result_vertices.append(vertices)
                result_edges.append(edges)
                result_faces.append(faces)
                result_face_data.append(face_data)
                r_inner_vertices.append(vertices)
                r_inner_edges.append(edges)
                r_inner_faces.append(faces)
                r_split_vertices.append(vertices)
                r_split_edges.append(edges)
                r_split_faces.append(faces)
                continue

            if use_face_data and len(face_data) > 0:
                if isinstance(face_data, ndarray):
                    face_data = numpy_full_list(face_data, len(faces)).tolist()
                else:
                    fullList(face_data, len(faces))

            bm = bmesh_from_pydata(
                vertices, edges, faces,
                markup_face_data=use_face_data,
                markup_edge_data=use_mask,
                normal_update=True)

            selected_edges = get_selected_edges(use_mask, masks, bm.edges)

            geom = subdivide_edges(
                bm,
                edges=selected_edges,
                smooth=smooth,
                smooth_falloff=self.falloff_type,
                fractal=fractal,
                along_normal=along_normal,
                cuts=cuts,
                seed=seed,
                quad_corner_type=self.corner_type,
                use_grid_fill=self.grid_fill,
                use_single_edge=self.single_edge,
                use_only_quads=self.only_quads,
                use_smooth_even=self.smooth_even)

            if output_numpy:
                new_verts, new_edges, new_faces, new_face_data = numpy_data_from_bmesh(bm, self.out_np, face_data)
            else:
                if use_face_data and len(face_data) > 0:
                    new_verts, new_edges, new_faces, new_face_data = pydata_from_bmesh(bm, face_data)
                else:
                    new_verts, new_edges, new_faces = pydata_from_bmesh(bm)
                    new_face_data = []

            result_vertices.append(new_verts)
            result_edges.append(new_edges)
            result_faces.append(new_faces)
            result_face_data.append(new_face_data)

            if show_new:
                inner_verts, inner_edges, inner_faces = self.get_result_pydata(geom['geom_inner'])
                r_inner_vertices.append(inner_verts)
                r_inner_edges.append(inner_edges)
                r_inner_faces.append(inner_faces)

            if show_old:
                split_verts, split_edges, split_faces = self.get_result_pydata(geom['geom_split'])
                r_split_vertices.append(split_verts)
                r_split_edges.append(split_edges)
                r_split_faces.append(split_faces)

            bm.free()


        outputs['Vertices'].sv_set(result_vertices)
        outputs['Edges'].sv_set(result_edges)
        outputs['Faces'].sv_set(result_faces)
        outputs['FaceData'].sv_set(result_face_data)

        outputs['NewVertices'].sv_set(r_inner_vertices)
        outputs['NewEdges'].sv_set(r_inner_edges)
        outputs['NewFaces'].sv_set(r_inner_faces)

        outputs['OldVertices'].sv_set(r_split_vertices)
        outputs['OldEdges'].sv_set(r_split_edges)
        outputs['OldFaces'].sv_set(r_split_faces)


def register():
    bpy.utils.register_class(SvSubdivideNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvSubdivideNodeMK2)
