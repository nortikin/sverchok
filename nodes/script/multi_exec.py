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

import json
import bpy
import mathutils
import bmesh as bm
import numpy as np
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


lines = """\
for i, i2 in zip(V1, V2):
    append([x + y for x, y in zip(i, i2)])
""".strip().split('\n')


def update_wrapper(self, context):
    try:
        updateNode(context.node, context)
    except:
        ...


class SvExecNodeDynaStringItem(bpy.types.PropertyGroup):
    line = bpy.props.StringProperty(name="line to eval", default="", update=update_wrapper)


class SvExecNodeModCallback(bpy.types.Operator):

    bl_idname = "node.callback_execnodemod"
    bl_label = "generic callback"

    cmd = bpy.props.StringProperty(default='')

    def execute(self, context):
        getattr(context.node, self.cmd)(self)
        return {'FINISHED'}


class SvExecNodeMod(bpy.types.Node, SverchCustomTreeNode):
    ''' Exec Node Mod'''
    bl_idname = 'SvExecNodeMod'
    bl_label = 'Exec Node Mod'
    bl_icon = 'CONSOLE'

    text = StringProperty(default='', update=updateNode)
    dynamic_strings = bpy.props.CollectionProperty(type=SvExecNodeDynaStringItem)

    def draw_buttons(self, context, layout):
        if len(self.dynamic_strings) == 0:
            return

        if not context.active_node == self:
            b = layout.box()
            col = b.column(align=True)
            for idx, line in enumerate(self.dynamic_strings):
                col.prop(self.dynamic_strings[idx], "line", text="", emboss=False)
        else:
            col = layout.column(align=True)
            for idx, line in enumerate(self.dynamic_strings):
                col.prop(self.dynamic_strings[idx], "line", text="")

        row = layout.row(align=True)
        # add() remove() clear() move()
        row.operator('node.callback_execnodemod', text='', icon='ZOOMIN').cmd = 'add_new_line'
        row.operator('node.callback_execnodemod', text='', icon='ZOOMOUT').cmd = 'remove_last_line'
        row.operator('node.callback_execnodemod', text='', icon='TRIA_UP').cmd = 'shift_up'
        row.operator('node.callback_execnodemod', text='', icon='TRIA_DOWN').cmd = 'shift_down'

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        col.operator('node.callback_execnodemod', text='copy to node').cmd = 'copy_from_text'
        col.prop_search(self, 'text', bpy.data, "texts", text="")

    def add_new_line(self, context):
        self.dynamic_strings.add().line = ""

    def remove_last_line(self, context):
        if len(self.dynamic_strings) > 1:
            self.dynamic_strings.remove(len(self.dynamic_strings)-1)

    def shift_up(self, context):
        sds = self.dynamic_strings
        for i in range(len(sds)):
            sds.move(i+1, i)

    def shift_down(self, context):
        sds = self.dynamic_strings
        L = len(sds)
        for i in range(L):
            sds.move(L-i, i-1)

    def copy_from_text(self, context):
        for i, i2 in zip(self.dynamic_strings, bpy.data.texts[self.text].lines):
            i.line = i2.body

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'V1')
        self.inputs.new('StringsSocket', 'V2')
        self.inputs.new('StringsSocket', 'V3')
        self.outputs.new('StringsSocket', 'out')

        # add default strings
        self.dynamic_strings.add().line = lines[0]
        self.dynamic_strings.add().line = lines[1]
        self.dynamic_strings.add().line = ""
        self.width = 289

    def process(self):
        v1, v2, v3 = self.inputs
        V1, V2, V3 = v1.sv_get(0), v2.sv_get(0), v3.sv_get(0)
        out = []
        extend = out.extend
        append = out.append
        exec('\n'.join([j.line for j in self.dynamic_strings]))
        self.outputs[0].sv_set(out)

    def storage_set_data(self, storage):
        strings_json = storage['string_storage']
        lines_list = json.loads(strings_json)['lines']
        self.id_data.freeze(hard=True)
        self.dynamic_strings.clear()
        for line in lines_list:
            self.dynamic_strings.add().line = line

        self.id_data.unfreeze(hard=True)

    def storage_get_data(self, node_dict):
        local_storage = {'lines': []}
        for item in self.dynamic_strings:
            local_storage['lines'].append(item.line)
        node_dict['string_storage'] = json.dumps(local_storage)


def register():
    bpy.utils.register_class(SvExecNodeDynaStringItem)
    bpy.utils.register_class(SvExecNodeMod)
    bpy.utils.register_class(SvExecNodeModCallback)


def unregister():
    bpy.utils.unregister_class(SvExecNodeModCallback)
    bpy.utils.unregister_class(SvExecNodeMod)
    bpy.utils.unregister_class(SvExecNodeDynaStringItem)
