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

from sverchok.nodes.matrix.apply_and_join import apply_and_join_python
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length
from sverchok.utils.sv_mesh_utils import mesh_join


class SvMeshViewer(SvViewerNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: viewer mesh object instance

    Generate mesh objects in viewport
    """

    bl_idname = 'SvMeshViewer'
    bl_label = 'Mesh viewer'
    bl_icon = 'OUTLINER_OB_MESH'
    sv_icon = 'SV_BMESH_VIEWER'

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData)

    is_merge: BoolProperty(default=False, update=updateNode, description="Merge all meshes into one object")

    is_smooth_mesh: BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    apply_matrices_to: bpy.props.EnumProperty(
        items=[(n, n, '', ic, i)for i, (n, ic) in enumerate(zip(['object', 'mesh'], ['OBJECT_DATA', 'MESH_DATA']))],
        description='Apply matrices to',
        update=updateNode)

    to3d: BoolProperty(name="Show in 3D panel", default=False, update=updateNode,
                       description="Show node properties in 3D panel")
    show_wireframe: BoolProperty(default=False, update=updateNode, name="Show Edges")
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

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'fast_mesh_update', text='Fast mesh update')
        layout.prop(self, 'is_smooth_mesh', text='smooth shade')
        layout.prop(self, 'to3d')

    def draw_matrix_props(self, socket, context, layout):
        socket.draw_quick_link(context, layout, self)
        layout.label(text=socket.name)
        layout.prop(self, 'apply_matrices_to', text='', expand=True)

    def draw_edges_props(self, socket, context, layout):
        socket.draw_quick_link(context, layout, self)
        layout.label(text=socket.name)
        layout.prop(self, 'show_wireframe', text='', expand=True,
                    icon='HIDE_OFF' if self.show_wireframe else 'HIDE_ON')

    def draw_label(self):
        if self.hide:
            return f"MeV {self.base_data_name}"
        else:
            return "Mesh viewer"

    @property
    def draw_3dpanel(self):
        return self.to3d

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
            if matrices:
                objects_number = max([len(verts), len(matrices)])
                mat_indexes = [[i for _, obj, mat_i in zip(range(objects_number), cycle(faces), cycle(mat_indexes))
                                for f, i in zip(obj, cycle(mat_i))]]
                _, *join_mesh_data = list(zip(*zip(range(objects_number), cycle(verts), cycle(edges), cycle(faces),
                                                   cycle(matrices))))
                verts, edges, faces = apply_and_join_python(*join_mesh_data, True)
                matrices = []
            else:
                mat_indexes = [[i for obj, mat_i in zip(faces, cycle(mat_indexes)) for f, i in zip(obj, cycle(mat_i))]]
                verts, edges, faces = mesh_join(verts, edges if edges[0] else [], faces)  # function has good API
                verts, edges, faces = [verts], [edges], [faces]

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
                mat_i = [mi for _, mi in zip(me_data.mesh.polygons, cycle(mat_i))]
                me_data.mesh.polygons.foreach_set('material_index', mat_i)
            me_data.set_smooth(self.is_smooth_mesh)


        # regenerate object data blocks
        self.regenerate_objects([self.base_data_name], [d.mesh for d in self.mesh_data], [self.collection])
        [setattr(prop.obj, 'matrix_local', m) for prop, m in zip(self.object_data, cycle(obj_matrices))]
        [setattr(prop.obj, 'show_wire', self.show_wireframe) for prop in self.object_data]

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

    # Serialization properties
    @property
    def properties_to_skip_iojson(self):
        return super().properties_to_skip_iojson + ['mesh_data']


class SvCreateMaterial(bpy.types.Operator):
    """It creates and add new material to a node"""
    bl_idname = 'node.sv_create_material'
    bl_label = "Create material"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Crate new material"

    def execute(self, context):
        mat = bpy.data.materials.new('sv_material')
        mat.use_nodes = True
        context.node.material = mat
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.node, 'material')


register, unregister = bpy.utils.register_classes_factory([SvMeshViewer, SvCreateMaterial])
