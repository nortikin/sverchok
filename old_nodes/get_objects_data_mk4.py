# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh
from mathutils import Vector, Matrix
import json

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.blender_mesh import (
    read_verts, read_edges, read_verts_normal,
    read_face_normal, read_face_center, read_face_area, read_materials_idx)
import numpy as np
from sverchok.ui.sv_object_names_utils_mk4 import SvNodeInDataMK4, SV_PT_ViewportDisplayPropertiesDialogMK4, ReadingObjectDataError, get_objects_from_item

numpy_socket_names = ['vertices', 'edges', 'vertex_normals', 'material_idx', 'polygon_areas', 'polygon_centers', 'polygon_normals']

class NODE_OT_open_extra(bpy.types.Operator):
    bl_idname = "node.open_extra"
    bl_label = "Extra Settings"

    def execute(self, context):
        bpy.ops.wm.call_panel(
            name="NODE_PT_my_extra",
            keep_open=True,
        )
        return {'FINISHED'}


def get_vertgroups(mesh):
    return [k for k,v in enumerate(mesh.vertices) if v.groups.values()]

def find_layer_collection(layer_coll, target_coll):
    if layer_coll.collection == target_coll:
        return layer_coll
    for child in layer_coll.children:
        found = find_layer_collection(child, target_coll)
        if found:
            return found
    return None

class SvOB3BCallbackMK4(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.ob3b_callback_mk4"
    bl_label = "Object In mk4 callback"
    bl_options = {'INTERNAL'}

    fn_name: bpy.props.StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)

