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


import bpy
from bpy.props import (BoolProperty, StringProperty, FloatProperty, IntProperty)

from sverchok.data_structure import updateNode

from sverchok.utils.sv_viewer_utils import (
    matrix_sanitizer,
    remove_non_updated_objects,
    get_children,
    natural_plus_one,
    get_random_init,
    greek_alphabet)


soh = 'node.sv_callback_svobjects_helper'


class SvObjectsHelperCallback(bpy.types.Operator):

    bl_idname = soh
    bl_label = "Sverchok objects helper"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')
    kind = StringProperty(default='CURVE')

    def dispatch(self, context, type_op):
        n = context.node
        objs = get_children(n, self.kind)  

        if type_op in {'object_hide', 'object_hide_render', 'object_hide_select', 'object_select'}:
            for obj in objs:
                setattr(obj, type_op, getattr(n, type_op))  # needs to cut off "object_"
            setattr(n, type_op, not getattr(n, type_op))

        elif type_op == 'random_basedata_name':   # random_data_name  ?
            n.basedata_name = get_random_init()

        elif type_op == 'add_material':
            mat = bpy.data.materials.new('sv_material')
            mat.use_nodes = True
            n.material = mat.name
            # print(mat.name)  info(mat.name)

    def execute(self, context):
        self.dispatch(context, self.fn_name)
        return {'FINISHED'}


class SvObjHelper():

    activate = BoolProperty(
        name='Show',
        description='When enabled this will process incoming data',
        default=True,
        update=updateNode)

    basedata_name = StringProperty(
        default='Alpha',
        description="which base name the object an data will use",
        update=updateNode
    )    

    # to be used if the node has no material input.
    material = StringProperty(default='', update=updateNode)

    # to be used as standard toggles for object attributes of same name
    object_hide = BoolProperty(default=True)
    object_hide_render = BoolProperty(default=True)
    object_select = BoolProperty(default=True)
    object_hide_select = BoolProperty(default=False)    

    show_wire = BoolProperty(update=updateNode)
    use_smooth = BoolProperty(default=True, update=updateNode)

    def __init__(self):
        ...


    def draw_object_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')

        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, "activate", text="UPD", toggle=True, icon=view_icon)

        row.operator(soh, text='', icon=self.icons('v')).fn_name = 'object_hide'
        row.operator(soh, text='', icon=self.icons('s')).fn_name = 'object_hide_select'
        row.operator(soh, text='', icon=self.icons('r')).fn_name = 'object_hide_render'

        col = layout.column(align=True)
        if col:
            row = col.row(align=True)
            row.scale_y = 1
            row.prop(self, "basedata_name", text="", icon='OUTLINER_OB_MESH')

            row = col.row(align=True)
            row.scale_y = 2
            row.operator(soh, text='Select / Deselect').fn_name = 'object_select'
            row = col.row(align=True)
            row.scale_y = 1

            row.prop_search(
                self, 'material', bpy.data, 'materials', text='',
                icon='MATERIAL_DATA')

        col = layout.column(align=True)
        if col:
            row = col.row(align=True)
            row.prop(self, 'show_wire', text='wire', toggle=True)
            row.prop(self, 'use_smooth', text='smooth', toggle=True)        

    def draw_ext_object_buttons(self, context, layout):
        layout.separator()
        row = layout.row(align=True)
        row.operator(soh, text='Rnd Name').fn_name = 'random_basedata_name'
        row.operator(soh, text='+Material').fn_name = 'add_material'        

    def copy(self, other):
        self.basedata_name = get_random_init()

    def set_corresponding_materials(self, kind='MESH'):
        if bpy.data.materials.get(self.material):
            for obj in get_children(self, kind):
                obj.active_material = bpy.data.materials[self.material]


def register():
    bpy.utils.register_class(SvObjectsHelperCallback)


def unregister():
    bpy.utils.unregister_class(SvObjectsHelperCallback)
