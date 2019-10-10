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
from bpy.props import FloatProperty, BoolProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, fullList_deep_copy
from sverchok.utils.sv_itertools import sv_zip_longest

class SvVectorFromCursor(bpy.types.Operator):
    "Vector from 3D Cursor"

    bl_idname = "node.sverchok_vector_from_cursor"
    bl_label = "Vector from 3D Cursor"
    bl_options = {'REGISTER'}

    nodename: StringProperty(name='nodename')
    treename: StringProperty(name='treename')

    def execute(self, context):
        cursor = bpy.context.scene.cursor_location

        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.x_, node.y_, node.z_ = tuple(cursor)

        return{'FINISHED'}

class GenVectorsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Generator vectors '''
    bl_idname = 'GenVectorsNode'
    bl_label = 'Vector in'
    sv_icon = 'SV_VECTOR_IN'

    x_: FloatProperty(name='X', description='X', default=0.0, precision=3, update=updateNode)
    y_: FloatProperty(name='Y', description='Y', default=0.0, precision=3, update=updateNode)
    z_: FloatProperty(name='Z', description='Z', default=0.0, precision=3, update=updateNode)

    advanced_mode: BoolProperty(name='deep copy', update=updateNode, default=True)
    show_3d_cursor_button: BoolProperty(name='show button', update=updateNode, default=False)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "X").prop_name = 'x_'
        self.inputs.new('SvStringsSocket', "Y").prop_name = 'y_'
        self.inputs.new('SvStringsSocket', "Z").prop_name = 'z_'
        self.width = 100
        self.outputs.new('SvVerticesSocket', "Vectors")

    def draw_buttons(self, context, layout):
        # unfortunately, the mere fact that this function is present, will inject vertical space
        # regardless of whether content is drawn.
        if not any(s.is_linked for s in self.inputs) and self.show_3d_cursor_button:
            row = layout.row()
            get_cursor = row.operator('node.sverchok_vector_from_cursor', text='3D Cursor')
            get_cursor.nodename = self.name
            get_cursor.treename = self.id_data.name

    def draw_buttons_ext(self, context, layout):
        layout.row().prop(self, 'advanced_mode')

    def rclick_menu(self, context, layout):
        layout.prop(self, "advanced_mode", text="use deep copy")
        layout.prop(self, "show_3d_cursor_button", text="show 3d cursor button")
        if not any(s.is_linked for s in self.inputs):
            opname = 'node.sverchok_vector_from_cursor'
            get_cursor = layout.operator(opname, text='Vector from 3D Cursor', icon='PIVOT_CURSOR')
            get_cursor.nodename = self.name
            get_cursor.treename = self.id_data.name

    def process(self):
        if not self.outputs['Vectors'].is_linked:
            return
        inputs = self.inputs
        X_ = inputs['X'].sv_get()
        Y_ = inputs['Y'].sv_get()
        Z_ = inputs['Z'].sv_get()
        series_vec = []
        max_obj = max(map(len, (X_, Y_, Z_)))

        fullList_main = fullList_deep_copy if self.advanced_mode else fullList
        fullList_main(X_, max_obj)
        fullList_main(Y_, max_obj)
        fullList_main(Z_, max_obj)

        for i in range(max_obj):

            max_v = max(map(len, (X_[i], Y_[i], Z_[i])))
            fullList(X_[i], max_v)
            fullList(Y_[i], max_v)
            fullList(Z_[i], max_v)
            series_vec.append(list(zip(X_[i], Y_[i], Z_[i])))

        self.outputs['Vectors'].sv_set(series_vec)


def register():
    bpy.utils.register_class(GenVectorsNode)
    bpy.utils.register_class(SvVectorFromCursor)


def unregister():
    bpy.utils.unregister_class(GenVectorsNode)
    bpy.utils.unregister_class(SvVectorFromCursor)
