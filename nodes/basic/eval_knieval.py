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

import re
import ast
from ast import literal_eval

import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
from bpy.props import FloatProperty, StringProperty, BoolProperty
from node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket, MatrixSocket
from data_structure import updateNode, SvGetSocketAnyType, SvSetSocketAnyType

'''
Each node starts out as a send node, but can be converted to a receiver node too.
Strings to trigger the two modes / mode change are:

- send:     `path.to.prop = {x}`
- receive:  `{x} = path.to.prop` , or `=path.to.prop`

    NodeItem("EvalKnievalNode", label="Eval Knieval"),

'''


def read_text(file_path, update=True):
    """ hold it! not implemented yet
    # if args has separators then look on local disk
    # else in .blend
    with open(fp) as new_text:
        text_body = ''.join(new_text.readlines())

    out_data = literal_eval(written_data)
    """
    pass


# def eval_text(node, function_text, out_text, update=True):
def eval_text(function_text, out_text, update=True):
    texts = bpy.data.texts

    # this text should be initiated outside of blender or made external.
    # if text on filesystem is modified between updates, reload it and
    # re-execute it.
    text = texts[function_text]
    if update:
        # might not even work without ui interact
        fp = text.filepath
        fp = bpy.path.abspath(fp)
        with open(fp) as new_text:
            text_body = ''.join(new_text.readlines())
            text.from_string(text_body)

    # at this point text is updated and can be executed.
    # could be cached in node.
    text = texts[function_text]
    exec(text.as_string())

    # if function_text execed OK, then it has written to texts[out_text]
    # This file out_text should exist.
    out_data = None
    if out_text in texts:
        written_data = texts[out_text].as_string()
        print(written_data)
        out_data = literal_eval(written_data)

    return out_data


def get_params(prop, pat):
    regex = re.compile(pat)
    return literal_eval(regex.findall(prop)[0])


def process_macro(node, macro, prop_to_eval):
    params = get_params(prop_to_eval, '\(.*?\)')
    tvar = None
    fn = None

    if macro == 'eval_text':
        if 2 <= len(params) <= 3:
            fn = eval_text
    else:
        if 1 <= len(params) <= 2:
            fn = read_text

    if not fn:
        return

    # do this once, if success skip the try on the next update
    if not node.eval_success:
        try:
            tvar = fn(*params)
        except:
            fail_msg = "nope, {type} with ({params}) failed"
            print(fail_msg.format(type=macro, params=str(params)))
            node.previous_eval_str = ""
        finally:
            node.eval_success = False if (tvar is None) else True
            print('success?', node.eval_success)
            return tvar
    else:
        print('running {macro} unevalled'.format(macro=macro))
        return fn(*params)


def process_prop_string(node, prop_to_eval):
    tvar = None

    c = bpy.context
    scene = c.scene
    data = bpy.data
    objs = data.objects
    mats = data.materials
    meshes = data.meshes
    texts = data.texts

    # yes there's a massive assumption here too.
    if not node.eval_success:
        try:
            tvar = eval(prop_to_eval)
        except:
            print("nope, crash n burn hard")
            node.previous_eval_str = ""
        finally:
            print('evalled', tvar)
            node.eval_success = False if (tvar is None) else True
    else:
        tvar = eval(prop_to_eval)

    return tvar


def wrap_output_data(tvar):
    if isinstance(tvar, Vector):
        data = [[tvar[:]]]
    elif isinstance(tvar, Matrix):
        data = [[r[:] for r in tvar[:]]]
    elif isinstance(tvar, (Euler, Quaternion)):
        tvar = tvar.to_matrix().to_4x4()
        data = [[r[:] for r in tvar[:]]]
    elif isinstance(tvar, list):
        data = [tvar]
    else:
        data = tvar

    return data


