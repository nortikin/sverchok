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
from sverchok.data_structure import updateNode, match_long_repeat, repeat_last_for_length, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

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
            ('BOOLEAN'         , "Bool"   , "Mask elements by boolean" , 'IMAGE_ALPHA'    , 0),
            ('INDEXES'         , "Indexes", "Mask elements by indexes" , 'LIGHTPROBE_GRID' if bpy.app.version< (4,1,0) else 'LIGHTPROBE_VOLUME', 1),
            #('GROUP_OF_INDEXES', "Groups" , "group elements by indexes", 'LINENUMBERS_ON' , 2), # Не помню, что хотел с этим сделать! Надо вспомнить!
        ]
    
    select_elements_mode : EnumProperty(
        name = "Mask elements mode",
        default = 'BOOLEAN',
        description = "Mask elements mode",
        items = select_elements_modes,
        update = updateNode
    ) # type: ignore

    offset_amounts_modes = [
        ('BEVEL_ALL_VERTICES', "All", "All vertices of every object has one bevel", 'DECORATE'  , 0),
        ('BEVEL_PER_VERTICES', "One", "Bevel per vertices in object"        , 'THREE_DOTS', 1),
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
        description='Amount to offset beveled elements (vertices or edges)',
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
        description = "Do not allow beveled edges/vertices to overlap each other",
        default = False,
        update = updateNode
    ) # type: ignore

    loop_slide : BoolProperty(
        name = "Loop Slide",
        description = "Prefer to slide along edges to having even widths",
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

    def draw_sub_elements_selected_in_socket(self, socket, context, layout):
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
        self.inputs['sub_elements_selected'].custom_draw = 'draw_sub_elements_selected_in_socket'
        self.inputs['offset_amounts'].prop_name = 'offset_amounts'
        self.inputs['offset_amounts'].label = 'Amounts'
        self.inputs['offset_amounts'].custom_draw = 'draw_amounts_in_socket'
        self.inputs['bevel_segments'].prop_name = 'bevel_segments'
        self.inputs['bevel_segments'].label = 'Segments'
        self.inputs['bevel_profiles'].prop_name = 'bevel_profiles'
        self.inputs['bevel_profiles'].label = 'Profiles'
        self.inputs['spread'].prop_name = 'spread'
        self.inputs['spread'].label = 'Spread'

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
        mask = self.inputs['sub_elements_selected'].sv_get(default=[[]], deepcopy=False)
        offsets = self.inputs['offset_amounts'].sv_get(deepcopy=False)[0]
        segments = self.inputs['bevel_segments'].sv_get(deepcopy=False)[0]
        profiles = self.inputs['bevel_profiles'].sv_get(deepcopy=False)[0]
        if 'spread' in self.inputs:
            spreads = self.inputs['spread'].sv_get(deepcopy=False)[0]
        else:
            spreads = [0.0]
        return vertices, edges, faces, face_data, bevel_face_data, spreads

    def create_geom(self, bm, mask):
        if not self.vertexOnly:
            # keep source indexes layer
            if mask:
                b_edges = get_bevel_edges(bm, mask)
            else:
                b_edges = bm.edges
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

        _sub_elements_selected   = self.inputs['sub_elements_selected'].sv_get(default=[[]], deepcopy=False)
        amounts_level = get_data_nesting_level(_sub_elements_selected)
        if amounts_level>4:
            raise Exception(f'Input level of Amounts has to be 3. Amount list has {amounts_level}')
        else:
            if amounts_level==4:
                if len(_sub_elements_selected)==1:
                    sub_elements_selected3 = _sub_elements_selected[0]
                else:
                    raise Exception(f'Input level of Amounts has to be 3')
            else:
                sub_elements_selected3   = ensure_nesting_level(_sub_elements_selected, 3)
        _offset_amounts   = self.inputs['offset_amounts'].sv_get(default=[[self.offset_amounts]], deepcopy=False)
        offset_amounts3   = ensure_nesting_level(_offset_amounts, 3)
        _bevel_segments   = self.inputs['bevel_segments'].sv_get(default=[[self.bevel_segments]], deepcopy=False)
        bevel_segments3   = ensure_nesting_level(_bevel_segments, 3)
        _bevel_profiles   = self.inputs['bevel_profiles'].sv_get(default=[[self.bevel_profiles]], deepcopy=False)
        bevel_profiles3   = ensure_nesting_level(_bevel_profiles, 3)


        meshes = match_long_repeat(self.get_socket_data())

        for I, (vertices, edges, faces, face_data, bevel_face_data, spread) in enumerate( zip(*meshes) ):
            # if face_data:
            #     face_data_matched = repeat_last_for_length(face_data, len(faces))
            # if bevel_face_data and isinstance(bevel_face_data, (list, tuple)):
            #     bevel_face_data = bevel_face_data[0]

            sub_elements_selected3_I = sub_elements_selected3[I] if I<=len(sub_elements_selected3)-1 else sub_elements_selected3[-1]
            if self.offset_amounts_mode=='BEVEL_ALL_VERTICES':
                join_sub_elements_selected3_I = []
                for elem in sub_elements_selected3_I:
                    join_sub_elements_selected3_I.extend(elem)
                sub_elements_selected3_I = [join_sub_elements_selected3_I]
                pass
            sub_elements_selected3I1 = []
            # Remove the duplicates in each list [[1,1,2,3],[4,4,5,5,5,6,7]] => [[1,2,3],[4,5,6,7]]
            for sub_elements in sub_elements_selected3_I:
                if len(sub_elements)==0:
                    # If the input list is empty, select all elements:
                    if self.vertexOnly==True:
                        sub_elements = list( range(len(vertices)) )
                    else:
                        sub_elements = list( range(len(edges)) )
                elif self.select_elements_mode=='BOOLEAN':
                    # Convert boolean selectors to indices (if the input list is not empty):
                    sub_elements = [IJ for IJ, sub_element in enumerate(sub_elements) if sub_element]
                sub_elements_selected3I1.append( list(set(sub_elements)))
            source_elements_indexes = [IJ for IJ in range(len(vertices if self.vertexOnly else edges))]
            # remove duplicates everywhere
            sub_elements_selected3I2 = []
            for sub_elements1 in sub_elements_selected3I1:
                sub_elements2 = []
                for index in sub_elements1:
                    if index in source_elements_indexes:
                        source_elements_indexes.remove(index)
                        sub_elements2.append( index )
                sub_elements_selected3I2.append(sub_elements2)
            sub_elements_selected3_I = sub_elements_selected3I2

            if self.vertexOnly:
                # If you want to process vertices, you need to rearrange the order of the sub-elements so that the indices of the sub-elements start from the end:
                vertices_dict_indexes = dict()
                sub_elements_selected3I3 = []
                new_vertices_list = []
                IJ=len(vertices)-1
                # Put the vertices in a new order, so that the vertices are used first from the end:
                for sub_elements in sub_elements_selected3I2:
                    sub_elements3 = []
                    for index in sub_elements:
                        vertices_dict_indexes[index] = IJ
                        sub_elements3.append(IJ)
                        IJ=IJ-1
                        new_vertices_list.append(vertices[index])
                    sub_elements_selected3I3.append(sub_elements3)
                for index in source_elements_indexes:
                    vertices_dict_indexes[index] = IJ
                    IJ=IJ-1
                    new_vertices_list.append(vertices[index])
                new_vertices_list.reverse()
                new_edges_list = []
                for e1 in edges:
                    edge1 = []
                    for index in e1:
                        edge1.append(vertices_dict_indexes[index])
                    new_edges_list.append(edge1)

                new_faces_list = []
                for face in faces:
                    face1 = []
                    for index in face:
                        face1.append(vertices_dict_indexes[index])
                    new_faces_list.append(face1)

                vertices = new_vertices_list
                edges = new_edges_list
                faces = new_faces_list
                sub_elements_selected3_I = sub_elements_selected3I3


            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, normal_update=True)
            index_bevel_layer = bm.faces.layers.int.new('index_bevel_layer')
            for face in bm.faces:
                face[index_bevel_layer] = 0

            # List of vertex indices for the current bmesh:
            bmesh_source_verts_indexes = [I for I in range(len(vertices))]

            
            for IJ, face in enumerate(bm.faces):
                face.material_index=IJ
            
            max_material_index = len(bm.faces)
            verts_adjacent_material = dict()
            edges_adjacent_material = dict()
            
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

            if self.offset_amounts_mode=='BEVEL_ALL_VERTICES':
                if I<=len(offset_amounts3[0][0])-1:
                    offset_amounts3_I = [[offset_amounts3[0][0][I]]]
                else:
                    offset_amounts3_I = [[offset_amounts3[0][0][-1]]]

                if I<=len(bevel_segments3[0][0])-1:
                    bevel_segments3_I = [[bevel_segments3[0][0][I]]]
                else:
                    bevel_segments3_I = [[bevel_segments3[0][0][-1]]]

                if I<=len(bevel_profiles3[0][0])-1:
                    bevel_profiles3_I = [[bevel_profiles3[0][0][I]]]
                else:
                    bevel_profiles3_I = [[bevel_profiles3[0][0][-1]]]
            else:
                if I<=len(offset_amounts3[0])-1:
                    offset_amounts3_I = [offset_amounts3[0][I]]
                else:
                    offset_amounts3_I = [offset_amounts3[0][-1]]

                if I<=len(bevel_segments3[0])-1:
                    bevel_segments3_I = [bevel_segments3[0][I]]
                else:
                    bevel_segments3_I = [bevel_segments3[0][-1]]

                if I<=len(bevel_profiles3[0])-1:
                    bevel_profiles3_I = [bevel_profiles3[0][I]]
                else:
                    bevel_profiles3_I = [bevel_profiles3[0][-1]]

            bevel_faces = []
            # new_bevel_faces = []
            for IJ, sub_elements_selected in enumerate( sub_elements_selected3_I ):

                # Get the mask of source indices:
                source_indexes_mask = [False]*len(vertices if self.vertexOnly else edges)
                for elem_index in sub_elements_selected:
                    if 0<=elem_index<=len(source_indexes_mask)-1:
                        source_indexes_mask[elem_index] = True
                pass

                # select elements by source indexes mask:
                mask = []
                if self.vertexOnly:
                    # Get index list for sub_elements_selected in current vertex index list:
                    sub_element_indexes_IJ = []
                    for index in sub_elements_selected:
                        if index in bmesh_source_verts_indexes:
                            sub_element_indexes_IJ.append(bmesh_source_verts_indexes.index(index))
                    # Remove duplicate indexes
                    sub_element_indexes_IJ = list(set(sub_element_indexes_IJ))
                    # Remove used indexes from the source list
                    for IJK in sub_elements_selected:
                        if IJK in bmesh_source_verts_indexes:
                            bmesh_source_verts_indexes.remove(IJK)
                    # Create a mask from sub-element indices:
                    for IJK in range(len(bm.verts)):
                        mask.append( IJK in sub_element_indexes_IJ )
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

                    _bevel_faces = bmesh.ops.bevel(bm,
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
                    bevel_faces.extend(_bevel_faces)
                    pass
                except TypeError as e:

                    # if the "try" failed, we try the new form of bmesh.ops.bevel arguments..
                    affect_geom = 'VERTICES' if self.vertexOnly else 'EDGES'

                    bevel_data = bmesh.ops.bevel(bm,
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
                    )
                    _bevel_faces = bevel_data['faces']
                    bevel_faces.extend(_bevel_faces)
                    pass
                except Exception as e:
                    self.exception(e)

                bm.faces.ensure_lookup_table()
                for bf in _bevel_faces:
                    bm.faces[bf.index][index_bevel_layer] = IJ+1

                pass

            faces_bevel_layer = [face[index_bevel_layer] for face in bm.faces]
            verts, edges, faces = pydata_from_bmesh(bm)
            verts_out.append(verts)
            edges_out.append(edges)
            faces_out.append(faces)

            if bevel_face_data:
                len_bevel_face_data = len(bevel_face_data)
            len_face_data = 0
            if face_data:
                len_face_data = len(face_data)
            
            new_bevel_faces=[]
            face_data1_out = []
            for IJK, fbl in enumerate(faces_bevel_layer):
                if fbl==0:
                    if face_data:
                        if IJK<=len_face_data-1:
                            face_data1_out.append(face_data[IJK])
                        else:
                            face_data1_out.append(face_data[-1])
                    else:
                        face_data1_out.append(None)
                    pass
                else:
                    face_verts = [vert.index for vert in bm.faces[IJK].verts]
                    new_bevel_faces.append(face_verts)
                    if bevel_face_data:
                        if fbl-1<=len_bevel_face_data-1:
                            face_data1_out.append(bevel_face_data[fbl-1])
                        else:
                            face_data1_out.append(bevel_face_data[-1])
                    else:
                        face_data1_out.append(None)
                    pass
                pass
            pass

            bm.free()
            result_bevel_faces.append(new_bevel_faces)
            face_data_out.append(face_data1_out)
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
