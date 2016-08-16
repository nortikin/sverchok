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

from collections import defaultdict

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty
from bpy.types import Node, NodeTree


from sverchok.node_tree import SverchCustomTreeNode, SvNodeTreeCommon
from sverchok.data_structure import node_id, replace_socket, get_other_socket
from sverchok.core.update_system import make_tree_from_nodes, do_update


# this should NOT be defined here but in the node file.
MONAD_COLOR = (0.4, 0.9, 1)


socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}

def make_valid_identifier(name):
    """Create a valid python identifier from name for use a a part of class name"""
    return "".join(ch for ch in name if ch.isalnum() or ch=="_")

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
        # this should perhaps be made more random
        cls_name = "SvGroupNodeExp{}".format(make_valid_identifier(monad.name))
    else:
        cls_name = monad.cls_bl_idname

    cls_dict["bl_idname"] = cls_name
    old_cls_ref = getattr(bpy.types, cls_name, None)

    in_socket = []

    def get_socket_data(socket):
        other = get_other_socket(socket)
        if socket.bl_idname == "SvDummySocket":
            socket = get_other_socket(socket)

        socket_bl_idname = socket.bl_idname
        socket_name = socket.name
        return socket_name, socket_bl_idname


    # if socket is dummysocket use the other for data
    for socket in monad_inputs.outputs:
        if socket.is_linked:

            other = get_other_socket(socket)
            prop_data = other.get_prop_data()
            if "prop_name" in prop_data:
                prop_name = prop_data["prop_name"]
                prop_rna = getattr(other.node.rna_type, prop_name)
                if prop_name in cls_dict:
                    # all properties need unique names,
                    # if 'x' is taken 'x2' etc.
                    for i in range(2, 100):
                        new_name = "{}{}".format(prop_name, i)
                        if new_name in cls_dict:
                            continue
                        prop_name = new_name
                        break
                cls_dict[prop_name] = prop_rna

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

    bases = (Node, SvGroupNodeExp, SverchCustomTreeNode)
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

    #
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



class SvGroupNodeExp:
    """
    Base class for all monad instances
    """
    bl_label = 'Group Exp'
    bl_icon = 'OUTLINER_OB_EMPTY'

    #group_name = StringProperty()

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

def average_of_selected(nodes):
    x, y = 0, 0
    for n in nodes:
        x += n.location[0]
        y += n.location[1]
    num_nodes = len(nodes)
    return x / num_nodes, y / num_nodes


def propose_io_locations(nodes):
    '''
    This make a bounding 2d and returns suggested
    optimal input and output node locations for the monad
    '''
    x_locs = [n.location[0] for n in nodes]
    y_locs = [n.location[1] for n in nodes]
    min_x, max_x = min(x_locs), max(x_locs)
    min_y, max_y = min(y_locs), max(y_locs)
    y = (min_y + max_y) / 2
    offset = 210

    return (min_x - offset, y), (max_x + offset - 30, y)



def reduce_links(links):
    reduced_links = dict(inputs=defaultdict(list), outputs=defaultdict(list))
    for k, v in links.items():
        for item in v:
            link = item['link']
            if k == 'inputs':
                reduced_links['inputs'][link.from_socket].append([link.to_node.name, item['socket_idx']])
            else:
                reduced_links['outputs'][(link.from_node.name, item['socket_idx'])].append(link.to_socket)
    return reduced_links



def get_relinks(ng):
    '''
    ng = bpy.data.node_groups['NodeTree']
    print(get_relinks(ng))
    '''
    nodes = [n for n in ng.nodes if n.select]
    relinks = dict(inputs=[], outputs=[])
    if not nodes:
        return relinks

    def gobble_links(link, link_kind, idx, kind):
        linked_node = getattr(link, link_kind)
        if not linked_node in nodes:
            relinks[kind].append(dict(socket_idx=idx, link=link))

    def get_links(node, kind='inputs', link_kind='from_node'):
        for idx, s in enumerate(getattr(node, kind)):
            if not s.is_linked:
                continue

            if kind == 'inputs':
                link = s.links[0]
                gobble_links(link, link_kind, idx, kind)
            else:
                for link in s.links:
                    gobble_links(link, link_kind, idx, kind)

    for node in nodes:
        get_links(node=node, kind='inputs', link_kind='from_node')
        get_links(node=node, kind='outputs', link_kind='to_node')

    return reduce_links(relinks)


