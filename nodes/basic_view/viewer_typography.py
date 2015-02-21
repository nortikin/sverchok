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

import itertools

import bpy
from bpy.props import BoolProperty, StringProperty, BoolVectorProperty
from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, fullList, updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_viewer_utils import (
    matrix_sanitizer,
    natural_plus_one,
    get_random_init
)


def make_bmesh_geometry(node, idx, context, *topology):
    scene = context.scene
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    str_info, matrix = topology

    name = node.basemesh_name + "_" + str(idx)

    if name in objects:
        sv_object = objects[name]
    else:
        temp_mesh = default_mesh(name)
        sv_object = objects.new(name, temp_mesh)
        scene.objects.link(sv_object)

    # book-keeping via ID-props!? even this is can be broken by renames
    sv_object['idx'] = idx
    sv_object['madeby'] = node.name
    sv_object['basename'] = node.basemesh_name

    mesh = sv_object.data

    ''' get bmesh, write bmesh to obj, free bmesh'''
    # TEXT HERE

    sv_object.hide_select = False

    if matrix:
        matrix = matrix_sanitizer(matrix)
        sv_object.matrix_local = matrix
    else:
        sv_object.matrix_local = Matrix.Identity(4)


class SvBmeshViewOp2(bpy.types.Operator):

    bl_idname = "node.sv_callback_bmesh_viewer"
    bl_label = "Sverchok bmesh general callback"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')

    def hide_unhide(self, context, type_op):
        n = context.node
        k = n.basemesh_name + "_"

        child = lambda obj: obj.type == "MESH" and obj.name.startswith(k)
        objs = list(filter(child, bpy.data.objects))

        if type_op in {'hide', 'hide_render', 'hide_select'}:
            op_value = getattr(n, type_op)
            for obj in objs:
                setattr(obj, type_op, op_value)
            setattr(n, type_op, not op_value)

        elif type_op == 'mesh_select':
            for obj in objs:
                obj.select = n.select_state_mesh
            n.select_state_mesh = not n.select_state_mesh

        elif type_op == 'random_mesh_name':
            n.basemesh_name = get_random_init()

        elif type_op == 'add_material':
            mat = bpy.data.materials.new('sv_material')
            mat.use_nodes = True
            mat.use_fake_user = True  # usually handy
            n.material = mat.name

    def execute(self, context):
        self.hide_unhide(context, self.fn_name)
        return {'FINISHED'}


class SvBmeshViewerNodeMK2(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvBmeshViewerNodeMK2'
    bl_label = 'Bmesh Viewer Draw 2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # hints found at ba.org/forum/showthread.php?290106
    # - this will not allow objects on multiple layers, yet.
    def g(self):
        self['lp'] = self.get('lp', [False] * 20)
        return self['lp']

    def s(self, value):
        val = []
        for b in zip(self['lp'], value):
            val.append(b[0] != b[1])
        self['lp'] = val

    def layer_updateNode(self, context):
        '''will update in place without geometry updates'''
        for obj in self.get_children():
            obj.layers = self.layer_choice[:]

    material = StringProperty(default='', update=updateNode)
    grouping = BoolProperty(default=False)

    hide = BoolProperty(default=True)
    hide_render = BoolProperty(default=True)
    hide_select = BoolProperty(default=True)

    select_state_mesh = BoolProperty(default=False)

    activate = BoolProperty(
        default=True,
        description='When enabled this will process incoming data',
        update=updateNode)

    basemesh_name = StringProperty(
        default='Alpha',
        update=updateNode,
        description="sets which base name the object will use, "
        "use N-panel to pick alternative random names")

    layer_choice = BoolVectorProperty(
        subtype='LAYER', size=20,
        update=layer_updateNode,
        description="This sets which layer objects are placed on",
        get=g, set=s)

    def sv_init(self, context):
        self.use_custom_color = True
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('StringsSocket', 'faces', 'faces')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')

    def draw_buttons(self, context, layout):
        view_icon = 'BLENDER' if self.activate else 'ERROR'
        sh = 'node.sv_callback_bmesh_viewer'

        def icons(TYPE):
            NAMED_ICON = {
                'hide': 'RESTRICT_VIEW',
                'hide_render': 'RESTRICT_RENDER',
                'hide_select': 'RESTRICT_SELECT'}.get(TYPE)
            if not NAMED_ICON:
                return 'WARNING'
            return NAMED_ICON + ['_ON', '_OFF'][getattr(self, TYPE)]

        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, "activate", text="UPD", toggle=True, icon=view_icon)
        row.separator()
        row.operator(sh, text='', icon=icons('hide')).fn_name = 'hide'
        row.operator(sh, text='', icon=icons('hide_select')).fn_name = 'hide_select'
        row.operator(sh, text='', icon=icons('hide_render')).fn_name = 'hide_render'

        col = layout.column(align=True)
        if col:
            row = col.row(align=True)
            row.prop(self, "grouping", text="Group", toggle=True)

            row = col.row(align=True)
            row.scale_y = 1
            row.prop(self, "basemesh_name", text="", icon='OUTLINER_OB_MESH')

            row = col.row(align=True)
            row.scale_y = 1.62
            row.operator(sh, text='Select Toggle').fn_name = 'mesh_select'

            col.separator()
            row = col.row(align=True)
            row.scale_y = 1
            row.prop_search(
                self, 'material', bpy.data, 'materials', text='',
                icon='MATERIAL_DATA')
            row.operator(sh, text='', icon='ZOOMIN').fn_name = 'add_material'

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.separator()

        row = layout.row(align=True)
        sh = 'node.sv_callback_bmesh_viewer'
        row.operator(sh, text='Rnd Name').fn_name = 'random_mesh_name'

        col = layout.column(align=True)
        box = col.box()
        if box:
            box.label(text="Beta options")
            box.prop(self, 'layer_choice', text='layer')

    def process(self):

        if not self.activate:
            return

        for obj_index, Verts in enumerate(mverts):
            make_text_object(self, obj_index, bpy.context, info)

        self.remove_non_updated_objects(obj_index)
        objs = self.get_children()

        if self.grouping:
            self.to_group(objs)

        # truthy if self.material is in .materials
        if bpy.data.materials.get(self.material):
            self.set_corresponding_materials(objs)

    def get_children(self):
        objs = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        return [o for o in objs if o.get('basename') == self.basemesh_name]

    def remove_non_updated_objects(self, obj_index):
        objs = self.get_children()
        objs = [obj.name for obj in objs if obj['idx'] > obj_index]
        if not objs:
            return

        meshes = bpy.data.meshes
        objects = bpy.data.objects
        scene = bpy.context.scene

        # remove excess objects
        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False
            scene.objects.unlink(obj)
            objects.remove(obj)

        # delete associated meshes
        for object_name in objs:
            meshes.remove(meshes[object_name])

    def to_group(self, objs):
        groups = bpy.data.groups
        named = self.basemesh_name

        # alias group, or generate new group and alias that
        group = groups.get(named, groups.new(named))

        for obj in objs:
            if obj.name not in group.objects:
                group.objects.link(obj)

    def set_corresponding_materials(self, objs):
        for obj in objs:
            obj.active_material = bpy.data.materials[self.material]


def register():
    bpy.utils.register_class(SvBmeshViewerNodeMK2)
    bpy.utils.register_class(SvBmeshViewOp2)


def unregister():
    bpy.utils.unregister_class(SvBmeshViewerNodeMK2)
    bpy.utils.unregister_class(SvBmeshViewOp2)
