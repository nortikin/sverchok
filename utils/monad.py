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

import sys

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty, FloatProperty


from sverchok.node_tree import SverchCustomTreeNode, SvNodeTreeCommon
from sverchok.data_structure import updateNode, get_other_socket, enum_item_4
from sverchok.core.monad import monad_make_unique


socket_types = [
    ("SvStringsSocket", "s", "Numbers, polygon data, generic"),
    ("SvVerticesSocket", "v", "Vertices, point and vector data"),
    ("SvMatrixSocket", "m", "Matrix")
]

reverse_lookup = {'outputs': 'inputs', 'inputs': 'outputs'}



class MonadOpCommon():
    node_name: StringProperty()
    pos: IntProperty()

    def get_data(self, context):
        """ expects:
                - self.node_name
                - and self.pos
                - space_data.path to have 2 members, ([1] being the upper visible)
        """
        node = context.space_data.edit_tree.nodes[self.node_name]
        kind = node.node_kind
        socket = getattr(node, kind)[self.pos]
        return node, kind, socket



class SvMoveSocketOpExp(Operator, MonadOpCommon):
    """Move a socket in the direction of the arrow, will wrap around"""
    bl_idname = "node.sverchok_move_socket_exp"
    bl_label = "Move Socket"

    direction: IntProperty()

    def execute(self, context):
        node, kind, socket = self.get_data(context)
        monad = node.id_data
        IO_node_sockets = getattr(node, kind)
        pos = self.pos

        if self.direction == 0:
            if socket.prop_name:
                monad.remove_prop(socket)
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

        monad.update_cls()
        return {"FINISHED"}


class SvRenameSocketOpExp(Operator, MonadOpCommon):
    """Rename a socket"""
    bl_idname = "node.sverchok_rename_socket_exp"
    bl_label = "Rename Socket"

    new_name: StringProperty()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        _, _, socket = self.get_data(context)
        if socket.prop_name:
            monad = socket.id_data
            settings = monad.find_prop(socket)
            row.prop(settings, 'name', text='(new) name')
            settings.draw(context, layout)
        else:
            row.prop(self, 'new_name', text='(new) name')


    def execute(self, context):
        # make changes to this node's socket name
        node, kind, socket = self.get_data(context)
        monad = node.id_data
        monad.update_cls()
        if socket.prop_name:
            settings = monad.find_prop(socket)
            new_name = settings.name
        else:
            new_name = self.new_name

        monad.update_cls()

        socket.name = new_name
        # make changes to parent node's socket name in parent tree
        for instance in monad.instances:
            sockets = getattr(instance, reverse_lookup[kind])
            sockets[self.pos].name = new_name
            if socket.prop_name:
                sockets[self.pos].prop_name = socket.prop_name

        return {"FINISHED"}

    def invoke(self, context, event):
        _, _, socket = self.get_data(context)
        self.new_name = socket.name
        return context.window_manager.invoke_props_dialog(self)


class SvEditSocketOpExp(Operator, MonadOpCommon):
    """Edit a socket signature"""
    bl_idname = "node.sverchok_edit_socket_exp"
    bl_label = "Edit Socket"

    socket_type: EnumProperty(
        items=socket_types, default="SvStringsSocket")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'socket_type', text='Socket Type')

    def execute(self, context):
        # make changes to this node's socket name
        node, kind, socket = self.get_data(context)
        monad = node.id_data

        socket.replace_socket(self.socket_type)

        for instance in monad.instances:
            sockets = getattr(instance, reverse_lookup[kind])
            sockets[self.pos].replace_socket(self.socket_type)

        monad.update_cls()
        return {"FINISHED"}

    def invoke(self, context, event):
        _, _, socket = self.get_data(context)
        self.socket_type = socket.bl_idname
        return context.window_manager.invoke_props_dialog(self)