def relink_parent(links, parent_node):
    '''
    expects input like:

    {'inputs': defaultdict(<class 'list'>,
        {bpy.data...nodes["Float"].outputs[0]: [
            ['function.003', 1], ['Vectors in.001', 0]
        ],
        bpy.data...nodes["Integer"].outputs[0]: [
            ['Float Series', 2]
        ]}),
    'outputs': defaultdict(<class 'list'>,
        {('Vectors', 0): [
            bpy.data...nodes["Viewer Draw2"].inputs[0],
            bpy.data...nodes["Vectors out"].inputs[0]
        ]})
    }
    '''

    parent_tree = parent_node.id_data
    input_links = links['inputs']
    output_links = links['outputs']

    for m_idx, (k, v) in enumerate(input_links.items()):

        from_periphery_socket = k
        parent_tree.links.new(from_periphery_socket, parent_node.inputs[m_idx])

    for m_idx, (k, v) in enumerate(output_links.items()):

        # connect a single link to monad output
        # connect the parent node output to all previously connected sockets.
        for to_periphery_socket in v:
            parent_tree.links.new(parent_node.outputs[m_idx], to_periphery_socket)

    print(links)

def relink_monad(links, monad):
    '''
    expects input like:

    {'inputs': defaultdict(<class 'list'>,
        {bpy.data...nodes["Float"].outputs[0]: [
            ['function.003', 1], ['Vectors in.001', 0]
        ],
        bpy.data...nodes["Integer"].outputs[0]: [
            ['Float Series', 2]
        ]}),
    'outputs': defaultdict(<class 'list'>,
        {('Vectors', 0): [
            bpy.data...nodes["Viewer Draw2"].inputs[0],
            bpy.data...nodes["Vectors out"].inputs[0]
        ]})
    }
    '''

    monad_in = monad.input_node
    monad_out = monad.output_node

    input_links = links['inputs']
    output_links = links['outputs']

    for m_idx, (k, v) in enumerate(input_links.items()):

        from_periphery_socket = k
        for f_idx, (monad_node_name, idx) in enumerate(v):
            dynamic_idx = -1 if f_idx == 0 else -2
            to_socket = monad.nodes[monad_node_name].inputs[idx]
            monad_in_socket = monad_in.outputs[dynamic_idx]
            monad.links.new(monad_in_socket, to_socket)

    for m_idx, (k, v) in enumerate(output_links.items()):

        # connect a single link to monad output
        monad_node_name, idx = k
        from_socket = monad.nodes[monad_node_name].outputs[idx]
        monad_out_socket = monad_out.inputs[-1]
        monad.links.new(from_socket, monad_out_socket)


    #print(links)

def get_data(self, context):
    """ expects:
            - self.node_name
            - and self.pos
            - space_data.path to have 2 members, ([1] being the upper visible)
    """
    node = context.space_data.path[1].node_tree.nodes[self.node_name]
    kind = node.node_kind
    socket = getattr(node, kind)[self.pos]
    return node, kind, socket



class SvMoveSocketOpExp(Operator):
    """Move a socket in the direction of the arrow, will wrap around"""
    bl_idname = "node.sverchok_move_socket_exp"
    bl_label = "Move Socket"

    pos = IntProperty()
    direction = IntProperty()
    node_name = StringProperty()

    def execute(self, context):
        node, kind, socket = get_data(self, context)
        monad = node.id_data
        IO_node_sockets = getattr(node, kind)
        pos = self.pos

        if self.direction == 0:
            IO_node_sockets.remove(socket)     # I/O interface (subgroup)
            for instance in monad.instances:
                sockets = getattr(instance, reverse_lookup[kind])
                sockets.remove(sockets[pos])
        else:
            def wrap_around(current_idx, direction, member_count):
                return (current_idx + direction) % member_count

            # -1 because subgroup IO interface has a dummysocket appendix
            IO_new_pos = wrap_around(pos, self.direction, len(IO_node_sockets)-1)
            IO_node_sockets.move(pos, IO_new_pos)

            for instance in monad.instances:

                sockets = getattr(instance, reverse_lookup[kind])
                new_pos = wrap_around(pos, self.direction, len(sockets))
                sockets.move(pos, new_pos)

        make_class_from_monad(monad.name)
        return {"FINISHED"}


