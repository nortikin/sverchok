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
from itertools import chain

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import Node, NodeTree


from sverchok.node_tree import SverchCustomTreeNode, SvNodeTreeCommon
from sverchok.data_structure import replace_socket, get_other_socket, updateNode, match_long_repeat
from sverchok.core.update_system import make_tree_from_nodes, do_update


MONAD_COLOR = (0.830819, 0.911391, 0.754562)


socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}

def make_valid_identifier(name):
    """Create a valid python identifier from name for use a a part of class name"""
    return "".join(ch for ch in name if ch.isalnum() or ch == "_")


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
            if not new_name in cls_dict:
                return new_name
    else:
        return prop_name




class SverchGroupTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - groups '''
    bl_idname = 'SverchGroupTreeType'
    bl_label = 'Sverchok Group Node Tree'
    bl_icon = 'NONE'

    # unique and non chaning identifier set upon first creation
    cls_bl_idname = StringProperty()

    def update(self):
        affected_trees = {instance.id_data for instance in self.instances}
        for tree in affected_trees:
            tree.update()

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
                if hasattr(node, "cls_bl_idname") and node.cls_bl_idname == self.cls_bl_idname:
                    res.append(node)
        return res

    @property
    def input_node(self):
        return self.nodes.get("Group Inputs Exp")

    @property
    def output_node(self):
        return self.nodes.get("Group Outputs Exp")

    def update_cls(self):
        """
        create or update the corresponding class reference
        """

        if not all((self.input_node, self.output_node)):
            print("Monad {} not setup correctly".format(self.name))
            return None

        cls_dict = {}

        if not self.cls_bl_idname:
            # the monad cls_bl_idname needs to be unique and cannot change
            cls_name = "SvGroupNode{}_{}".format(make_valid_identifier(self.name),
                                                 id(self) ^ random.randint(0, 4294967296))
            # set the unique name for the class, depending on context this might fail
            # then we cannot do the setup of the class properly so abandon
            try:
                self.cls_bl_idname = cls_name
            except Exception:
                return None
        else:
            cls_name = self.cls_bl_idname

        cls_dict["bl_idname"] = cls_name
        cls_dict["bl_label"] = self.name

        cls_dict["input_template"] = self.generate_inputs(cls_dict)
        cls_dict["output_template"] = self.generate_outputs()

        # done with setup

        old_cls_ref = getattr(bpy.types, cls_name, None)

        bases = (SvGroupNodeExp, Node, SverchCustomTreeNode)

        cls_ref = type(cls_name, bases, cls_dict)

        if old_cls_ref:
            bpy.utils.unregister_class(old_cls_ref)
        bpy.utils.register_class(cls_ref)

        return cls_ref

    def generate_inputs(self, cls_dict={}):
        in_socket = []
        # if socket is dummysocket use the other for data
        for socket in self.input_node.outputs:
            if socket.is_linked:

                other = get_other_socket(socket)
                prop_data = other.get_prop_data()
                if "prop_name" in prop_data:
                    prop_name = prop_data["prop_name"]
                    prop_func, prop_dict = getattr(other.node.rna_type, prop_name)
                    prop_dict = prop_dict.copy()
                    prop_name = generate_name(prop_name, cls_dict)
                    if "attr" in prop_dict:
                        del prop_dict["attr"]
                    # some nodes (int and float) have custom functions in place,
                    # replace with standard functiong
                    prop_dict["update"] = updateNode
                    cls_dict[prop_name] = prop_func(**prop_dict)
                    prop_data = {"prop_name": prop_name}

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

        return in_socket

    def generate_outputs(self):
        out_socket = []
        for socket in self.output_node.inputs:
            if socket.is_linked:
                data = get_socket_data(socket)
                out_socket.append(data)
        return out_socket

def _get_monad_name(self):
    return self.monad.name

def _set_monad_name(self, value):
    print("set value", value)
    self.monad.name = value

def split_list(data, size=1):
    size = max(1, int(size))
    return (data[i:i+size] for i in range(0, len(data), size))

def unwrap(data):
    return list(chain.from_iterable(data))

class SvGroupNodeExp:
    """
    Base class for all monad instances
    """
    bl_icon = 'OUTLINER_OB_EMPTY'

    vectorize = BoolProperty(name="Vectorize",
                             description="Vectorize using monad",
                             default=False,
                             update=updateNode)
    split = BoolProperty(name="Split",
                         description="Split inputs into lenght 1",
                         default=False,
                         update=updateNode)

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
        self.draw_buttons(context, layout)

    def draw_buttons(self, context, layout):
        c = layout.column()
        c.prop(self, "vectorize", expand=True)
        row = c.row()
        row.prop(self, "split", expand=True)# = self.vectorize
        row.active = self.vectorize

        monad = self.monad
        if monad:
            c.prop(monad, "name", text='name')

            d = layout.column()
            d.active = bool(monad)
            f = d.operator('node.sv_group_edit', text='edit!')
            f.group_name = monad.name

    def process(self):
        if not self.monad:
            return
        if self.vectorize:
            self.process_vectorize()
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

    def process_vectorize(self):
        monad = self.monad
        in_node = monad.input_node
        out_node = monad.output_node
        ul = make_tree_from_nodes([out_node.name], monad, down=False)

        data_out = [[] for s in self.outputs]

        data_in = match_long_repeat([s.sv_get(deepcopy=False) for s in self.inputs])
        if self.split:
            for idx, data in enumerate(data_in):
                new_data = unwrap(split_list(d) for d in data)
                data_in[idx] = new_data
            data_in = match_long_repeat(data_in)

        monad["current_total"] = len(data_in[0])


        for master_idx, data in enumerate(zip(*data_in)):
            for idx, d in enumerate(data):
                socket = in_node.outputs[idx]
                if socket.is_linked:
                    socket.sv_set([d])
            monad["current_index"] = master_idx
            do_update(ul, monad.nodes)
            for idx, s in enumerate(out_node.inputs[:-1]):
                data_out[idx].extend(s.sv_get(deepcopy=False))

        for idx, socket in enumerate(self.outputs):
            if socket.is_linked:
                socket.sv_set(data_out[idx])


    def load(self):
        pass


def register():
    bpy.utils.register_class(SverchGroupTree)

def unregister():
    bpy.utils.unregister_class(SverchGroupTree)
