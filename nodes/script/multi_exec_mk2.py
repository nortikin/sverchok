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

import sys
import json
import bpy
import mathutils
import bmesh as bm
import numpy as np
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

callback_id = 'node.callback_execnodemod'

lines = """\
for i, i2 in zip(V1, V2):
    append([x + y for x, y in zip(i, i2)])
""".strip().split('\n')

default_imports = "# from math import pi, sin;# import numpy as np"

def update_wrapper(self, context):
    try:
        updateNode(context.node, context)
    except:
        ...


class SvExecNodeDynaStringItemMK2(bpy.types.PropertyGroup):
    line = bpy.props.StringProperty(name="line to eval", default="", update=update_wrapper)


class SvExecNodeModMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Exec Node Mod'''
    bl_idname = 'SvExecNodeModMK2'
    bl_label = 'Exec Node Mod+'
    bl_icon = 'CONSOLE'

    node_dict = {}

    def update_import_locals(self, context):
        try:
            exec(self.imports)
            if not hash(self) in self.node_dict:
                self.node_dict[hash(self)] = {}
                self.node_dict[hash(self)]['imports'] = locals()
        
        except Exception as err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            print(sys.exc_info()[-1].tb_frame.f_code)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            print('')
            self.node_dict[hash(self)] = {}
            self.node_dict[hash(self)]['imports'] = {}

    def get_imports(self):
        if not self.imports:
            return {}

        node_key = self.node_dict.get(hash(self))
        if node_key:
            return node_key.get('imports', {})
        return {}
        
    imports = StringProperty(
        default=default_imports,
        name='defined imports', description='string to store imports', update=update_import_locals)


    text = StringProperty(default='', update=updateNode)
    dynamic_strings = bpy.props.CollectionProperty(type=SvExecNodeDynaStringItemMK2)

    def draw_imports(self, context, col):
        if self.imports:
            import_lines = self.imports.split(';')
            for line in import_lines:
                col.row().label(line)

    def print_locals(self):
        t = self.get_imports()
        if t:
            for k, v in t.items():
                print('...', k)

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        # add() remove() clear() move()
        row.operator(callback_id, text='', icon='ZOOMIN').cmd = 'add_new_line'
        row.operator(callback_id, text='', icon='ZOOMOUT').cmd = 'remove_last_line'
        row.operator(callback_id, text='', icon='TRIA_UP').cmd = 'shift_up'
        row.operator(callback_id, text='', icon='TRIA_DOWN').cmd = 'shift_down'
        row.operator(callback_id, text='', icon='SNAP_ON').cmd = 'delete_blank'
        row.operator(callback_id, text='', icon='SNAP_OFF').cmd = 'insert_blank'

        if len(self.dynamic_strings) == 0:
            return

        col = layout.column()
        self.draw_imports(context, col)

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
        col = layout.column(align=True)
        col.operator(callback_id, text='copy to node').cmd = 'copy_from_text'
        col.prop_search(self, 'text', bpy.data, "texts", text="")

        row = layout.row()
        col.operator(callback_id, text='cc code to clipboard').cmd = 'copy_node_text_to_clipboard'

        box = layout.box()
        box.label('define imports')
        row = box.row()
        row.prop(self, 'imports', text='')
        box.separator()
        col = box.column()
        self.draw_imports(context, col)
        col = box.column()
        

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
        slines = bpy.data.texts[self.text].lines
        while len(self.dynamic_strings) < len(slines):
            self.dynamic_strings.add()

        for i, i2 in zip(self.dynamic_strings, slines):
            i.line = i2.body

    def copy_node_text_to_clipboard(self, context):
        lines = [d.line for d in self.dynamic_strings]
        if not lines:
            return
        str_lines = "\n".join(lines)
        bpy.context.window_manager.clipboard = str_lines

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

        self.print_locals()

        locals().update(self.get_imports())
        exec('\n'.join([j.line for j in self.dynamic_strings]), locals())

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
    bpy.utils.register_class(SvExecNodeDynaStringItemMK2)
    bpy.utils.register_class(SvExecNodeModMK2)


def unregister():
    bpy.utils.unregister_class(SvExecNodeModMK2)
    bpy.utils.unregister_class(SvExecNodeDynaStringItemMK2)
