# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle

import bpy
from bpy.props import BoolProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
import sverchok.utils.meshes as me
from sverchok.utils.sv_logging import fix_error_msg

class SV_PT_SvMeshViewerVieweportDsiplayOptionsMenu(bpy.types.Panel):
    bl_label = "Like Object Viewport Display properties"

    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_context = "data"

    #bl_ui_units_x = 12

    def is_extended():
        return True

    def draw(self, context):
        layout = self.layout
        #layout.use_property_split = True https://blender.stackexchange.com/questions/161581/how-to-display-the-animate-property-diamond-keyframe-insert-button-2-8x
        if hasattr(context, 'node'):
            #layout.emboss='RADIAL_MENU'
            #grid = layout.grid_flow(row_major=False, columns=2, align=True)
            #context.socket.draw_menu_items(context, layout)
            layout.label(text='Vieweport Display:')
            col = layout.column(align=True, heading='Show')
            col.use_property_decorate = False
            col.use_property_split = True

            col.prop(context.node, 'show_name')
            col.prop(context.node, 'show_axis')
            col.prop(context.node, 'show_wireframe')
            col.prop(context.node, 'show_all_edges')
            col.prop(context.node, 'show_texture_space')
            col.prop(context.node, 'show_shadows')
            col.prop(context.node, 'show_in_front')

            col = layout.column(align=True, heading='Color')
            col.use_property_decorate = False
            col.use_property_split = True
            col.prop(context.node, 'color')
    
            # col = layout.column(align=True, heading='Display As')
            # col.use_property_decorate = False
            # col.use_property_split = True
            # col.prop(context.node, 'display_type', expand=True, text='')

            col = layout.row(align=True)
            col.use_property_decorate = False
            col.use_property_split = True
            col.prop(context.node, 'display_type', expand=True, text='Display As', icon_only=True)

            col = layout.row(align=True, heading='Bounds')
            col.use_property_decorate = False
            col.use_property_split = True
            col.prop(context.node, 'show_bounds', text='',)
            row1 = col.row(align=True)
            row1.enabled = context.node.show_bounds
            row1.prop(context.node, 'display_bounds_type', expand=True, text=' ', icon_only=True)
            
        pass