class SvNewSocketOpExp(Operator, MonadOpCommon):
    """Generate new socket"""
    bl_idname = "node.sverchok_new_socket_exp"
    bl_label = "New Socket"

    # private
    kind: StringProperty(name="io kind")

    # client
    socket_type: EnumProperty(items=socket_types, default="SvStringsSocket")
    new_prop_name: StringProperty(name="prop name")
    new_prop_type: EnumProperty(name="prop type", items=enum_item_4(["Int", "Float"]), default='Int')
    new_prop_description: StringProperty(name="description", default="lazy?")
    
    # no subtype. it is not worth it.
    enable_min: BoolProperty(default=False, name="enable min")
    enable_max: BoolProperty(default=False, name="enable max")
    enable_soft_min: BoolProperty(default=False, name="enable soft min")
    enable_soft_max: BoolProperty(default=False, name="enable soft max")
    
    # int specific
    new_prop_int_default: IntProperty(default=0, name="default")
    new_prop_int_min: IntProperty(default=-2**31, name="min")
    new_prop_int_max: IntProperty(default=2**31-1, name="max")
    new_prop_int_soft_min: IntProperty(default=-2**31, name="soft min")
    new_prop_int_soft_max: IntProperty(default=2**31-1, name="soft max")
    new_prop_int_step: IntProperty(default=1, name="step")
    
    # float specific
    new_prop_float_default: FloatProperty(default=0, name="default")
    new_prop_float_min: FloatProperty(default=-2**31, name="min")
    new_prop_float_max: FloatProperty(default=2**31-1, name="max")
    new_prop_float_soft_min: FloatProperty(default=-2**31, name="soft min")
    new_prop_float_soft_max: FloatProperty(default=2**31-1, name="soft max")
    new_prop_float_step: FloatProperty(default=1.0, name="step")

    @classmethod
    def poll(cls, context):
        try:
            if context.space_data.edit_tree.bl_idname == 'SverchGroupTreeType':
                return not context.space_data.edit_tree.library
        except:
            return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def get_display_props(self):
        prop_prefix = f"new_prop_{self.new_prop_type.lower()}_"
        props = "default", "min", "max", "soft_min", "soft_max", "step"
        return [(prop_prefix + prop) for prop in props]

    def draw(self, context):
        layout = self.layout
        col1 = layout.column()
        socket_row = col1.row()
        socket_row.prop(self, 'socket_type', text='Socket Type', expand=True)
        col1.prop(self, 'new_prop_name')

        if self.kind == "outputs":
            # there are no other properties to configure for the <output node>
            return

        col1.prop(self, 'new_prop_type')

        if self.socket_type == "SvStringsSocket":
            default, min, max, soft_min, soft_max, step = self.get_display_props()
            col1.prop(self, default, text="default")

            # enable min / max
            row1 = col1.row(align=True)
            row1_col1_r = row1.column().row(align=True)
            row1_col1_r.active = self.enable_min
            row1_col1_r.prop(self, "enable_min", text="", icon="CHECKMARK")
            row1_col1_r.prop(self, min)
            row1_col2_r = row1.column().row(align=True)
            row1_col2_r.active = self.enable_max
            row1_col2_r.prop(self, "enable_max", text="", icon="CHECKMARK")
            row1_col2_r.prop(self, max)

            # enable soft min / max
            row2 = col1.row(align=True)
            row2_col1_r = row2.column().row(align=True)
            row2_col1_r.active = self.enable_soft_min
            row2_col1_r.prop(self, "enable_soft_min", text="", icon="CHECKMARK")
            row2_col1_r.prop(self, soft_min)
            row2_col2_r = row2.column().row(align=True)
            row2_col2_r.active = self.enable_soft_max
            row2_col2_r.prop(self, "enable_soft_max", text="", icon="CHECKMARK")
            row2_col2_r.prop(self, soft_max)

        col1.prop(self, "new_prop_description")

    def get_prop_dict(self):
        empty_dict = {}
        sig = self.new_prop_type
        empty_dict['name'] = self.new_prop_name

        if self.kind == 'outputs':
            # we do not set the slider on the <output node> sockets
            return {}

        if sig in {"Int", "Float"}:
            empty_dict['update'] = updateNode
            empty_dict['default'] = getattr(self, f"new_prop_{sig.lower()}_default")
            if self.enable_min:
                empty_dict['min'] = getattr(self, f"new_prop_{sig.lower()}_min")
            if self.enable_max:
                empty_dict['max'] = getattr(self, f"new_prop_{sig.lower()}_max")
            if self.enable_soft_min:
                empty_dict['soft_min'] = getattr(self, f"new_prop_{sig.lower()}_soft_min")
            if self.enable_soft_max:
                empty_dict['soft_max'] = getattr(self, f"new_prop_{sig.lower()}_soft_max")

        return empty_dict

    def execute(self, context):

        monad = context.space_data.edit_tree
        io_node = monad.input_node if self.kind == 'inputs' else monad.output_node

        # if we want to add a socket to the inputs node, we must update that node's output sokets.
        # because the output sockets are the sockets that feed data into the monad tree. This is
        # why the reverse lookup is used.
        socket_kind_to_add = reverse_lookup.get(self.kind)
        socket_list = getattr(io_node, socket_kind_to_add)
        socket = socket_list[-1]

        # we'll compose a prop_dict from the user configured properties. 
        # These shall be sparse representations.
        prop_dict = self.get_prop_dict()
        print(prop_dict)

        # this is a partial code duplication from the monad.py in nodes/scene/monad
        if False:

            # gather socket data
            if self.kind == reverse_lookup.get("outputs"):
                
                prop_name = monad.add_prop_from(socket)
                cls = monad.update_cls()
                new_name, new_type, prop_data = cls.input_template[-1]
            else:
                # adding to the input socket of output-into-parent-tree node
                prop_name = ""
                cls = monad.update_cls()
                prop_data = {}
                new_name, new_type = cls.output_template[-1]

            # transform socket type from dummy to new type
            new_socket = socket.replace_socket(new_type, new_name=new_name)
            if prop_name:
                new_socket.prop_name = prop_name

            # update all monad nodes (front facing)
            for instance in monad.instances:
                sockets = getattr(instance, reverse_lookup[kind])
                new_socket = sockets.new(new_type, new_name)
                for name, value in prop_data.items():
                    if not name == 'prop_name':
                        setattr(new_socket, name, value)
                    else:
                        new_socket.prop_name = prop_name or ''


            # add new dangling dummy
            socket_list.new('SvDummySocket', 'connect me')

        return {'FINISHED'}


