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

from sverchok.data_structure import node_id, replace_socket

socket_types = [
    ("StringsSocket", "s", "Numbers, polygon data, generic"),
    ("VerticesSocket", "v", "Vertices, point and vector data"),
    ("MatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}

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
  

def find_node(id_name, ng):
    for n in ng.nodes:
        if n.bl_idname == id_name:
            return n
    raise NotFoundErr


def set_multiple_attrs(cls_ref, **kwargs):
    for arg_name, value in kwargs.items():
        setattr(cls_ref, arg_name, value)


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


def get_parent_data(node, kind):
    """
        gets the correct set of sockets on the external (parent) node
    """
    ntree = bpy.data.node_groups[node.parent_tree_name]
    parent_node = ntree.nodes[node.parent_node_name]
    sockets = getattr(parent_node, reverse_lookup.get(kind))
    return sockets


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


def relink(links, monad, parent_node):
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

    monad_in = 'Group Inputs Exp'
    monad_out = 'Group Outputs Exp'
    parent_tree = parent_node.id_data
    input_links = links['inputs']
    output_links = links['outputs']

    for m_idx, (k, v) in enumerate(input_links.items()):

        from_periphery_socket = k
        for f_idx, (monad_node_name, idx) in enumerate(v):
            dynamic_idx = -1 if f_idx == 0 else -2
            to_socket = monad.nodes[monad_node_name].inputs[idx]
            monad_in_socket = monad.nodes[monad_in].outputs[dynamic_idx]
            monad.links.new(monad_in_socket, to_socket)
        parent_tree.links.new(from_periphery_socket, parent_node.inputs[m_idx])

    for m_idx, (k, v) in enumerate(output_links.items()):

        # connect a single link to monad output
        monad_node_name, idx = k
        from_socket = monad.nodes[monad_node_name].outputs[idx]
        monad_out_socket = monad.nodes[monad_out].inputs[-1]
        monad.links.new(from_socket, monad_out_socket)

        # connect the parent node output to all previously connected sockets.
        for to_periphery_socket in v:
            parent_tree.links.new(parent_node.outputs[m_idx], to_periphery_socket)

    print(links)


def group_make(self, new_group_name):
    self.node_tree = bpy.data.node_groups.new(new_group_name, 'SverchGroupTreeType')
    self.node_tree['sub_group'] = True
    self.group_name = self.node_tree.name
    nodes = self.node_tree.nodes

    inputnode = nodes.new('SvGroupInputsNodeExp')
    inputnode.location = (-200, 0)
    inputnode.selected = False
    inputnode.parent_node_name = self.name
    inputnode.parent_tree_name = self.id_data.name

    outputnode = nodes.new('SvGroupOutputsNodeExp')
    outputnode.location = (200, 0)
    outputnode.selected = False
    outputnode.parent_node_name = self.name
    outputnode.parent_tree_name = self.id_data.name

    return self.node_tree


class SvMoveSocketOpExp(Operator):
    """Move a socket in the direction of the arrow, will wrap around"""
    bl_idname = "node.sverchok_move_socket_exp"
    bl_label = "Move Socket"

    pos = IntProperty()
    direction = IntProperty()
    node_name = StringProperty()

    def execute(self, context):
        node, kind, socket = get_data(self, context)
        parent_sockets = get_parent_data(node, kind)
        IO_node_sockets = getattr(node, kind)
        pos = self.pos

        if self.direction == 0:
            IO_node_sockets.remove(socket)     # I/O interface (subgroup)
            parent_sockets.remove(parent_sockets[pos])
        else:
            def wrap_around(current_idx, direction, member_count):
                return (current_idx + direction) % member_count

            # -1 because subgroup IO interface has a dummysocket appendix
            IO_new_pos = wrap_around(pos, self.direction, len(IO_node_sockets)-1)
            IO_node_sockets.move(pos, IO_new_pos)

            parent_new_pos = wrap_around(pos, self.direction, len(parent_sockets))
            parent_sockets.move(pos, parent_new_pos)

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
        socket.name = self.new_name

        # make changes to parent node's socket name in parent tree
        sockets = get_parent_data(node, kind)
        sockets[self.pos].name = self.new_name
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

        # make changes to parent node's socket name in parent tree
        parent_sockets = get_parent_data(node, kind)
        parent_socket = parent_sockets[self.pos]

        # replace socket types of subgroup IO and parent node
        for s in [socket, parent_socket]:
            replace_socket(s, self.socket_type)

        return {"FINISHED"}

    def invoke(self, context, event):
        _, _, socket = get_data(self, context)
        self.socket_type = socket.bl_idname
        return context.window_manager.invoke_props_dialog(self)


class SvGroupEdit(Operator):
    bl_idname = "node.sv_group_edit"
    bl_label = "edits an sv group"
    
    group_name = StringProperty()
    
    def execute(self, context):
        ng = bpy.data.node_groups
        node = context.node
        parent_tree = node.id_data

        monad = ng.get(self.group_name)
        if not monad:
            monad = group_make(node, new_group_name=self.group_name)
        
        bpy.ops.node.sv_switch_layout(layout_name=self.group_name)
        
        # by switching, space_data is now different
        path = context.space_data.path
        path.clear()
        path.append(parent_tree) # below the green opacity layer
        path.append(monad)       # top level

        return {"FINISHED"}


class SvTreePathParent(Operator):
    '''Go to parent node tree'''
    bl_idname = "node.sv_tree_path_parent"
    bl_label = "Parent Sv Node Tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and len(space.path) > 1

    def execute(self, context):
        space = context.space_data
        space.path.pop()
        context.space_data.node_tree = space.path[0].node_tree
        return {'FINISHED'}


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

        parent_node = ng.nodes.new('SvGroupNodeExp')
        parent_node.select = False
        parent_tree = parent_node.id_data
        parent_node.location = average_of_selected(nodes)
        bpy.ops.node.clipboard_copy()

        if self.use_relinking:
            # get links for relinking sockets in monad IO
            links = get_relinks(ng)

        monad = group_make(parent_node, self.group_name)
        bpy.ops.node.sv_switch_layout(layout_name=monad.name)
        
        # by switching, space_data is now different
        path = context.space_data.path
        path.clear()
        path.append(parent_tree) # below the green opacity layer
        path.append(monad)  # top level

        bpy.ops.node.clipboard_paste()
        
        # get optimal location for IO nodes..
        i_loc, o_loc = propose_io_locations(nodes)
        monad.nodes.get('Group Inputs Exp').location = i_loc
        monad.nodes.get('Group Outputs Exp').location = o_loc

        # remove nodes from parent_tree
        for n in reversed(nodes):
            parent_tree.nodes.remove(n)

        if self.use_relinking:
            relink(links, monad, parent_node)

        return {'FINISHED'}


class SvSocketAquisition:

    socket_map = {'outputs': 'to_socket', 'inputs': 'from_socket'}
    node_kind = StringProperty()

    def update(self):
        kind = self.node_kind
        if not kind:
            return

        socket_list = getattr(self, kind)
        _socket = self.socket_map.get(kind) # from_socket, to_socket
        _puts = reverse_lookup.get(kind) # inputs, outputs

        if socket_list[-1].is_linked:

            # first switch socket type
            socket = socket_list[-1]
            links = socket.links[0]
            linked_socket = getattr(links, _socket)
            new_type = linked_socket.bl_idname

            # if no 'linked_socket.prop_name' then use 'linked_socket.name'
            socket_prop_name = getattr(linked_socket, 'prop_name')
            
            no_prop_name = (not socket_prop_name or len(socket_prop_name) == 0)
            if no_prop_name:
                new_name = linked_socket.name
            else:
                new_name = socket_prop_name

            new_name = new_name.replace('_', ' ').strip() # more elaborate sanitizing needed?
            replace_socket(socket, new_type, new_name=new_name)

            # add new input socket to parent node
            parent_tree = bpy.data.node_groups[self.parent_tree_name].nodes
            parent_node = parent_tree[self.parent_node_name]
            sok = getattr(parent_node, _puts).new(new_type, new_name)


            # add new dangling dummy
            socket_list.new('SvDummySocket', 'connect me')