class SvMeshViewer(Show3DProperties, SvViewerNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: viewer mesh object instance
    Tooltip: Generate/Update mesh objects in viewport. Blender’s Modifier stack can be used but Skin modifier.\n\tIn: Vertices, Edges, Faces, Materials/idx, Matrixes\n\tParams: Mesh Name, Origin, Merge\n\tExtra:Fast Update, Smooth Shade (N-panel)
    """

    bl_idname = 'SvMeshViewer'
    bl_label = 'Mesh Viewer'
    bl_icon = 'OUTLINER_OB_MESH'
    sv_icon = 'SV_BMESH_VIEWER'

    replacement_nodes = [('SvViewerDrawMk4', 
                            dict(vertices = 'Vertices',
                                 edges = 'Edges',
                                 faces = 'Polygons',
                                 matrix = 'Matrix'
                            ),
                        None)]

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData, options={'SKIP_SAVE'})

    is_merge: BoolProperty(default=False, update=updateNode, description="Merge all meshes into one object")

    is_smooth_mesh: BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    apply_matrices_to: bpy.props.EnumProperty(
        items=[(n, n, '', ic, i)for i, (n, ic) in enumerate(zip(['object', 'mesh'], ['OBJECT_DATA', 'MESH_DATA']))],
        description='Apply matrices to',
        update=updateNode)

    show_name: BoolProperty(default=False, update=updateNode, name="Name")
    show_axis: BoolProperty(default=False, update=updateNode, name="Axes")
    show_wireframe: BoolProperty(default=False, update=updateNode, name="Edges")
    show_all_edges: BoolProperty(default=False, update=updateNode, name="All Edges")
    show_texture_space: BoolProperty(default=False, update=updateNode, name="Texture Space")
    show_shadows: BoolProperty(default=False, update=updateNode, name="Shadows")
    show_in_front: BoolProperty(default=False, update=updateNode, name="In Front")
    color: bpy.props.FloatVectorProperty(
            name        = "Color",
            subtype     = 'COLOR',
            description = "Object Color and alpha, used when the Object Color mode is enabled",
            default     = (1., 1., 1., 1.),
            size=4, min=0., max=1.,
            update      = updateNode,
        )

    display_types = [
        ('BOUNDS', "Bounds", "BOUNDS: Display the bounds of the object", "MATPLANE", 0),
        ('WIRE', "Wire", "WIRE: Display the object as a wireframe", "MESH_CUBE", 1),
        ('SOLID', "Solid", "SOLID: Display the object as a solid (if solid drawing is enabled in the viewport)", "SNAP_VOLUME", 2),  #custom_icon("SV_MAKE_SOLID")
        ('TEXTURED', "Textured", "TEXTURED: Display the object with textures (if textures are enabled in the viewport)", "TEXTURE",  3),
    ]

    display_type : bpy.props.EnumProperty(
        name    = "Display As",
        items   = display_types,
        default = 'TEXTURED',
        update  = updateNode)

    show_bounds: BoolProperty(
        default     = False,
        name        = "Display Bounds",
        description = "Display the object's bounds",
        update      = updateNode,
    )

    display_bounds_types = [
        ('BOX', "Box", "Display bounds as box", "CUBE", 0),
        ('SHPERE', "Sphere", "Display bounds as sphere", "SPHERE", 1),
        ('CYLINDER', "Cylinder", "Display bounds as cylinder", "MESH_CYLINDER", 2),  #custom_icon("SV_MAKE_SOLID")
        ('CONE', "Cone", "Display bounds as cone", "CONE",  3),
        ('CAPSULE', "Capsule", "Display bounds as capsule", "META_CAPSULE",  4),
    ]

    display_bounds_type : bpy.props.EnumProperty(
        name    = "Display As",
        items   = display_bounds_types,
        default = 'BOX',
        update  = updateNode)



    material: bpy.props.PointerProperty(type=bpy.types.Material, update=updateNode)
    is_lock_origin: bpy.props.BoolProperty(name="Lock Origin", default=True, update=updateNode,
                                           description="If unlock origin can be set manually")
    fast_mesh_update: bpy.props.BoolProperty(
        default=True, update=updateNode,
        description="Usually should be enabled. If some glitches with mesh update, switch it off")

    def sv_init(self, context):
        self.init_viewer()
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edges').custom_draw = 'draw_edges_props'
        self.inputs.new('SvStringsSocket', 'faces')
        self.inputs.new('SvStringsSocket', 'material_idx')
        self.inputs.new('SvMatrixSocket', 'matrix').custom_draw = 'draw_matrix_props'

    def draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)

        row = layout.row(align=True)
        row.prop_search(self, 'material', bpy.data, 'materials', text='', icon='MATERIAL_DATA')
        row.operator('node.sv_create_material', text='', icon='ADD')

        row = layout.row(align=True)
        col = row.column(align=True)
        col.active = False if \
            not self.is_merge and self.inputs['matrix'].is_linked and self.apply_matrices_to == 'object' else True
        col.prop(self, 'is_lock_origin', text="Origin", icon='LOCKED' if self.is_lock_origin else 'UNLOCKED')
        row.prop(self, 'is_merge', text='Merge', toggle=1, icon='AUTOMERGE_ON' if self.is_merge else 'AUTOMERGE_OFF')

        row = layout.row(align=True)
        row.label(text='Vieweport Display:')
        row.popover(panel="SV_PT_SvMeshViewerVieweportDsiplayOptionsMenu", icon='TRIA_DOWN', text="")



    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'fast_mesh_update', text='Fast mesh update')
        layout.prop(self, 'is_smooth_mesh', text='smooth shade')
        layout.prop(self, 'draw_3dpanel')

        layout.label(text='Vieweport Display:')
        col = layout.column(align=True, heading='Show')
        col.use_property_decorate = False
        col.use_property_split = True
        col.prop(self, 'show_name')
        col.prop(self, 'show_axis')
        col.prop(self, 'show_wireframe')
        col.prop(self, 'show_all_edges')
        col.prop(self, 'show_texture_space')
        col.prop(self, 'show_shadows')
        col.prop(self, 'show_in_front')

        col = layout.row(align=True)
        col.use_property_decorate = False
        col.use_property_split = True
        col.prop(self, 'color')

        # layout.label(text='Display As:')
        # layout.prop(self, 'display_type', expand=True, text='')
        col = layout.row(align=True)
        col.use_property_decorate = False
        col.use_property_split = True
        col.prop(self, 'display_type', expand=True, text='Display As', icon_only=True)

        col = layout.row(align=True, heading='Bounds')
        col.use_property_decorate = False
        col.use_property_split = True
        col.prop(self, 'show_bounds', text='',)
        row1 = col.row(align=True)
        row1.enabled = self.show_bounds
        row1.prop(self, 'display_bounds_type', expand=True, text=' ', icon_only=True)
        return

    def draw_matrix_props(self, socket, context, layout):
        socket.draw_quick_link(context, layout, self)
        layout.label(text=socket.name)
        layout.prop(self, 'apply_matrices_to', text='', expand=True)
        return

    def draw_edges_props(self, socket, context, layout):
        socket.draw_quick_link(context, layout, self)
        layout.label(text=socket.name)
        layout.prop(self, 'show_wireframe', text='', expand=True, icon='HIDE_OFF' if self.show_wireframe else 'HIDE_ON')
        return

    def draw_label(self):
        if self.hide:
            return f"MeV {self.base_data_name}"
        else:
            return "Mesh Viewer"

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.prop(self, 'base_data_name', text='')
        row.prop_search(self, 'material', bpy.data, 'materials', text='', icon='MATERIAL_DATA')

    def sv_copy(self, other):
        super().sv_copy(other)
        self.mesh_data.clear()

    def process(self):

        if not self.is_active:
            return

        verts = self.inputs['vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['edges'].sv_get(deepcopy=False, default=[[]])
        faces = self.inputs['faces'].sv_get(deepcopy=False, default=[[]])
        mat_indexes = self.inputs['material_idx'].sv_get(deepcopy=False, default=[[]])
        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])

        # first step is merge everything if the option
        if self.is_merge:
            objects_number = max([len(verts), len(matrices)])
            meshes = []
            for i, *elements, materials, matrix in zip(
                    range(objects_number),
                    repeat_last(verts),
                    repeat_last(edges),
                    repeat_last(faces),
                    repeat_last(mat_indexes),
                    repeat_last(matrices if matrices else [[]])):

                mesh = me.to_mesh(*elements)
                if materials:
                    mesh.polygons['material'] = materials
                if matrix:
                    mesh.apply_matrix(matrix)
                meshes.append(mesh)
            base_mesh = me.join(meshes)

            verts, edges, faces = [base_mesh.vertices.data], [base_mesh.edges.data], [base_mesh.polygons.data]
            mat_indexes = [base_mesh.polygons.get_attribute('material', [])]
            matrices = []

        objects_number = max([len(verts), len(matrices)]) if verts else 0

        # extract mesh matrices
        if self.apply_matrices_to == 'mesh':
            if matrices:
                mesh_matrices = matrices
            else:
                mesh_matrices = cycle([None])
        else:
            mesh_matrices = cycle([None])

        # extract object matrices
        if self.apply_matrices_to == 'object':
            if matrices:
                obj_matrices = matrices
            else:
                if self.is_lock_origin:
                    obj_matrices = cycle([Matrix.Identity(4)])
                else:
                    obj_matrices = []
        else:
            if self.is_lock_origin:
                obj_matrices = cycle([Matrix.Identity(4)])
            else:
                obj_matrices = []

        # regenerate mesh data blocks
        correct_collection_length(self.mesh_data, objects_number)
        create_mesh_data = zip(self.mesh_data, cycle(verts), cycle(edges), cycle(faces), cycle(mesh_matrices),
                               cycle(mat_indexes))
        for me_data, v, e, f, m, mat_i in create_mesh_data:
            me_data.regenerate_mesh(self.base_data_name, v, e, f, m, self.fast_mesh_update)
            if self.material:
                me_data.mesh.materials.clear()
                me_data.mesh.materials.append(self.material)
            if mat_indexes:
                with fix_error_msg({TypeError: "Unsupported material format"}):
                    mat_i = [int(mi) for _, mi in zip(me_data.mesh.polygons, cycle(mat_i))]
                me_data.mesh.polygons.foreach_set('material_index', mat_i)
            me_data.set_smooth(self.is_smooth_mesh)
            # https://blender.stackexchange.com/questions/274330/set-shade-smooth-with-a-script
            # if self.is_smooth_mesh:
            #     with bpy.context.temp_override(selected_editable_objects=[bpy.data.objects[me_data.mesh.name]]):
            #         bpy.ops.object.shade_smooth(use_auto_smooth=True)
            #         pass
            # else:
            #     with bpy.context.temp_override(selected_editable_objects=[bpy.data.objects[me_data.mesh.name]]):
            #         bpy.ops.object.shade_flat()
            #         pass



        # regenerate object data blocks
        self.regenerate_objects([self.base_data_name],
                                [d.mesh for d in self.mesh_data],
                                [self.collection],
                                to_show=[self.id_data.sv_show and self.show_objects]
                                )
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, cycle(obj_matrices))]
        [setattr(prop.obj, 'show_name', self.show_name) for prop in self.object_data]
        [setattr(prop.obj, 'show_axis', self.show_axis) for prop in self.object_data]
        [setattr(prop.obj, 'show_wire', self.show_wireframe) for prop in self.object_data]
        [setattr(prop.obj, 'show_all_edges', self.show_all_edges) for prop in self.object_data]
        [setattr(prop.obj, 'show_texture_space', self.show_texture_space) for prop in self.object_data]
        [setattr(prop.obj.display, 'show_shadows', self.show_shadows) for prop in self.object_data]
        [setattr(prop.obj, 'show_in_front', self.show_in_front) for prop in self.object_data]
        [setattr(prop.obj, 'display_type', self.display_type) for prop in self.object_data]
        [setattr(prop.obj, 'color', self.color) for prop in self.object_data]
        [setattr(prop.obj, 'show_bounds', self.show_bounds) for prop in self.object_data]
        [setattr(prop.obj, 'display_bounds_type', self.display_bounds_type) for prop in self.object_data]

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])


register, unregister = bpy.utils.register_classes_factory([SV_PT_SvMeshViewerVieweportDsiplayOptionsMenu, SvMeshViewer])
