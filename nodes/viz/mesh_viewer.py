# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle

import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_obj_helper import SvObjHelper, get_random_init_v3
from sverchok.utils.nodes_mixins.generating_objects import BlenderObjects, SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length


class SvMeshViewer(bpy.types.Node, SverchCustomTreeNode, SvObjHelper, BlenderObjects, SvViewerNode):
    """ bmv Generate Live geom """

    bl_idname = 'SvMeshViewer'
    bl_label = 'Mesh viewer'
    bl_icon = 'OUTLINER_OB_MESH'
    sv_icon = 'SV_BMESH_VIEWER'

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData)

    merge: BoolProperty(default=False, update=updateNode)

    auto_smooth: BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    extended_matrix: BoolProperty(  # todo check functionality
        default=False,
        description='Allows mesh.transform(matrix) operation, quite fast!')

    to3d: BoolProperty(default=False, update=updateNode)
    show_wireframe: BoolProperty(default=False, update=updateNode, name="Show Edges")

    def sv_init(self, context):
        self.init_viewer()
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvStringsSocket', 'faces')
        self.inputs.new('SvStringsSocket', 'material_idx')
        self.inputs.new('SvMatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)

    def draw_buttons_ext(self, context, layout):
        self.draw_ext_object_buttons(context, layout)

        col = layout.column(align=True)
        col.prop(self, 'extended_matrix', text='Extended Matrix')
        col.prop(self, 'auto_smooth', text='smooth shade')
        col.prop(self, 'show_wireframe')
        col.prop(self, 'to3d')

    def draw_label(self):
        return f"MeV {self.basedata_name}"

    @property
    def draw_3dpanel(self):
        return self.to3d

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.prop(self, 'base_data_name', text='')
        row.prop_search(self, 'material_pointer', bpy.data, 'materials', text='', icon='MATERIAL_DATA')

    def process(self):

        if not self.activate:
            return

        verts = self.inputs['vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['edges'].sv_get(deepcopy=False, default=cycle([None]))
        faces = self.inputs['faces'].sv_get(deepcopy=False, default=cycle([None]))
        mat_indexes = self.inputs['material_idx'].sv_get(deepcopy=False, default=[])
        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])

        objects_number = max([len(verts), len(matrices)])  # todo if merged

        correct_collection_length(self.mesh_data, objects_number)
        [me_data.regenerate_mesh(self.basedata_name, v, e, f) for me_data, v, e, f in
            zip(self.mesh_data, verts, edges, faces)]
        self.regenerate_objects([self.basedata_name], [d.mesh for d in self.mesh_data], [self.collection])

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

    def sv_copy(self, other):
        with self.sv_throttle_tree_update():
            self.base_data_name = get_random_init_v3()


register, unregister = bpy.utils.register_classes_factory([SvMeshViewer])
