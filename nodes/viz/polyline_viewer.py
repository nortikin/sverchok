# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Matrix
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvViewerNode, SvCurveData
from sverchok.utils.handle_blender_data import correct_collection_length
import sverchok.utils.meshes as me


class SvPolylineViewerNode(SvViewerNode, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: viewer polyline object nurbs NURBS curves splines

    Generate curve objects in viewport
    """
    bl_idname = 'SvPolylineViewerNode'
    bl_label = 'Polyline Viewer'
    bl_icon = 'MOD_CURVE'
    sv_icon = 'SV_POLYLINE_VIEWER'

    curve_data: bpy.props.CollectionProperty(type=SvCurveData, options={'SKIP_SAVE'})
    material: bpy.props.PointerProperty(type=bpy.types.Material, update=updateNode)
    curve_dimensions: bpy.props.EnumProperty(
        items=[(k, k, '', i) for i, k in enumerate(["3D", "2D"])], update=updateNode,
        description="2D or 3D curves", default="3D")
    is_lock_origin: bpy.props.BoolProperty(name="Lock Origin", default=True, update=updateNode,
                                           description="If unlock origin can be set manually")
    is_merge: bpy.props.BoolProperty(default=False, update=updateNode, description="Merge all meshes into one object")
    bevel_depth: bpy.props.FloatProperty(name="Bevel depth", min=0.0, default=0.2, update=updateNode,
                                         description="Changes the size of the bevel")
    resolution: bpy.props.IntProperty(name="Resolution", min=0, default=3, update=updateNode,
                                      description="Alters the smoothness of the bevel")
    curve_type: bpy.props.EnumProperty(items=[(i, i, '') for i in ['NURBS', 'POLY']], update=updateNode,
                                       description="Curve type")
    close: bpy.props.BoolProperty(default=False, update=updateNode, description="Closes generated curves")
    caps: bpy.props.BoolProperty(update=updateNode, description="Seals the ends of a beveled curve")
    data_kind: bpy.props.StringProperty(default='CURVE')
    use_smooth: bpy.props.BoolProperty(update=updateNode, default=True)
    show_wire: bpy.props.BoolProperty(update=updateNode)
    preview_resolution_u: bpy.props.IntProperty(
        name="Resolution Preview U", default=2, min=1, max=5, update=updateNode,
        description="The resolution property defines the number of points that are"
                    " computed between every pair of control points.")
    apply_matrices_to: bpy.props.EnumProperty(
        items=[(n, n, '', ic, i)for i, (n, ic) in enumerate(zip(['object', 'mesh'], ['OBJECT_DATA', 'MESH_DATA']))],
        description='Apply matrices to', update=updateNode)

    def sv_init(self, context):
        super().init_viewer()

        self.inputs.new('SvVerticesSocket', 'vertices').custom_draw = 'draw_vertices_props'
        self.inputs.new('SvMatrixSocket', 'matrix').custom_draw = 'draw_matrix_props'
        radii = self.inputs.new('SvStringsSocket', 'radius')
        radii.use_prop = True
        radii.default_float_property = 0.2
        self.inputs.new('SvStringsSocket', 'tilt').use_prop = True
        obj_socket = self.inputs.new('SvObjectSocket', 'bevel object')
        obj_socket.custom_draw = 'draw_object_props'
        obj_socket.object_kinds = "CURVE"

    def draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)

        col = layout.column()
        row = col.row(align=True)
        row.prop_search(self, 'material', bpy.data, 'materials', text='', icon='MATERIAL_DATA')
        row.operator('node.sv_create_material', text='', icon='ADD')

        row = col.row(align=True)
        row_lock = row.row(align=True)
        row_lock.active = False if \
            not self.is_merge and self.inputs['matrix'].is_linked and self.apply_matrices_to == 'object' else True
        row_lock.prop(self, 'is_lock_origin', text="Origin", icon='LOCKED' if self.is_lock_origin else 'UNLOCKED')
        row.prop(self, 'is_merge', text='Merge', toggle=1, icon='AUTOMERGE_ON' if self.is_merge else 'AUTOMERGE_OFF')

        col_dimensions = col.column(align=True)
        col_dimensions.row(align=True).prop(self, 'curve_dimensions', expand=True)
        col_dimensions.prop(self, 'bevel_depth')
        col_dimensions.prop(self, 'resolution')

        row = col.row(align=True)
        row.prop(self, 'curve_type', expand=True)

    def draw_buttons_ext(self, context, layout):
        col = layout.column()
        col.prop(self, 'show_wire', text='wire')
        col.prop(self, 'use_smooth', text='smooth')
        col.prop(self, "preview_resolution_u")

    def draw_matrix_props(self, socket, context, layout):
        if not socket.is_linked:
            socket.draw_quick_link(context, layout, self)
        layout.label(text=socket.name)
        layout.prop(self, 'apply_matrices_to', text='', expand=True)

    def draw_vertices_props(self, socket, context, layout):
        row = layout.row(align=True)
        if not socket.is_linked:
            socket.draw_quick_link(context, row, self)
        row.label(text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        row = row.row()
        row.scale_x = 0.5
        row.prop(self, 'close', toggle=True)

    def draw_object_props(self, socket, context, layout):
        row = layout.row(align=True)
        if not socket.is_linked:
            row.prop_search(socket, 'object_ref_pointer', bpy.data, 'objects', 
                            text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        else:
            row.label(text=f'{socket.name}. {socket.objects_number if socket.objects_number else ""}')
        row = row.row(align=True)
        row.ui_units_x = 0.6
        row.prop(self, 'caps', text='C', toggle=True)

    def process(self):
        if not self.is_active:
            return

        vertices = self.inputs['vertices'].sv_get(deepcopy=False, default=[])
        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])
        radius = self.inputs['radius'].sv_get(deepcopy=False)
        tilt = self.inputs['tilt'].sv_get(deepcopy=False)
        bevel_objects = self.inputs['bevel object'].sv_get(default=[])

        # first step is merge everything if the option
        if self.is_merge:
            objects_number = max([len(vertices), len(matrices)])
            meshes = []
            for i, verts, matrix in zip(range(objects_number), repeat_last(vertices),
                                        repeat_last(matrices if matrices else [[]])):
                mesh = me.to_mesh(verts)
                if matrix:
                    mesh.apply_matrix(matrix)
                meshes.append(mesh)

            vertices = [m.vertices.data for m in meshes]
            matrices = []

        objects_number = max([len(vertices), len(matrices)]) if len(vertices) else 0

        # extract mesh matrices
        if self.apply_matrices_to == 'mesh':
            if matrices:
                mesh_matrices = matrices
            else:
                mesh_matrices = [None]
        else:
            mesh_matrices = [None]

        # extract object matrices
        if self.apply_matrices_to == 'object':
            if matrices:
                obj_matrices = matrices
            else:
                if self.is_lock_origin:
                    obj_matrices = [Matrix.Identity(4)]
                else:
                    obj_matrices = []
        else:
            if self.is_lock_origin:
                obj_matrices = [Matrix.Identity(4)]
            else:
                obj_matrices = []

        # regenerate curve data blocks
        if self.is_merge:
            correct_collection_length(self.curve_data, 1)
            self.curve_data[0].regenerate_curve(
                self.base_data_name, vertices, self.curve_type, radius, self.close, self.use_smooth, tilt)
        else:
            correct_collection_length(self.curve_data, objects_number)
            for cu_data, verts, matrix, r, t in zip(self.curve_data, repeat_last(vertices), repeat_last(mesh_matrices), 
                                                 repeat_last(radius), repeat_last(tilt)):
                if matrix:
                    mesh = me.to_mesh(verts)
                    mesh.apply_matrix(matrix)
                    verts = mesh.vertices.data
                cu_data.regenerate_curve(
                    self.base_data_name, [verts], self.curve_type, [r], self.close, self.use_smooth, [t])

        # assign curve properties
        for cu_data, bevel_object in zip(self.curve_data, repeat_last(bevel_objects or [None])):
            cu_data.curve.dimensions = self.curve_dimensions
            cu_data.curve.bevel_depth = self.bevel_depth
            cu_data.curve.bevel_resolution = self.resolution
            cu_data.curve.resolution_u = self.preview_resolution_u
            cu_data.curve.bevel_object = bevel_object
            cu_data.curve.use_fill_caps = self.caps
            if self.material:
                cu_data.curve.materials.clear()
                cu_data.curve.materials.append(self.material)

        # regenerate object data blocks
        self.regenerate_objects([self.base_data_name], [d.curve for d in self.curve_data], [self.collection])
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, repeat_last(obj_matrices))]
        [setattr(prop.obj, 'show_wire', self.show_wire) for prop in self.object_data]

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

    def sv_copy(self, other):
        super().sv_copy(other)
        self.curve_data.clear()


register, unregister = bpy.utils.register_classes_factory([SvPolylineViewerNode])
