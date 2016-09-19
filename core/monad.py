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
from bpy.props import (StringProperty, FloatProperty,
                       IntProperty, BoolProperty,
                       CollectionProperty)

from bpy.types import Node, NodeTree


from sverchok.node_tree import SverchCustomTreeNode, SvNodeTreeCommon
from sverchok.data_structure import replace_socket, get_other_socket, updateNode, match_long_repeat
from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.core.monad_properties import SvIntPropertySettingsGroup, SvFloatPropertySettingsGroup

MONAD_COLOR = (0.830819, 0.911391, 0.754562)


socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}

def make_valid_identifier(name):
    """Create a valid python identifier from name for use a a part of class name"""
    while name and not name[0].isalpha():
        name = name[1:]
    if not name:
        return "generic"
    return "".join(ch for ch in name if ch.isalnum() or ch == "_")


def get_socket_data(socket):
    other = get_other_socket(socket)
    if socket.bl_idname == "SvDummySocket":
        socket = get_other_socket(socket)

    socket_bl_idname = socket.bl_idname
    socket_name = socket.name
    return socket_name, socket_bl_idname, socket.prop_name

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

    float_props = CollectionProperty(type=SvFloatPropertySettingsGroup)
    int_props = CollectionProperty(type=SvIntPropertySettingsGroup)

    def add_prop_from(self, socket):
        other = socket.other
        cls = getattr(bpy.types, self.cls_bl_idname, None)
        cls_dict = cls.__dict__ if cls else {}

        if other.prop_name:
            prop_name = other.prop_name
            prop_func, prop_dict = getattr(other.node.rna_type, prop_name, ("", {}))
            if prop_func.__name__ == "FloatProperty":
                prop_settings = self.float_props.add()
            elif prop_func.__name__ == "IntProperty":
                prop_settings = self.int_props.add()
            elif prop_func.__name__ == "FloatVectorProperty":
                pass # etc
            else:
                pass

            prop_settings.prop_name = generate_name(prop_name, cls_dict)
            prop_settings.set_settings(prop_dict)
            socket.prop_name = prop_settings.prop_name
            return prop_settings.prop_name
        elif hasattr(other, "prop_type"):
            if "float" in other.prop_type:
                prop_settings = self.float_props.add()
            elif "int" in other.prop_type:
                prop_settings = self.int_props.add()

            prop_settings.prop_name = generate_name(make_valid_identifier(other.name), cls_dict)
            prop_settings.set_settings({"name": other.name})
            socket.prop_name = prop_settings.prop_name
            return prop_settings.prop_name

        return ""

    def get_all_props(self):
        """
        return a dict with all data needed to setup monad
        """
        monad_data  = {"name": self.name, "cls_bl_idname": self.cls_bl_idname}
        float_props = {}
        for prop in self.float_props:
            float_props[prop.prop_name] = prop.get_settings()
        monad_data["float_props"] = float_props

        monad_data["int_props"] = {prop.prop_name: prop.get_settings() for prop in self.int_props}

        return monad_data

    def set_all_props(self, data):

        self.cls_bl_idname = data["cls_bl_idname"]

        for prop_name, values in data["float_props"].items():
            settings = self.float_props.add()
            settings.set_settings(values)
            settings.prop_name = prop_name

        for prop_name, values in data["int_props"].items():
            settings = self.int_props.add()
            settings.set_settings(values)
            settings.prop_name = prop_name



    def remove_prop(self, socket):
        prop_name = socket.prop_name
        for prop_list in ("float_props", "int_props"):
            p_list = getattr(self, prop_list)
            for idx, setting in enumerate(p_list):
                if setting.prop_name == prop_name:
                    p_list.remove(idx)
                    return

    def find_prop(self, socket):
        prop_name = socket.prop_name
        for prop_list in ("float_props", "int_props"):
            p_list = getattr(self, prop_list)
            for setting in p_list:
                if setting.prop_name == prop_name:
                    return setting
        return None

    def verify_props(self):
        '''
        parse sockets and add any props as
        for backwarads compablility
        '''
        prop_names = {s.prop_name for s in chain(self.float_props, self.int_props)}
        for socket in self.input_node.outputs:
            if socket.is_linked:
                if socket.prop_name:
                    if socket.prop_name in prop_names:
                        continue
                    else:
                        self.add_prop_from(socket)
                        continue

                if socket.other.prop_name:
                    if socket.other.prop_name not in prop_names:
                        self.add_prop_from(socket)
                    else:
                        socket.prop_name = socket.other.prop_name



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

        self.verify_props()

        cls_dict["bl_idname"] = cls_name
        cls_dict["bl_label"] = self.name

        cls_dict["input_template"] = self.generate_inputs()
        cls_dict["output_template"] = self.generate_outputs()

        self.make_props(cls_dict)

        # done with setup

        old_cls_ref = getattr(bpy.types, cls_name, None)

        bases = (SvGroupNodeExp, Node, SverchCustomTreeNode)

        cls_ref = type(cls_name, bases, cls_dict)

        if old_cls_ref:
            bpy.utils.unregister_class(old_cls_ref)
        bpy.utils.register_class(cls_ref)

        return cls_ref

    def make_props(self, cls_dict):
        for s in self.float_props:
            prop_dict = s.get_settings()
            prop_dict["update"] = updateNode
            cls_dict[s.prop_name] = FloatProperty(**prop_dict)

        for s in self.int_props:
            prop_dict = s.get_settings()
            prop_dict["update"] = updateNode
            cls_dict[s.prop_name] = IntProperty(**prop_dict)


    def generate_inputs(self):
        in_socket = []

        # if socket is dummysocket use the other for data
        for idx, socket in enumerate(self.input_node.outputs):
            if socket.is_linked:
                socket_name, socket_bl_idname, prop_name = get_socket_data(socket)
                if prop_name:
                    prop_data = {"prop_name": prop_name}
                else:
                    prop_data = {}
                data = [socket_name, socket_bl_idname, prop_data]
                in_socket.append(data)

        return in_socket

    def generate_outputs(self):
        out_socket = []
        for socket in self.output_node.inputs:
            if socket.is_linked:
                socket_name, socket_bl_idname, _ = get_socket_data(socket)
                out_socket.append((socket_name, socket_bl_idname))
        return out_socket



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