class SvMonadNewEmpty(Operator):
    """generate a new empty monad at the mouse cursor location"""
    bl_idname = "node.sverchok_new_empty_monad"
    bl_label = "New Empty Monad"

    new_monad_name: StringProperty(name="new monad name")
    mouse_xy: bpy.props.IntVectorProperty(size=2, default=(0,0), name="mouse location")

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
            return True

    @staticmethod
    def store_mouse_cursor(context, event):
        space = context.space_data
        tree = space.edit_tree

        # convert mouse position to the View2D for later node placement
        if context.region.type == 'WINDOW':
            # convert mouse position to the View2D for later node placement
            space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        else:
            space.cursor_location = tree.view_center

    def draw(self, context):
        ... # draw this dialogue

    def execute(self, context):
        ...  # monad_make(new_monad_name)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SvGroupEdit(Operator):
    bl_idname = "node.sv_group_edit"
    bl_label = "edits an sv group"

    group_name: StringProperty()
    short_cut: BoolProperty()

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
        if not node:
            monad = ng.get(self.group_name)
            if not monad:
                monad = monad_make(new_group_name=self.group_name)
        else:
            monad = node.monad


        path = context.space_data.path
        space_data = context.space_data
        if len(path) == 1:
            path.start(parent_tree)
            path.append(monad, node=node)
        else:
            path.append(monad, node=node)

        return {"FINISHED"}


class SvMonadEnter(Operator):
    bl_idname = "node.sv_monad_enter"
    bl_label = "Exit or Enter a monad"

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
            if len(context.space_data.path) > 1:
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
                if space.edit_tree.bl_idname == "SverchGroupTreeType":
                    return True
        return False

    def execute(self, context):
        space = context.space_data
        space.path.pop()
        return {'FINISHED'}



