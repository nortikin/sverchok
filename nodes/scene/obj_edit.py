# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


import json

class SvObjEditCallback(bpy.types.Operator):
    """ """
    bl_idname = "node.sverchok_objectedit_cb"
    bl_label = "Sverchok object in lite callback"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    cmd: StringProperty()
    mode: StringProperty()

    def execute(self, context):
        getattr(context.node, self.cmd)(self, self.mode)
        return {'FINISHED'}


class SvObjEdit(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Set Edit/Object Mode'''
    bl_idname = 'SvObjEdit'
    bl_label = 'Obj Edit mode'
    bl_icon = 'EDITMODE_HLT'

    obj_passed_in: StringProperty()

    def set_edit(self, ops, mode):
        try:
            obj_name = self.obj_passed_in or self.inputs[0].object_ref

            bpy.context.view_layer.objects.active = bpy.data.objects.get(obj_name)
            bpy.ops.object.mode_set(mode=mode)

        except Exception as err:
            ops.report({'WARNING'}, 'No object selected / active')
            print(err)


    def sv_init(self, context):
        inputsocket = self.inputs.new
        inputsocket('SvObjectSocket', 'Objects')

    def draw_buttons(self, context, layout):

        if not (self.inputs and self.inputs[0]):
            return

        callback = 'node.sverchok_objectedit_cb'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 4.0 if self.prefs_over_sized_buttons else 1

        objects = bpy.data.objects
        if self.obj_passed_in or self.inputs[0].object_ref:
            obj = objects.get(self.obj_passed_in) or objects.get(self.inputs[0].object_ref)
            if obj:
                button_data, new_mode = {
                    'OBJECT': [dict(icon='EDITMODE_HLT', text='Edit'), 'EDIT'],
                    'EDIT': [dict(icon='OBJECT_DATAMODE', text='Object'), 'OBJECT']
                }.get(obj.mode)

                op1 = row.operator(callback, **button_data)
                op1.cmd = 'set_edit'
                op1.mode = new_mode


    def process(self):
        obj_socket = self.inputs[0]
        not_linked = not obj_socket.is_linked

        self.obj_passed_in = ''

        if not_linked:
            self.obj_passed_in = obj_socket.object_ref
        else:
            objlist = obj_socket.sv_get()
            if objlist and len(objlist) == 1:
                self.obj_passed_in = objlist[0].name


def register():
    bpy.utils.register_class(SvObjEditCallback)
    bpy.utils.register_class(SvObjEdit)


def unregister():
    bpy.utils.unregister_class(SvObjEditCallback)
    bpy.utils.unregister_class(SvObjEdit)
