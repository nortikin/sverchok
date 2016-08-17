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

import random

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import Node, NodeTree


from sverchok.node_tree import SverchCustomTreeNode, SvNodeTreeCommon
from sverchok.data_structure import replace_socket, get_other_socket, updateNode
from sverchok.core.update_system import make_tree_from_nodes, do_update


# this should NOT be defined here but in the node file.
MONAD_COLOR = (0.196, 0.92, 1.0)


socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}

def make_valid_identifier(name):
    """Create a valid python identifier from name for use a a part of class name"""
    return "".join(ch for ch in name if ch.isalnum() or ch == "_")

def make_class_from_monad(monad):
    """
    create a new node class dynamiclly from a monad, either a monad or a str with a name
    """
    if isinstance(monad, str):
        monad = bpy.data.node_groups.get(monad)
    if not monad:
        print("no monad found")
        return None

    monad_inputs = monad.input_node
    monad_outputs = monad.output_node

    if not all((monad_outputs, monad_inputs)):
        print("Monad {} not setup correctly".format(monad.name))
        return None

    cls_dict = {}

    if not monad.cls_bl_idname:
        # the monad cls_bl_idname needs to be unique and cannot change
        cls_name = "SvGroupNode{}_{}".format(make_valid_identifier(monad.name),
                                             id(monad)^random.randint(0, 4294967296))
    else:
        cls_name = monad.cls_bl_idname

    cls_dict["bl_idname"] = cls_name
    cls_dict["bl_label"] = monad.name
    old_cls_ref = getattr(bpy.types, cls_name, None)

    in_socket = []

    def get_socket_data(socket):
        other = get_other_socket(socket)
        if socket.bl_idname == "SvDummySocket":
            socket = get_other_socket(socket)

        socket_bl_idname = socket.bl_idname
        socket_name = socket.name
        return socket_name, socket_bl_idname

    def generate_name(prop_name, cls_dict):
        if prop_name in cls_dict:
            # all properties need unique names,
            # if 'x' is taken 'x2' etc.
            for i in range(2, 100):
                new_name = "{}{}".format(prop_name, i)
                if new_name in cls_dict:
                    continue
                return new_name
        else:
            return prop_name


    # if socket is dummysocket use the other for data
    for socket in monad_inputs.outputs:
        if socket.is_linked:

            other = get_other_socket(socket)
            prop_data = other.get_prop_data()
            if "prop_name" in prop_data:
                prop_name = prop_data["prop_name"]
                prop_rna = getattr(other.node.rna_type, prop_name)
                prop_name = generate_name(prop_name, cls_dict)
                cls_dict[prop_name] = prop_rna

            if "prop_type" in prop_data:
                # I think only scriptnode uses this interface, if not true might
                # need more testing and proctection.
                # anyway replace the prop data with new prop data
                if "float" in prop_data["prop_type"]:
                    prop_rna = FloatProperty(name=other.name, update=updateNode)
                elif "int" in prop_data["prop_type"]:
                    prop_rna = IntProperty(name=other.name, update=updateNode)
                prop_name = generate_name(make_valid_identifier(other.name), cls_dict)
                cls_dict[prop_name] = prop_rna
                prop_data = {"prop_name": prop_name}

            socket_name, socket_bl_idname = get_socket_data(socket)

            data = [socket_name, socket_bl_idname, prop_data]
            in_socket.append(data)

    out_socket = []
    for socket in monad_outputs.inputs:
        if socket.is_linked:
            data = get_socket_data(socket)
            out_socket.append(data)

    cls_dict["input_template"] = in_socket
    cls_dict["output_template"] = out_socket

    bases = (SvGroupNodeExp, Node, SverchCustomTreeNode)
    cls_ref = type(cls_name, bases, cls_dict)
    monad.cls_bl_idname = cls_ref.bl_idname
    if old_cls_ref:
        bpy.utils.unregister_class(old_cls_ref)
    bpy.utils.register_class(cls_ref)

    return cls_ref


class SverchGroupTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - groups '''
    bl_idname = 'SverchGroupTreeType'
    bl_label = 'Sverchok Group Node Tree'
    bl_icon = 'NONE'

    # unique and non chaning identifier set upon first creation
    cls_bl_idname = StringProperty()

    def update(self):
        pass

    @classmethod
    def poll(cls, context):
        # keeps us from haivng an selectable icon
        return False

    @property
    def instances(self):
        res = []
        for ng in self.sv_trees:
            for node in ng.nodes:
                if node.bl_idname == self.cls_bl_idname:
                    res.append(node)
        return res

    @property
    def input_node(self):
        return self.nodes.get("Group Inputs Exp")

    @property
    def output_node(self):
        return self.nodes.get("Group Outputs Exp")

    def update_cls(self):
        res = make_class_from_monad(self)
        return res



def _get_monad_name(self):
    return self.monad.name

def _set_monad_name(self, value):
    print("set value", value)
    self.monad.name = value

class SvGroupNodeExp:
    """
    Base class for all monad instances
    """
    bl_icon = 'OUTLINER_OB_EMPTY'

    # fun experiment
    #label = StringProperty(get=_get_monad_name, set=_set_monad_name)
    def draw_label(self):
        return self.monad.name

    @property
    def monad(self):
        for tree in bpy.data.node_groups:
            if tree.bl_idname == 'SverchGroupTreeType' and self.bl_idname == tree.cls_bl_idname:
               return tree
        return None # or raise LookupError or something, anyway big FAIL

    def sv_init(self, context):
        self.use_custom_color = True
        self.color = MONAD_COLOR

        for socket_name, socket_bl_idname, prop_data in self.input_template:
            s = self.inputs.new(socket_bl_idname, socket_name)
            for name, value in prop_data.items():
                setattr(s, name, value)

        for socket_name, socket_bl_idname in self.output_template:
            self.outputs.new(socket_bl_idname, socket_name)


    def update(self):
        ''' Override inherited '''
        pass

    def draw_buttons_ext(self, context, layout):
        pass

    def draw_buttons(self, context, layout):
        c = layout.column()

        #c.prop(self, 'group_name', text='name')
        monad = self.monad
        c.prop(monad, "name", text='name')

        d = layout.column()
        d.active = bool(monad)
        f = d.operator('node.sv_group_edit', text='edit!')
        f.group_name = monad.name

    def process(self):
        if not self.monad:
            return

        monad = self.monad
        in_node = monad.input_node
        out_node = monad.output_node

        for index, socket in enumerate(self.inputs):
            data = socket.sv_get(deepcopy=False)
            in_node.outputs[index].sv_set(data)

        #  get update list
        #  could be cached
        ul = make_tree_from_nodes([out_node.name], monad, down=False)
        do_update(ul, monad.nodes)
        # set output sockets correctly
        for index, socket in enumerate(self.outputs):
            if socket.is_linked:
                data = out_node.inputs[index].sv_get(deepcopy=False)
                socket.sv_set(data)

    def load(self):
        pass


def register():
    bpy.utils.register_class(SverchGroupTree)

def unregister():
    bpy.utils.unregister_class(SverchGroupTree)