# methods for collecting links etc to help with monad creation

def get_socket_index(socket):
    try:
        return socket.index
    # for reroutes, since they don't have .index property/attribute
    except AttributeError:
        return 0

def collect_links(ng):
    """
    collect links between unselected and selected in ng
    return {"input": links_to_seleted[], "outputs" : links_from_selecte[]}
    """
    in_links = [l for l in ng.links if (not l.from_node.select) and (l.to_node.select)]
    out_links = [l for l in ng.links if (l.from_node.select) and (not l.to_node.select)]
    return dict(input=in_links, output=out_links)

def sort_keys_out(link):
     return (get_socket_index(link.to_socket), link.from_node.location.y)

def sort_keys_in(link):
     return (get_socket_index(link.to_socket) , link.from_node.location.y)

def link_monad(monad, links):
    """
    link up the new created monad
    """
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
    """
    Link the monad instance after creation
    """
    ng = instance.id_data
    relink_in, relink_out = re_links
    for socket, idx in relink_in:
        ng.links.new(socket, instance.inputs[idx])

    for idx, node_name, socket_idx in relink_out:
        ng.links.new(instance.outputs[idx], ng.nodes[node_name].inputs[socket_idx])


def monad_make(new_group_name):
    """
    Create new monad and set it up
    """

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


class SvMonadCreateFromSelected(Operator):
    '''Makes node group, relink will enforce peripheral connections'''
    bl_idname = "node.sv_monad_from_selected"
    bl_label = "Create monad from selected nodes (sub graph)"

    group_name: StringProperty(default="Monad")
    use_relinking: BoolProperty(default=True)

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

        # by appending, space_data is now different
        path = context.space_data.path
        path.append(monad)

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
        cls_ref = monad.update_cls()
        parent_node = ng.nodes.new(cls_ref.bl_idname)
        parent_node.select = False
        parent_node.location = average_of_selected(nodes)

        # remove nodes from parent_tree
        for n in nodes:
            ng.nodes.remove(n)

        # relink the new node
        if self.use_relinking:
            link_monad_instance(parent_node, re_links)

        # to make it pretty we pop and then append with the node
        path.pop()
        path.append(monad, node=parent_node)

        bpy.ops.node.view_all()
        return {'FINISHED'}


class SvMonadExpand(Operator):
    '''Expands monad into parent Layout will enforce peripheral connections'''
    bl_idname = "node.sv_monad_expand"
    bl_label = "Expand monad into parent tree/layout (ungroup)"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        tree_type = space_data.tree_type

        if not tree_type == 'SverchCustomTreeType':
            return

        node = context.active_node
        if node:
            return hasattr(node, 'monad')

    def get_io_nodes(self, ng):
        input_node, output_node = None, None
        for n in ng.nodes:
            if n.select:
                if n.bl_idname == 'SvGroupInputsNodeExp':
                    input_node = n
                elif n.bl_idname == 'SvGroupOutputsNodeExp':
                    output_node = n
        if not all([input_node, output_node]):
            print('failure. was inevitable')
            return None
        return input_node, output_node

    def execute(self, context):
        '''
        1. [x] get the node to expand, via context or as argument, verify that it is a monad instance
        2. [x] get the monad and append into it
        3. [x] select all and copy all
        4. [x] pop the path back
        5. [x] deselect all and paste
        6. [x] find the input/output nodes
        7.     now we have whole monad and monad instance
        8. [ ] replace the links one by one by parsing instance/input and then instance/output
        9. [ ] remove the instance, input, and output

        '''

        # 1 (make sure only the monad_instance node is selected)
        monad_instance_node = context.active_node
        bpy.ops.node.select_all(action='DESELECT')

        # 2
        monad = monad_instance_node.monad
        group_name = monad.name
        path = context.space_data.path
        path.append(monad)
        # 3
        #bpy.ops.node.select_all() does not work?
        for n in monad.nodes:
            n.select = True

        bpy.ops.node.clipboard_copy()

        # 4
        path.pop()
        # 5
        bpy.ops.node.clipboard_paste()
        # bpy.ops.node.select_all(action='DESELECT')

        # 6
        ng = context.space_data.edit_tree
        response = self.get_io_nodes(ng)
        if not response:
            return {'CANCELLED'}
        else:
            input_node, output_node = response

        # 7

        # 8
        for min_socket, in_socket in zip(monad_instance_node.inputs, input_node.outputs):
            # check that both are linked
            if min_socket.is_linked and in_socket.is_linked:
                # only one from link per input
                from_socket = min_socket.links[0].from_socket
                for link in in_socket.links:
                    to_socket = link.to_socket
                    ng.links.new(from_socket, to_socket)

        for on_socket, min_socket in zip(output_node.inputs, monad_instance_node.outputs):
            if on_socket.is_linked and min_socket.is_linked:
                from_socket = on_socket.links[0].from_socket
                for link in min_socket.links:
                    to_socket = link.to_socket
                    ng.links.new(from_socket, to_socket)
        # 9
        for node in (monad_instance_node, input_node, output_node):
            ng.nodes.remove(node)

        # order the nodes nicely...
        return {'FINISHED'}