class SvRenameSocketOpExp(Operator):
    """Rename a socket"""
    bl_idname = "node.sverchok_rename_socket_exp"
    bl_label = "Rename Socket"

    pos = IntProperty()
    node_name = StringProperty()
    new_name = StringProperty()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'new_name', text='(new) name')

    def execute(self, context):
        # make changes to this node's socket name
        node, kind, socket = get_data(self, context)
        monad = node.id_data

        socket.name = self.new_name
        # make changes to parent node's socket name in parent tree
        for instance in monad.instances:
            sockets = getattr(instance, reverse_lookup[kind])
            sockets[self.pos].name = self.new_name

        make_class_from_monad(monad.name)
        return {"FINISHED"}

    def invoke(self, context, event):
        _, _, socket = get_data(self, context)
        self.new_name = socket.name
        return context.window_manager.invoke_props_dialog(self)


class SvEditSocketOpExp(Operator):
    """Edit a socket signature"""
    bl_idname = "node.sverchok_edit_socket_exp"
    bl_label = "Edit Socket"

    node_name = StringProperty()
    pos = IntProperty()
    socket_type = EnumProperty(
        items=socket_types, default="StringsSocket")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'socket_type', text='Socket Type')

    def execute(self, context):
        # make changes to this node's socket name
        node, kind, socket = get_data(self, context)
        monad = node.id_data

        replace_socket(socket, self.socket_type)

        for instance in monad.instances:
            sockets = getattr(instance, reverse_lookup[kind])
            replace_socket(sockets[self.pos], self.socket_type)

        make_class_from_monad(monad.name)
        return {"FINISHED"}

    def invoke(self, context, event):
        _, _, socket = get_data(self, context)
        self.socket_type = socket.bl_idname
        return context.window_manager.invoke_props_dialog(self)


class SvGroupEdit(Operator):
    bl_idname = "node.sv_group_edit"
    bl_label = "edits an sv group"

    group_name = StringProperty()
    short_cut = BoolProperty()

    def execute(self, context):
        ng = bpy.data.node_groups

        # if this operator is triggered from nodeview / TAB
        if self.short_cut:
            node = context.active_node
            if node:
                if not hasattr(node, 'monad'):
                    self.report({"WARNING"}, 'Active node is not a monad instance')
                    return {'CANCELLED'}
                self.group_name = node.monad.name
            else:
                msg = 'Select 1 monad instance node to enter the monad'
                self.report({"WARNING"}, msg)
                return {'CANCELLED'}
        else:
            # else it is triggered from directly on the node by the button
            node = context.node

        parent_tree = node.id_data

        monad = ng.get(self.group_name)
        if not monad:
            monad = monad_make(new_group_name=self.group_name)

        bpy.ops.node.sv_switch_layout(layout_name=self.group_name)

        # by switching, space_data is now different
        path = context.space_data.path
        path.clear()
        path.append(parent_tree) # below the green opacity layer
        path.append(monad) # top level

        return {"FINISHED"}


class SvMonadEnter(Operator):
    '''Makes node group, relink will enforce peripheral connections'''
    bl_idname = "node.sv_monad_enter"
    bl_label = "Exit or Enter a monad"

    # group_name = StringProperty(default="Monad")
    # use_relinking = BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
            return True

    def execute(self, context):
        tree_type = context.space_data.tree_type
        node = context.active_node
        
        if node and hasattr(node, 'monad'):
            bpy.ops.node.sv_group_edit(short_cut=True)
            return {'FINISHED'}

        else:
            if len(context.space_data.path) == 2:
                bpy.ops.node.sv_tree_path_parent()
                return {'FINISHED'}

        return {'CANCELLED'}



class SvTreePathParent(Operator):
    '''Go to parent node tree'''
    bl_idname = "node.sv_tree_path_parent"
    bl_label = "Parent Sv Node Tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if space.type == 'NODE_EDITOR':
            if len(space.path) > 1:
                if space.path[-1].node_tree.bl_idname == "SverchGroupTreeType":
                    return True
        return False

    def execute(self, context):
        space = context.space_data
        space.path.pop()
        context.space_data.node_tree = space.path[0].node_tree
        return {'FINISHED'}



