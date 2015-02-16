# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

'''
The intention of this node is to provide optimal js execution speed by
precompiling the .js file, and functions. Hopefully it will serve to
show what can be done in this arena.

- you will be able to declare inputs and outputs
- sliders if it makes sense

'''

import importlib

# necessary for import checking
if importlib.find_loader('execjs'):
    import execjs
    print('execjs will be available')
else:
    print('execjs will not be available, prototype node will not function.')
    print('obtain execjs from: https://github.com/doloopwhile/PyExecJS')

import ast
import os
import traceback

import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatVectorProperty,
    IntVectorProperty
)

from sverchok.utils.sv_panels_tools import sv_get_local_path
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (dataCorrect, updateNode)


FAIL_COLOR = (0.8, 0.1, 0.1)
READY_COLOR = (0, 0.8, 0.95)


class SvPrototypeCB(bpy.types.Operator):

    bl_idname = "node.sv_prototypejs_callback"
    bl_label = "PrototypeJS callback"

    fn_name = bpy.props.StringProperty(default='')

    def dispatch(self, context, type_op):
        n = context.node

        if type_op == 'LOAD':
            n.import_script()

        if type_op == 'RELOAD':  # temp testing
            n.import_script()

        if type_op == 'CLEAR':  # temp testing
            n.deport_script()

    def execute(self, context):
        self.dispatch(context, self.fn_name)
        return {'FINISHED'}


class SvPrototypeJS(bpy.types.Node, SverchCustomTreeNode):

    ''' Script node JS'''
    bl_idname = 'SvPrototypeJS'
    bl_label = 'JS Generator'

    node_dict = {}
    script_name = StringProperty()
    STATE = StringProperty(default='UNLOADED')

    mode_options = [
        ("Internal", "Internal", "", 0),
        ("External", "External", "", 1),
    ]

    origin = EnumProperty(
        items=mode_options,
        description="pick where to load the js from",
        default="Internal",
        update=updateNode
    )

    def set_node_function(self, node_function):
        self.node_dict[hash(self)]['node_function'] = node_function

    def get_node_function(self):
        return self.node_dict[hash(self)].get('node_function')

    def init(self, context):
        self.node_dict[hash(self)] = {}

    def draw_buttons(self, context, layout):
        D = bpy.data
        sv_callback = "node.sv_prototypejs_callback"

        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "origin", expand=True)

        if self.STATE == 'UNLOADED':
            if self.origin == 'Internal':
                row2 = col.row()
                row2.prop_search(self, 'script_name', D, 'texts', text='', icon='TEXT')
                if self.script_name:
                    row2.operator(sv_callback, text='', icon='PLUGIN').fn_name = 'LOAD'
            else:
                # show file loading, this will import to bpy.data.texts
                pass
        else:

            row = layout.row()
            for action in ['RELOAD', 'CLEAR']:
                row.operator(sv_callback, text=action).fn_name = action

    def import_script(self):
        try:
            local_file = bpy.data.texts[self.script_name].as_string()
            ctx = execjs.compile(local_file)
            self.set_node_function(ctx.call)
            self.STATE = 'LOADED'
        except:
            self.STATE = 'UNLOADED'
        print(self.STATE)

    def deport_script(self):
        self.set_node_function({})
        self.STATE = 'UNLOADED'
        print('unloaded: '.format(self.script_name))

    def process(self):
        this_func = self.get_node_function()

        args = (10, 20, 30)
        v, e = this_func("sv_proto_main", *args)
        print(v, e)

        fg = this_func('inputs', '')
        print(fg)


classes = [SvPrototypeCB, SvPrototypeJS]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