class SvUpdateMonadClasses(Operator):
    '''Import update'''
    bl_idname = "node.sv_monad_class_update"
    bl_label = "Expand monad into parent tree/layout (ungroup)"

    @classmethod
    def poll(cls, context):
        for monad in context.blend_data.node_groups:
            if monad.bl_idname == "SverchGroupTreeType":
                cls_ref = getattr(bpy.types, monad.cls_bl_idname, None)
                if not cls_ref:
                    return True
        return False

    def execute(self, context):
        for monad in context.blend_data.node_groups:
            if monad.bl_idname == "SverchGroupTreeType":
                if not getattr(bpy.types, monad.cls_bl_idname, None):
                    try:
                        monad.update_cls()
                    except Exception as err:
                        print(err)
                        print("{} group class could not be created".format(monad.name))
        return {'FINISHED'}


class SvMonadMakeUnique(Operator):
    '''Duplicate monad into a unique monad'''
    bl_idname = "node.sv_monad_make_unique"
    bl_label = "Make Unique (Monad)"

    # partial copy of Blender's own NodeAddOperator

    use_transform: BoolProperty(
        name="Use Transform",
        description="Start transform operator after inserting the node",
        default=True)

    @staticmethod
    def store_mouse_cursor(context, event):
        space = context.space_data
        tree = space.edit_tree

        # convert mouse position to the View2D for later node placement
        if context.region.type == 'WINDOW':
            # convert mouse position to the View2D for later node placement
            space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        else:
            space.cursor_location = tree.view_center

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        tree_type = space_data.tree_type

        if not tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
            return

        node = context.active_node
        if node:
            return hasattr(node, 'monad')

    def execute(self, context):
        """
        - get associated monad from data.node_groups. (node.monad)
        - make a copy of that node_group. (obtain resulting name)
        - duplicate the node
        - replace the new node.monad with the copy

        """
        space = context.space_data
        tree = space.edit_tree

        try:
            node = monad_make_unique(context.active_node)
    
            # select only the new node
            for n in tree.nodes:
                n.select = False
    
            node.select = True
            tree.nodes.active = node
            node.location = space.cursor_location                


        except Exception as err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            print(sys.exc_info()[-1].tb_frame.f_code)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            return {'CANCELLED'}
        
        return {'FINISHED'}

    # Default invoke stores the mouse position to place the node correctly
    # and optionally invokes the transform operator
    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        result = self.execute(context)

        if self.use_transform and ('FINISHED' in result):
            # removes the node again if transform is canceled
            bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')

        return result


classes = [
    SvMoveSocketOpExp,
    SvRenameSocketOpExp,
    SvEditSocketOpExp,
    SvGroupEdit,
    SvMonadEnter,
    SvMonadExpand,
    SvMonadMakeUnique,
    SvMonadCreateFromSelected,
    SvMonadNewEmpty,
    SvTreePathParent,
    SvUpdateMonadClasses,
    SvNewSocketOpExp
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
