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
from sverchok.utils.nodes_mixins.generating_objects import BlenderObjects, SvMeshData
from sverchok.utils.handle_blender_data import correct_collection_length


class SvMeshViewer(bpy.types.Node, SverchCustomTreeNode, SvObjHelper, BlenderObjects):
    """ bmv Generate Live geom """

    bl_idname = 'SvMeshViewer'
    bl_label = 'Mesh viewer'
    bl_icon = 'OUTLINER_OB_MESH'
    sv_icon = 'SV_BMESH_VIEWER'

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData)

    grouping: BoolProperty(default=False, update=SvObjHelper.group_state_update_handler)
    merge: BoolProperty(default=False, update=updateNode)

    calc_normals: BoolProperty(default=False, update=updateNode)

    fixed_verts: BoolProperty(
        default=False,
        description="Use only with unchanging topology")

    autosmooth: BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    extended_matrix: BoolProperty(
        default=False,
        description='Allows mesh.transform(matrix) operation, quite fast!')

    randomize_vcol_islands: BoolProperty(
        default=False,
        description="experimental option to find islands in the outputmesh and colour them randomly")

    to3d: BoolProperty(default=False, update=updateNode)
    show_wireframe: BoolProperty(default=False, update=updateNode, name="Show Edges")

    def sv_init(self, context):
        self.sv_init_helper_basedata_name()

        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvStringsSocket', 'faces')
        self.inputs.new('SvStringsSocket', 'material_idx')
        self.inputs.new('SvMatrixSocket', 'matrix')

        self.outputs.new('SvObjectSocket', "Objects")

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)

        # additional UI options.
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "grouping", text="Group", toggle=True)
        row.prop(self, "merge", text="Merge", toggle=True)

        self.draw_object_buttons(context, layout)

    def draw_buttons_ext(self, context, layout):
        # self.draw_buttons(context, layout)
        self.draw_ext_object_buttons(context, layout)

        col = layout.column(align=True)
        box = col.box()
        if box:
            box.label(text='Beta options')
            box.prop(self, 'extended_matrix', text='Extended Matrix')
            box.prop(self, 'fixed_verts', text='Fixed vert count')
            box.prop(self, 'autosmooth', text='smooth shade')
            box.prop(self, 'calc_normals', text='calculate normals')
            box.prop(self, 'layer_choice', text='layer')
            box.prop(self, 'randomize_vcol_islands', text='randomize vcol islands')
            box.prop(self, 'show_wireframe')
        col.prop(self, 'to3d')

    def draw_label(self):
        return f"MeV {self.basedata_name}"

    @property
    def draw_3dpanel(self):
        return self.to3d

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        # row.alert = warning
        row.prop(self, 'basedata_name', text='')
        row.prop_search(self, 'material_pointer', bpy.data, 'materials', text='', icon='MATERIAL_DATA')
        # row.operator('node.sv_callback_bmesh_viewer',text='',icon='RESTRICT_SELECT_OFF')

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
        self.regenerate_objects([self.basedata_name], [d.mesh for d in self.mesh_data])

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

    def sv_copy(self, other):
        with self.sv_throttle_tree_update():
            dname = get_random_init_v3()
            self.basedata_name = dname


def register():
    bpy.utils.register_class(SvMeshViewer)


def unregister():
    bpy.utils.unregister_class(SvMeshViewer)
