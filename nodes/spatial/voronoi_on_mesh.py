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
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, ensure_min_nesting
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.voronoi3d import voronoi_on_mesh
from mathutils import Vector, Matrix
import numpy as np
import collections

def separate_loose_mesh(verts_in, poly_edge_in):
        ''' separate a mesh by loose parts.
        input:
          1. list of verts
          2. list of edges/polygons
        output: list of
          1. separated list of verts
          2. separated list of edges/polygons with new indices of separated elements
          3. separated list of edges/polygons (like 2) with old indices
        '''

        verts_out = []
        poly_edge_out = []
        poly_edge_old_indexes_out = []  # faces with old indices 

        # build links
        node_links = {}
        for edge_face in poly_edge_in:
            for i in edge_face:
                if i not in node_links:
                    node_links[i] = set()
                node_links[i].update(edge_face)

        nodes = set(node_links.keys())
        n = nodes.pop()
        node_set_list = [set([n])]
        node_stack = collections.deque()
        node_stack_append = node_stack.append
        node_stack_pop = node_stack.pop
        node_set = node_set_list[-1]
        # find separate sets
        while nodes:
            for node in node_links[n]:
                if node not in node_set:
                    node_stack_append(node)
            if not node_stack:  # new mesh part
                n = nodes.pop()
                node_set_list.append(set([n]))
                node_set = node_set_list[-1]
            else:
                while node_stack and n in node_set:
                    n = node_stack_pop()
                nodes.discard(n)
                node_set.add(n)
        # create new meshes from sets, new_pe is the slow line.
        if len(node_set_list) >= 1:
            for node_set in node_set_list:
                mesh_index = sorted(node_set)
                vert_dict = {j: i for i, j in enumerate(mesh_index)}
                new_vert = [verts_in[i] for i in mesh_index]
                new_pe = [[vert_dict[n] for n in fe]
                            for fe in poly_edge_in
                            if fe[0] in node_set]
                old_pe = [fe for fe in poly_edge_in
                             if fe[0] in node_set]
                verts_out.append(new_vert)
                poly_edge_out.append(new_pe)
                poly_edge_old_indexes_out.append(old_pe)
        elif node_set_list:  # no reprocessing needed
            verts_out.append(verts_in)
            poly_edge_out.append(poly_edge_in)
            poly_edge_old_indexes_out.append(poly_edge_in)

        return verts_out, poly_edge_out, poly_edge_old_indexes_out

class SvVoronoiOnMeshOffUnlinkedSocketsMK5(bpy.types.Operator):
    '''Hide all unlinked sockets'''
    bl_idname = "node.sv_on_voronoi_on_mesh_off_unlinked_sockets_mk5"
    bl_label = "Select object as active"
    description_text: bpy.props.StringProperty(default='Only hide unlinked output sockets.\nTo hide linked socket you have to unlink it first.')

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, property):
        s = property.description_text
        return s

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.node_group].nodes[self.node_name]
        #node = context.node
        if node:
            for s in node.outputs:
                if not s.is_linked:
                    s.hide = True
            pass
        return {'FINISHED'}

