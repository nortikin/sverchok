# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty, EnumProperty
import bmesh
from mathutils import Vector, Matrix

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


class SvOB3BDataCollectionMK2(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    icon: bpy.props.StringProperty(default="BLANK1")


class ReadingObjectDataError(Exception):
    pass


class SVOB3B_UL_NamesListMK2(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        item_icon = item.icon
        if not item.icon or item.icon == "BLANK1":
            try:
                item_icon = 'OUTLINER_OB_' + bpy.data.objects[item.name].type
            except:
                item_icon = ""

        layout.label(text=item.name, icon=item_icon)
        action = data.wrapper_tracked_ui_draw_op(layout, "node.sv_ob3b_collection_operator_mk2", icon='X', text='')
        action.fn_name = 'REMOVE'
        action.idx = index


class SvOB3BItemOperatorMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_collection_operator_mk2"
    bl_label = "generic bladibla"

    fn_name: StringProperty(default='')
    idx: IntProperty()

    def sv_execute(self, context, node):
        if self.fn_name == 'REMOVE':
            node.object_names.remove(self.idx)
        node.process_node(None)


class SvOB3CallbackMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.ob3_callback_mk2"
    bl_label = "Object In mk3 callback"
    bl_options = {'INTERNAL'}

    fn_name: StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)

def get_vertgroups(mesh):
    return [k for k,v in enumerate(mesh.vertices) if v.groups.values()]

numpy_socket_names = ['vertices', 'edges', 'vertex_normals', 'material_idx', 'polygon_areas', 'polygon_centers', 'polygon_normals']


class SvGetObjectsDataMK3(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Object Info
    Tooltip: Get Scene Objects into Sverchok Tree
    """

    bl_idname = 'SvGetObjectsDataMK3'
    bl_label = 'Get Objects Data'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

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

    modifiers: BoolProperty(
        name='Modifiers',
        description='Apply modifier geometry to import (original untouched)',
        default=False, update=updateNode) # type: ignore

    vergroups: BoolProperty(
        name='Vergroups',
        description='Use vertex groups to nesty insertion',
        default=False, update=hide_show_versgroups) # type: ignore

    sort: BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True, update=updateNode) # type: ignore

    object_names: bpy.props.CollectionProperty(type=SvOB3BDataCollectionMK2) # type: ignore

    active_obj_index: bpy.props.IntProperty() # type: ignore

    out_np: bpy.props.BoolVectorProperty(
        name="Output Numpy",
        description="Output NumPy arrays (makes node faster)",
        size=7, update=updateNode) # type: ignore

    output_np_all: BoolProperty(
        name='Output all numpy',
        description='Output numpy arrays if possible',
        default=False, update=updateNode) # type: ignore
    
    apply_matrix: BoolProperty(
        name = "Apply matrices",
        description = "Apply objects matrices",
        default = True,
        update = updateNode) # type: ignore
    
    mesh_join : BoolProperty(
        name = "merge",
        description = "If checked, join mesh elements into one object",
        default = False,
        update = updateNode) # type: ignore

    display_types = [
            ('BOUNDS', "", "BOUNDS: Display the bounds of the object", "MATPLANE", 0),
            ('WIRE', "", "WIRE: Display the object as a wireframe", "MESH_CUBE", 1),
            ('SOLID', "", "SOLID: Display the object as a solid (if solid drawing is enabled in the viewport)", "SNAP_VOLUME", 2),  #custom_icon("SV_MAKE_SOLID")
            ('TEXTURED', "", "TEXTURED: Display the object with textures (if textures are enabled in the viewport)", "TEXTURE",  3),
        ]
    
    def update_display_type(self, context):
        for obj in self.object_names:
            bpy.data.objects[obj.name].display_type=self.display_type
        return
    
    display_type : EnumProperty(
        name = "Display Types",
        items = display_types,
        default = 'WIRE',
        update = update_display_type) # type: ignore
    
    hide_render_types = [
            ('RESTRICT_RENDER_ON', "", "Render objects", "RESTRICT_RENDER_ON", 0),
            ('RESTRICT_RENDER_OFF', "", "Do not render objects", "RESTRICT_RENDER_OFF", 1),
        ]
    
    def update_render_type(self, context):
        for obj in self.object_names:
            bpy.data.objects[obj.name].hide_render = True if self.hide_render_type=='RESTRICT_RENDER_ON' else False
        return
    
    hide_render_type : EnumProperty(
        name = "Render Types",
        items = hide_render_types,
        default = 'RESTRICT_RENDER_OFF',
        update = update_render_type) # type: ignore
    
    align_3dview_types = [
            ('ISOLATE_CURRENT', "", "Toggle local view with only current selected object in the list\nPress again to restore view", "PIVOT_CURSOR", 0),
            ('ISOLATE_ALL', "", "Toggle local view with all objects in the list\nPress again to restore view", "PIVOT_INDIVIDUAL", 1),
        ]


    def verts_sockets_update(self, context):
        for name in ['vertices_select', 'vertices_crease', 'vertices_bevel_weight']:
            self.outputs[name].hide = not(self.enable_verts_attribute_sockets)
        updateNode(self, context)

    def edges_sockets_update(self, context):
        for name in ['edges_select', 'edges_seams', 'edges_sharps', 'edges_crease', 'edges_bevel_weight',]:
            self.outputs[name].hide = not(self.enable_edges_attribute_sockets)
        updateNode(self, context)

    def polygons_sockets_update(self, context):
        for name in ['polygon_selects', 'polygon_smooth', ]:
            self.outputs[name].hide = not(self.enable_polygons_attribute_sockets)
        updateNode(self, context)

    enable_verts_attribute_sockets: BoolProperty(
        name = "Show verts attribute sockets",
        description = "Show additional sockets for verts attributes:\n1. select\n2. crease\n3. bevel weight",
        default = False,
        update = verts_sockets_update) # type: ignore

    enable_edges_attribute_sockets: BoolProperty(
        name = "Show edges attribute sockets",
        description = "Show additional sockets for edges attributes:\n1. select\n2. sharp\n3. seams\n4. crease\n4. bevel weight",
        default = False,
        update = edges_sockets_update) # type: ignore

    enable_polygons_attribute_sockets: BoolProperty(
        name = "Show polygons attribute sockets",
        description = "Show additional sockets for faces attributes:\n1. select\n2. smooth",
        default = False,
        update = polygons_sockets_update) # type: ignore
    
    vertex_attribute_types = [
        ('SELECTED', "", "Get faces indicex, currently selected", "FACESEL", 0),
        ('ACTIVE_FACE_MAP', "", "Get faces indices, currently actived in Face Maps of object", "FACE_MAPS", 1),
    ]

    vertex_attribute_type : EnumProperty(
        name = "Render Types",
        items = vertex_attribute_types,
        default = 'SELECTED',
        update = updateNode) # type: ignore

    def update_align_3dview(self, context):
        if len(self.object_names)==0:
            return
        obj_in_list = self.object_names[self.active_obj_index]
        if obj_in_list:
            # reset all selections
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            
            # select all objects in list of this node
            if self.align_3dview_type=='ISOLATE_ALL':
                for obj in self.object_names:
                    if obj.name in bpy.data.objects:
                        bpy.data.objects[obj.name].select_set(True)

            if obj_in_list.name in bpy.data.objects:
                obj_in_scene = bpy.data.objects[obj_in_list.name]
                obj_in_scene.select_set(True)
                bpy.context.view_layer.objects.active = obj_in_scene

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    ctx = bpy.context.copy()
                    ctx['area'] = area
                    ctx['region'] = area.regions[-1]
                    # test if current mode is local view: https://blender.stackexchange.com/questions/290669/checking-for-object-being-in-local-view
                    if self.align_3dview_type_previous_value!=self.align_3dview_type and area.spaces.active.local_view:
                        bpy.ops.view3d.localview(ctx, frame_selected=False)
                    self.align_3dview_type_previous_value = self.align_3dview_type
                    bpy.ops.view3d.localview(ctx, frame_selected=False)
                    #bpy.ops.view3d.view_selected(ctx)
                    break

            pass
        return
    
    align_3dview_type : EnumProperty(
        name = "Local View",
        items = align_3dview_types,
        default = 'ISOLATE_CURRENT',
        update = update_align_3dview) # type: ignore
    
    align_3dview_type_previous_value : EnumProperty(
        name = "Local View",
        items = align_3dview_types,
        default = 'ISOLATE_CURRENT') # type: ignore

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
        layout.prop(self, 'hide_render_type', expand=True)
        layout.separator()
        layout.prop(self, 'align_3dview_type', expand=True)
        layout.separator()
        layout.label(text=f'  {socket.label} ')
        layout.prop(self, 'enable_edges_attribute_sockets', icon='MESH_DATA', text='', toggle=True)
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()

    def draw_polygons_out_socket(self, socket, context, layout):
        layout.prop(self, 'display_type', expand=True, text='')
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

        self.outputs.new('SvVerticesSocket', "vertices")
        self.outputs.new('SvStringsSocket' , "edges")
        self.outputs.new('SvStringsSocket' , "polygons")
        self.outputs.new('SvStringsSocket' , "vertices_select")
        self.outputs.new('SvStringsSocket' , "vertices_crease")
        self.outputs.new('SvStringsSocket' , "vertices_bevel_weight")
        self.outputs.new('SvStringsSocket' , "edges_select")
        self.outputs.new('SvStringsSocket' , "edges_crease")
        self.outputs.new('SvStringsSocket' , "edges_seams")
        self.outputs.new('SvStringsSocket' , "edges_sharps")
        self.outputs.new('SvStringsSocket' , "edges_bevel_weight")
        self.outputs.new('SvStringsSocket' , "polygon_selects")
        self.outputs.new('SvStringsSocket' , "polygon_smooth")
        self.outputs.new('SvVerticesSocket', "vertex_normals")
        self.outputs.new('SvStringsSocket' , "material_idx")
        self.outputs.new('SvStringsSocket' , "polygon_areas")
        self.outputs.new('SvVerticesSocket', "polygon_centers")
        self.outputs.new('SvVerticesSocket', "polygon_normals")
        self.outputs.new('SvMatrixSocket'  , "matrix")
        self.outputs.new('SvObjectSocket'  , "object")

        self.inputs ["objects"]         .label = "Objects"

        self.outputs["vertices"]                .label = "Vertices"
        self.outputs["edges"]                   .label = "Edges"
        self.outputs["polygons"]                .label = "Polygons"
        self.outputs["vertices_select"]         .label = "(*) Vertices Select"
        self.outputs["vertices_crease"]         .label = "(*) Vertices Crease"
        self.outputs["vertices_bevel_weight"]   .label = "(*) Vertices Bevel Weight"
        self.outputs["edges_select"]            .label = "(|) Edges Select"
        self.outputs["edges_seams"]             .label = "(|) Edges Seam"
        self.outputs["edges_sharps"]            .label = "(|) Edges Sharp"
        self.outputs["edges_crease"]            .label = "(|) Edges Crease"
        self.outputs["edges_bevel_weight"]      .label = "(|) Edges Bevel Weight"
        self.outputs["polygon_selects"]         .label = "(+) Polygons Select"
        self.outputs["polygon_smooth"]          .label = "(+) Polygons Smooth"
        self.outputs["vertex_normals"]          .label = "Vertex Normals"
        self.outputs["material_idx"]            .label = "Material Idx"
        self.outputs["polygon_areas"]           .label = "Polygon Areas"
        self.outputs["polygon_centers"]         .label = "Polygon Centers"
        self.outputs["polygon_normals"]         .label = "Polygon Normals"
        self.outputs["matrix"]                  .label = "Matrix"
        self.outputs["object"]                  .label = "Object"

        self.outputs["vertices_select"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_crease"]         .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["vertices_bevel_weight"]   .hide = not(self.enable_verts_attribute_sockets)
        self.outputs["edges_select"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_seams"]             .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_sharps"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_crease"]            .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["edges_bevel_weight"]      .hide = not(self.enable_edges_attribute_sockets)
        self.outputs["polygon_selects"]         .hide = not(self.enable_polygons_attribute_sockets)
        self.outputs["polygon_smooth"]          .hide = not(self.enable_polygons_attribute_sockets)

        self.outputs["vertices"].custom_draw = 'draw_vertices_out_socket'
        self.outputs["edges"].custom_draw = 'draw_edges_out_socket'
        self.outputs["polygons"].custom_draw = 'draw_polygons_out_socket'

    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()

        names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

        if self.sort:
            names.sort()

        for name in names:
            item = self.object_names.add()
            item.name = name
            item.icon = 'OUTLINER_OB_' + bpy.data.objects[name].type

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)

    def select_objs(self, ops):
        """select all objects referenced by node"""
        for item in self.object_names:
            bpy.data.objects[item.name].select = True

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no object associated with the obj in Node")


    def draw_obj_names(self, layout):
        if self.object_names:
            layout.template_list("SVOB3B_UL_NamesListMK2", "", self, "object_names", self, "active_obj_index")
        else:
            layout.label(text='--None--')

    @property
    def by_input(self):
        return self.inputs[0].object_ref_pointer is not None or self.inputs[0].is_linked

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        by_input = self.by_input
        if not by_input:
            row = col.row()

            op_text = "Get selection"  # fallback
            callback = 'node.ob3_callback_mk2'

            if self.prefs_over_sized_buttons:
                row.scale_y = 4.0
                op_text = "G E T"

            self.wrapper_tracked_ui_draw_op(row, callback, text=op_text).fn_name = 'get_objects_from_scene'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "apply_matrix", text="Apply matrix", toggle=True)
        row.prop(self, "mesh_join", text="merge", toggle=True)
        
        col = layout.column(align=True)
        row = col.row(align=True)
        if not by_input:
            row.prop(self, 'sort', text='Sort', toggle=True)
        row.prop(self, "modifiers", text="Post", toggle=True)
        row.prop(self, "vergroups", text="VeGr", toggle=True)
        if not by_input:
            self.draw_obj_names(layout)

    def sv_draw_buttons_ext(self, context, layout):
        r = layout.column(align=True)
        row = r.row(align=True)
        row.label(text="Output Numpy:")
        row.prop(self, 'output_np_all', text='If possible', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                r.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

        layout.prop(self, 'draw_3dpanel', text="To Control panel")

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.label(text="Output Numpy:")
        layout.prop(self, 'output_np_all', text='All', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                layout.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

    def draw_buttons_3dpanel(self, layout):
        if not self.by_input:
            callback = 'node.ob3_callback_mk2'
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
        objs = self.inputs[0].sv_get(default=[[]])
        if not self.object_names and not objs[0]:
            return
        
        data_objects = bpy.data.objects
        outputs = self.outputs

        vers_out_grouped = []

        o_vertices, o_edges, o_polygons, o_vertices_select, o_vertices_crease, o_vertices_bevel_weight, o_edges_select, o_edges_crease, o_edges_seams, o_edges_sharps, o_edges_bevel_weight, o_polygon_selects, o_polygon_smooth, o_vertex_normals, o_material_idx, o_polygon_areas, o_polygon_centers, o_polygon_normals, o_matrices, o_objects = [s.is_linked for s in self.outputs[:20]]
        l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_crease, l_edges_seams, l_edges_sharps, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_material_idx, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_matrices = [[] for s in self.outputs[:19]]
        if self.modifiers:
            sv_depsgraph = bpy.context.evaluated_depsgraph_get()

        out_np = self.out_np if not self.output_np_all else [True for i in range(7)]
        if isinstance(objs[0], list):
            objs = objs[0]
        if not objs:
            objs = (data_objects.get(o.name) for o in self.object_names)

        # iterate through references
        for obj in objs:

            if not obj:
                continue

            mtrx = obj.matrix_world
            if obj.type in {'EMPTY', 'CAMERA', 'LAMP' }:
                if o_matrices:
                    l_matrices.append(mtrx)
                continue
            try:
                if obj.mode == 'EDIT' and obj.type == 'MESH':
                    # Mesh objects do not currently return what you see
                    # from 3dview while in edit mode when using obj.to_mesh.
                    me = obj.data
                    bm = bmesh.from_edit_mesh(me)
                    # verts, edgs, pols = pydata_from_bmesh(bm)

                    if o_vertices:
                        verts = [ v.co[:] for v in bm.verts]  # v.co is a Vector()
                    if o_edges:
                        edgs = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
                    if o_polygons:
                        pols = [[i.index for i in p.verts] for p in bm.faces]
                    if o_vertices_select:
                        vertices_select1 = [v.select for v in bm.verts]
                    if o_vertices_crease:
                        crease_layer = bm.verts.layers.crease.verify()
                        vertices_crease1 = [v[crease_layer] for v in bm.verts]
                    if o_vertices_bevel_weight:
                        bevel_weight_layer = bm.verts.layers.bevel_weight.verify()
                        vertices_bevel_weight1 = [v[bevel_weight_layer] for v in bm.verts]
                    if o_edges_select:
                        edges_select1 = [e.select for e in bm.edges]
                    if o_edges_seams:
                        edges_seams1 = [e.seam for e in bm.edges]
                    if o_edges_sharps:
                        edges_sharps1 = [not(e.smooth) for e in bm.edges]
                    if o_edges_crease:
                        crease_layer = bm.edges.layers.crease.verify()
                        edges_crease1 = [ e[crease_layer] for e in bm.edges ]
                    if o_edges_bevel_weight:
                        bevel_weight_layer = bm.edges.layers.bevel_weight.verify()
                        edges_bevel_weight1 = [e[bevel_weight_layer] for e in bm.edges]
                    if o_polygon_selects:
                        polygon_selects1 = [f.select for f in bm.faces]
                    if o_polygon_smooth:
                        polygon_smooth1 = [f.smooth for f in bm.faces]
                    if self.vergroups:
                        vert_groups      = get_vertgroups(obj.data)
                    if o_vertex_normals:
                        vertex_normals = [ v.normal[:] for v in bm.verts] # v.normal is a Vector()
                    if o_material_idx:
                        material_indexes = self.get_materials_from_bmesh(bm)
                    if o_polygon_areas:
                        polygons_areas = [ p.calc_area() for p in bm.faces ]
                    if o_polygon_centers:
                        polygon_centers = [ p.calc_center_median()[:] for p in bm.faces ]
                    if o_polygon_normals:
                        polygon_normals = [ p.normal[:] for p in bm.faces ]

                    del bm
                else:

                    # https://developer.blender.org/T99661
                    if obj.type == 'CURVE' and obj.mode == 'EDIT' and bpy.app.version[:2] == (3, 2):
                        raise ReadingObjectDataError("Does not support curves in edit mode in Blender 3.2")
                    elif self.modifiers:
                        obj = sv_depsgraph.objects[obj.name]
                        obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                    else:
                        obj_data = obj.to_mesh()
                    
                    T, R, S = mtrx.decompose()

                    if o_vertices:
                        verts            = [ ((mtrx @ v.co) if self.apply_matrix else v.co)[:] for v in obj_data.vertices]  # v.co is a Vector()
                    if o_edges:
                        edgs             = [[ e.vertices[0], e.vertices[1] ] for e in obj_data.edges]
                    if o_polygons:
                        pols             = [list(p.vertices) for p in obj_data.polygons]
                    if o_vertices_select:
                        vertices_select1 = [v.select for v in obj_data.vertices]
                    if o_vertices_crease:
                        creases = obj_data.vertex_creases[0]
                        vertices_crease1 = [creases.data[i].value for i, v in enumerate(obj_data.vertices)]
                    if o_vertices_bevel_weight:
                        vertices_bevel_weight1 = [v.bevel_weight for v in obj_data.vertices]
                    if o_edges_select:
                        edges_select1 = [e.select for e in obj_data.edges]
                    if o_edges_seams:
                        edges_seams1 = [e.use_seam for e in obj_data.edges]
                    if o_edges_sharps:
                        edges_sharps1 = [e.use_edge_sharp for e in obj_data.edges]
                    if o_edges_crease:
                        edges_crease1 = [e.crease for e in obj_data.edges]
                    if o_edges_bevel_weight:
                        edges_bevel_weight1 = [e.bevel_weight for e in obj_data.edges]
                    if o_polygon_selects:
                        polygon_selects1 = [p.select for p in obj_data.polygons]
                    if o_polygon_smooth:
                        polygon_smooth1 = [p.use_smooth for p in obj_data.polygons]
                    if self.vergroups:
                        vert_groups      = get_vertgroups(obj_data)
                    if o_vertex_normals:
                        vertex_normals   = [ ((   R @ v.co) if self.apply_matrix else v.normal)[:] for v in obj_data.vertices ] # v.normal is a Vector(). Update. Blender 3.6.3 crash in no wrap Vector(v.normal). I think this is after line "obj.to_mesh_clear()"
                    if o_material_idx:
                        material_indexes = read_materials_idx(obj_data, out_np[3])
                    if o_polygon_areas:
                        polygons_areas   = [ polygon.area for polygon in obj_data.polygons]
                    if o_polygon_centers:
                        polygon_centers  = [ ((mtrx @ polygon.center) if self.apply_matrix else polygon.center)[:] for polygon in obj_data.polygons]
                    if o_polygon_normals:
                        polygon_normals  = [ ((   R @ polygon.normal) if self.apply_matrix else polygon.normal)[:] for polygon in obj_data.polygons]

                obj.to_mesh_clear()
                
                if o_vertices:
                    l_vertices.append( verts )
                if o_edges:
                    l_edges.append( edgs )
                if o_polygons:
                    l_polygons.append( pols )
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
                if self.vergroups:
                    vers_out_grouped.append( vert_groups )
                if o_vertex_normals:
                    l_vertex_normals.append( vertex_normals )
                if o_material_idx:
                    l_material_idx.append( material_indexes )
                if o_polygon_areas:
                    l_polygon_areas.append( polygons_areas )
                if o_polygon_centers:
                    l_polygon_centers.append( polygon_centers )
                if o_polygon_normals:
                    l_polygon_normals.append( polygon_normals )

            except ReadingObjectDataError:
                raise
            except Exception as err:
                # it's not clear which cases this try catch should handle
                # probably it should skip wrong object types
                self.debug('failure in process between frozen area', self.name, err)

            if o_matrices:
                l_matrices.append(mtrx)

        if self.mesh_join:
            # l_vertices, l_edges, l_polygons, l_vertex_normals, l_material_idx, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_matrices
            offset = 0
            _vertices, _edges, _polygons, _vertices_select, _vertices_crease, _vertices_bevel_weight, _edges_select, _edges_seams, _edges_sharps, _edges_crease, _edges_bevel_weight, _polygon_selects, _polygon_smooth, _vertex_normals, _polygon_areas, _polygon_centers, _polygon_normals, _vg = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
            for idx, vertices in enumerate(l_vertices):
                _vertices.extend(vertices)
                if l_edges:
                    _edges.extend( [[i + offset for i in o] for o in l_edges[idx] ] ) # edges
                if l_polygons:
                    _polygons.extend( [[i + offset for i in o] for o in l_polygons[idx] ] ) # polygons
                #_l_vertex_normals.extend( [tuple(i + offset for i in o) for o in ps[idx] ] ) # vers_out_grouped. Skip in mesh_join
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
                # _l_material_idx - materia index. Do not change
                # if l_material_idx and len(l_material_idx)>idx:
                #     _l_material_idx.extend( l_material_idx[idx] ) # Skip in mesh_join
                if l_polygon_areas:
                    _polygon_areas.extend( l_polygon_areas[idx] ) # polygon area
                if l_polygon_centers:
                    _polygon_centers.extend( l_polygon_centers[idx] ) # polygon center
                if l_polygon_normals:
                    _polygon_normals.extend( l_polygon_normals[idx] ) # polygon normal
                # if l_matrices: Do not change
                #     _ms.append( l_matrices[idx] ) # matrices. Skip in mesh_join
                if vers_out_grouped:
                    _vg.extend( [ i + offset for i in vers_out_grouped[idx] ] ) # vertex groups
                
                offset += len(vertices)
            
            l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_seams, l_edges_sharps, l_edges_crease, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_polygon_areas, l_polygon_centers, l_polygon_normals, vers_out_grouped = [_vertices], [_edges], [_polygons], [_vertices_select], [_vertices_crease], [_vertices_bevel_weight], [_edges_select], [_edges_seams], [_edges_sharps], [_edges_crease], [_edges_bevel_weight], [_polygon_selects], [_polygon_smooth], [_vertex_normals], [_polygon_areas], [_polygon_centers], [_polygon_normals], [_vg]

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

        for i, i2 in zip(self.outputs, [l_vertices, l_edges, l_polygons, l_vertices_select, l_vertices_crease, l_vertices_bevel_weight, l_edges_select, l_edges_crease, l_edges_seams, l_edges_sharps, l_edges_bevel_weight, l_polygon_selects, l_polygon_smooth, l_vertex_normals, l_material_idx, l_polygon_areas, l_polygon_centers, l_polygon_normals, l_matrices]):
            if i.is_linked:
                i.sv_set(i2)

        if vers_out_grouped and vers_out_grouped[0]:
            if 'Vers_grouped' in outputs and self.vergroups:
                outputs['Vers_grouped'].sv_set(vers_out_grouped)
        if o_objects:
            if self.by_input:
                outputs['object'].sv_set(objs)
            else:
                outputs['object'].sv_set([data_objects.get(o.name) for o in self.object_names])


classes = [SvOB3BItemOperatorMK2, SvOB3BDataCollectionMK2, SVOB3B_UL_NamesListMK2, SvOB3CallbackMK2, SvGetObjectsDataMK3]
register, unregister = bpy.utils.register_classes_factory(classes)
