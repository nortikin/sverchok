# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import random

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode
from sverchok.utils.sv_viewer_utils import greek_alphabet

def get_random_init():
    return random.choice(greek_alphabet)


def make_or_update_instance(node, obj_name, matrix):
    context = bpy.context
    scene = context.scene
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    mesh_name = node.mesh_to_clone

    if not mesh_name:
        return

    if obj_name in objects:
        sv_object = objects[obj_name]
    else:
        mesh = meshes.get(mesh_name)
        sv_object = objects.new(obj_name, mesh)
        scene.collection.objects.link(sv_object)

    # apply matrices
    if matrix:
        sv_object.matrix_local = list(zip(*matrix))
        sv_object.data.update()   # for some reason this _is_ necessary.


class SvInstancerOp(bpy.types.Operator):

    bl_idname = "node.instancer_config"
    bl_label = "Sverchok instancer op"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: StringProperty(default="")

    def execute(self, context):
        n = context.node
        named = self.obj_name

        if named == "__SV_INSTANCE_RESET__":
            n.mesh_to_clone = ""
            n.has_instance = False
        else:
            # we assume these objects have not disappeared in the mean time.
            n.mesh_to_clone = bpy.data.objects[named].data.name
            n.has_instance = True
        return {'FINISHED'}


class SvInstancerNode(bpy.types.Node, SverchCustomTreeNode):
    '''Copy by mesh data'''
    bl_idname = 'SvInstancerNode'
    bl_label = 'Mesh instancer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSTANCER'

    def obj_available(self, context):
        if not bpy.data.meshes:
            return [('None', 'None', "", 0)]

        objs = bpy.data.objects
        display = lambda i: (not i.name.startswith(self.basedata_name)) and i.type == "MESH"
        sorted_named_objects = sorted([i.name for i in objs if display(i)])
        return [(name, name, "") for name in sorted_named_objects]

    objects_to_choose: EnumProperty(
        items=obj_available,
        name="Objects",
        description="Choose Object to take mesh from",
        update=updateNode)

    grouping: BoolProperty(default=False, update=updateNode)

    activate: BoolProperty(
        default=True,
        name='Show', description='Activate node?',
        update=updateNode)

    basedata_name: StringProperty(
        default='Alpha',
        description='stores the mesh name found in the object, this mesh is instanced',
        update=updateNode)

    mesh_to_clone: StringProperty(
        default='',
        description='stores the name of the object from where to get the mesh',
        update=updateNode)

    has_instance: BoolProperty(default=False)
    data_kind: StringProperty(name='data kind', default='MESH')

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Update")
        row.prop(self, "grouping", text="Grouped")

        cfg = "node.instancer_config"
        if not self.has_instance:
            row = layout.row(align=True)
            row.label(text='pick object by name')
            row = layout.row(align=True)
            row.prop(self, "objects_to_choose", text='')
            row.operator(cfg, text="use").obj_name = self.objects_to_choose
        else:
            row = layout.row()
            col1 = row.column()
            col1.label(text=self.mesh_to_clone, icon='MESH_DATA')
            col2 = row.column()
            col2.scale_x = 0.3
            col2.operator(cfg, text="reset").obj_name = "__SV_INSTANCE_RESET__"

        layout.label(text="Object base name", icon='OUTLINER_OB_MESH')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "basedata_name", text="")


    def get_matrices(self):
        matrices = []
        if self.inputs[s_name].is_linked:
            matrices = dataCorrect(self.inputs['matrix'].sv_get())
        return matrices

    def process(self):
        """
        hello
        """
        if not self.activate:
            return

        matrices = self.get_matrices()
        if not matrices:
            return

        with self.sv_throttle_tree_update():

            for obj_index, matrix in enumerate(matrices):
                obj_name = f'{self.basedata_name}.{obj_index:04d}'
                make_or_update_instance(self, obj_name, matrix)

            num_objects = len(matrices)
            self.remove_non_updated_objects(num_objects)

    def remove_non_updated_objects(self, num_objects):
        meshes = bpy.data.meshes
        objects = bpy.data.objects

        objs = [obj for obj in objects if obj.type == self.data_kind]
        objs = [obj for obj in objs if obj.name.startswith(self.basedata_name)]
        objs = [obj.name for obj in objs if int(obj.name.split(".")[-1]) >= num_objects]
        if not objs:
            return

        # select and finally remove all excess objects
        scene = bpy.context.scene

        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False
            scene.collection.objects.unlink(obj)
            objects.remove(obj)


    def free(self):
        self.remove_non_updated_objects(-1)


def register():
    bpy.utils.register_class(SvInstancerNode)
    bpy.utils.register_class(SvInstancerOp)


def unregister():
    bpy.utils.unregister_class(SvInstancerNode)
    bpy.utils.unregister_class(SvInstancerOp)
