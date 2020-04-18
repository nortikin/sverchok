# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import itertools

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import dataCorrect, updateNode


def make_or_update_instance(node, obj_name, matrix, blueprint_obj):
    context = bpy.context
    scene = context.scene
    objects = bpy.data.objects

    # WHAT ABOUT MODIFIERS ON THESE OBJECTS?

    collections = bpy.data.collections
    collection = collections.get(node.basedata_name)

    if obj_name in objects:
        sv_object = objects[obj_name]
    else:
        data = blueprint_obj.data# data_kind.get(data_name)

        if node.full_copy:
            sv_object = blueprint_obj.copy()
            sv_object.name = obj_name
        else:
            sv_object = objects.new(obj_name, blueprint_obj.data)
        
        collection.objects.link(sv_object)

    # if the object is selected in the scene, this node can keep the instance unselected
    sv_object.select_set(0)

    # apply matrices
    if matrix:
        sv_object.matrix_local = list(zip(*matrix))
        
        if sv_object.data:
            if hasattr(sv_object.data, "update"):
                sv_object.data.update()   # for some reason this _is_ necessary.
    
    return sv_object


class SvInstancerNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Copy by mesh data from object input '''
    bl_idname = 'SvInstancerNodeMK2'
    bl_label = 'Obj instancer MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INSTANCER'

    @throttled
    def updateNode_copy(self, context):
        # this means we should empty the collection, and let process repopulate
        objects = bpy.data.collections[self.basedata_name].objects
        for obj in objects:
            bpy.data.objects.remove(obj)


    activate: BoolProperty(
        default=True,
        name='Show', description='Activate node?',
        update=updateNode)

    full_copy: BoolProperty(name="Full Copy", update=updateNode_copy)
    delete_source: BoolProperty(
        default=False,
        name='Delete Source', description='Delete Source Objects',
        update=updateNode)

    basedata_name: StringProperty(
        default='Alpha',
        description='stores the mesh name found in the object, this mesh is instanced',
        update=updateNode)

    has_instance: BoolProperty(default=False)
    

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'objects')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.outputs.new('SvObjectSocket', 'objects')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Update")
        row = layout.row(align=True)
        row.prop(self, "delete_source", text="RM Source", toggle=True)
        row.prop(self, "full_copy", text="full copy", toggle=True)

        layout.label(text="Object base name")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "basedata_name", text="", icon='FILE_CACHE')
        

    def get_matrices(self):
        if self.inputs['matrix'].is_linked:
            return dataCorrect(self.inputs['matrix'].sv_get())
        return []

    def process(self):

        if not self.activate:
            return

        matrices = self.get_matrices()
        if not matrices:
            return

        objects = self.inputs['objects'].sv_get()
        if not objects:
            return
        
        new_objects = [ ]
        with self.sv_throttle_tree_update():

            self.ensure_collection()
            combinations = zip(itertools.cycle(objects), matrices)
            for obj_index, (obj, matrix) in enumerate(combinations):
                obj_name = f'{self.basedata_name}.{obj_index:04d}'
                new_objects.append(make_or_update_instance(self, obj_name, matrix, obj))

            num_objects = len(matrices)

            if self.delete_source:
                for obj in objects:
                    bpy.data.objects.remove(obj)

            self.remove_non_updated_objects(num_objects)

        self.outputs['objects'].sv_set(new_objects)

    def ensure_collection(self):
        collections = bpy.data.collections
        if not collections.get(self.basedata_name):
            collection = collections.new(self.basedata_name)
            bpy.context.scene.collection.children.link(collection)


    def remove_non_updated_objects(self, num_objects):
        meshes = bpy.data.meshes
        objects = bpy.data.objects
        collections = bpy.data.collections

        # use collections to gather objects.
        objs = collections.get(self.basedata_name)
        if not objs:
            return

        objs = [obj.name for obj in objs.objects if int(obj.name.split(".")[-1]) >= num_objects]
        if not objs:
            return

        # select and finally remove all excess objects
        collections = bpy.data.collections
        collection = collections.get(self.basedata_name)

        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False
            collection.objects.unlink(obj)
            objects.remove(obj)


    # def sv_free(self):
    #     # self.remove_non_updated_objects(-1)
    #     # or remove content of associated collection...undecided, lets see what
    #     # people expect...
    #     pass


def register():
    bpy.utils.register_class(SvInstancerNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvInstancerNodeMK2)
