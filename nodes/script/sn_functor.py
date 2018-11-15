# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
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
    node_dict = {}

    def init_ui(self, context):
        # this function is like sv_init but dynamic
        try:
            node_dict[self.n_id]["functor_init"](self, context)
        except Exception as err:
            print('failed to initialize sockets\n', err)


    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.svfunctor_callback").fn_name='load'
        row.operator("node.svfunctor_callback").fn_name='reset'
        self.draw_buttons_script(context, layout)

    def process_script(self, context):
        try:
            node_dict[self.n_id]["process"](self, context)
        except Exception as err:
            print('failed to process custom function\n', err)

    def process(self):
        self.process_script(context)

    def load(self):
        ...

    def reset(self):
        ...

classes = [SvSNCallbackFunctor, SvSNFunctor]
register, unregister = bpy.utils.register_classes_factory(classes)