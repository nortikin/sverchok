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
import numpy as np

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
    bl_label = "Voronoi Onn Mesh Node properties"
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
        min = 0.0,
        description="Percent of space to leave between generated fragment meshes",
        update=updateNode) # type: ignore

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="Make sure that all normals of generated meshes point outside",
        update = updateNode) # type: ignore

    def update_sockets(self, context):
        self.inputs['spacing'].hide_safe = self.mode not in {'VOLUME', 'SURFACE'}
        updateNode(self, context)

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        default = 'VOLUME',
        update = update_sockets) # type: ignore
    
    join_modes = [
            ('FLAT', "Separate All Meshes", "Post processing: Separate the result meshes into individual meshes", 'SNAP_VERTEX', 0),
            ('SEPARATE', "Keep Source Meshes", "Post processing: Keep parts of the source meshes as source meshes.", 'SYNTAX_ON', 1),
            ('JOIN', "Join All Meshes", "Post processing: Join all results meshes into a single mesh", 'STICKY_UVS_LOC', 2)
        ]

    join_mode : EnumProperty(
        name = "Output mode",
        items = join_modes,
        default = 'FLAT',
        update = updateNode) # type: ignore

    def updateMaskMode(self, context):
        if self.mask_mode=='MASK':
            self.inputs["voronoi_sites_mask"].label = "Mask of Sites"
        elif self.mask_mode=='INDEXES':
            self.inputs["voronoi_sites_mask"].label = "Indexes of Sites"
        updateNode(self, context)

    mask_modes = [
            ('MASK', "Booleans", "Boolean values (0/1) as mask of Voronoi Sites per objects [[0,1,0,0,1,1],[1,1,0,0,1],...]. Has no influence if socket is not connected (All sites are used)", 0),
            ('INDEXES', "Indexes", "Indexes as mask of Voronoi Sites per objects [[1,2,0,4],[0,1,4,5,7],..]. Has no influence if socket is not connected (All sites are used)", 1),
        ]
    mask_mode : EnumProperty(
        name = "Mask mode",
        items = mask_modes,
        default = 'MASK',
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

    def draw_vertices_out_socket(self, socket, context, layout):
        layout.prop(self, 'join_mode', text='')
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f'{socket.label}')
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
        self.inputs.new('SvVerticesSocket', 'vertices').label = 'Vertices'
        self.inputs.new('SvStringsSocket', 'polygons').label = 'Polygons'
        self.inputs.new('SvVerticesSocket', 'voronoi_sites').label = 'Voronoi Sites'
        self.inputs.new('SvStringsSocket', 'voronoi_sites_mask').label = "Mask of Voronoi Sites"
        self.inputs.new('SvStringsSocket', 'spacing').prop_name = 'spacing'

        self.inputs['voronoi_sites_mask'].custom_draw = 'draw_voronoi_sites_mask_in_socket'

        self.outputs.new('SvVerticesSocket', "vertices"             ).label = 'Vertices'
        self.outputs.new('SvVerticesSocket', "verticesOuter"        ).label = 'Vertices Outer'
        self.outputs.new('SvVerticesSocket', "verticesInner"        ).label = 'Vertices Inner'
        self.outputs.new('SvVerticesSocket', "verticesBorder"       ).label = 'Vertices Border'
        self.outputs.new('SvStringsSocket' , "verticesOuterIndexes" ).label = 'Vertices Outer Indexes'
        self.outputs.new('SvStringsSocket' , "verticesInnerIndexes" ).label = 'Vertices Inner Indexes'
        self.outputs.new('SvStringsSocket' , "verticesBorderIndexes").label = 'Vertices Border Indexes'
        self.outputs.new('SvStringsSocket' , "edges"                ).label = 'Edges'
        self.outputs.new('SvStringsSocket' , "edgesOuter"           ).label = 'Edges Outer'
        self.outputs.new('SvStringsSocket' , "edgesInner"           ).label = 'Edges Inner'
        self.outputs.new('SvStringsSocket' , "edgesBorder"          ).label = 'Edges Border'
        self.outputs.new('SvStringsSocket' , "edgesOuterIndexes"    ).label = 'Edges Outer Index'
        self.outputs.new('SvStringsSocket' , "edgesInnerIndexes"    ).label = 'Edges Inner Index'
        self.outputs.new('SvStringsSocket' , "edgesBorderIndexes"   ).label = 'Edges Border Index'
        self.outputs.new('SvStringsSocket' , "polygons"             ).label = 'Polygons'
        self.outputs.new('SvStringsSocket' , "polygonsOuterInner"   ).label = 'Polygons Outer Inner Mask'
        self.outputs.new('SvStringsSocket' , "polygonsOuter"        ).label = 'Polygons Outer'
        self.outputs.new('SvStringsSocket' , "polygonsInner"        ).label = 'Polygons Inner'
        self.outputs.new('SvStringsSocket' , "polygonsOuterIndexes" ).label = 'Polygons Outer Indexes'
        self.outputs.new('SvStringsSocket' , "polygonsInnerIndexes" ).label = 'Polygons Inner Indexes'
        self.outputs.new('SvStringsSocket' , "sites_idx"            ).label = 'Used Sites Idx'
        self.outputs.new('SvStringsSocket' , "sites_verts"          ).label = 'Used Sites Verts'

        self.outputs['vertices'].custom_draw = 'draw_vertices_out_socket'

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        row0 = layout.row(align=True)
        row0.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row0.column(align=True).popover(panel=SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5.bl_idname, icon='DOWNARROW_HLT', text="")

        #layout.operator(SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        layout.label(text="Mode:")
        layout.prop(self, "mode", expand=True)
        # split = layout.column().split(factor=0.6)
        # split.column().prop(self, "mask_mode", text='')
        # split.column().prop(self, "mask_inversion", text='Invert')
        if self.mode == 'VOLUME':
            layout.prop(self, 'normals')
        # layout.label(text='Recombine result:')
        # layout.prop(self, 'join_mode', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['vertices'].sv_get(deepcopy=False)
        faces_in = self.inputs['polygons'].sv_get(deepcopy=False)
        sites_in = self.inputs['voronoi_sites'].sv_get(deepcopy=False)

        mask_in = self.inputs['voronoi_sites_mask'] #.sv_get(deepcopy=False)
        if mask_in.is_linked==False:
            mask_in = [[]]
        else:
            mask_in = mask_in.sv_get(deepcopy=False)
            
        spacing_in = self.inputs['spacing'].sv_get(deepcopy=False)

        verts_in = ensure_nesting_level(verts_in, 3)
        input_level = get_data_nesting_level(sites_in, search_first_data=True)
        if input_level<=2:
            sites_in = ensure_nesting_level(sites_in, 3)

        faces_in = ensure_nesting_level(faces_in, 3)
        spacing_in = ensure_min_nesting(spacing_in, 2)
        mask_in = ensure_min_nesting(mask_in, 2)

        precision = 10 ** (-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        outer_verts_property_out = []
        outer_edges_property_out = []
        outer_polygons_property_out = []
        sites_idx_out = []
        sites_verts_out = []

        for verts, faces, sites, spacing, mask in zip_long_repeat(verts_in, faces_in, sites_in, spacing_in, mask_in):
            # if mask is zero or not connected then do not mask any. Except of inversion,
            if not mask:
                np_mask = np.ones(len(sites), dtype=bool)
                if self.inputs['voronoi_sites_mask'].is_linked and self.mask_inversion==True:
                    np_mask = np.invert(np_mask)
                mask = np_mask.tolist()
            else:
                if self.mask_mode=='MASK':
                    if self.mask_inversion==True:
                        mask = list( map( lambda v: False if v==0 else True, mask) )
                        mask = mask[:len(sites)]
                        np_mask = np.zeros(len(sites), dtype=bool)
                        np_mask[0:len(mask)]=mask
                        np_mask = np.invert(np_mask)
                        mask = np_mask.tolist()
                    pass
                elif self.mask_mode=='INDEXES':
                    mask_len = len(sites)
                    mask_range = []
                    for x in mask:
                        if -mask_len<x<mask_len:
                            mask_range.append(x)
                    np_mask = np.zeros(len(sites), dtype=bool)
                    np_mask[mask_range] = True
                    if self.mask_inversion==True:
                        np_mask = np.invert(np_mask)
                    mask = np_mask.tolist()

            new_verts, new_edges, new_faces, new_used_sites_idx, new_used_sites_verts, outer_verts_property, outer_edges_property, outer_faces_property = voronoi_on_mesh(verts, faces, sites, thickness=0,
                            spacing = spacing,
                            #clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            do_clip=True, clipping=None,
                            mode = self.mode,
                            normal_update = self.normals,
                            precision = precision,
                            mask = mask
                            )

            # collect sites_idx and used_sites_verts independently of self.join_mode
            sites_idx_out.append(new_used_sites_idx)
            sites_verts_out.append(new_used_sites_verts)
            
            if self.join_mode == 'FLAT':
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                outer_verts_property_out.extend(outer_verts_property) # dict {is_outer:True/False, is_inner: True/False}
                outer_edges_property_out.extend(outer_edges_property) # dict {is_outer:True/False, is_inner: True/False}
                outer_polygons_property_out.extend(outer_faces_property)
            elif self.join_mode == 'SEPARATE' or self.join_mode == 'JOIN':
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

        if self.join_mode == 'JOIN':
            verts1, edges1, faces1 = mesh_join(verts_out, edges_out, faces_out)
            verts_out = [verts1]
            edges_out = [edges1]
            faces_out = [faces1]
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
        for I, mask in enumerate(outer_verts_property_out):
            verts_out_I = verts_out[I]
            vertsOuter_out_I = []
            vertsInner_out_I = []
            vertsBorder_out_I = []
            vertsOuterIndexes_out_I = []
            vertsInnerIndexes_out_I = []
            vertsBorderIndexes_out_I = []
            for IJ, (m, v) in enumerate(zip(mask, verts_out_I)):
                m_is_outer = m["is_outer"]
                m_is_inner = m["is_inner"]
                if m_is_outer==True:
                    vertsInner_out_I.append(v)
                    vertsOuterIndexes_out_I.append(IJ)
                if m_is_inner==True:
                    vertsOuter_out_I.append(v)
                    vertsInnerIndexes_out_I.append(IJ)
                if m_is_outer==True and m_is_inner==True:
                    vertsBorder_out_I.append(v)
                    vertsBorderIndexes_out_I.append(IJ)
                pass
            vertsOuter_out.append(vertsInner_out_I)
            vertsInner_out.append(vertsOuter_out_I)
            vertsBorder_out.append(vertsBorder_out_I)
            vertsOuterIndexes_out.append(vertsInnerIndexes_out_I)
            vertsInnerIndexes_out.append(vertsOuterIndexes_out_I)
            vertsBorderIndexes_out.append(vertsBorderIndexes_out_I)
            pass

        edgesOuter_out = []
        edgesInner_out = []
        edgesBorder_out = []
        edgesOuterIndexes_out = []
        edgesInnerIndexes_out = []
        edgesBorderIndexes_out = []
        for I, mask in enumerate(outer_edges_property_out):
            edges_out_I = edges_out[I]
            edgesOuter_out_I = []
            edgesInner_out_I = []
            edgesBorder_out_I = []
            edgesOuterIndexes_out_I = []
            edgesInnerIndexes_out_I = []
            edgesBorderIndexes_out_I = []
            for IJ, (m, v) in enumerate(zip(mask, edges_out_I)):
                m_is_outer = m["is_outer"]
                m_is_inner = m["is_inner"]
                if m_is_outer==True:
                    edgesInner_out_I.append(v)
                    edgesOuterIndexes_out_I.append(IJ)
                if m_is_inner==True:
                    edgesOuter_out_I.append(v)
                    edgesInnerIndexes_out_I.append(IJ)
                if m_is_outer==True and m_is_inner==True:
                    edgesBorder_out_I.append(v)
                    edgesBorderIndexes_out_I.append(IJ)
                pass
            edgesOuter_out.append(edgesInner_out_I)
            edgesInner_out.append(edgesOuter_out_I)
            edgesBorder_out.append(edgesBorder_out_I)
            edgesOuterIndexes_out.append(edgesInnerIndexes_out_I)
            edgesInnerIndexes_out.append(edgesOuterIndexes_out_I)
            edgesBorderIndexes_out.append(edgesBorderIndexes_out_I)
            pass

        polygonsOuter_out = []
        polygonsInner_out = []
        polygonsOuterIndexes_out = []
        polygonsInnerIndexes_out = []
        for I, mask in enumerate(outer_polygons_property_out):
            faces_out_I = faces_out[I]
            polygonsOuter_out_I = []
            polygonsInner_out_I = []
            polygonsOuterIndexes_out_I = []
            polygonsInnerIndexes_out_I = []
            for IJ, (m, v) in enumerate(zip(mask, faces_out_I)):
                if m==1:
                    polygonsInner_out_I.append(v)
                    polygonsOuterIndexes_out_I.append(IJ)
                else:
                    polygonsOuter_out_I.append(v)
                    polygonsInnerIndexes_out_I.append(IJ)
                pass
            polygonsOuter_out.append(polygonsInner_out_I)
            polygonsInner_out.append(polygonsOuter_out_I)
            polygonsOuterIndexes_out.append(polygonsInnerIndexes_out_I)
            polygonsInnerIndexes_out.append(polygonsOuterIndexes_out_I)
            pass

        self.outputs['vertices'             ].sv_set(verts_out)
        self.outputs['verticesOuter'        ].sv_set(vertsOuter_out)
        self.outputs['verticesInner'        ].sv_set(vertsInner_out)
        self.outputs['verticesBorder'       ].sv_set(vertsBorder_out)
        self.outputs['verticesOuterIndexes' ].sv_set(vertsOuterIndexes_out)
        self.outputs['verticesInnerIndexes' ].sv_set(vertsInnerIndexes_out)
        self.outputs['verticesBorderIndexes'].sv_set(vertsBorderIndexes_out)
        self.outputs['edges'                ].sv_set(edges_out)
        self.outputs['edgesOuter'           ].sv_set(edgesOuter_out)
        self.outputs['edgesInner'           ].sv_set(edgesInner_out)
        self.outputs['edgesBorder'          ].sv_set(edgesBorder_out)
        self.outputs['edgesOuterIndexes'    ].sv_set(edgesOuterIndexes_out)
        self.outputs['edgesInnerIndexes'    ].sv_set(edgesInnerIndexes_out)
        self.outputs['edgesBorderIndexes'   ].sv_set(edgesBorderIndexes_out)
        self.outputs['polygons'             ].sv_set(faces_out)
        self.outputs['polygonsOuterInner'   ].sv_set(outer_polygons_property_out)
        self.outputs['polygonsOuter'        ].sv_set(polygonsOuter_out)
        self.outputs['polygonsInner'        ].sv_set(polygonsInner_out)
        self.outputs['polygonsOuterIndexes' ].sv_set(polygonsOuterIndexes_out)
        self.outputs['polygonsInnerIndexes' ].sv_set(polygonsInnerIndexes_out)
        self.outputs['sites_idx'            ].sv_set(sites_idx_out)
        self.outputs['sites_verts'          ].sv_set(sites_verts_out)

classes = [SvVoronoiOnMeshOffUnlinkedSocketsMK5, SV_PT_ViewportDisplayPropertiesDialogVoronoiOnMeshMK5, SV_PT_ViewportDisplayPropertiesVoronoiOnMeshMK5, SvVoronoiOnMeshNodeMK5]
register, unregister = bpy.utils.register_classes_factory(classes)