# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from functools import reduce

import bpy
from mathutils import Matrix
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvViewerNode, SvCurveData
from sverchok.utils.handle_blender_data import correct_collection_length
import sverchok.utils.meshes as me


class SvPolylineViewerNode(SvViewerNode, bpy.types.Node, SverchCustomTreeNode):
    """Poly line"""  # todo fix
    bl_idname = 'SvPolylineViewerNode'
    bl_label = 'Polyline Viewer'
    bl_icon = 'MOD_CURVE'
    sv_icon = 'SV_POLYLINE_VIEWER'

    mode_options = [(k, k, '', i) for i, k in enumerate(["Multi", "Single"])]
    selected_mode: bpy.props.EnumProperty(
        items=mode_options,
        description="offers joined of unique curves",
        default="Multi", update=updateNode
    )

    dimension_modes = [(k, k, '', i) for i, k in enumerate(["3D", "2D"])]

    curve_data: bpy.props.CollectionProperty(type=SvCurveData, options={'SKIP_SAVE'})
    material: bpy.props.PointerProperty(type=bpy.types.Material, update=updateNode)

    curve_dimensions: bpy.props.EnumProperty(
        items=dimension_modes, update=updateNode,
        description="2D or 3D curves", default="3D"
    )

    is_lock_origin: bpy.props.BoolProperty(name="Lock Origin", default=True, update=updateNode,
                                           description="If unlock origin can be set manually")
    is_merge: bpy.props.BoolProperty(default=False, update=updateNode, description="Merge all meshes into one object")
    depth: bpy.props.FloatProperty(min=0.0, default=0.2, update=updateNode)
    resolution: bpy.props.IntProperty(min=0, default=3, update=updateNode)
    b_spline: bpy.props.BoolProperty(default=False, update=updateNode)
    close: bpy.props.BoolProperty(default=False, update=updateNode)
    caps: bpy.props.BoolProperty(update=updateNode)
    use_auto_uv: bpy.props.BoolProperty(name="auto uv", update=updateNode)
    data_kind: bpy.props.StringProperty(default='CURVE')
    use_smooth: bpy.props.BoolProperty(update=updateNode)
    show_wire: bpy.props.BoolProperty(update=updateNode)
    preview_resolution_u: bpy.props.IntProperty(
        name="Resolution Preview U",
        default=2, min=1, max=5, update=updateNode)
    apply_matrices_to: bpy.props.EnumProperty(
        items=[(n, n, '', ic, i)for i, (n, ic) in enumerate(zip(['object', 'mesh'], ['OBJECT_DATA', 'MESH_DATA']))],
        description='Apply matrices to',
        update=updateNode)

    def sv_init(self, context):
        super().init_viewer()

        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvMatrixSocket', 'matrix').custom_draw = 'draw_matrix_props'
        radii = self.inputs.new('SvStringsSocket', 'radii')
        radii.use_prop = True
        radii.default_float_property = 0.2
        self.inputs.new('SvStringsSocket', 'twist').use_prop = True
        self.inputs.new('SvObjectSocket', 'bevel object').object_kinds = "CURVE"

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

        layout.row().prop(self, 'curve_dimensions', expand=True)

        col = layout.column()
        if self.curve_dimensions == '3D':
            r1 = col.row(align=True)
            r1.prop(self, 'depth', text='radius')
            r1.prop(self, 'resolution', text='subdiv')
        row = col.row(align=True)
        row.prop(self, 'b_spline', text='Bspline', toggle=True)
        row.prop(self, 'close', text='close', toggle=True)
        if self.inputs['bevel object'].sv_get(default=[]):
            row.prop(self, 'caps', text='caps', toggle=True)
        row = col.row(align=True)
        row.prop(self, 'show_wire', text='wire', toggle=True)
        row.prop(self, 'use_smooth', text='smooth', toggle=True)
        row.separator()
        row.prop(self, 'selected_mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        row = layout.row()
        row.prop(self, "use_auto_uv", text="Use UV for mapping")  # todo?? soon to be deprecated
        row = layout.row()
        row.prop(self, "preview_resolution_u")

    def draw_matrix_props(self, socket, context, layout):
        socket.draw_quick_link(context, layout, self)
        layout.label(text=socket.name)
        layout.prop(self, 'apply_matrices_to', text='', expand=True)

    def process(self):
        if not self.is_active:
            return

        vertices = self.inputs['vertices'].sv_get(deepcopy=False, default=[])
        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])

        # first step is merge everything if the option
        if self.is_merge:
            objects_number = max([len(vertices), len(matrices)])
            meshes = []
            for i, verts, matrix in zip(range(objects_number), repeat_last(vertices), repeat_last(matrices)):
                mesh = me.to_mesh(verts)
                if matrix:
                    mesh.apply_matrix(matrix)
                meshes.append(mesh)

            base_mesh = reduce(lambda m1, m2: m1.add_mesh(m2), meshes)
            vertices = [base_mesh.vertices.data]
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

        # regenerate mesh data blocks
        correct_collection_length(self.curve_data, objects_number)
        for cu_data, verts, matrix in zip(self.curve_data, repeat_last(vertices), repeat_last(mesh_matrices)):
            if matrix:
                mesh = me.to_mesh(verts)
                mesh.apply_matrix(matrix)
                verts = mesh.vertices.data
            cu_data.regenerate_curve(self.base_data_name, verts)

        # regenerate object data blocks
        self.regenerate_objects([self.base_data_name], [d.curve for d in self.curve_data], [self.collection])
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, repeat_last(obj_matrices))]

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])


register, unregister = bpy.utils.register_classes_factory([SvPolylineViewerNode])