# methods for collecting links

def get_socket_index(socket):
    try:
        return socket.index
    # for reroutes, since they don't have .index property/attribute
    except AttributeError:
        return 0

def collect_links(ng):
    in_links = [l for l in ng.links if (not l.from_node.select) and (l.to_node.select)]
    out_links = [l for l in ng.links if (l.from_node.select) and (not l.to_node.select)]
    return dict(input=in_links, output=out_links)

def sort_keys_out(link):
     return (get_socket_index(link.to_socket), link.from_node.location.y)

def sort_keys_in(link):
     return (get_socket_index(link.to_socket) , link.from_node.location.y)

def compile_link_monad(link):
    return link.from_node.name, link.from_socket.index, link.to_node.name, link.to_socket.index

def link_monad(monad, links):
    in_links = sorted(links["input"], key=sort_keys_in)
    out_links = sorted(links["output"], key=sort_keys_out)
    nodes = monad.nodes
    input_node = monad.input_node
    output_node = monad.output_node
    remap_inputs = {}
    relink_in = []
    for idx, link in enumerate(in_links):
        to_socket = nodes[link.to_node.name].inputs[link.to_socket.index]
        original_from_socket = link.from_socket
        if original_from_socket in remap_inputs:
            from_socket = input_node.outputs[remap_inputs[original_from_socket]]
            l = monad.links.new(from_socket, to_socket)
        else:
            remap_inputs[original_from_socket] = len(input_node.outputs) - 1
            l = monad.links.new(input_node.outputs[-1], to_socket)
        relink_in.append((original_from_socket, remap_inputs[original_from_socket]))

    relink_out = []
    for idx, link in enumerate(out_links):
        from_socket = nodes[link.from_node.name].outputs[link.from_socket.index]
        monad.links.new(from_socket, output_node.inputs[-1])
        # here we can't just use the to_socket since with dynamic socket count
        # it might not exist when we get around to relinking it.
        relink_out.append((idx, link.to_node.name, get_socket_index(link.to_socket)))

    return relink_in, relink_out

def link_monad_instance(instance, re_links):
    ng = instance.id_data
    relink_in, relink_out = re_links
    for socket, idx in relink_in:
        ng.links.new(socket, instance.inputs[idx])

    for idx, node_name, socket_idx in relink_out:
        ng.links.new(instance.outputs[idx], ng.nodes[node_name].inputs[socket_idx])


class SvMonadCreateFromSelected(Operator):
    '''Makes node group, relink will enforce peripheral connections'''
    bl_idname = "node.sv_monad_from_selected"
    bl_label = "Create monad from selected nodes (sub graph)"

    group_name = StringProperty(default="Monad")
    use_relinking = BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type == 'SverchCustomTreeType':
            return True

    def execute(self, context):

        ng = context.space_data.edit_tree
        nodes = [n for n in ng.nodes if n.select]

        if not nodes:
            self.report({"CANCELLED"}, "No nodes selected")
            return {'CANCELLED'}

        bpy.ops.node.clipboard_copy()

        if self.use_relinking:
            # get links for relinking sockets in monad IO
            links = collect_links(ng)

        monad = monad_make(self.group_name)
        bpy.ops.node.sv_switch_layout(layout_name=monad.name)

        # by switching, space_data is now different
        path = context.space_data.path
        path.clear()
        path.append(ng) # below the green opacity layer
        path.append(monad)  # top level

        bpy.ops.node.clipboard_paste()

        # get optimal location for IO nodes..
        i_loc, o_loc = propose_io_locations(nodes)
        monad.input_node.location = i_loc
        monad.output_node.location = o_loc

        if self.use_relinking:
            re_links = link_monad(monad, links)

        """
         the monad is created, create a the class and then with class
         create the node, place and link it up
        """
        cls_ref = make_class_from_monad(monad.name)
        parent_node = ng.nodes.new(cls_ref.bl_idname)
        parent_node.select = False
        parent_node.location = average_of_selected(nodes)

        # remove nodes from parent_tree
        for n in nodes:
            ng.nodes.remove(n)

        # relink the new node
        if self.use_relinking:
            link_monad_instance(parent_node, re_links)

        bpy.ops.node.view_all()
        return {'FINISHED'}