class EvalKnievalNode(bpy.types.Node, SverchCustomTreeNode):

    ''' Eval Knieval Node '''
    bl_idname = 'EvalKnievalNode'
    bl_label = 'Eval Knieval Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    x = FloatProperty(
        name='x', description='x variable', default=0.0, precision=5, update=updateNode)

    eval_str = StringProperty(update=updateNode)
    previous_eval_str = StringProperty()

    mode = StringProperty(default="input")
    previous_mode = StringProperty(default="input")

    eval_success = BoolProperty(default=False)
    eval_knieval_mode = BoolProperty(
        default=True,
        description="when unticked, try/except is done only once")

    def init(self, context):
        self.inputs.new('StringsSocket', "x").prop_name = 'x'
        self.width = 400

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'eval_str', text='')

    def draw_buttons_ext(self, context, layout):
        row = layout.row()
        row.prop(self, 'eval_knieval_mode', text='eval knieval mode')

    def input_mode(self):
        inputs = self.inputs
        if (len(inputs) == 0) or (not inputs[0].links):
            return
        print('has a link!')

        # then morph default socket type to whatever we plug into it.
        from_socket = inputs[0].links[0].from_socket
        incoming_socket_type = type(from_socket)
        stype = {
            VerticesSocket: 'VerticesSocket',
            MatrixSocket: 'MatrixSocket',
            StringsSocket: 'StringsSocket'
        }.get(incoming_socket_type, None)

        print(incoming_socket_type, from_socket, stype)

        if not stype:
            print('unidentified flying input')
            return

        # if the current self.input socket is different to incoming
        if not (stype == self.inputs[0].bl_idname):
            self.morph_input_socket_type(stype)

        # I you want to send complex data to bpy use SN.
        tvar = None
        tvar = SvGetSocketAnyType(self, inputs[0])[0][0]

        # input can still be empty or []
        if not tvar:
            return

        # convenience accessors,
        # if in render mode these must be obtain some other way
        c = bpy.context
        scene = bpy.context.scene
        data = bpy.data
        objs = data.objects
        mats = data.materials
        meshes = data.meshes
        cursor = scene.cursor_location

        fxed = self.eval_str.format(x=tvar)

        # yes there's a massive assumption here.
        if not self.eval_success:
            success = False
            try:
                exec(fxed)
                success = True
                self.previous_eval_str = self.eval_str
            except:
                print("nope, crash n burn")
                success = False
                self.previous_eval_str = ""
            finally:
                self.eval_success = success
        else:
            exec(fxed)

    def output_mode(self):
        outputs = self.outputs
        if (len(outputs) == 0) or (not outputs[0].links):
            print('has no link!')
            return

        prop_to_eval = self.eval_str.split('=')[1].strip()
        macro = prop_to_eval.split("(")[0]
        tvar = None

        if macro in ['eval_text', 'read_text']:
            tvar = process_macro(self, macro, prop_to_eval)
        else:
            tvar = process_prop_string(self, prop_to_eval)

        # explicit None must be caught. not 0 or False
        if tvar is None:
            return

        if not (self.previous_eval_str == self.eval_str):
            print("tvar: ", tvar)
            self.morph_output_socket_type(tvar)

        # finally we can set this.
        data = wrap_output_data(tvar)
        SvSetSocketAnyType(self, 0, data)
        self.previous_eval_str = self.eval_str

    def set_sockets(self):
        """
        Triggered by mode changes between [input, output] this removes the socket
        from one side and adds a socket to the other side. This way you have something
        to plug into. When you connect a node to a socket, the socket can then be
        automagically morphed to match the socket-type. (morhing is however done in the
        morph functions)
        """
        a, b = {
            'input': (self.inputs, self.outputs),
            'output': (self.outputs, self.inputs)
        }[self.mode]
        b.clear()

        a.new('StringsSocket', 'x')
        if self.mode == 'input':
            a[0].prop_name = 'x'

    def update(self):
        """
        Update behaves like the conductor, it detects the modes and sends flow control
        to functions that know how to deal with socket data consistent for those modes.

        It also avoids extra calculation by figuring out if input/output critera are
        met before anything is processed. It returns early if it can.

        """
        inputs = self.inputs
        outputs = self.outputs

        if self.mode == "input" and len(inputs) == 0:
            # self.set_ui_color()
            return
        elif self.mode == "output" and len(outputs) == 0:
            # self.set_ui_color()
            return

        if (len(self.eval_str) <= 4) or not ("=" in self.eval_str):
            # self.set_ui_color()
            return

        if not (self.eval_str == self.previous_eval_str):
            t = self.eval_str.split("=")
            right_to_left = len(t[0]) > len(t[1])
            self.mode = 'input' if right_to_left else 'output'
            self.eval_success = False

        if not (self.mode == self.previous_mode):
            self.set_sockets()
            self.previous_mode = self.mode
            self.eval_success = False

        {
            "input": self.input_mode,
            "output": self.output_mode
        }.get(self.mode, lambda: None)()

        self.set_ui_color()

    def set_ui_color(self):
        self.use_custom_color = True
        self.color = (1.0, 1.0, 1.0) if self.eval_success else (0.98, 0.6, 0.6)

    def morph_output_socket_type(self, tvar):
        """
        Set the output according to the data types
        the body of this if-statement is done only infrequently,
        when the eval string is not the same as the last eval.
        """
        outputs = self.outputs
        output_socket_type = 'StringsSocket'

        if isinstance(tvar, Vector):
            output_socket_type = 'VerticesSocket'
        elif isinstance(tvar, (list, tuple)):
            output_socket_type = 'VerticesSocket'
        elif isinstance(tvar, (Matrix, Euler, Quaternion)):
            output_socket_type = 'MatrixSocket'
        elif isinstance(tvar, (int, float)):
            output_socket_type = 'StringsSocket'

        links = outputs[0].links
        needs_reconnect = False

        if links and links[0]:
            needs_reconnect = True
            link = links[0]
            node_to = link.to_node
            socket_to = link.to_socket

        # needs clever reconnect? maybe not.
        if outputs[0].bl_idname != output_socket_type:
            outputs.clear()
            outputs.new(output_socket_type, 'x')

        if needs_reconnect:
            ng = self.id_data
            ng.links.new(outputs[0], socket_to)

    def morph_input_socket_type(self, new_type):
        """
        Recasts current input socket type to conform to incoming type
        Preserves the connection.
        """

        # where is the data coming from?
        inputs = self.inputs
        node_from = inputs[0].links[0].from_node

        # flatten and reinstate
        inputs.clear()
        inputs.new(new_type, 'x')

        # reconnect
        ng = self.id_data
        ng.links.new(inputs[0], socket_to)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(EvalKnievalNode)


def unregister():
    bpy.utils.unregister_class(EvalKnievalNode)
