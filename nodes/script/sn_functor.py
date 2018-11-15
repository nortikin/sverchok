# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import sys
import bpy
# import mathutils
from mathutils import Matrix, Vector
from bpy.props import FloatProperty, IntProperty, StringProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, node_id
from sverchok.utils.sv_operator_mixins import SvGenericCallbackWithParams


def make_name(type_, index_):
    return type_ + '_0{0}'.format(index_)

class SvSNCallbackFunctor(bpy.types.Operator, SvGenericCallbackWithParams):
    bl_idname = "node.svfunctor_callback"
    bl_label = "Callback for functor node"

class SvSNPropsFunctor:

    __annotations__ = {}
    __annotations__['n_id'] = StringProperty()

    for i in range(5):
        iname = make_name('int', i)
        __annotations__[iname] = IntProperty(name=iname, update=updateNode)
        fname = make_name('float', i)
        __annotations__[fname] = FloatProperty(name=fname, update=updateNode)

    def clear_sockets(self):
        self.inputs.clear()
        self.outputs.clear()

class SvSNFunctor(bpy.types.Node, SverchCustomTreeNode, SvSNPropsFunctor):
    """
    Triggers:  functor
    Tooltip:  use a simpler nodescript style
    
    A short description for reader of node code
    """

    bl_idname = 'SvSNFunctor'
    bl_label = 'SN Functor'
    bl_icon = 'SYSTEM'

    script_name: StringProperty()
    script_str: StringProperty()
    loaded: BoolProperty()
    node_dict = {}

    def handle_execution_nid(self, func_name, msg, *args):
        try:
            self.node_dict[self.n_id][func_name](*args)
        except Exception as err:
            print("error in funcname:", func_name)
            print(msg + '\n', err)
            sys.stderr.write('ERROR: %s\n' % str(err))
            print(sys.exc_info()[-1].tb_frame.f_code)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

    def init_socket(self, context):
        msg = 'failed to initialize sockets'
        self.handle_execution_nid("functor_init", msg, (self, context))

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.svfunctor_callback", text='Load').fn_name='load'
        row.operator("node.svfunctor_callback", text='Reset').fn_name='reset'
        self.draw_buttons_script(context, layout)

    def draw_buttons_script(self, context, layout):
        msg = 'failed to load custom draw_buttons function'
        self.handle_execution_nid("draw_buttons", msg, (self, context, layout))

    def process(self):
        self.process_script(context)

    def process_script(self, context):
        msg = 'failed to process custom function'
        self.handle_execution_nid("process", msg, (self, context))

    def load(self, context):
        print('time to load')
        self.init_socket(context)
        self.loaded = True

    def reset(self, context):
        print('reset')
        ...

classes = [SvSNCallbackFunctor, SvSNFunctor]
register, unregister = bpy.utils.register_classes_factory(classes)