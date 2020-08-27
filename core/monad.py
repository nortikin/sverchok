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

import pprint
import random
from itertools import chain

import bpy
from bpy.types import Node, NodeTree
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, CollectionProperty

import sverchok
from sverchok.utils import get_node_class_reference, sv_IO_monad_helpers
from sverchok.utils.sv_IO_panel_tools import create_dict_of_tree, import_tree
from sverchok.utils.logging import info, error
from sverchok.node_tree import SverchCustomTreeNode, SvNodeTreeCommon
from sverchok.data_structure import get_other_socket, updateNode, match_long_repeat
from sverchok.core.update_system import make_tree_from_nodes, do_update
from sverchok.core.monad_properties import SvIntPropertySettingsGroup, SvFloatPropertySettingsGroup, ensure_unique
from sverchok.core.events import CurrentEvents, BlenderEventsTypes
from sverchok.utils.handle_blender_data import get_sv_trees

MONAD_COLOR = (0.830819, 0.911391, 0.754562)


socket_types = [
    ("SvStringsSocket", "s", "Numbers, polygon data, generic"),
    ("SvVerticesSocket", "v", "Vertices, point and vector data"),
    ("SvMatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}


def nice_ui_name(input_str):
    a = input_str.replace('_', ' ')
    b = a.title()
    return b

def make_valid_identifier(name):
    """Create a valid python identifier from name for use a a part of class name"""
    while name and not name[0].isalpha():
        name = name[1:]
    if not name:
        return "generic"
    return "".join(ch for ch in name if ch.isalnum() or ch == "_")


def make_new_classname(monad_node_group):
    monad_base_name = make_valid_identifier(monad_node_group.name)
    monad_itentifier = id(monad_node_group) ^ random.randint(0, 4294967296)

    cls_name = "SvGroupNode{}_{}".format(monad_base_name, monad_itentifier)
    return cls_name


def monad_make_unique(node):

    """
    Create a new version of the monad class (duplicate but unique)

    This will attempt to store the duplicate in a json using create_dict_of_tree (from the Gist IO).
    The upside is that this will test the pack/unpack routine continuously. 
    The downside is that this will likely expose all the shortcommings that we don't know 
    about because it wasn't being tested extensively.
    """

    node_tree = node.id_data
    nodes = node_tree.nodes

    # generate a new copy of monad group node. using ( copy? ) 
    monad_group = bpy.data.node_groups[node.monad.name]
    new_monad_group = monad_group.copy()
    new_cls_name = make_new_classname(new_monad_group) 

    # the new tree dict will contain information about 1 node only, and 
    # the node_group too (at the moment) but the node_group data can be ignored.
    layout_json = create_dict_of_tree(ng=node_tree, identified_node=node)

    # do not restore links this way. wipe this entry and restore at a later stage.
    layout_json['update_lists'] = []

    # massage content of node_items, to correspond with the new desired name.
    node_ref = layout_json['nodes'][node.name]
    node_items = node_ref['params']
    node_items['all_props']['name'] = new_monad_group.name
    node_items['all_props']['cls_bl_idname'] = new_cls_name
    node_items['monad'] = new_monad_group.name
    node_items['cls_dict']['cls_bl_idname'] = new_cls_name

    pre_nodes = set(nodes)

    # place new empty version of the monad node
    import_tree(node_tree, nodes_json=layout_json)

    """
    notions..:
    
        if (original instance has no connections) then 
            replace it outright.
        else
            if mode=='replace':
                store connections
                replace instance with new unique instance
                reconnect old connections
            elif mode=='dupe_translate':
                generate unique instance
                attache node to transform operator.


    """

    # return newly generated node!
    return (set(node_tree.nodes) ^ pre_nodes).pop() 



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
    cls_bl_idname: StringProperty()

    float_props: CollectionProperty(type=SvFloatPropertySettingsGroup)
    int_props: CollectionProperty(type=SvIntPropertySettingsGroup)

    @property
    def sv_draft(self):
        # One monad tree can be used in several trees simultaneously;
        # they can have different draft mode status.
        # Let's assume that the monad tree is in Draft mode if *all*
        # trees that use it are in the draft mode.
        affected_trees = {instance.id_data for instance in self.instances}
        return all(hasattr(tree, 'sv_draft') and tree.sv_draft for tree in affected_trees)

    def get_current_as_default(self, prop_dict, node, prop_name):
        prop_dict['default'] = getattr(node, prop_name)
        # if not prop_dict['name']:
        #     prop_dict['name'] = node.name + '|' + prop_name

    def get_stored_prop_names(self):
        """ 
        - this will list all currently stored props for this monad / tree 
        - it reflects the state prior to acquisition of a new socket with prop.
        """
        props = self.get_all_props()
        return list(props['float_props'].keys()) + list(props['int_props'].keys())        


    def add_prop_from(self, socket):
        """
        Add a property if possible
        """
        other = socket.other
        cls = get_node_class_reference(self.cls_bl_idname)
        cls_dict = cls.__dict__ if cls else {}

        local_debug = False
        # reference_obj_id = cls.instances[0]
        # print(reference_obj_id.__annotations__)

        try:
            monad_prop_names = self.get_stored_prop_names()
            has_monad_prop_names = True
            print(monad_prop_names)
        except:
            print('no prop names yet in : add_prop_from call')
            has_monad_prop_names = False


        if other.prop_name:

            prop_name = other.prop_name
            prop_func, prop_dict = other.node.__annotations__.get(prop_name, ("", {}))

            if 'attr' in prop_dict:
                prop_dict.pop('attr')  # this we store in prop_name anyway
            
            if 'update' in prop_dict:
                """
                the node may be doing a tonne of stuff in a wrapped update,
                but because this property will be on a shell node (the monad outside) we can
                replace it with a reference to updateNode. i think this is a sane thing to ensure.
                """
                prop_dict['update'] = updateNode
            
            if not 'name' in prop_dict:
                """ 
                name is used exclusively for displaying name on the slider or label 
                most properties will have this defined anyway, but just in case.
                """ 
                regex = re.compile('[^a-z A-Z0-9]')
                prop_dict['name'] = regex.sub('', prop_name)
                print(f"monad: generated name for property function: {prop_name} -> {prop_dict['name']}")

            if local_debug:
                print("prop_func:", prop_func)   # tells us the kind of property to make
                print("prop_dict:", prop_dict)   # tells us the attributes of the property
                print("prop_name:", prop_name)   # tells the socket / slider ui which prop to display
                #                                # and its associated 'name' attribute from the prop_dict
            
            if prop_func.__name__ == "FloatProperty":
                self.get_current_as_default(prop_dict, other.node, prop_name)
                prop_settings = self.float_props.add()
                prop_name_prefix = f"floats_{len(self.float_props)}_"
            elif prop_func.__name__ == "IntProperty":
                self.get_current_as_default(prop_dict, other.node, prop_name)
                prop_settings = self.int_props.add()
                prop_name_prefix = f"ints_{len(self.int_props)}_"
            elif prop_func.__name__ == "FloatVectorProperty":
                info("FloatVectorProperty ignored (normal behaviour since day one). prop_func: %s, prop_dict: %s.", prop_func, prop_dict)
                return None
            else: # no way to handle it
                return None

            if other.node.bl_idname == "SvNumberNode":
                if "float" in prop_name:
                    prop_dict['min'] = other.node.float_min
                    prop_dict['max'] = other.node.float_max
                elif "int" in prop_name:
                    prop_dict['min'] = other.node.int_min
                    prop_dict['max'] = other.node.int_max

            new_name = prop_name_prefix + prop_name
            if has_monad_prop_names:
                new_name = ensure_unique(monad_prop_names, new_name)
            
            prop_settings.prop_name = new_name
            prop_settings.set_settings(prop_dict)
            socket.prop_name = new_name
            return new_name

        elif hasattr(other, "prop_type"):
            
            # if you are seeing errors with this and the other.node.bl_idname is not scriptnodelite
            # the fix will be here somewhere.
            print(f'{other.node} = other.node')
            print(f'{other.prop_type} = other.prop_type')
            
            if not any(substring in other.prop_type for substring in ["float", "int"]): 
                return None    
        
            if "float" in other.prop_type:
                prop_settings = self.float_props.add()
                prop_name_prefix = f"floats_{len(self.float_props)}_"
            elif "int" in other.prop_type:
                prop_settings = self.int_props.add()
                prop_name_prefix = f"ints_{len(self.int_props)}_"

            new_name = prop_name_prefix + other.name
            if has_monad_prop_names:
                new_name = ensure_unique(monad_prop_names, new_name)
            
            # this name will be used as the attr name of the newly generated property for the shellnode
            # essentially this is 
            #       __annotations__[prop_name] = new property function
            prop_settings.prop_name = new_name
      
            custom_prop_dict = {
                "name": nice_ui_name(other.name),
                "update": updateNode
            }

            # there are other nodes that use this technique, 
            if other.node.bl_idname == "SvScriptNodeLite":
                prop_list = other.node.float_list if "float" in other.prop_type else other.node.int_list
                default = prop_list[other.prop_index]
                custom_prop_dict["default"] = default

            prop_settings.set_settings(custom_prop_dict)
            socket.prop_name = new_name
            return new_name

        return None

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
        parse sockets and add any props as needed
        for backwarads compablility
        '''
        prop_names = [s.prop_name for s in chain(self.float_props, self.int_props)]
        prop_from_socket = [s.prop_name for s in self.input_node.outputs if s.prop_name]
        if len(prop_names) != len(prop_from_socket):
            pass
            #  here we could do something clever to create things.

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
        CurrentEvents.new_event(BlenderEventsTypes.monad_tree_update, self)
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
        for ng in get_sv_trees():
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
            error("Monad %s not set up correctly", self.name)
            return None

        cls_dict = {}

        if not self.cls_bl_idname:
            
            # the monad cls_bl_idname needs to be unique and cannot change
            monad_base_name = make_valid_identifier(self.name)
            monad_itentifier = id(self) ^ random.randint(0, 4294967296)

            cls_name = "SvGroupNode{}_{}".format(monad_base_name, monad_itentifier)
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

        self.verify_props()
        cls_dict["input_template"] = self.generate_inputs()
        cls_dict["output_template"] = self.generate_outputs()

        self.make_props(cls_dict)

        # done with setup

        old_cls_ref = get_node_class_reference(cls_name)
        bases = (SvGroupNodeExp, Node, SverchCustomTreeNode)
        cls_ref = type(cls_name, bases, cls_dict)

        if old_cls_ref:
            sverchok.utils.unregister_node_class(old_cls_ref)
        sverchok.utils.register_node_class(cls_ref)

        return cls_ref



    def make_props(self, cls_dict):
        cls_dict['__annotations__'] = {}

        for s in self.float_props:
            prop_dict = s.get_settings()
            prop_dict["update"] = updateNode
            cls_dict['__annotations__'][s.prop_name] = FloatProperty(**prop_dict)

        for s in self.int_props:
            prop_dict = s.get_settings()
            prop_dict["update"] = updateNode
            cls_dict['__annotations__'][s.prop_name] = IntProperty(**prop_dict)


    def generate_inputs(self):
        in_socket = []

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

def uget(self, origin):
    return self[origin]

def uset(self, value, origin):
    MAX = abs(getattr(self, 'loops_max'))
    MIN = 0

    if MIN <= value <= MAX:
        self[origin] = value
    elif value > MAX:
        self[origin] = MAX
    else:
        self[origin] = MIN
    return None


class SvGroupNodeExp:
    """
    Base class for all monad instances
    """
    bl_icon = 'OUTLINER_OB_EMPTY'

    vectorize: BoolProperty(
        name="Vectorize", description="Vectorize using monad",
        default=False, update=updateNode)

    split: BoolProperty(
        name="Split", description="Split inputs into lenght 1",
        default=False, update=updateNode)

    loop_me: BoolProperty(default=False, update=updateNode)
    loops_max: IntProperty(default=5, description='maximum')
    loops: IntProperty(
        name='loop n times', default=0,
        description='change max value in sidebar with variable named loops_max',
        get=lambda s: uget(s, 'loops'),
        set=lambda s, val: uset(s, val, 'loops'),
        update=updateNode)

    def draw_label(self):
        return self.monad.name

    @property
    def monad(self):
        for tree in bpy.data.node_groups:
            if tree.bl_idname == 'SverchGroupTreeType' and self.bl_idname == tree.cls_bl_idname:
               return tree
        return None # or raise LookupError or something, anyway big FAIL

    def sv_init(self, context):
        self['loops'] = 0
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
        layout.prop(self, 'loops_max')

    def draw_buttons(self, context, layout):

        split = layout.column().split()
        cA = split.column()
        cB = split.column()
        cA.active = not self.loop_me
        cA.prop(self, "vectorize", toggle=True)
        cB.active = self.vectorize
        cB.prop(self, "split", toggle=True)
        
        c2 = layout.column()
        row = c2.row(align=True)
        row.prop(self, "loop_me", text='Loop', toggle=True)
        row.prop(self, "loops", text='N')

        monad = self.monad
        if monad:
            c3 = layout.column()
            c3.prop(monad, "name", text='name')

            d = layout.column()
            d.active = bool(monad)
            if context:
                f = d.operator('node.sv_group_edit', text='edit!')
                f.group_name = monad.name
            else:
                layout.prop(self, 'loops_max')

    def get_nodes_to_process(self, out_node_name):
        """
        nodes not indirectly / directly contributing to the data we eventually pass to "monad.output_node" 
        are discarded if only `self.monad.outputs_node.name` is passed in endpoints_nodes.

        The exceptions are nodes that we use for debugging inside the monad. At present SvDebugPrint instances
        are added as endpoints (this allows them to be processed and they can write to the bpy.data.texta
        """
        endpoint_nodes = [out_node_name]
        nodes = self.monad.nodes
        for n in nodes:
            if n.bl_idname == 'SvDebugPrintNode' and n.print_data:
                endpoint_nodes.append(n.name)
        return endpoint_nodes

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        if not self.monad:
            return
        if self.vectorize:
            self.process_vectorize()
            return
        elif self.loop_me:
            self.process_looped(self.loops)
            return

        monad = self.monad
        in_node = monad.input_node
        out_node = monad.output_node
        monad['current_index'] = 0
        monad['current_total'] = 0

        for index, socket in enumerate(self.inputs):
            data = socket.sv_get(deepcopy=False)
            in_node.outputs[index].sv_set(data)

        node_names = self.get_nodes_to_process(out_node.name)
        ul = make_tree_from_nodes(node_names, monad, down=False)

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

        node_names = self.get_nodes_to_process(out_node.name)
        ul = make_tree_from_nodes(node_names, monad, down=False)

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


    # ----------- loop (iterate 2)

    def do_process(self, sockets_data_in):

        monad = self.monad
        in_node = monad.input_node
        out_node = monad.output_node

        for index, data in enumerate(sockets_data_in):
            in_node.outputs[index].sv_set(data)        

        node_names = self.get_nodes_to_process(out_node.name)
        ul = make_tree_from_nodes(node_names, monad, down=False)
        do_update(ul, monad.nodes)

        # set output sockets correctly
        socket_data_out = []
        for index, socket in enumerate(self.outputs):
            if socket.is_linked:
                data = out_node.inputs[index].sv_get(deepcopy=False)
                socket_data_out.append(data)

        return socket_data_out


    def apply_output(self, socket_data):
        for idx, data in enumerate(socket_data):
            self.outputs[idx].sv_set(data)


    def process_looped(self, iterations_remaining):
        sockets_in = [i.sv_get() for i in self.inputs]

        monad = self.monad
        monad['current_total'] = iterations_remaining
        monad['current_index'] = 0

        in_node = monad.input_node
        out_node = monad.output_node

        for iteration in range(iterations_remaining):
            # if 'Monad Info' in monad.nodes:
            #     info_node = monad.nodes['Monad Info']
            #     info_node.outputs[0].sv_set([[iteration]])
            monad["current_index"] = iteration
            sockets_in = self.do_process(sockets_in)
        self.apply_output(sockets_in)


    def load(self):
        pass


def register():
    bpy.utils.register_class(SverchGroupTree)

def unregister():
    bpy.utils.unregister_class(SverchGroupTree)
