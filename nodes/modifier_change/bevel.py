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
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, repeat_last_for_length, ensure_nesting_level
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


# def get_bevel_edges(bm, bevel_edges):
#     if bevel_edges:
#         b_edges = []
#         for edge in bevel_edges:
#             b_edge = [e for e in bm.edges if set([v.index for v in e.verts]) == set(edge)]
#             if b_edge:
#                 b_edges.append(b_edge[0])
#     else:
#         b_edges = bm.edges

#     return b_edges

def get_bevel_edges(bm, mask):
    if mask:
        b_edges_list = list(bm.edges)
        b_edges = [bv for bv, m in zip(b_edges_list, mask) if m]
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


class SvBevelNodeMK2(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Bevel, Round, Smooth
    Tooltip: Bevel vertices, edges and faces. Create rounded corners.
    """
    bl_idname = 'SvBevelNodeMK2'
    bl_label = 'Bevel'
    bl_icon = 'MOD_BEVEL'

    def mode_change(self, context):
        self.inputs["sub_elements_selected"].label = 'Edges selected' if not self.vertexOnly else 'Vertices selected'
        if 'spread' in self.inputs:
            self.inputs['spread'].hide_safe = self.miter_inner == 'SHARP' and self.miter_outer == 'SHARP'
        updateNode(self, context)

    select_elements_modes = [
            ('BOOLEAN', "Bool", "Mask elements by boolean"         , 'IMAGE_ALPHA'    , 0),
            ('INDEXES', "Indexes", "Mask elements by indexes"         , 'LIGHTPROBE_GRID', 1),
            ('GROUP_OF_INDEXES', "Groups", "group elements by indexes", 'LINENUMBERS_ON' , 2),
        ]
    
    select_elements_mode : EnumProperty(
        name = "Mask elements mode",
        default = 'BOOLEAN',
        description = "Mask elements mode",
        items = select_elements_modes,
        update = updateNode
    ) # type: ignore

    offset_amounts_modes = [
        ('BEVEL_ALL_VERTICES', "All", "All vertices has one bevel", 'DECORATE'  , 0),
        ('BEVEL_PER_VERTICES', "One", "Bevel per vertices"        , 'THREE_DOTS', 1),
    ]

    offset_amounts_mode : EnumProperty(
        name = "Offset mode",
        default = 'BEVEL_PER_VERTICES',
        description = "How many offsets per object (One or All)",
        items = offset_amounts_modes,
        update = updateNode
    ) # type: ignore


    offset_amounts: FloatProperty(
        name='Amount',
        description='Amount to offset beveled elemets (vertices or edges)',
        default=0.0,
        min=0.0,
        update=updateNode
    ) # type: ignore
    

    offset_modes = [
        ("OFFSET", "Offset", "Amount is offset of new edges from original", 1),
        ("WIDTH", "Width", "Amount is width of new face", 2),
        ("DEPTH", "Depth", "Amount is perpendicular distance from original edge to bevel face", 3),
        ("PERCENT", "Percent", "Amount is percent of adjacent edge length", 4)
    ]

    offset_mode: EnumProperty(
        name='Amount Type',
        description="What distance Amount measures",
        items=offset_modes,
        default='OFFSET',
        update=updateNode
    )  # type: ignore

    bevel_segments: IntProperty(
        name="Segments",
        description="Number of segments in bevel",
        default=1,
        min=1,
        update=updateNode
    ) # type: ignore

    bevel_profiles: FloatProperty(
        name="Profile",
        description="Profile shape; 0.5 - round",
        default=0.5,
        min=0.0,
        max=1.0,
        update=updateNode
    ) # type: ignore

    vertexOnly: BoolProperty(
        name="Vertex mode",
        description="Only bevel vertices, not edges",
        default=False,
        update=mode_change
        ) # type: ignore

    clamp_overlap : BoolProperty(
        name = "Clamp Overlap",
        description = "do not allow beveled edges/vertices to overlap each other",
        default = False,
        update = updateNode
    ) # type: ignore

    loop_slide : BoolProperty(
        name = "Loop Slide",
        description = "prefer to slide along edges to having even widths",
        default = True,
        update = updateNode
        ) # type: ignore

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
        update = mode_change
    ) # type: ignore

    miter_inner : EnumProperty(
        name = "Inner",
        description = "Inner mitter type",
        items = miter_types,
        default = 'SHARP',
        update = mode_change
    ) # type: ignore

    spread : FloatProperty(
        name = "Spread",
        description = "Amount to offset beveled edge",
        default = 0.0, min = 0.0,
        update = updateNode
    ) # type: ignore

    def draw_sub_elemets_selected_in_socket(self, socket, context, layout):
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f"{socket.label}")
        layout.prop(self, 'select_elements_mode', text='', expand=True)
        pass

    def draw_amounts_in_socket(self, socket, context, layout):
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.prop(self, socket.prop_name)
        layout.prop(self, 'offset_amounts_mode', text='', expand=True)
        pass


    def sv_init(self, context):
        si, so = self.inputs.new, self.outputs.new
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket' , 'edges')
        self.inputs.new('SvStringsSocket' , 'polygons')
        self.inputs.new('SvStringsSocket' , 'FaceData')
        self.inputs.new('SvStringsSocket' , 'BevelFaceData')
        self.inputs.new('SvStringsSocket' , 'sub_elements_selected')
        self.inputs.new('SvStringsSocket' , 'offset_amounts')
        self.inputs.new('SvStringsSocket' , 'bevel_segments')
        self.inputs.new('SvStringsSocket' , 'bevel_profiles')
        self.inputs.new('SvStringsSocket' , 'spread')

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['edges'].label = 'Edges'
        self.inputs['polygons'].label = 'Polygons'
        self.inputs["sub_elements_selected"].label = 'Edges selected' if not self.vertexOnly else 'Vertices selected'
        self.inputs['sub_elements_selected'].custom_draw = 'draw_sub_elemets_selected_in_socket'
        self.inputs['offset_amounts'].prop_name = 'offset_amounts'
        self.inputs['offset_amounts'].label = 'Amounts'
        self.inputs['offset_amounts'].custom_draw = 'draw_amounts_in_socket'
        self.inputs['bevel_segments'].prop_name = 'bevel_segments'
        self.inputs['bevel_segments'].label = 'Segments'
        self.inputs['bevel_profiles'].prop_name = 'bevel_profiles'
        self.inputs['bevel_profiles'].label = 'Profiles'
        self.inputs['spread'].prop_name = 'spread'
        self.inputs['spread'].label = 'Spread'

        #si('SvStringsSocket', "Profile").prop_name = "profile_"
        #si('SvStringsSocket', "Spread").prop_name = 'spread'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket', 'edges')
        self.outputs.new('SvStringsSocket', 'polygons')
        self.outputs.new('SvStringsSocket', 'FaceData')
        self.outputs.new('SvStringsSocket', 'NewPolys')
        self.outputs['vertices'].label = "Vertices"
        self.outputs['edges'].label = "Edges"
        self.outputs['polygons'].label = "Polygons"

        self.mode_change(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "vertexOnly")
        layout.prop(self, "clamp_overlap")
        layout.label(text="Width type:")
        layout.prop(self, "offset_mode", expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "loop_slide")
        layout.label(text="Miter type:")
        layout.prop(self, 'miter_inner')
        layout.prop(self, 'miter_outer')

    def get_socket_data(self):
        vertices = self.inputs['vertices'].sv_get(default=[[]], deepcopy=False)
        edges = self.inputs['edges'].sv_get(default=[[]], deepcopy=False)
        faces = self.inputs['polygons'].sv_get(default=[[]], deepcopy=False)
        if 'FaceData' in self.inputs:
            face_data = self.inputs['FaceData'].sv_get(default=[[]], deepcopy=False)
        else:
            face_data = [[]]
        if 'BevelFaceData' in self.inputs:
            bevel_face_data = self.inputs['BevelFaceData'].sv_get(default=[[]], deepcopy=False)
        else:
            bevel_face_data = [[]]
        # if self.vertexOnly:
        #     mask = self.inputs['sub_elements_mask'].sv_get(default=[[]], deepcopy=False)
        # else:
        #     mask = self.inputs['BevelEdges'].sv_get(default=[[]], deepcopy=False)
        mask = self.inputs['sub_elements_selected'].sv_get(default=[[]], deepcopy=False)
        offsets = self.inputs['offset_amounts'].sv_get(deepcopy=False)[0]
        segments = self.inputs['bevel_segments'].sv_get(deepcopy=False)[0]
        profiles = self.inputs['bevel_profiles'].sv_get(deepcopy=False)[0]
        if 'spread' in self.inputs:
            spreads = self.inputs['spread'].sv_get(deepcopy=False)[0]
        else:
            spreads = [0.0]
        #return vertices, edges, faces, face_data, mask, offsets, segments, profiles, bevel_face_data, spreads
        return vertices, edges, faces, face_data, bevel_face_data, spreads

    def create_geom(self, bm, mask):
        if not self.vertexOnly:
            # keep source indexes layer
            if mask:
                # edges_mask = [bv for bv, m in zip(edges, mask) if m]
                # b_edges = get_bevel_edges(bm, edges_mask)
                b_edges = get_bevel_edges(bm, mask)
            else:
                b_edges = bm.edges

            #geom = list(bm.verts) + list(b_edges) + list(bm.faces)
            geom = list(b_edges)
        else:
            # keep source indexes layer
            ind_vertices = bm.verts.layers.int.new('bevel indexes')
            for I, vert in enumerate(bm.verts):
                vert[ind_vertices] = -1

            b_verts = get_bevel_verts(bm, mask)
            b_verts_set = set(b_verts)
            for I, vert in enumerate(b_verts):
                vert[ind_vertices] = I

            b_edges = [edge for edge in bm.edges if all(v in b_verts_set for v in edge.verts)]
            b_faces = [face for face in bm.faces if all(v in b_verts_set for v in face.verts)]

            geom = b_verts + b_edges + b_faces
            #geom = b_verts + list(bm.edges) + list(bm.faces)
        return geom

    def process(self):

        if not (self.inputs[0].is_linked and (self.inputs[2].is_linked or self.inputs[1].is_linked)):
            return
        if not any(self.outputs[name].is_linked for name in ['vertices', 'edges', 'polygons', 'NewPolys']):
            return

        verts_out = []
        edges_out = []
        faces_out = []
        face_data_out = []
        result_bevel_faces = []

        _sub_elements_selected   = self.inputs['sub_elements_selected'].sv_get(default=[[True]], deepcopy=False)
        sub_elements_selected3   = ensure_nesting_level(_sub_elements_selected, 3)
        _offset_amounts   = self.inputs['offset_amounts'].sv_get(default=[[self.offset_amounts]], deepcopy=False)
        offset_amounts3   = ensure_nesting_level(_offset_amounts, 3)
        _bevel_segments   = self.inputs['bevel_segments'].sv_get(default=[[self.bevel_segments]], deepcopy=False)
        bevel_segments3   = ensure_nesting_level(_bevel_segments, 3)
        _bevel_profiles   = self.inputs['bevel_profiles'].sv_get(default=[[self.bevel_profiles]], deepcopy=False)
        bevel_profiles3   = ensure_nesting_level(_bevel_profiles, 3)


        meshes = match_long_repeat(self.get_socket_data())

        for I, (vertices, edges, faces, face_data, bevel_face_data, spread) in enumerate( zip(*meshes) ):
            if face_data:
                face_data_matched = repeat_last_for_length(face_data, len(faces))
            if bevel_face_data and isinstance(bevel_face_data, (list, tuple)):
                bevel_face_data = bevel_face_data[0]

            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, normal_update=True)
            
            for IJ, face in enumerate(bm.faces):
                face.material_index=IJ
            
            max_material_index = len(bm.faces)
            edges_adjacent_material = dict()
            verts_adjacent_material = dict()
            
            for vert in bm.verts:
                vert_adjacent_faces_material = tuple(sorted(set((face.material_index for face in vert.link_faces))))
                if len(vert_adjacent_faces_material)>0:
                    verts_adjacent_material[tuple(vert_adjacent_faces_material)] = vert.index
                pass

            source_edges_indexes = dict()
            for IJ, edges_indexes in enumerate(edges):
                source_edges_indexes[tuple(sorted(set(edges_indexes)))] = IJ
            pass
            for edge in bm.edges:
                edge_adjacent_faces_material = tuple(sorted(set(face.material_index for face in edge.link_faces)))
                if len(edge_adjacent_faces_material)>0:
                    bm_edges_indexes = tuple(sorted(set(vert.index for vert in edge.verts)))
                    edges_adjacent_material[edge_adjacent_faces_material] = source_edges_indexes[bm_edges_indexes]
                pass
            pass




            # #if self.vertexOnly:
            # source_verts_indexes_layer = bm.verts.layers.int.new('source_indexes')
            # bm.verts.ensure_lookup_table()
            # for IJ, vert in enumerate(bm.verts):
            #     vert[source_verts_indexes_layer] = IJ
            # bm.verts.ensure_lookup_table()
            # #else:
            # source_edges_indexes_layer = bm.edges.layers.int.new('source_indexes')
            # bm.edges.ensure_lookup_table()
            # source_edges_list_set = []
            # for edges_indexes in edges:
            #     source_edges_list_set.append(set(edges_indexes))
            # for IJ, bm_edge in enumerate(bm.edges):
            #     bm_edge_indexes_set = set([v.index for v in bm_edge.verts])
            #     bm_edge[source_edges_indexes_layer] = source_edges_list_set.index(bm_edge_indexes_set)
            # bm.edges.ensure_lookup_table()

            if I<=len(offset_amounts3)-1:
                offset_amounts3_I = offset_amounts3[I]
            else:
                offset_amounts3_I = offset_amounts3[-1]

            if I<=len(bevel_segments3)-1:
                bevel_segments3_I = bevel_segments3[I]
            else:
                bevel_segments3_I = bevel_segments3[-1]

            if I<=len(bevel_profiles3)-1:
                bevel_profiles3_I = bevel_profiles3[I]
            else:
                bevel_profiles3_I = bevel_profiles3[-1]


            for IJ, sub_elements_selected in enumerate( sub_elements_selected3[I] ):

                if self.select_elements_mode=='BOOL':
                    source_indexes_mask = sub_elements_selected
                    pass
                else:
                    source_indexes_mask = [False]*len(vertices if self.vertexOnly else edges)
                    for elem_index in sub_elements_selected:
                        if 0<=elem_index<=len(source_indexes_mask)-1:
                            source_indexes_mask[elem_index] = True
                    pass

                # select elements by source indexes mask:
                mask = []
                if self.vertexOnly:
                    pass
                    for IJK, bm_vert in enumerate(bm.verts):
                        #mask.append( source_indexes_mask[vert[source_verts_indexes_layer]]==True )
                        vert_adjacent_faces_material = tuple(sorted(set(face.material_index for face in bm_vert.link_faces)))
                        if len(vert_adjacent_faces_material)>0:
                            if vert_adjacent_faces_material in verts_adjacent_material:
                                source_vert_index = verts_adjacent_material[vert_adjacent_faces_material]
                                mask.append(source_indexes_mask[source_vert_index]==True)
                            else:
                                mask.append(False)
                            pass
                        pass

                    pass
                else:
                    pass
                    for IJK, bm_edge in enumerate(bm.edges):
                        edge_adjacent_faces_material = tuple(sorted(set(face.material_index for face in bm_edge.link_faces)))
                        if len(edge_adjacent_faces_material)>0:
                            if edge_adjacent_faces_material in edges_adjacent_material:
                                source_edge_index = edges_adjacent_material[edge_adjacent_faces_material]
                                mask.append(source_indexes_mask[source_edge_index]==True)
                            else:
                                mask.append(False)
                            pass
                        pass
                    pass
                            #mask.append(source_indexes_mask[bm_edge[source_edges_indexes_layer]]==True)
                        # if source_indexes_mask[bm_edge[source_edges_indexes_layer]]==True:
                        #     source_verts_set = set([vert[source_verts_indexes_layer] for vert in bm_edge.verts])
                        #     if source_verts_set in source_edges_list_set:
                        #         mask.append( True )
                        #     else:
                        #         mask.append( False )
                        # else:
                        #     mask.append( False )
                    pass
                
                if IJ<=len(offset_amounts3_I[0])-1:
                    bevel_offset = offset_amounts3_I[0][IJ]
                else:
                    bevel_offset = offset_amounts3_I[0][-1]

                if IJ<=len(bevel_segments3_I[0])-1:
                    bevel_segments = bevel_segments3_I[0][IJ]
                else:
                    bevel_segments = bevel_segments3_I[0][-1]

                if IJ<=len(bevel_profiles3_I[0])-1:
                    bevel_profiles = bevel_profiles3_I[0][IJ]
                else:
                    bevel_profiles = bevel_profiles3_I[0][-1]

                geom = self.create_geom(bm, mask)

                try:
                    # we try the most likely blender binary compatible version first (official builds)

                    bevel_faces = bmesh.ops.bevel(bm,
                        geom=geom,
                        offset=bevel_offset,
                        offset_type=self.offset_mode,
                        segments=bevel_segments,
                        profile=bevel_profiles,
                        vertex_only=self.vertexOnly,
                        clamp_overlap = self.clamp_overlap,
                        loop_slide = self.loop_slide,
                        spread = spread,
                        miter_inner = self.miter_inner,
                        miter_outer = self.miter_outer,
                        # strength= (float)
                        # hnmode= (enum in ['NONE', 'FACE', 'ADJACENT', 'FIXED_NORMAL_SHADING'], default 'NONE')
                        material=max_material_index
                    )['faces']
                except TypeError as e:

                    # if the "try" failed, we try the new form of bmesh.ops.bevel arguments..
                    affect_geom = 'VERTICES' if self.vertexOnly else 'EDGES'

                    bevel_faces = bmesh.ops.bevel(bm,
                        geom=geom,
                        offset=bevel_offset,
                        offset_type=self.offset_mode,
                        segments=bevel_segments,
                        profile=bevel_profiles,
                        #   profile_type=  (enum:  'SUPERELLIPSE', 'CUSTOM' ), default super
                        affect=affect_geom,
                        clamp_overlap = self.clamp_overlap,
                        loop_slide = self.loop_slide,
                        spread = spread,
                        miter_inner = self.miter_inner,
                        miter_outer = self.miter_outer,
                        material=max_material_index
                )['faces']

                except Exception as e:
                    self.exception(e)
                bm.verts.index_update()
                bm.edges.index_update()
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                pass

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
                verts, edges, faces, new_face_data = pydata_from_bmesh(bm, face_data_matched)
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
            pass

        self.outputs['vertices'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)
        self.outputs['polygons'].sv_set(faces_out)
        if 'FaceData' in self.outputs:
            self.outputs['FaceData'].sv_set(face_data_out)
        self.outputs['NewPolys'].sv_set(result_bevel_faces)


def register():
    bpy.utils.register_class(SvBevelNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvBevelNodeMK2)