def draw_properties(layout, node_group, node_name):
    node = bpy.data.node_groups[node_group].nodes[node_name]
    #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
    root_grid = layout.grid_flow(row_major=False, columns=2, align=True)
    root_grid.alignment = 'EXPAND'
    grid1 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    grid1.label(text='Viewport Display:')

    grid2 = root_grid.grid_flow(row_major=False, columns=1, align=True)
    grid2.label(text='Output Sockets:')
    row0 = grid2.row(align=True)
    row0.label(text='- socket is visible', icon='CHECKBOX_HLT')
    row0.label(text='- socket is hidden', icon='CHECKBOX_DEHLT')
    grid2.separator()
    row_op = grid2.row(align=True)
    row_op.alignment = "LEFT"
    op = row_op.operator(SvVoronoiOnMeshOffUnlinkedSocketsMK5.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    op.node_group = node_group
    op.node_name  = node_name

    for s in node.outputs:
        row = grid2.row(align=True)
        row.enabled = not s.is_linked
        row.prop(s, 'hide', text=f'{s.label if s.label else s.name}{" (linked)" if s.is_linked else ""}', invert_checkbox=True)

    row_op = grid2.row(align=True)
    row_op.alignment = "LEFT"
    op = row_op.operator(SvVoronoiOnMeshOffUnlinkedSocketsMK5.bl_idname, icon='GP_CAPS_FLAT', text='Hide unlinked sockets', emboss=True)
    op.node_group = node_group
    op.node_name  = node_name
    pass


class SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5(bpy.types.Operator):
    '''Additional objects properties\nYou can pan dialog window out of node.'''
    # this combination do not show this panel on the right side panel
    bl_idname="sv.viewport_display_properties_dialog_voronoi_on_mesh_mk5"
    bl_label = "Objects 3DViewport properties as Dialog Window."

    # horizontal size
    # bl_ui_units_x = 40 - Has no influence in Dialog mode

    description_text: bpy.props.StringProperty(default='')
    node_group      : bpy.props.StringProperty(default='')
    node_name       : bpy.props.StringProperty(default='')

    # def is_extended():
    #     return True

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.node_name = context.node.name
        self.node_group = context.annotation_data_owner.name_full
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        draw_properties(self.layout, self.node_group, self.node_name)
        pass

class SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5(bpy.types.Panel):
    '''Additional objects properties'''
    # this combination do not show this panel on the right side panel
    bl_idname="SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5"
    bl_label = "Voronoi On Mesh Node properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    # @classmethod
    # def description(cls, context, properties):
    #     s = "properties.description_text"
    #     return s

    # horizontal size
    bl_ui_units_x = 22

    def draw(self, context):
        if hasattr(context, "node"):
            node_name = context.node.name
            node_group = context.annotation_data_owner.name_full
            draw_properties(self.layout, node_group, node_name)
        pass


class SvVoronoiOnMeshNodeMK5(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Voronoi Mesh
    Tooltip: Generate Voronoi diagram on the surface of a mesh object
    """
    bl_idname = 'SvVoronoiOnMeshNodeMK5'
    bl_label = 'Voronoi on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'scipy'}

    modes = [
            ('VOLUME', "Split Volume", "Split volume of the mesh into regions of Voronoi diagram", 0),
            ('SURFACE', "Split Surface", "Split the surface of the mesh into regions of Vornoi diagram", 1),
            #('RIDGES', "Ridges near Surface", "Generate ridges of 3D Voronoi diagram near the surface of the mesh", 2),
            #('REGIONS', "Regions near Surface", "Generate regions of 3D Voronoi diagram near the surface of the mesh", 3)
        ]

    spacing : FloatProperty(
        name = "Spacing",
        default = 0.0,
        #min = 0.0,
        description="Percent of space to leave between generated fragment meshes",
        update=updateNode) # type: ignore

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Make sure that all normals of generated meshes point outside (Works in volume mode only)",
        update = updateNode) # type: ignore

    def update_sockets(self, context):
        self.inputs['spacing'].hide_safe = self.mode not in {'VOLUME', 'SURFACE'}
        updateNode(self, context)

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'VOLUME',
        update = update_sockets) # type: ignore
    
    results_join_modes = [
            ('SPLIT', "Split (disconnect)", "Post processing: Separate the result meshes into individual meshes", 'SNAP_VERTEX', 0),
            ('KEEP', "Keep", "Post processing: Keep parts of the source meshes as source meshes.", 'SYNTAX_ON', 1),
            ('MERGE', "Merge", "Post processing: Join all results meshes into a single mesh", 'STICKY_UVS_LOC', 2)
        ]

    results_join_mode : EnumProperty(
        name = "Output mode",
        items = results_join_modes,
        default = 'KEEP',
        update = updateNode) # type: ignore
    
    results_objects_origins_modes = [
            ('ALIGHT_PARENT_OBJECTS_ORIGIN', "Parent origins", "Post processing: Align results objects origins to parent objects origins", 'ORIENTATION_VIEW', 0),
            ('ALIGHT_INPUT_SITES', "Sites origins", "Post processing: Align results objects origins to input sites", 'STICKY_UVS_DISABLE', 1),
        ]

    results_objects_origins : EnumProperty(
        name = "Origins results objects",
        default = 'ALIGHT_PARENT_OBJECTS_ORIGIN',
        items = results_objects_origins_modes,
        description="Set results objects origins",
        update = updateNode) # type: ignore
    
    source_objects_join_modes = [
            ('SPLIT', "Split (disconnect)", "Separate the result meshes into individual meshes", 'SNAP_VERTEX', 0),
            ('KEEP' , "Keep", "Keep as input meshes", 'SYNTAX_ON', 1),
            ('MERGE', "Merge", "Join all meshes into a single mesh", 'STICKY_UVS_LOC', 2)
        ]

    source_objects_join_mode : EnumProperty(
        name = "How process input objects",
        items = source_objects_join_modes,
        default = 'KEEP',
        update = updateNode) # type: ignore

    def updateMaskMode(self, context):
        if self.mask_mode=='BOOLEAN':
            self.inputs["voronoi_sites_mask"].label = "Mask of Sites"
        elif self.mask_mode=='INDEXES':
            self.inputs["voronoi_sites_mask"].label = "Indexes of Sites"
        updateNode(self, context)

    mask_modes = [
            ('BOOLEAN', "Booleans", "Boolean values (0/1) as mask of Voronoi Sites per objects [[0,1,0,0,1,1],[1,1,0,0,1],...]. Has no influence if socket is not connected (All sites are used)", 0),
            ('INDEXES', "Indexes", "Indexes as mask of Voronoi Sites per objects [[1,2,0,4],[0,1,4,5,7],..]. Has no influence if socket is not connected (All sites are used)", 1),
        ]
    mask_mode : EnumProperty(
        name = "Mask mode",
        items = mask_modes,
        default = 'BOOLEAN',
        #update = updateMaskMode
        update = updateNode
        ) # type: ignore

    mask_inversion : BoolProperty(
        name = "Invert",
        default = False,
        description="Invert mask of sites. Has no influence if socket is not connected (All sites are used)",
        update = updateNode) # type: ignore


    accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy for mesh bisecting procedure",
            default = 6,
            min = 1,
            update = updateNode) # type: ignore
    
    def draw_vertices_in_socket(self, socket, context, layout):
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f'{socket.label}')
        layout.prop(self, 'source_objects_join_mode', text='')
        pass

    def draw_vertices_out_socket(self, socket, context, layout):
        layout.prop(self, 'results_join_mode', text='')
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f'{socket.label}')
        pass

    def draw_matrices_out_socket(self, socket, context, layout):
        col = layout.row(align=True)
        col.alignment='RIGHT'
        col_prop = col.row()
        col_prop.alignment='RIGHT'
        if self.results_join_mode!='SPLIT':
            col_prop.enabled=False
        col_prop.prop(self, 'results_objects_origins', text='')
        if socket.is_linked:  # linked INPUT or OUTPUT
            col.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            col.label(text=f'{socket.label}')
        pass

    def draw_voronoi_sites_mask_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=True, columns=2)
        if not socket.is_linked:
            grid.enabled = False
        col2 = grid.column()
        col2_row1 = col2.row()
        col2_row1.alignment='LEFT'
        if socket.is_linked:
            col2_row1.label(text=f"Mask of sites. {socket.objects_number or ''}:")
        else:
            col2_row1.label(text=f"Mask of sites:")
        col2_row2 = col2.row()
        col2_row2.alignment='LEFT'
        col2_row2.column(align=True).prop(self, "mask_inversion")
        col3 = grid.column()
        col3.prop(self, "mask_mode", expand=True)


    def sv_init(self, context):
        self.width = 250
        self.inputs.new('SvVerticesSocket', 'vertices'          ).label     = 'Vertices'
        self.inputs.new('SvStringsSocket' , 'polygons'          ).label     = 'Polygons'
        self.inputs.new('SvMatrixSocket'  , 'matrices'          ).label     = 'Matrices of Meshes'
        self.inputs.new('SvVerticesSocket', 'voronoi_sites'     ).label     = 'Voronoi Sites'
        self.inputs.new('SvStringsSocket' , 'voronoi_sites_mask').label     = "Mask of Voronoi Sites"
        self.inputs.new('SvStringsSocket' , 'spacing'           ).prop_name = 'spacing'

        self.inputs['vertices'].custom_draw = 'draw_vertices_in_socket'
        self.inputs['voronoi_sites_mask'].custom_draw = 'draw_voronoi_sites_mask_in_socket'

        self.outputs.new('SvVerticesSocket', "vertices"             ).label = 'Vertices'
        self.outputs.new('SvVerticesSocket', "verticesOuter"        ).label = 'Vertices Outer'
        self.outputs.new('SvVerticesSocket', "verticesInner"        ).label = 'Vertices Inner'
        self.outputs.new('SvVerticesSocket', "verticesBorder"       ).label = 'Vertices Border'
        self.outputs.new('SvStringsSocket' , "verticesOuterIndexes" ).label = 'Vertices Outer Indexes'
        self.outputs.new('SvStringsSocket' , "verticesInnerIndexes" ).label = 'Vertices Inner Indexes'
        self.outputs.new('SvStringsSocket' , "verticesBorderIndexes").label = 'Vertices Border Indexes'
        self.outputs.new('SvStringsSocket' , "verticesOuterMasks"   ).label = 'Vertices Outer Masks'
        self.outputs.new('SvStringsSocket' , "verticesInnerMasks"   ).label = 'Vertices Inner Masks'
        self.outputs.new('SvStringsSocket' , "verticesBorderMasks"  ).label = 'Vertices Border Masks'
        self.outputs.new('SvStringsSocket' , "edges"                ).label = 'Edges'
        self.outputs.new('SvStringsSocket' , "edgesOuter"           ).label = 'Edges Outer'
        self.outputs.new('SvStringsSocket' , "edgesInner"           ).label = 'Edges Inner'
        self.outputs.new('SvStringsSocket' , "edgesBorder"          ).label = 'Edges Border'
        self.outputs.new('SvStringsSocket' , "edgesOuterIndexes"    ).label = 'Edges Outer Indexes'
        self.outputs.new('SvStringsSocket' , "edgesInnerIndexes"    ).label = 'Edges Inner Indexes'
        self.outputs.new('SvStringsSocket' , "edgesBorderIndexes"   ).label = 'Edges Border Indexes'
        self.outputs.new('SvStringsSocket' , "edgesOuterMasks"      ).label = 'Edges Outer Masks'
        self.outputs.new('SvStringsSocket' , "edgesInnerMasks"      ).label = 'Edges Inner Masks'
        self.outputs.new('SvStringsSocket' , "edgesBorderMasks"     ).label = 'Edges Border Masks'
        self.outputs.new('SvStringsSocket' , "polygons"             ).label = 'Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsOuterInner"   ).label = 'Polygons Outer Inner Mask'
        self.outputs.new('SvStringsSocket' , "polygonsOuter"        ).label = 'Polygons Outer'
        self.outputs.new('SvStringsSocket' , "polygonsInner"        ).label = 'Polygons Inner'
        self.outputs.new('SvStringsSocket' , "polygonsOuterIndexes" ).label = 'Polygons Outer Indexes'
        self.outputs.new('SvStringsSocket' , "polygonsInnerIndexes" ).label = 'Polygons Inner Indexes'
        self.outputs.new('SvStringsSocket' , "polygonsOuterMasks"   ).label = 'Polygons Outer Masks'
        self.outputs.new('SvStringsSocket' , "polygonsInnerMasks"   ).label = 'Polygons Inner Masks'
        self.outputs.new('SvStringsSocket' , "sites_idx"            ).label = 'Used Sites Idx'
        self.outputs.new('SvStringsSocket' , "sites_verts"          ).label = 'Used Sites Verts'
        self.outputs.new('SvMatrixSocket'  , 'matrices'             ).label = 'Origins Matrices'
        self.outputs.new('SvMatrixSocket'  , 'matrices_split_mode'  ).label = 'Local Sites'

        self.outputs['vertices'].custom_draw = 'draw_vertices_out_socket'
        self.outputs['matrices'].custom_draw = 'draw_matrices_out_socket'

        self.outputs["verticesOuter"]           .hide = True
        self.outputs["verticesInner"]           .hide = True
        self.outputs["verticesBorder"]          .hide = True
        self.outputs["verticesOuterIndexes"]    .hide = True
        self.outputs["verticesInnerIndexes"]    .hide = True
        self.outputs["verticesBorderIndexes"]   .hide = True
        self.outputs["edgesOuter"]              .hide = True
        self.outputs["edgesInner"]              .hide = True
        self.outputs["edgesBorder"]             .hide = True
        self.outputs["edgesOuterIndexes"]       .hide = True
        self.outputs["edgesInnerIndexes"]       .hide = True
        self.outputs["edgesBorderIndexes"]      .hide = True
        self.outputs["polygonsOuterInner"]      .hide = True
        self.outputs["polygonsOuter"]           .hide = True
        self.outputs["polygonsInner"]           .hide = True
        self.outputs["polygonsOuterIndexes"]    .hide = True
        self.outputs["polygonsInnerIndexes"]    .hide = True

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        row0 = layout.row(align=True)
        row0.alignment='RIGHT'
        row0_col0 = row0.column(align=True)
        row0_col0.alignment='RIGHT'
        row0_col0.label(text='Settings: ')
        row0.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row0.column(align=True).popover(panel=SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5.bl_idname, icon='DOWNARROW_HLT', text="")

        layout.label(text="Mode:")
        layout.prop(self, "mode", expand=True)
        row1 = layout.row(align=True)
        row1.prop(self, 'normals')
        if self.mode != 'VOLUME':
            row1.enabled = False
        pass

    def draw_buttons_ext(self, context, layout):
        #self.draw_buttons(context, layout)
        layout.label(text="Mode:")
        layout.prop(self, "mode", expand=True)
        layout.prop(self, 'accuracy')
        # TODO: remove input sockets
        pass

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return
        
        if self.inputs["vertices"].is_linked:
            if self.inputs["polygons"].is_linked==False:
                raise Exception(f'socket Polygons are not connected')
            if self.inputs["voronoi_sites"].is_linked==False:
                raise Exception(f'socket "Voronoi Sites" are not connected')

        verts_in    = self.inputs['vertices']      .sv_get(deepcopy=False)
        faces_in    = self.inputs['polygons']      .sv_get(deepcopy=False)
        _Matrices   = self.inputs['matrices'].sv_get(default=[[Matrix()]], deepcopy=False)
        Matrices2   = ensure_nesting_level(_Matrices, 2)
        sites_in    = self.inputs['voronoi_sites'] .sv_get(deepcopy=False)

        mask_in     = self.inputs['voronoi_sites_mask'] #.sv_get(deepcopy=False)
        if mask_in.is_linked==False:
            mask_in = [[]]
        else:
            mask_in = mask_in.sv_get(deepcopy=False)
            
        spacing_in  = self.inputs['spacing'].sv_get(deepcopy=False)

        verts_in    = ensure_nesting_level(verts_in, 3)
        input_level = get_data_nesting_level(sites_in, search_first_data=True)
        if input_level<=2:
            sites_in = ensure_nesting_level(sites_in, 3)

        faces_in    = ensure_nesting_level(faces_in, 3)
        spacing_in  = ensure_min_nesting(spacing_in, 2)
        mask_in     = ensure_min_nesting(mask_in, 2)

        precision   = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        matrices_out = []
        matrices_split_mode_out = []
        outer_verts_property_out = []
        outer_edges_property_out = []
        outer_polygons_property_out = []
        sites_idx_out = []
        sites_verts_out = []

        matrix_0 = None
        matrix_0_inverted = None

        verts_in_1 = []
        faces_in_1 = []
        sites_in_1 = []
        spacing_in_1 = []
        mask_in_1 = []
        matrices_in_1 = []

        len_verts_in = len(verts_in)
        if len_verts_in>len(faces_in):
            raise Exception(f'list of verts less than faces [{len(verts_in)}<{len(faces_in)}]')
        
        #for I, (verts_I, faces_I, sites_I, spacing_I, mask_I) in enumerate(zip_long_repeat(verts_in, faces_in, sites_in, spacing_in, mask_in)):
        for I, verts_I in enumerate(verts_in):
            faces_I = faces_in[I if I<=len(faces_in)-1 else -1]
            sites_I = sites_in[I if I<=len(sites_in)-1 else -1]
            spacing_I = spacing_in[I if I<=len(spacing_in)-1 else -1]
            mask_I = mask_in[I if I<=len(mask_in)-1 else -1]

            if len(faces_I)==0:
                raise Exception(f'no faces in Polygons[{I}]')
            if len(sites_I)==0:
                raise Exception(f'no sites in socket "Voronoi Sites" {I} ')
            else:
                empty_sites = [I for I, s in enumerate(sites_I) if len(s)==0]
                if len(empty_sites)>0:
                    raise Exception(f'no sites in socket "Voronoi Sites" {empty_sites}')

            if I<=len(Matrices2[0])-1:
                matrix_I = Matrices2[0][I]
            else:
                matrix_I = Matrices2[0][-1]
            
            if matrix_0 is None:
                matrix_0 = matrix_I
                matrix_0_inverted = matrix_0.inverted()

            # if mask is zero or not connected then do not mask any. Except of inversion,
            if not mask_I:
                np_mask = np.ones(len(sites_I), dtype=bool)
                if self.inputs['voronoi_sites_mask'].is_linked and self.mask_inversion==True:
                    np_mask = np.invert(np_mask)
                mask_I = np_mask.tolist()
            else:
                if self.mask_mode=='BOOLEAN':
                    if self.mask_inversion==True:
                        mask_I = list( map( lambda v: False if v==0 else True, mask_I) )
                        mask_I = mask_I[:len(sites_I)]
                        np_mask = np.zeros(len(sites_I), dtype=bool)
                        np_mask[0:len(mask_I)]=mask_I
                        np_mask = np.invert(np_mask)
                        mask_I = np_mask.tolist()
                    pass
                elif self.mask_mode=='INDEXES':
                    mask_len = len(sites_I)
                    mask_range = []
                    for x in mask_I:
                        if -mask_len<x<mask_len:
                            mask_range.append(x)
                    np_mask = np.zeros(len(sites_I), dtype=bool)
                    np_mask[mask_range] = True
                    if self.mask_inversion==True:
                        np_mask = np.invert(np_mask)
                    mask_I = np_mask.tolist()
                pass

            mtr = matrix_I@matrix_0_inverted

            verts_in_1   .append(verts_I)
            faces_in_1   .append(faces_I)
            matrices_in_1.append(matrix_I)
            sites_in_1   .append(sites_I)
            spacing_in_1 .append(spacing_I)
            mask_in_1    .append(mask_I)

            pass


        verts_in_2    = []
        faces_in_2    = []
        matrices_in_2 = []
        sites_in_2    = []
        spacing_in_2  = []
        mask_in_2     = []

        if self.source_objects_join_mode=='SPLIT':
            for I, verts_in_1_I in enumerate(verts_in_1):
                objects_I_verts, object_I_faces, _ = separate_loose_mesh(verts_in_1_I, faces_in_1[I])
                if len(objects_I_verts)>1:
                    for IJ, verts_IJ in enumerate(objects_I_verts):
                        verts_in_2   .append(verts_IJ          )
                        faces_in_2   .append(object_I_faces[IJ])
                        matrices_in_2.append(matrices_in_1 [I ])
                        sites_in_2   .append(sites_in_1    [I ])
                        spacing_in_2 .append(spacing_in_1  [I ])
                        mask_in_2    .append(mask_in_1     [I ])
                        pass
                else:
                    verts_in_2   .append(verts_in_1_I     )
                    faces_in_2   .append(faces_in_1    [I])
                    matrices_in_2.append(matrices_in_1 [I])
                    sites_in_2   .append(sites_in_1    [I])
                    spacing_in_2 .append(spacing_in_1  [I])
                    mask_in_2    .append(mask_in_1     [I])
                pass
            pass
        elif self.source_objects_join_mode=='MERGE':
            matrices_in_1_0_inverted = matrices_in_1[0].inverted()
            verts_for_merge = [verts_in_1[0]]
            sites_for_merge = sites_in_1[0][:]
            for I, mat_I in enumerate(matrices_in_1):
                if I>0:
                    mat = matrices_in_1_0_inverted @ mat_I
                    verts_mat = []
                    for v in verts_in_1[I]:
                        v1 = mat @ Vector(v)
                        verts_mat.append( (v1.x, v1.y, v1.z) )
                        pass
                    verts_for_merge.append(verts_mat)

                    sites_mat = []
                    # On merge source meshes do use source sites, not zipped in zip_long_repeat. 
                    # If original sites are less objects then use only these sites
                    if len(sites_in)-1>=I:
                        for s in sites_in[I]:
                            s1 = mat @ Vector(s)
                            sites_mat.append((s1.x, s1.y, s1.z))
                            pass
                        sites_for_merge.extend(sites_mat)
                    #sites_for_merge.extend(sites_in_1[I]) # use sites as local
                    pass
                pass
            merged_verts, _, merged_faces  = mesh_join(verts_for_merge, [], faces_in_1)
            verts_in_2       = [merged_verts]
            faces_in_2       = [merged_faces]
            matrices_in_2.append(matrices_in_1[0])
            sites_in_2       = [sites_for_merge]
            spacing_in_2     = [spacing_in_1[0]]
            merged_masks = []
            for m in mask_in_1:
                merged_masks = merged_masks+m
            mask_in_2 = [merged_masks]
            pass
        else:
            verts_in_2    = verts_in_1
            faces_in_2    = faces_in_1
            matrices_in_2 = matrices_in_1
            sites_in_2    = sites_in_1
            spacing_in_2  = spacing_in_1
            mask_in_2     = mask_in_1
            pass
        pass



        for I, (verts_I, faces_I, matrices_I, sites_I, spacing_I, mask_I) in enumerate( zip(verts_in_2, faces_in_2, matrices_in_2, sites_in_2, spacing_in_2, mask_in_2) ):
            new_verts, new_edges, new_faces, new_used_sites_idx, new_used_sites_verts, outer_verts_property, outer_edges_property, outer_faces_property = voronoi_on_mesh(verts_I, faces_I, sites_I, thickness=0,
                            spacing = spacing_I,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.mode,
                            normal_update = self.normals,
                            precision = precision,
                            mask = mask_I
                            )

            # collect sites_idx and used_sites_verts independently of self.results_join_mode
            sites_idx_out.append(new_used_sites_idx)
            sites_verts_out.append(new_used_sites_verts)
            
            if self.results_join_mode == 'SPLIT':
                if self.results_objects_origins=='ALIGHT_INPUT_SITES':
                    for IJ, obj_verts in enumerate(new_verts):
                        s1 = new_used_sites_verts[IJ]
                        mat_site_translation = Matrix.Translation(s1)
                        mat_site_translation_inverted = mat_site_translation.inverted()
                        obj_verts_site = []
                        for obj_vert in obj_verts:
                            v = mat_site_translation_inverted @ Vector(obj_vert)
                            obj_verts_site.append(v)
                        verts_out.append(obj_verts_site)
                        matrices_split_mode_out.append(mat_site_translation)
                    pass
                elif self.results_objects_origins=='ALIGHT_PARENT_OBJECTS_ORIGIN':
                    verts_out.extend(new_verts)
                    matrices_split_mode_out.extend([Matrix()]*len(new_verts))
                    pass
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                # for s1 in new_used_sites_verts:
                #     mat_site_translation = Matrix.Translation(s1)
                #     mat = matrices_I @ mat_site_translation.inverted()
                #     matrices_split_mode_out.append(mat_site_translation)
                #     matrices_out.append(mat)
                matrices_out.extend([matrices_I]*len(new_verts))
                outer_verts_property_out.extend(outer_verts_property) # dict {is_outer:True/False, is_inner: True/False}
                outer_edges_property_out.extend(outer_edges_property) # dict {is_outer:True/False, is_inner: True/False}
                outer_polygons_property_out.extend(outer_faces_property)
            elif self.results_join_mode == 'KEEP' or self.results_join_mode == 'MERGE':
                if self.results_join_mode == 'KEEP':
                    matrices_out.append(matrices_I)
                    matrices_split_mode_out.append(Matrix())
                verts1, edges1, faces1 = mesh_join(new_verts, new_edges, new_faces)
                verts_out.append(verts1)
                edges_out.append(edges1)
                faces_out.append(faces1)
                outer_verts = [item for sublist in outer_verts_property for item in sublist]
                outer_verts_property_out.append(outer_verts)  # dict {is_outer:True/False, is_inner: True/False}
                outer_edges = [item for sublist in outer_edges_property for item in sublist]
                outer_edges_property_out.append(outer_edges)  # dict {is_outer:True/False, is_inner: True/False}
                outer_faces = [item for sublist in outer_faces_property for item in sublist]
                outer_polygons_property_out.append(outer_faces)
            pass

        if self.results_join_mode == 'MERGE':
            matrices_in_1_0_inverted = matrices_in_1[0].inverted()
            verts_out_for_merge = [verts_out[0]]
            for I, mat_I in enumerate(matrices_in_2):
                if I>0:
                    mat = matrices_in_1_0_inverted @ mat_I
                    verts_mat = []
                    for v in verts_out[I]:
                        v1 = mat @ Vector(v)
                        verts_mat.append( (v1.x, v1.y, v1.z) )
                        pass
                    verts_out_for_merge.append(verts_mat)
                    pass
                pass
            verts1, edges1, faces1 = mesh_join(verts_out_for_merge, edges_out, faces_out)
            verts_out = [verts1]
            edges_out = [edges1]
            faces_out = [faces1]
            matrices_out.append(matrices_in_2[0])
            matrices_split_mode_out.append(Matrix())
            outer_verts = [item for sublist in outer_verts_property_out for item in sublist]
            outer_verts_property_out = [outer_verts]
            outer_edges = [item for sublist in outer_edges_property_out for item in sublist]
            outer_edges_property_out = [outer_edges]
            outer_faces = [item for sublist in outer_polygons_property_out for item in sublist]
            outer_polygons_property_out = [outer_faces]
            pass

        vertsOuter_out = []
        vertsInner_out = []
        vertsBorder_out = []
        vertsOuterIndexes_out = []
        vertsInnerIndexes_out = []
        vertsBorderIndexes_out = []
        vertsOuterMasks_out = []
        vertsInnerMasks_out = []
        vertsBorderMasks_out = []
        for I, mask in enumerate(outer_verts_property_out):
            verts_out_I = verts_out[I]
            len_verts_out_I = len(verts_out_I)
            vertsOuter_out_I = []
            vertsInner_out_I = []
            vertsBorder_out_I = []
            vertsOuterIndexes_out_I = []
            vertsInnerIndexes_out_I = []
            vertsBorderIndexes_out_I = []
            vertsOuterMasks_out_I  = [False]*len_verts_out_I
            vertsInnerMasks_out_I  = [False]*len_verts_out_I
            vertsBorderMasks_out_I = [False]*len_verts_out_I
            for IJ, (m, v) in enumerate(zip(mask, verts_out_I)):
                m_is_outer = m["is_outer"]
                m_is_inner = m["is_inner"]
                if m_is_outer==True:
                    vertsOuter_out_I       .append(v)
                    vertsOuterIndexes_out_I.append(IJ)
                    vertsOuterMasks_out_I[IJ] = True
                if m_is_inner==True:
                    vertsInner_out_I       .append(v)
                    vertsInnerIndexes_out_I.append(IJ)
                    vertsInnerMasks_out_I[IJ] = True

                if self.mode=='VOLUME':
                    if m_is_outer==True and m_is_inner==True:
                        vertsBorder_out_I       .append(v)
                        vertsBorderIndexes_out_I.append(IJ)
                        vertsBorderMasks_out_I[IJ] = True
                    pass
                elif self.mode=='SURFACE':
                    m_is_surface_border = m["is_surface_border"]
                    if m_is_surface_border==True:
                        vertsBorder_out_I       .append(v)
                        vertsBorderIndexes_out_I.append(IJ)
                        vertsBorderMasks_out_I[IJ] = True
                    pass
                else:
                    raise Exception(f'Unknown mode="{self.mode}" in SvVoronoiOnMeshNodeMK5->process')
                
                if self.mode=='SURFACE':
                    pass
                pass
            vertsOuter_out        .append(vertsOuter_out_I)
            vertsInner_out        .append(vertsInner_out_I)
            vertsBorder_out       .append(vertsBorder_out_I)
            vertsOuterIndexes_out .append(vertsOuterIndexes_out_I)
            vertsInnerIndexes_out .append(vertsInnerIndexes_out_I)
            vertsBorderIndexes_out.append(vertsBorderIndexes_out_I)
            vertsOuterMasks_out   .append(vertsOuterMasks_out_I)
            vertsInnerMasks_out   .append(vertsInnerMasks_out_I)
            vertsBorderMasks_out  .append(vertsBorderMasks_out_I)
            pass

        edgesOuter_out = []
        edgesInner_out = []
        edgesBorder_out = []
        edgesOuterIndexes_out = []
        edgesInnerIndexes_out = []
        edgesBorderIndexes_out = []
        edgesOuterMasks_out = []
        edgesInnerMasks_out = []
        edgesBorderMasks_out = []

        for I, mask in enumerate(outer_edges_property_out):
            edges_out_I = edges_out[I]
            len_edges_out_I = len(edges_out_I)
            edgesOuter_out_I = []
            edgesInner_out_I = []
            edgesBorder_out_I = []
            edgesOuterIndexes_out_I = []
            edgesInnerIndexes_out_I = []
            edgesBorderIndexes_out_I = []
            edgesOuterMasks_out_I  = [False]*len_edges_out_I
            edgesInnerMasks_out_I  = [False]*len_edges_out_I
            edgesBorderMasks_out_I = [False]*len_edges_out_I

            for IJ, (m, v) in enumerate(zip(mask, edges_out_I)):
                m_is_outer = m["is_outer"]
                m_is_inner = m["is_inner"]
                if m_is_outer==True:
                    edgesOuter_out_I.append(v)
                    edgesOuterIndexes_out_I.append(IJ)
                    edgesOuterMasks_out_I[IJ] = True
                if m_is_inner==True:
                    edgesInner_out_I.append(v)
                    edgesInnerIndexes_out_I.append(IJ)
                    edgesInnerMasks_out_I[IJ] = True
                if self.mode=='VOLUME':
                    if m_is_outer==True and m_is_inner==True:
                        edgesBorder_out_I.append(v)
                        edgesBorderIndexes_out_I.append(IJ)
                        edgesBorderMasks_out_I[IJ] = True
                    pass
                elif self.mode=='SURFACE':
                    m_is_surface_border = m["is_surface_border"]
                    if m_is_surface_border==True:
                        edgesBorder_out_I.append(v)
                        edgesBorderIndexes_out_I.append(IJ)
                        edgesBorderMasks_out_I[IJ] = True
                        pass
                    pass
                else:
                    raise Exception(f'Unknown mode="{self.mode}" in SvVoronoiOnMeshNodeMK5->process')
                
                if self.mode=='SURFACE':
                    pass
                pass
            edgesOuter_out.append(edgesOuter_out_I)
            edgesInner_out.append(edgesInner_out_I)
            edgesBorder_out.append(edgesBorder_out_I)
            edgesOuterIndexes_out.append(edgesOuterIndexes_out_I)
            edgesInnerIndexes_out.append(edgesInnerIndexes_out_I)
            edgesBorderIndexes_out.append(edgesBorderIndexes_out_I)
            edgesOuterMasks_out   .append(edgesOuterMasks_out_I)
            edgesInnerMasks_out   .append(edgesInnerMasks_out_I)
            edgesBorderMasks_out  .append(edgesBorderMasks_out_I)

            pass

        polygonsOuter_out = []
        polygonsInner_out = []
        polygonsOuterIndexes_out = []
        polygonsInnerIndexes_out = []
        polygonsOuterMasks_out = []
        polygonsInnerMasks_out = []

        for I, mask in enumerate(outer_polygons_property_out):
            faces_out_I = faces_out[I]
            len_faces_out_I = len(faces_out_I)
            polygonsOuter_out_I = []
            polygonsInner_out_I = []
            polygonsOuterIndexes_out_I = []
            polygonsInnerIndexes_out_I = []
            polygonsOuterMasks_out_I  = [False]*len_faces_out_I
            polygonsInnerMasks_out_I  = [False]*len_faces_out_I

            for IJ, (m, v) in enumerate(zip(mask, faces_out_I)):
                if m==1:
                    polygonsOuter_out_I.append(v)
                    polygonsOuterIndexes_out_I.append(IJ)
                    polygonsOuterMasks_out_I[IJ] = True
                else:
                    polygonsInner_out_I.append(v)
                    polygonsInnerIndexes_out_I.append(IJ)
                    polygonsInnerMasks_out_I[IJ] = True
                pass
            polygonsOuter_out.append(polygonsOuter_out_I)
            polygonsInner_out.append(polygonsInner_out_I)
            polygonsOuterIndexes_out.append(polygonsOuterIndexes_out_I)
            polygonsInnerIndexes_out.append(polygonsInnerIndexes_out_I)
            polygonsOuterMasks_out   .append(polygonsOuterMasks_out_I)
            polygonsInnerMasks_out   .append(polygonsInnerMasks_out_I)

            pass

        self.outputs['vertices'             ].sv_set(verts_out)
        self.outputs['verticesOuter'        ].sv_set(vertsOuter_out)
        self.outputs['verticesInner'        ].sv_set(vertsInner_out)
        self.outputs['verticesBorder'       ].sv_set(vertsBorder_out)
        self.outputs['verticesOuterIndexes' ].sv_set(vertsOuterIndexes_out)
        self.outputs['verticesInnerIndexes' ].sv_set(vertsInnerIndexes_out)
        self.outputs['verticesBorderIndexes'].sv_set(vertsBorderIndexes_out)
        self.outputs['verticesOuterMasks'   ].sv_set(vertsOuterMasks_out)
        self.outputs['verticesInnerMasks'   ].sv_set(vertsInnerMasks_out)
        self.outputs['verticesBorderMasks'  ].sv_set(vertsBorderMasks_out)
        self.outputs['edges'                ].sv_set(edges_out)
        self.outputs['edgesOuter'           ].sv_set(edgesOuter_out)
        self.outputs['edgesInner'           ].sv_set(edgesInner_out)
        self.outputs['edgesBorder'          ].sv_set(edgesBorder_out)
        self.outputs['edgesOuterIndexes'    ].sv_set(edgesOuterIndexes_out)
        self.outputs['edgesInnerIndexes'    ].sv_set(edgesInnerIndexes_out)
        self.outputs['edgesBorderIndexes'   ].sv_set(edgesBorderIndexes_out)
        self.outputs['edgesOuterMasks'      ].sv_set(edgesOuterMasks_out)
        self.outputs['edgesInnerMasks'      ].sv_set(edgesInnerMasks_out)
        self.outputs['edgesBorderMasks'     ].sv_set(edgesBorderMasks_out)
        self.outputs['polygons'             ].sv_set(faces_out)
        self.outputs['polygonsOuterInner'   ].sv_set(outer_polygons_property_out)
        self.outputs['polygonsOuter'        ].sv_set(polygonsOuter_out)
        self.outputs['polygonsInner'        ].sv_set(polygonsInner_out)
        self.outputs['polygonsOuterIndexes' ].sv_set(polygonsOuterIndexes_out)
        self.outputs['polygonsInnerIndexes' ].sv_set(polygonsInnerIndexes_out)
        self.outputs['polygonsOuterMasks'   ].sv_set(polygonsOuterMasks_out)
        self.outputs['polygonsInnerMasks'   ].sv_set(polygonsInnerMasks_out)
        self.outputs['sites_idx'            ].sv_set(sites_idx_out)
        self.outputs['sites_verts'          ].sv_set(sites_verts_out)
        self.outputs['matrices'             ].sv_set(matrices_out)
        self.outputs['matrices_split_mode'  ].sv_set(matrices_split_mode_out)

classes = [SvVoronoiOnMeshOffUnlinkedSocketsMK5, SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5, SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5, SvVoronoiOnMeshNodeMK5]
register, unregister = bpy.utils.register_classes_factory(classes)