class SvMonadExpand(Operator):
    '''Expands monad into parent Layout will enforce peripheral connections'''
    bl_idname = "node.sv_monad_expand"
    bl_label = "Create monad from selected nodes (sub graph)"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        tree_type = space_data.tree_type
        multiple_paths = len(space_data.path) > 1

        if tree_type == 'SverchCustomTreeType' and multiple_paths:
            return True

    def execute(self, context):
        '''
        first possibly an ugly, but functional implementation.

        - 1 (in monad) select all nodes
        - 2 (in monad) deselect I/O nodes
        - 3 (in monad) copy selection
        - 4 (in monad) acquire links between selected / non selected
        - 5 (in parent) aquire direct links to/from monad_instance_node
        - 6 (in parent) unlink periphery of monad_instance_node
        - 7 (in monad) pop to parent
        - 8 (in parent) paste selection
        - 9 (in parent) move selection to logical position
        - 10 (in parent) relink periphery
        - 11 (in parent) delete monad_instance_node
        - 12 deselect all

        '''
        monad = context.space_data.edit_tree

        # 1 - (in monad) select all nodes
        bpy.ops.node.select_all()

        # 2 - (in monad) deselect I/O nodes
        for n in monad.nodes:
            n.select = not (n.bl_idname in {'SvGroupInputsNodeExp', 'SvGroupOutputsNodeExp'})

        # 3 - (in monad) copy selection
        bpy.ops.node.clipboard_copy()

        # 4 - (in monad) acquire links between selected / non selected
        inner_links = collect_links(monad)
        print(inner_links)

        # 5 - (in parent) aquire direct links to/from monad_instance_node
        # outer_links = collect_external_links(monad_instance_node)

        # 6 - (in parent) unlink periphery of monad_instance_node
        #     or let the monad_instance_node removal take care of this?

        # 7 - (in monad) pop to parent
        # path = context.space_data.path
        # path.pop()

        # 7.5 - (in parent) deselect all

        # 8 - (in parent) paste selection
        # bpy.ops.node.clipboard_paste()

        # 9 - (in parent) move selection to logical position

        # 10 - (in parent) relink periphery

        # 11 - (in parent) delete monad_instance_node
        # ng.nodes.remove(monad_instance_node)

        # 12 - deselect all

        return {'FINISHED'}


def monad_make(new_group_name):

    monad = bpy.data.node_groups.new(new_group_name, 'SverchGroupTreeType')
    monad.use_fake_user = True
    nodes = monad.nodes

    inputnode = nodes.new('SvGroupInputsNodeExp')
    inputnode.location = (-200, 0)
    inputnode.selected = False

    outputnode = nodes.new('SvGroupOutputsNodeExp')
    outputnode.location = (200, 0)
    outputnode.selected = False

    return monad

class SvSocketAquisition:

    socket_map = {'outputs': 'to_socket', 'inputs': 'from_socket'}
    node_kind = StringProperty()

    def update(self):
        kind = self.node_kind
        if not kind:
            return

        monad = self.id_data
        # still being manipulated
        #if not monad.cls_bl_idname:
        #    return

        socket_list = getattr(self, kind)
        _socket = self.socket_map.get(kind) # from_socket, to_socket

        if socket_list[-1].is_linked:

            # first switch socket type
            socket = socket_list[-1]

            cls = make_class_from_monad(monad)
            if kind == "outputs":
                new_name, new_type, prop_data = cls.input_template[-1]
            else:
                new_name, new_type = cls.output_template[-1]
                prop_data = {}

            # if no 'linked_socket.prop_name' then use 'linked_socket.name'
            replace_socket(socket, new_type, new_name=new_name)

            for instance in monad.instances:
                sockets = getattr(instance, reverse_lookup[kind])
                new_socket = sockets.new(new_type, new_name)
                for name, value in prop_data.items():
                    setattr(new_socket, name, value)

            # add new dangling dummy
            socket_list.new('SvDummySocket', 'connect me')
