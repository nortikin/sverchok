# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import sys
import inspect
import imp
import types
import itertools
from importlib import reload

import bpy
from mathutils import Matrix, Vector
from bpy.props import FloatProperty, IntProperty, StringProperty, BoolProperty, PointerProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode, node_id
from sverchok.utils.sv_operator_mixins import SvGenericCallbackWithParams
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

functions = "draw_buttons", "process", "functor_init"
sn_callback = "node.svfunctor_callback_b"

def make_name(type_, index_):
    return type_ + '_0{0}'.format(index_)


class SvSNCallbackFunctorB(bpy.types.Operator, SvGenericCallbackWithParams):
    bl_idname = sn_callback
    bl_label = "Callback for functor node"
    bl_options = {'INTERNAL'}


def make_annotations():
    annotations = {}
    for i in range(5):
        iname = make_name('int', i)
        annotations[iname] = IntProperty(name=iname, update=updateNode)
        fname = make_name('float', i)
        annotations[fname] = FloatProperty(name=fname, update=updateNode)
        bname = make_name('bool', i)
        annotations[bname] = BoolProperty(name=bname, update=updateNode)
    return annotations

class SvSNPropsFunctor:
    __annotations__ = make_annotations()

    def clear_sockets(self):
        self.inputs.clear()
        self.outputs.clear()

class SvSNFunctorB(bpy.types.Node, SverchCustomTreeNode, SvSNPropsFunctor, SvAnimatableNode):
    """
    Triggers:  functorB
    Tooltip:  use a simpler nodescript style
    
    A short description for reader of node code
    """

    bl_idname = 'SvSNFunctorB'
    bl_label = 'SN Functor B'
    bl_icon = 'SYSTEM'

    def wrapped_update(self, context):
        if self.script_pointer:
            self.info(f'set self.script_name to:|{self.script_pointer.name}|')

    # depreciated
    script_name: StringProperty(update=wrapped_update)

    script_pointer: PointerProperty(
        name="Script", poll=lambda self, object: True,
        type=bpy.types.Text, update=updateNode)

    script_str: StringProperty()
    loaded: BoolProperty()
    node_dict = {}

    def handle_execution_nid(self, func_name, msg, args):
        ND = self.node_dict.get(hash(self))
        if not ND:
            print(self.name,': node dict not found for', hash(self))
            if func_name == 'functor_init':
                print('this is probably a .blend load event..')
            print('ending early')
            return

        if func_name == 'process':
            locals().update(ND.get("all_members"))
        elif func_name == 'functor_init':
            print('will attempt to functor init!')
 
        try:

            if not ND.get(func_name) and func_name == 'draw_buttons':
                return

            if args:
                ND[func_name](self, *args)
            else:
                ND[func_name](self)

        except Exception as err:
            print(msg, ": error in funcname :", func_name)
            sys.stderr.write('ERROR: %s\n' % str(err))
            exec_info = sys.exc_info()[-1]
            print('on line # {}'.format(exec_info.tb_lineno))
            print('code:', exec_info.tb_frame.f_code)

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        if not self.loaded:
            row = layout.row()
            row.prop_search(self, 'script_pointer', bpy.data, 'texts', text='')
            row.operator(sn_callback, text='', icon='PLUGIN').fn_name = 'load'
        
        row = layout.row()
        row.operator(sn_callback, text='Load').fn_name='load'
        row.operator(sn_callback, text='Reset').fn_name='reset'

        if self.loaded:
            self.draw_buttons_script(context, layout)

    ###  delegation funcions

    def draw_buttons_script(self, context, layout):
        """ This will call the hoisted function:  draw_buttons(self, context, layout) """
        msg = 'failed to load custom draw_buttons function'
        self.handle_execution_nid("draw_buttons", msg, args=(context, layout))

    def process_script(self):
        """ This will call the hoisted function:  process(self, context) """
        msg = 'failed to process custom function'
        self.handle_execution_nid("process", msg, args=None)

    def init_socket(self, context):
        """ This will call the hoisted function:  functor_init(self, context) """
        msg = 'failed to initialize sockets'
        self.handle_execution_nid("functor_init", msg, args=(context,))

    ###  processors :)

    def process(self):

        # one of these must be set, script_name is legacy
        if not any([self.script_pointer, self.script_name])
            return
        if not self.script_str:
            return

        if self.loaded and not self.node_dict.get(hash(self)):
            self.node_dict[hash(self)] = self.get_functions()
            self.loaded = True
        self.process_script()

    def get_functions(self):

        try:
            if self.script_pointer:
                self.script_str = self.script_pointer.as_string
                text_datablock = self.self.script_pointer
            else:
                # recover from old .blend file in new Blender
                text_datablock = self.get_bpy_data_from_name(self.script_name, bpy.data.texts)
                if text_datablock:
                    self.script_str = text_datablock.as_string()
                    self.sv_setattr_with_throttle("script_pointer", text_datablock)
                else:
                    raise
            
            module = types.ModuleType(text_datablock.name)
            exec(self.script_str, module.__dict__)

        except Exception as err:
            self.error('wtf man', err)

        dict_functions = {named: getattr(module, named) for named in functions if hasattr(module, named)}
        dict_functions['all_members'] = module.__dict__
        return dict_functions

    # todo below this mark

    def load(self, context):

        print('time to load', self.script_name)
        self.clear_sockets()
        self.script_str = bpy.data.texts[self.script_name.strip()].as_string()
        self.node_dict[hash(self)] = self.get_functions()
        self.init_socket(context)
        self.loaded = True

    def reset(self, context):
        print('reset')
        self.loaded = False
        self.script_name = ""
        self.script_str = ""
        self.node_dict[hash(self)] = {}
        self.clear_sockets()

    def sv_copy(self, node):
        self.node_dict[hash(self)] = {}
        self.load(bpy.context)

    def draw_label(self):
        if self.script_name:
            return 'SNF: ' + self.script_name
        else:
            return self.bl_label

    def handle_reload(self, context):
        """
        Handles the reload event.
          - gather existing connections
          - perform reload / refresh
          - try to set the connections
        """
        print('handling reload')
        node = self
        nodes = self.id_data.nodes

        # if any current connections... gather them 
        reconnections = []
        mappings = itertools.chain.from_iterable([node.inputs, node.outputs])
        for i in (i for i in mappings if i.is_linked):
            for L in i.links:
                link = lambda: None
                link.from_node = L.from_socket.node.name
                link.from_socket = L.from_socket.index
                link.to_node = L.to_socket.node.name
                link.to_socket = L.to_socket.index
                reconnections.append(link)

        self.load(context)

        # restore connections where applicable (by socket name)
        node_tree = self.id_data
        for link in reconnections:
            try:
                from_part = nodes[link.from_node].outputs[link.from_socket]
                to_part = nodes[link.to_node].inputs[link.to_socket]
                node_tree.links.new(from_part, to_part)
            except Exception as err:
                str_from = f'nodes[{link.from_node}].outputs[{link.from_socket}]'
                str_to = f'nodes[{link.to_node}].inputs[{link.to_socket}]'
                print(f'failed: {str_from} -> {str_to}')
                print(err)



classes = [SvSNCallbackFunctorB, SvSNFunctorB]
register, unregister = bpy.utils.register_classes_factory(classes)