class SvGetObjectsDataMK4(Show3DProperties, SvNodeInDataMK4, bpy.types.Node):
    """
    Triggers: Object Info
    Tooltip: Get Scene Objects into Sverchok Tree
    """

    bl_idname = 'SvGetObjectsDataMK4'
    bl_label = 'Get Objects Data'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    replacement_nodes = [('SvGetObjectsDataMK5', None, None)]

    @property
    def is_scene_dependent(self):
        return (not self.inputs['objects'].is_linked) and (self.inputs['objects'].object_ref_pointer
                                                           or self.object_names)

    @property
    def is_animation_dependent(self):
        return (not self.inputs['objects'].is_linked) and (self.inputs['objects'].object_ref_pointer
                                                           or self.object_names)

    def hide_show_versgroups(self, context):
        outs = self.outputs
        showing_vg = 'Vers_grouped' in outs

        if self.vergroups and not showing_vg:
            outs.new('SvStringsSocket', 'Vers_grouped')
        elif not self.vergroups and showing_vg:
            outs.remove(outs['Vers_grouped'])

    modifiers: bpy.props.BoolProperty(
        name='Post',
        description='Apply modifier geometry to import (original untouched)',
        default=False, update=updateNode) # type: ignore

    vergroups: bpy.props.BoolProperty(
        name='Verts Groups',
        description='Use vertex groups to nesty insertion',
        default=False, update=hide_show_versgroups) # type: ignore

    sort: bpy.props.BoolProperty(
        name='Sort',
        description='sorting inserted objects by names',
        default=True, update=updateNode) # type: ignore

    out_np: bpy.props.BoolVectorProperty(
        name="Output Numpy",
        description="Output NumPy arrays (makes node faster)",
        size=7, update=updateNode) # type: ignore

    output_np_all: bpy.props.BoolProperty(
        name='Output all numpy',
        description='Output numpy arrays if possible',
        default=False, update=updateNode) # type: ignore
    
    mesh_join : bpy.props.BoolProperty(
        name = "Mesh Join",
        description = "If checked, join mesh elements into one object",
        default = False,
        update = updateNode) # type: ignore
    
    def _verts_sockets_update(self, context):
        for name in ['vertices_select', 'vertices_crease', 'vertices_bevel_weight']:
            self.outputs[name].hide = not(self.enable_verts_attribute_sockets)

    def verts_sockets_update(self, context):
        self._verts_sockets_update(context)
        updateNode(self, context)

    def _edges_sockets_update(self, context):
        for name in ['edges_select', 'edges_seams', 'edges_sharps', 'edges_crease', 'edges_bevel_weight',]:
            self.outputs[name].hide = not(self.enable_edges_attribute_sockets)

    def edges_sockets_update(self, context):
        self._edges_sockets_update(context)
        updateNode(self, context)

    def _polygons_sockets_update(self, context):
        for name in ['polygon_selects', 'polygon_smooth', ]:
            self.outputs[name].hide = not(self.enable_polygons_attribute_sockets)
    def polygons_sockets_update(self, context):
        self._polygons_sockets_update(context)
        updateNode(self, context)

    enable_verts_attribute_sockets: bpy.props.BoolProperty(
        name = "Show verts attribute sockets",
        description = "Show additional sockets for verts attributes:\n1. select\n2. crease\n3. bevel weight",
        default = False,
        update = verts_sockets_update) # type: ignore

    enable_edges_attribute_sockets: bpy.props.BoolProperty(
        name = "Show edges attribute sockets",
        description = "Show additional sockets for edges attributes:\n1. select\n2. sharp\n3. seams\n4. crease\n4. bevel weight",
        default = False,
        update = edges_sockets_update) # type: ignore

    enable_polygons_attribute_sockets: bpy.props.BoolProperty(
        name = "Show polygons attribute sockets",
        description = "Show additional sockets for faces attributes:\n1. select\n2. smooth",
        default = False,
        update = polygons_sockets_update) # type: ignore
    
    vertex_attribute_types = [
        ('SELECTED', "", "Get faces indicex, currently selected", "FACESEL", 0),
        ('ACTIVE_FACE_MAP', "", "Get faces indices, currently actived in Face Maps of object", "FACE_MAPS", 1),
    ]

    vertex_attribute_type : bpy.props.EnumProperty(
        name = "Render Types",
        items = vertex_attribute_types,
        default = 'SELECTED',
        update = updateNode) # type: ignore

    def migrate_from(self, old_node):
        self.outputs["vertices_select"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_crease"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_bevel_weight"]   .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["edges_select"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_crease"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_seams"]             .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_sharps"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_bevel_weight"]      .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["polygon_selects"]         .hide = not(self.enable_polygons_attribute_sockets)
        self.outputs["polygon_smooth"]          .hide = not(self.enable_polygons_attribute_sockets)
    
    def draw_vertices_out_socket(self, socket, context, layout):
        layout.label(text=f'{socket.label} ')
        layout.prop(self, 'enable_verts_attribute_sockets', icon='STICKY_UVS_DISABLE', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def draw_edges_out_socket(self, socket, context, layout):
        # layout.prop(self, 'hide_render_type', expand=True)
        # layout.separator()
        # layout.prop(self, 'align_3dview_type', expand=True)
        # layout.separator()
        layout.label(text=f'  {socket.label} ')
        layout.prop(self, 'enable_edges_attribute_sockets', icon='MESH_DATA', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def draw_polygons_out_socket(self, socket, context, layout):
        #layout.popover(panel="SV_PT_ViewportDisplayPropertiesMK4", icon='DOWNARROW_HLT', text="")
        ##layout.operator(SV_PT_ViewportDisplayPropertiesMK4.bl_idname, icon='TRIA_DOWN', text="")
        #layout.prop(self, 'display_type', expand=True, text='')
        layout.separator()
        layout.label(text=f'{socket.label} ')
        layout.prop(self, 'enable_polygons_attribute_sockets', icon='FILE_3D', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def sv_init(self, context):
        #new = self.outputs.new
        self.width = 225
        
        self.inputs.new('SvObjectSocket'   , "objects")
        self.inputs ['objects']         .label = 'Objects'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket' , 'edges')
        self.outputs.new('SvStringsSocket' , 'polygons')
        self.outputs.new('SvStringsSocket' , 'vertices_select')
        self.outputs.new('SvStringsSocket' , 'vertices_crease')
        self.outputs.new('SvStringsSocket' , 'vertices_bevel_weight')
        self.outputs.new('SvStringsSocket' , 'edges_select')
        self.outputs.new('SvStringsSocket' , 'edges_crease')
        self.outputs.new('SvStringsSocket' , 'edges_seams')
        self.outputs.new('SvStringsSocket' , 'edges_sharps')
        self.outputs.new('SvStringsSocket' , 'edges_bevel_weight')
        self.outputs.new('SvStringsSocket' , 'polygon_selects')
        self.outputs.new('SvStringsSocket' , 'polygon_smooth')
        self.outputs.new('SvVerticesSocket', 'vertex_normals')
        self.outputs.new('SvStringsSocket' , 'material_idx')
        self.outputs.new('SvStringsSocket' , 'material_names')
        self.outputs.new('SvStringsSocket' , 'polygon_areas')
        self.outputs.new('SvVerticesSocket', 'polygon_centers')
        self.outputs.new('SvVerticesSocket', 'polygon_normals')
        self.outputs.new('SvStringsSocket' , 'object_names')
        self.outputs.new('SvMatrixSocket'  , 'matrices')
        self.outputs.new('SvObjectSocket'  , 'objects')


        self.outputs['vertices']                .label = 'Vertices'
        self.outputs['edges']                   .label = 'Edges'
        self.outputs['polygons']                .label = 'Polygons'
        self.outputs['vertices_select']         .label = '(*) Vertices Select'
        self.outputs['vertices_crease']         .label = '(*) Vertices Crease'
        self.outputs['vertices_bevel_weight']   .label = '(*) Vertices Bevel Weight'
        self.outputs['edges_select']            .label = '(|) Edges Select'
        self.outputs['edges_seams']             .label = '(|) Edges Seam'
        self.outputs['edges_sharps']            .label = '(|) Edges Sharp'
        self.outputs['edges_crease']            .label = '(|) Edges Crease'
        self.outputs['edges_bevel_weight']      .label = '(|) Edges Bevel Weight'
        self.outputs['polygon_selects']         .label = '(+) Polygons Select'
        self.outputs['polygon_smooth']          .label = '(+) Polygons Smooth'
        self.outputs['vertex_normals']          .label = 'Vertex Normals'
        self.outputs['material_idx']            .label = 'Material Idx'
        self.outputs['material_names']          .label = 'Material Names'
        self.outputs['polygon_areas']           .label = 'Polygon Areas'
        self.outputs['polygon_centers']         .label = 'Polygon Centers'
        self.outputs['polygon_normals']         .label = 'Polygon Normals'
        self.outputs['object_names']            .label = 'Object Names'
        self.outputs['matrices']                .label = 'Matrices'
        self.outputs['objects']                 .label = 'Objects'

        self.outputs['vertices_select']         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs['vertices_crease']         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs['vertices_bevel_weight']   .hide = not(self.enable_verts_attribute_sockets)
        self.outputs['edges_select']            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs['edges_seams']             .hide = not(self.enable_edges_attribute_sockets)
        self.outputs['edges_sharps']            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs['edges_crease']            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs['edges_bevel_weight']      .hide = not(self.enable_edges_attribute_sockets)
        self.outputs['polygon_selects']         .hide = not(self.enable_polygons_attribute_sockets)
        self.outputs['polygon_smooth']          .hide = not(self.enable_polygons_attribute_sockets)

        self.outputs['vertices'].custom_draw = 'draw_vertices_out_socket'
        self.outputs['edges']   .custom_draw = 'draw_edges_out_socket'
        self.outputs['polygons'].custom_draw = 'draw_polygons_out_socket'

    @property
    def by_input(self):
        return self.inputs[0].object_ref_pointer is not None or self.inputs[0].is_linked

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        by_input = self.by_input
        if not by_input:
            row = col.row()
            row.alignment='EXPAND'

            op_text = "Get selection"  # fallback
            callback = SvOB3BCallbackMK4.bl_idname

            if self.prefs_over_sized_buttons:
                row.scale_y = 4.0
                op_text = "G E T"

            self.wrapper_tracked_ui_draw_op(row, callback, text=op_text, icon='IMPORT').fn_name = 'get_objects_from_scene'

        grid = layout.grid_flow(row_major=False, columns=2, align=True)
        grid.column(align=True).prop(self, 'sort')
        grid.column(align=True).prop(self, 'apply_matrix')
        grid.column(align=True).prop(self, 'mesh_join')
        grid.column(align=True).prop(self, 'modifiers')
        grid.column(align=True).prop(self, 'vergroups')
        row0 = grid.row(align=True)
        row0.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogMK4.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row0.column(align=True).popover(panel="SV_PT_ViewportDisplayPropertiesMK4", icon='DOWNARROW_HLT', text="")
        # row0.separator()
        # row0.row().prop(self, 'display_type', expand=True, text='')

        if not by_input:
            if self.object_names:
                col = layout.column(align=True)
                elem = col.row(align=True)
                self.draw_controls(elem)
                self.draw_object_names(col.row(align=True))
            else:
                layout.label(text='--None--')
        pass

    def sv_draw_buttons_ext(self, context, layout):
        r = layout.column(align=True)
        row = r.row(align=True)
        row.label(text="Output Numpy:")
        row.prop(self, 'output_np_all', text='If possible', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                r.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.label(text="Output Numpy:")
        layout.prop(self, 'output_np_all', text='All', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                layout.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN")
        self.sv_draw_buttons_ext(context, layout)

    def draw_buttons_3dpanel(self, layout):
        if not self.by_input:
            callback = SvOB3BCallbackMK4.bl_idname
            row = layout.row(align=True)
            row.label(text=self.label if self.label else self.name)
            colo = row.row(align=True)
            colo.scale_x = 1.6

            self.wrapper_tracked_ui_draw_op(colo, callback, text='Get').fn_name = 'get_objects_from_scene'
        else:
            row = layout.row(align=True)
            row.label(text=self.label if self.label else self.name)
            self.draw_animatable_buttons(row, icon_only=True)

    def get_materials_from_bmesh(self, bm):
        return [face.material_index for face in bm.faces[:]]

    def process(self):
        #self.update_display_type(None)
        objs = self.inputs[0].sv_get(default=[[]])
        if not self.object_names and not objs[0]:
            return
        
        data_objects = bpy.data.objects
        outputs = self.outputs

        vers_out_grouped = []

        lst_output_sockets = ['vertices', 'edges', 'polygons', 'vertices_select', 'vertices_crease', 'vertices_bevel_weight', 'edges_select', 'edges_crease', 'edges_seams', 'edges_sharps', 'edges_bevel_weight', 'polygon_selects', 'polygon_smooth', 'vertex_normals', 'material_idx', 'material_names', 'polygon_areas', 'polygon_centers', 'polygon_normals', 'object_names', 'matrices', 'objects']
        o_vertices, o_edges, o_polygons, o_vertices_select, o_vertices_crease, o_vertices_bevel_weight, o_edges_select, o_edges_crease, o_edges_seams, o_edges_sharps, o_edges_bevel_weight, o_polygon_selects, o_polygon_smooth, o_vertex_normals, o_material_idx, o_material_names, o_polygon_areas, o_polygon_centers, o_polygon_normals, o_object_names, o_matrices, o_objects = [ (self.outputs[socket_name].is_linked if socket_name in self.outputs else False) for socket_name in lst_output_sockets]
        l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_crease, l_edges_seams, l_edges_sharps, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_material_idx, l_material_names, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_object_names, l_matrices            = [[]                                  for socket_name in lst_output_sockets if socket_name not in 'objects']
        sv_depsgraph = None
        if self.modifiers:
            sv_depsgraph = bpy.context.evaluated_depsgraph_get()

        out_np = self.out_np if not self.output_np_all else [True for i in range(7)]
        if isinstance(objs[0], list):
            objs = objs[0]
        if not objs:
            objs = []
            for o in self.object_names:
                if o.exclude==False and o.name in bpy.context.scene.objects: # objects can be in object_pointer but absent in the scene
                    _obj = get_objects_from_item(o)
                    objs.extend(_obj)
                pass
            pass

        # iterate through references
        for I, obj in enumerate(objs):

            if not obj:
                continue

            mtrx = obj.matrix_world

            if o_object_names:
                l_object_names.append([obj.name])

            if obj.type in {'EMPTY', 'CAMERA', 'LAMP', 'LIGHT' }:
                if o_matrices:
                    l_matrices.append(mtrx)
                if o_vertices:
                    verts = []
                if o_edges:
                    edgs = []
                if o_polygons:
                    pols = []
                if o_vertices_select:
                    vertices_select1 = []

                material_indexes = []
                materials_info = dict()
            else:
                try:
                    if obj.mode == 'EDIT' and obj.type == 'MESH':
                        # Mesh objects do not currently return what you see
                        # from 3dview while in edit mode when using obj.to_mesh.
                        me = obj.data
                        bm = bmesh.from_edit_mesh(me)
                        # verts, edgs, pols = pydata_from_bmesh(bm)

                        if o_vertices or o_edges or o_polygons or self.vergroups:
                            if self.apply_matrix:
                                verts = [ (mtrx @ Vector(v.co[:]))[:] for v in bm.verts]  # v.co is a Vector()
                            else:
                                verts = [ (Vector(v.co[:]))[:] for v in bm.verts]  # v.co is a Vector()
                            if o_edges:
                                edgs = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
                            if o_polygons:
                                pols = [[i.index for i in p.verts] for p in bm.faces]
                            if self.vergroups:
                                vert_groups      = get_vertgroups(obj.data)

                        if o_vertices_select:
                            vertices_select1 = [v.select for v in bm.verts]

                        if o_vertices_crease:
                            if hasattr(bm.verts.layers, 'crease'):
                                # before blender 4.0
                                crease_layer = bm.verts.layers.crease.verify()
                                vertices_crease1 = [v[crease_layer] for v in bm.verts]
                            elif hasattr(bm.verts.layers, 'float') and 'crease_vert' in bm.verts.layers.float:
                                # after blender 4.0
                                crease_vert_layer = bm.verts.layers.float.get('crease_vert')
                                vertices_crease1 = [v[crease_vert_layer] for v in bm.verts]
                            else:
                                # if no layer then all creases are 0.0
                                vertices_crease1 = [0.0 for v in bm.verts]

                        if o_vertices_bevel_weight:
                            if hasattr(bm.verts.layers, 'bevel_weight'):
                                # before blender 4.0
                                bevel_weight_layer = bm.verts.layers.bevel_weight.verify()
                                vertices_bevel_weight1 = [v[bevel_weight_layer] for v in bm.verts]
                            elif hasattr(bm.verts.layers, 'float') and 'bevel_weight_vert' in bm.verts.layers.float:
                                # after blender 4.0
                                bevel_weight_vert_layer = bm.verts.layers.float.get('bevel_weight_vert')
                                vertices_bevel_weight1 = [v[bevel_weight_vert_layer] for v in bm.verts]
                            else:
                                # if no layer then all bevels are 0.0
                                vertices_bevel_weight1 = [0.0 for v in bm.verts]

                        if o_edges_select:
                            edges_select1 = [e.select for e in bm.edges]
                        if o_edges_seams:
                            edges_seams1  = [e.seam for e in bm.edges]
                        if o_edges_sharps:
                            edges_sharps1 = [not(e.smooth) for e in bm.edges]

                        if o_edges_crease:
                            if hasattr(bm.edges.layers, "crease"):
                                # before blender 4.0
                                crease_layer = bm.edges.layers.crease.verify()
                                edges_crease1 = [ e[crease_layer] for e in bm.edges ]
                            elif hasattr(bm.edges.layers, 'float') and 'crease_edge' in bm.edges.layers.float:
                                # after blender 4.0
                                cel = bm.edges.layers.float.get("crease_edge") # crease edge layer
                                edges_crease1 = [e[cel] for e in bm.edges]
                            else:
                                # edges has no data for crease (not initalized)
                                edges_crease1 = [0.0 for e in bm.edges]
                            pass

                        if o_edges_bevel_weight:
                            if hasattr(bm.edges.layers, "bevel_weight"):
                                # before blender 4.0
                                bevel_weight_layer = bm.edges.layers.bevel_weight.verify()
                                edges_bevel_weight1 = [e[bevel_weight_layer] for e in bm.edges]
                            elif hasattr(bm.edges.layers, 'float') and 'bevel_weight_edge' in bm.edges.layers.float:
                                # after blender 4.0
                                bevel_weight_layer = bm.edges.layers.float.get("bevel_weight_edge") # crease edge layer
                                edges_bevel_weight1 = [e[bevel_weight_layer] for e in bm.edges]
                            else:
                                # edges has no data for bevel (not initalized)
                                edges_bevel_weight1 = [0.0 for e in bm.edges]
                            pass

                        if o_polygon_selects:
                            polygon_selects1 = [f.select for f in bm.faces]
                        if o_polygon_smooth:
                            polygon_smooth1 = [f.smooth for f in bm.faces]
                        # if self.vergroups:
                        #     vert_groups      = get_vertgroups(obj.data)
                        if o_vertex_normals:
                            vertex_normals = [ v.normal[:] for v in bm.verts] # v.normal is a Vector()
                        if o_material_idx or o_material_names:
                            if obj.material_slots:
                                material_indexes = self.get_materials_from_bmesh(bm)
                                material_socket_ids = set(material_indexes)
                                # save all sockets materials in materials sockets of object (materials name if it is not null and info about faces)
                                materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), is_faces=id in material_socket_ids )) for id in range(len(obj.material_slots))])
                            else:
                                if bm.faces:
                                    material_indexes = [0]*len(bm.faces)
                                    materials_info = dict( [(0,dict(material_name=None, is_faces=True))] )
                                else:
                                    material_indexes = []
                                    materials_info = dict()
                            pass

                        if o_polygon_areas:
                            polygons_areas = [ p.calc_area() for p in bm.faces ]
                        if o_polygon_centers:
                            polygon_centers = [ p.calc_center_median()[:] for p in bm.faces ]
                        if o_polygon_normals:
                            polygon_normals = [ p.normal[:] for p in bm.faces ]

                        del bm

                    else: # do in Object mode

                        # https://developer.blender.org/T99661
                        if obj.type == 'CURVE' and obj.mode == 'EDIT' and bpy.app.version[:2] == (3, 2):
                            raise ReadingObjectDataError("Does not support curves in edit mode in Blender 3.2")
                        elif self.modifiers:
                            if obj.type in ['POINTCLOUD']:
                                if sv_depsgraph is None:
                                    sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                                obj = sv_depsgraph.objects[obj.name]
                                obj_eval = obj.evaluated_get(sv_depsgraph)
                                obj_data = obj_eval.data
                            else:
                                obj = sv_depsgraph.objects[obj.name]
                                obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                        else:
                            if obj.type in ['META']:
                                if sv_depsgraph is None:
                                    sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                                obj = sv_depsgraph.objects[obj.name]
                                obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                            elif obj.type in ['POINTCLOUD']:
                                if sv_depsgraph is None:
                                    sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                                obj = sv_depsgraph.objects[obj.name]
                                #obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                                obj_eval = obj.evaluated_get(sv_depsgraph)
                                obj_data = obj_eval.data
                            else:
                                obj_data = obj.to_mesh()
                        
                        T, R, S = mtrx.decompose()

                        if obj.type in ['POINTCLOUD']:
                            if o_vertices or o_edges or o_polygons or self.vergroups:
                                # any of verts, edges, faces or vergroups are connected to verts
                                verts            = [ ((mtrx @ v.co)[:] if self.apply_matrix else v.co)[:] for v in obj_data.points]  # v.co is a Vector()
                                if o_edges:
                                    edgs         = []
                                if o_polygons:
                                    pols         = []
                                if self.vergroups:
                                    vert_groups  = []

                            if o_vertices_select:
                                vertices_select1 = []
                            if o_vertices_crease:
                                vertices_crease1 = []
                            if o_vertices_bevel_weight:
                                vertices_bevel_weight1 = []
                            if o_edges_select:
                                edges_select1 = []
                            if o_edges_seams:
                                edges_seams1  = []
                            if o_edges_sharps:
                                edges_sharps1 = []
                            if o_edges_crease:
                                edges_crease1 = []
                            if o_edges_bevel_weight:
                                edges_bevel_weight1 = []
                            if o_polygon_selects:
                                polygon_selects1 = []
                            if o_polygon_smooth:
                                polygon_smooth1  = []
                            if o_vertex_normals:
                                vertex_normals   = [] # v.normal is a Vector(). Update. Blender 3.6.3 crash in no wrap Vector(v.normal). I think this is after line "obj.to_mesh_clear()"
                            if o_material_idx or o_material_names:
                                if obj.material_slots:
                                    material_indexes = []
                                    material_socket_ids = set(material_indexes)
                                    # save all sockets materials in materials sockets of object (materials name if it is not null and info about faces)
                                    materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), is_faces=id in material_socket_ids )) for id in range(len(obj.material_slots))])
                                else:
                                    # POINT_CLOUDS has no polygons
                                    material_indexes = []
                                    materials_info = dict()

                            if o_polygon_areas:
                                polygons_areas   = []
                            if o_polygon_centers:
                                polygon_centers  = []
                            if o_polygon_normals:
                                polygon_normals  = []

                        else:
                            if o_vertices or o_edges or o_polygons or self.vergroups:
                                # any of verts, edges, faces or vergroups are connected to verts
                                verts            = [ ((mtrx @ v.co)[:] if self.apply_matrix else v.co)[:] for v in obj_data.vertices]  # v.co is a Vector()
                                if o_edges:
                                    edgs         = [[ e.vertices[0], e.vertices[1] ] for e in obj_data.edges]
                                if o_polygons:
                                    pols         = [list(p.vertices) for p in obj_data.polygons]

                            if o_vertices_select:
                                vertices_select1 = [v.select for v in obj_data.vertices]

                            if o_vertices_crease:
                                if hasattr(obj_data, 'vertex_creases') and (obj_data.vertex_creases is not None) and hasattr(obj_data.vertex_creases, '__len__') and len(obj_data.vertex_creases)>0:
                                    # it is very hard to identify creases in object mode in blender before 4.0
                                    creases = obj_data.vertex_creases[0]
                                    vertices_crease1 = [creases.data[i].value for i, v in enumerate(obj_data.vertices)]
                                elif 'crease_vert' in obj_data.attributes:
                                    # get creases of vertices in Blender 4.x
                                    vertices_crease1 = [e.value for e in obj_data.attributes['crease_vert'].data]
                                else:
                                    # if no data then all creases are 0.0
                                    vertices_crease1 = [0.0 for i in range( len(obj_data.vertices) )]
                                pass

                            if o_vertices_bevel_weight:
                                if 'bevel_weight_vert' in obj_data.attributes:
                                    # after Blender 4.0
                                    vertices_bevel_weight1 = [e.value for e in obj_data.attributes['bevel_weight_vert'].data]
                                elif len(obj_data.vertices)>0 and hasattr(obj_data.vertices[0], 'bevel_weight'):
                                    # before Blender 4.0
                                    vertices_bevel_weight1 = [v.bevel_weight for v in obj_data.vertices]
                                else:
                                    # vertices has no data in e (not initalized)
                                    vertices_bevel_weight1 = [0.0 for i in range( len(obj_data.vertices) )]
                                pass

                            if o_edges_select:
                                edges_select1 = [e.select for e in obj_data.edges]
                            if o_edges_seams:
                                edges_seams1 = [e.use_seam for e in obj_data.edges]
                            if o_edges_sharps:
                                edges_sharps1 = [e.use_edge_sharp for e in obj_data.edges]

                            if o_edges_crease:
                                if 'crease_edge' in obj_data.attributes:
                                    # after blender 4.0
                                    edges_crease1 = [e.value for e in obj_data.attributes['crease_edge'].data]
                                elif len(obj_data.edges)>0 and hasattr(obj_data.edges[0], 'crease'):
                                    # before Blender 4.0
                                    edges_crease1 = [e.crease for e in obj_data.edges]
                                else:
                                    # edges has no data in e (not initalized)
                                    edges_crease1 = [0.0 for e in obj_data.edges]
                                pass
                            
                            if o_edges_bevel_weight:
                                if 'bevel_weight_edge' in obj_data.attributes:
                                    # after Blender 4.0
                                    edges_bevel_weight1 = [e.value for e in obj_data.attributes['bevel_weight_edge'].data]
                                elif len(obj_data.edges)>0 and hasattr(obj_data.edges[0], 'bevel_weight'):
                                    # before Blender 4.0
                                    edges_bevel_weight1 = [e.bevel_weight for e in obj_data.edges]
                                else:
                                    # edges has no data for bevel (not initalized)
                                    edges_bevel_weight1 = [0.0 for e in obj_data.edges]
                                pass
                                    
                            if o_polygon_selects:
                                polygon_selects1 = [p.select for p in obj_data.polygons]
                            if o_polygon_smooth:
                                polygon_smooth1 = [p.use_smooth for p in obj_data.polygons]
                            if self.vergroups:
                                vert_groups      = get_vertgroups(obj_data)
                            if o_vertex_normals:
                                vertex_normals   = [ ((   R @ v.co) if self.apply_matrix else v.normal)[:] for v in obj_data.vertices ] # v.normal is a Vector(). Update. Blender 3.6.3 crash in no wrap Vector(v.normal). I think this is after line "obj.to_mesh_clear()"
                            if o_material_idx or o_material_names:
                                if obj.material_slots:
                                    material_indexes = read_materials_idx(obj_data, out_np[3])
                                    material_socket_ids = set(material_indexes)
                                    # save all sockets materials in materials sockets of object (materials name if it is not null and info about faces)
                                    materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), is_faces=id in material_socket_ids )) for id in range(len(obj.material_slots))])
                                else:
                                    if obj_data.polygons:
                                        material_indexes = [0]*len(obj_data.polygons)
                                        materials_info = dict( [(0,dict(material_name=None, is_faces=True))] )
                                    else:
                                        material_indexes = []
                                        materials_info = dict()

                            if o_polygon_areas:
                                polygons_areas   = [ polygon.area for polygon in obj_data.polygons]
                            if o_polygon_centers:
                                polygon_centers  = [ ((mtrx @ polygon.center) if self.apply_matrix else polygon.center)[:] for polygon in obj_data.polygons]
                            if o_polygon_normals:
                                polygon_normals  = [ ((   R @ polygon.normal) if self.apply_matrix else polygon.normal)[:] for polygon in obj_data.polygons]

                    if o_matrices:
                        l_matrices.append(mtrx)

                    obj.to_mesh_clear()
                except ReadingObjectDataError as _ex:
                    raise
                except Exception as err:
                    # it's not clear which cases this try catch should handle
                    # probably it should skip wrong object types
                    self.debug('failure in process between frozen area', self.name, err)

            pass
        
            if o_vertices or o_edges or o_polygons or self.vergroups:
                l_vertices.append( verts )
                if o_edges:
                    l_edges.append( edgs )
                if o_polygons:
                    l_polygons.append( pols )
                if self.vergroups:
                    vers_out_grouped.append( vert_groups )

            if o_vertices_select:
                l_vertices_select.append( vertices_select1 )
            if o_vertices_crease:
                l_vertices_crease.append( vertices_crease1 )
            if o_vertices_bevel_weight:
                l_vertices_bevel_weight.append( vertices_bevel_weight1 )
            if o_edges_select:
                l_edges_select.append( edges_select1 )
            if o_edges_seams:
                l_edges_seams.append( edges_seams1 )
            if o_edges_sharps:
                l_edges_sharps.append( edges_sharps1 )
            if o_edges_crease:
                l_edges_crease.append( edges_crease1 )
            if o_edges_bevel_weight:
                l_edges_bevel_weight.append( edges_bevel_weight1 )
            if o_polygon_selects:
                l_polygon_selects.append( polygon_selects1 )
            if o_polygon_smooth:
                l_polygon_smooth.append( polygon_smooth1 )
            if o_vertex_normals:
                l_vertex_normals.append( vertex_normals )
            if o_material_idx or o_material_names:
                l_material_idx.append( material_indexes )
                l_material_names.append(materials_info)
            if o_polygon_areas:
                l_polygon_areas.append( polygons_areas )
            if o_polygon_centers:
                l_polygon_centers.append( polygon_centers )
            if o_polygon_normals:
                l_polygon_normals.append( polygon_normals )
            
            pass

        if self.mesh_join:
            offset = 0
            _vertices, _edges, _polygons, _vertices_select, _vertices_crease, _vertices_bevel_weight, _edges_select, _edges_seams, _edges_sharps, _edges_crease, _edges_bevel_weight, _polygon_selects, _polygon_smooth, _vertex_normals, _polygon_areas, _polygon_centers, _polygon_normals, _vg = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []

            # Create dict of unique materials before join polygons
            _materials_ids = []
            _l_materials_names_unique = set()  # Unique materials names before sorting: {'Material.002.Red', None, 'Material.005.Green', 'Material.001.Blue'}
            for l_material in l_material_names:
                for K in l_material:
                    # do not use material if it has no faces
                    if l_material[K]['is_faces']==True:
                        _l_materials_names_unique.update( [l_material[K]['material_name']] )
                    pass
                pass
            _l_materials_names_unique_sorted = sorted(_l_materials_names_unique, key=lambda x: (x is None, x)) # # sorted unique names, None is a last element (for convinience reading, has no influence for mesh join): ['Material.001.Blue', 'Material.002.Red', 'Material.005.Green', None]
            _l_materials_names_uniques = dict( zip( _l_materials_names_unique_sorted, list(range(len(_l_materials_names_unique))))) # Global materials idx: {'Material.001.Blue': 0, 'Material.002.Red': 1, 'Material.005.Green': 2, None: 3}
            for idx, obj in enumerate(objs):
                if l_vertices or l_edges or l_polygons or vers_out_grouped:
                    _vertices.extend(l_vertices[idx])
                    if l_edges:
                        _edges.extend( [[i + offset for i in o] for o in l_edges[idx] ] ) # edges
                    if l_polygons:
                        _polygons.extend( [[i + offset for i in o] for o in l_polygons[idx] ] ) # polygons
                    if vers_out_grouped:
                        _vg.extend( [ i + offset for i in vers_out_grouped[idx] ] ) # vertex groups
                    offset += len(l_vertices[idx])

                if l_vertices_select:
                    _vertices_select.extend( l_vertices_select[idx] )
                if l_vertices_crease:
                    _vertices_crease.extend( l_vertices_crease[idx] )
                if l_vertices_bevel_weight:
                    _vertices_bevel_weight.extend( l_vertices_bevel_weight[idx] )
                if l_edges_select:
                    _edges_select.extend( l_edges_select[idx] )
                if l_edges_seams:
                    _edges_seams.extend( l_edges_seams[idx] )
                if l_edges_sharps:
                    _edges_sharps.extend( l_edges_sharps[idx] )
                if l_edges_crease:
                    _edges_crease.extend( l_edges_crease[idx] )
                if l_edges_bevel_weight:
                    _edges_bevel_weight.extend( l_edges_bevel_weight[idx] )
                if l_polygon_selects:
                    _polygon_selects.extend( l_polygon_selects[idx] )
                if l_polygon_smooth:
                    _polygon_smooth.extend( l_polygon_smooth[idx] )
                if l_vertex_normals:
                    _vertex_normals.extend( l_vertex_normals[idx] ) # vertex normals

                if l_material_idx:
                    # material changes in mesh join:
                    l_material_idx_I   = l_material_idx[idx]    # what sockets idx: [2, 1, 0, 3, 1, 1]
                    l_material_info_I  = l_material_names[idx]  # what materials info of sockets: {0: {'material_name': 'Material.006', 'is_faces': False}, 1: {'material_name': 'Material.005.Green', 'is_faces': True}, 2: {'material_name': 'Material.007_Object', 'is_faces': False}}
                    l_material_names_I = dict([(K, l_material_info_I[K]['material_name']) for K in l_material_info_I if l_material_info_I[K]['is_faces']==True]) # What used materials info: {0: None, 1: 'Material.001.Blue', 2: 'Material.002.Red', 3: 'Material.005.Green'}

                    l_materials_I_repack_materials = dict([(k, _l_materials_names_uniques[l_material_names_I[k]]) for k in l_material_names_I])   # repack info of materials for global materials indexes: {0: 3, 1: 0, 2: 1, 3: 2}
                    l_material_idx_I_repack        = [l_materials_I_repack_materials[s] for s in l_material_idx_I]                                # replace local sockets idx for global materials idx: [1, 0, 3, 2, 0, 0] This idx may do not equals Mesh Join in reality, but algorithm does equals results
                    _materials_ids.extend(l_material_idx_I_repack)

                if l_polygon_areas:
                    _polygon_areas.extend( l_polygon_areas[idx] ) # polygon area
                if l_polygon_centers:
                    _polygon_centers.extend( l_polygon_centers[idx] ) # polygon center
                if l_polygon_normals:
                    _polygon_normals.extend( l_polygon_normals[idx] ) # polygon normal
            
            (l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight,
            l_edges_select, l_edges_seams, l_edges_sharps, l_edges_crease, l_edges_bevel_weight,
            l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_material_idx, l_material_names, l_polygon_areas, l_polygon_centers,
            l_polygon_normals, vers_out_grouped) = ([_vertices], [_edges], [_polygons], [_vertices_select], [_vertices_crease], [_vertices_bevel_weight],
            [_edges_select], [_edges_seams], [_edges_sharps], [_edges_crease], [_edges_bevel_weight],
            [_polygon_selects], [_polygon_smooth], [_vertex_normals], [_materials_ids], [ list(_l_materials_names_uniques.keys())], [_polygon_areas], [_polygon_centers],
            [_polygon_normals], [_vg])
        else:
            _t = []
            for materials_of_object in l_material_names:
                _to = []
                for material_socket in sorted(materials_of_object.keys()):
                    _to.append(materials_of_object[material_socket]['material_name'])
                _t.append(_to)
            l_material_names = _t
            pass

        if o_vertices and (out_np[0]):
            l_vertices = [np.array(vert) for vert in l_vertices]
        if o_edges and (out_np[1]):
            l_edges = [np.array(edge) for edge in l_edges]
        # if o_polygons and (out_np[2]):
        #     l_polygons = [np.array(pol)  for pol  in l_polygons]
        # if self.vergroups:
        #     vers_out_grouped = [np.array(group)  for group  in vers_out_grouped]
        if o_vertex_normals and (out_np[2]):
            l_vertex_normals = [np.array(vert_normal)     for vert_normal     in l_vertex_normals]
        if o_material_idx and (out_np[3]):
            l_material_idx = [np.array(material_index)  for material_index  in l_material_idx]
        if o_polygon_areas and (out_np[4]):
            l_polygon_areas = [np.array(polygon_areas)   for polygon_areas   in l_polygon_areas]
        if o_polygon_centers and (out_np[5]):
            l_polygon_centers = [np.array(polygon_centers) for polygon_centers in l_polygon_centers]
        if o_polygon_normals and (out_np[6]):
            l_polygon_normals = [np.array(polygon_normals) for polygon_normals in l_polygon_normals]

        for socket_name, values in zip([socket_name for socket_name in lst_output_sockets if socket_name not in ['objects']] , [l_vertices, l_edges, l_polygons,
                                        l_vertices_select, l_vertices_crease, l_vertices_bevel_weight,
                                        l_edges_select, l_edges_crease, l_edges_seams, l_edges_sharps, l_edges_bevel_weight,
                                        l_polygon_selects, l_polygon_smooth, l_vertex_normals,
                                        l_material_idx, l_material_names, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_object_names, l_matrices]):
            if socket_name in self.outputs:
                if self.outputs[socket_name].is_linked:
                    self.outputs[socket_name].sv_set(values)

        if vers_out_grouped and vers_out_grouped[0]:
            if 'Vers_grouped' in outputs and self.vergroups:
                outputs['Vers_grouped'].sv_set(vers_out_grouped)
        if o_objects:
            if self.by_input:
                outputs['objects'].sv_set(objs)
            else:
                outputs['objects'].sv_set([data_objects.get(o.name) for o in self.object_names])
            pass
        pass
    pass

    def migrate_links_from(self, old_node, operator):
        '''replace socket names to lowercase'''
        # copy of "ui\nodes_replacement.py"

        tree = self.id_data
        # Copy incoming / outgoing links
        old_in_links = [link for link in tree.links if link.to_node == old_node]
        old_out_links = [link for link in tree.links if link.from_node == old_node]

        for old_link in old_in_links:
            new_target_socket_name = operator.get_new_input_name(old_link.to_socket.name)
            new_target_socket_name = new_target_socket_name.lower()
            if new_target_socket_name in self.inputs:
                new_target_socket = self.inputs[new_target_socket_name]
                new_link = tree.links.new(old_link.from_socket, new_target_socket)
            else:
                self.debug("New node %s has no input named %s, skipping", self.name, new_target_socket_name)
            tree.links.remove(old_link)

        for old_link in old_out_links:
            new_source_socket_name = operator.get_new_output_name(old_link.from_socket.name)
            new_source_socket_name = new_source_socket_name.lower()
            if new_source_socket_name=='object':
                new_source_socket_name='objects'
            elif new_source_socket_name=='matrix':
                new_source_socket_name='matrices'
            # We have to remove old link before creating new one
            # Blender would not allow two links pointing to the same target socket
            old_target_socket = old_link.to_socket
            tree.links.remove(old_link)
            if new_source_socket_name in self.outputs:
                new_source_socket = self.outputs[new_source_socket_name]
                new_link = tree.links.new(new_source_socket, old_target_socket)
            else:
                self.debug("New node %s has no output named %s, skipping", self.name, new_source_socket_name)
        
        # recreate hide property of socket:
        for s in old_node.outputs:
            if s.name in self.outputs:
                self.outputs[s.name].hide = old_node.outputs[s.name].hide
            pass
        pass
            

    def migrate_from(self, old_node):
        if hasattr(self, 'location_absolute'):
            # Blender 3.0 has no this attribute
            self.location_absolute = old_node.location_absolute
        
        #copy old objects to new object_names table (old table has only names of objects, no pointers):
        for I, item in enumerate(old_node.object_names):
            if I<=len(self.object_names)-1:
                if hasattr(item, 'pointer_type')==False:
                    if hasattr(item, 'name')==True:
                        if item.name in bpy.data.objects:
                            self.object_names[I].object_pointer = bpy.data.objects[item.name]
                        pass
                    pass
                pass
            pass

        pass


classes = [
    NODE_OT_open_extra,
    SvOB3BCallbackMK4,
    SvGetObjectsDataMK4,
]
register, unregister = bpy.utils.register_classes_factory(classes)
