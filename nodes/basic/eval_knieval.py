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
        # the scheme is: first make a generic socket and then morph it to
        # whatever we plug into it.
        tvar = None
        socket = type(inputs[0].links[0].from_socket)
        stypes = {
            StringsSocket: 's',
            VerticesSocket: 'v',
            MatrixSocket: 'm'
        }

        stype = stypes.get(socket, None)
        if stype:
            tvar = SvGetSocketAnyType(self, inputs[0])[0][0]
        else:
            return

        # input can still be empty
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
        print('you are here')
        outputs = self.outputs
        if (len(outputs) == 0) or (not outputs[0].links):
            print('has no link!')
            return

        c = bpy.context
        scene = c.scene
        data = bpy.data
        objs = data.objects
        mats = data.materials
        meshes = data.meshes

        prop_to_eval = self.eval_str.split('=')[1].strip()
        tvar = None

        # yes there's a massive assumption here too.
        if not self.eval_success:
            try:
                tvar = eval(prop_to_eval)
            except:
                print("nope, crash n burn hard")
                self.previous_eval_str = ""
            finally:
                print('evalled', tvar)
                self.eval_success = True if tvar else False
        else:
            tvar = eval(prop_to_eval)

        if not tvar:
            return
        print("Tvar", tvar)
        # set the outputs again.
        if not (self.previous_eval_str == self.eval_str):
            output_socket_type = 'StringsSocket'
            if isinstance(tvar, Vector):
                output_socket_type = 'VerticesSocket'
            elif isinstance(tvar, tuple):
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

        if isinstance(tvar, Vector):
            data = [[tvar[:]]]
        elif isinstance(tvar, Matrix):
            data = [[r[:] for r in tvar[:]]]
        elif isinstance(tvar, (Euler, Quaternion)):
            tvar = tvar.to_matrix().to_4x4()
            data = [[r[:] for r in tvar[:]]]
        # finally we can set this.
        SvSetSocketAnyType(self, 0, data)
        self.previous_eval_str = self.eval_str

    def set_sockets(self):
        # what kind of obfuscated magic is this?
        a, b = {
            'input': (self.inputs, self.outputs),
            'output': (self.outputs, self.inputs)
        }[self.mode]
        b.clear()
        
        # can do exact socket here, info is known at this point
        a.new('StringsSocket', 'x')
        if self.mode == 'input':
            a[0].prop_name = 'x'

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        if self.mode == "input" and len(inputs) == 0:
            #self.set_ui_color()
            return
        elif self.mode == "output" and len(outputs) == 0:
            #self.set_ui_color()
            return

        if (len(self.eval_str) <= 5) or not ("=" in self.eval_str):
            #self.set_ui_color()
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
            "input": self.input_mode, "output": self.output_mode
        }.get(self.mode, lambda: None)()

        self.set_ui_color()

    def set_ui_color(self):
        self.use_custom_color = True
        if not self.eval_success:
            self.color = (0.98, 0.6, 0.6)
        else:
            self.color = (1.0, 1.0, 1.0)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(EvalKnievalNode)


def unregister():
    bpy.utils.unregister_class(EvalKnievalNode)
