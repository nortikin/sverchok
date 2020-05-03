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
from bpy.props import StringProperty, PointerProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode

callback_id = 'node.callback_execnodemod'

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
    line: bpy.props.StringProperty(name="line to eval", default="", update=update_wrapper)


class SvExecNodeModCallback(bpy.types.Operator):

    bl_idname = callback_id
    bl_label = "generic callback"
    bl_options = {'INTERNAL'}

    cmd: bpy.props.StringProperty(default='')
    idx: bpy.props.IntProperty(default=-1)
    form: bpy.props.StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        return properties.cmd

    def execute(self, context):
        try:
            getattr(context.node, self.cmd)(self)
        except:
            # else we have to pass nodetree/nodename 
            if context.active_node:
                getattr(context.active_node, self.cmd)(self)
        return {'FINISHED'}


class SvExecNodeMod(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''Execute small script'''
    bl_idname = 'SvExecNodeMod'
    bl_label = 'Exec Node Mod'
    bl_icon = 'CONSOLE'

    # depreciated
    text: StringProperty(default='', update=updateNode)

    text_pointer: PointerProperty(
        name="Text", poll=lambda self, object: True,
        type=bpy.types.Text, update=updateNode)

    dynamic_strings: bpy.props.CollectionProperty(type=SvExecNodeDynaStringItem)

    properties_to_skip_iojson = ['text_pointer']

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        row = layout.row(align=True)
        # add() remove() clear() move()
        row.operator(callback_id, text='', icon='ZOOM_IN').cmd = 'add_new_line'
        row.operator(callback_id, text='', icon='ZOOM_OUT').cmd = 'remove_last_line'
        row.operator(callback_id, text='', icon='TRIA_UP').cmd = 'shift_up'
        row.operator(callback_id, text='', icon='TRIA_DOWN').cmd = 'shift_down'
        row.operator(callback_id, text='', icon='SNAP_ON').cmd = 'delete_blank'
        row.operator(callback_id, text='', icon='SNAP_OFF').cmd = 'insert_blank'

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
                row = col.row(align=True)
                row.prop(self.dynamic_strings[idx], "line", text="")

                # if UI , then 

                opp = row.operator(callback_id, text='', icon='TRIA_DOWN_BAR')
                opp.cmd = 'insert_line'
                opp.form = 'below'
                opp.idx = idx
                opp2 = row.operator(callback_id, text='', icon='TRIA_UP_BAR')
                opp2.cmd = 'insert_line'
                opp2.form = 'above'
                opp2.idx = idx


    def draw_buttons_ext(self, context, layout):
        self.draw_animatable_buttons(layout)
        col = layout.column(align=True)
        col.operator(callback_id, text='copy to node').cmd = 'copy_from_text'
        col.prop_search(self, 'text_pointer', bpy.data, "texts", text="")

        col.label(text='Code')
        col.operator(callback_id, text='cc to clipboard').cmd = 'copy_node_text_to_clipboard'
        col.operator(callback_id, text='cc from clipboard').cmd = 'copy_node_text_from_clipboard'


    def rclick_menu(self, context, layout):
        layout.label(text='Code CC')
        layout.operator(callback_id, text='to clipboard', icon='COPYDOWN').cmd = 'copy_node_text_to_clipboard'
        layout.operator(callback_id, text='from clipboard', icon='PASTEDOWN').cmd = 'copy_node_text_from_clipboard'

        # self.node_replacement_menu(context, layout)


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
    
    def delete_blank(self, context):
        sds = self.dynamic_strings
        Lines = [i.line for i in sds if i.line != ""]
        sds.clear()
        for i in Lines:
            sds.add().line = i

    def insert_blank(self, context):
        sds = self.dynamic_strings
        Lines = [i.line for i in sds]
        sds.clear()
        for i in Lines:
            sds.add().line = i
            if i != "":
                sds.add().line = ""

    def copy_from_text(self, context):
        """ make sure self.dynamic_strings has enough strings to do this """
        
        try:
            text = self.text_pointer
            if not text:
                self.info("no text selected")
                raise
            slines = text.lines
            
            self.dynamic_strings.clear()
            for line in slines:
                self.dynamic_strings.add().line = line.body
        except Exception as err:
            self.info(f"copy_from_text: encountered error {err}")

    def copy_node_text_to_clipboard(self, context):
        lines = [d.line for d in self.dynamic_strings]
        if not lines:
            return
        str_lines = "\n".join(lines)
        bpy.context.window_manager.clipboard = str_lines

    def copy_node_text_from_clipboard(self, context):
        lines = bpy.context.window_manager.clipboard
        lines = lines.splitlines()

        self.dynamic_strings.clear()
        for line in lines:
            self.dynamic_strings.add().line = line

    def insert_line(self, op_props):

        sds = self.dynamic_strings
        Lines = [i.line for i in sds]
        sds.clear()
        for tidx, i in enumerate(Lines):
            if op_props.form == 'below':
                sds.add().line = i
                if op_props.idx == tidx:
                    sds.add().line = ""
            else:
                if op_props.idx == tidx:
                    sds.add().line = ""                
                sds.add().line = i


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'V1')
        self.inputs.new('SvStringsSocket', 'V2')
        self.inputs.new('SvStringsSocket', 'V3')
        self.outputs.new('SvStringsSocket', 'out')

        # add default strings
        with self.sv_throttle_tree_update():
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

        # locals() is needed for generic module imports.
        exec('\n'.join([j.line for j in self.dynamic_strings]), globals(), locals())

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
