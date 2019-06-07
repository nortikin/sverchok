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
import logging

import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, StringProperty, FloatVectorProperty, PointerProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat


"""
Data structure:

Data stored in Material internal type of data of Blender:
Material - (type=ID)
  └ sv_props - (type=Group)
    ├ sv_created - (type=Bool)
    └ children_branch - (type=Collection)
      ├ nodes_data - (type=Collection)
      │ └ required_number - (type=Int)
      └ children - (type=Collection)
        └ mat - (type=ID)
"""

TEMP_MESH_NAME = 'SV_Temp_mesh'
TEMP_OBJECT_NAME = 'SV_Temp_object'
AGENT_NAME = 'Sverchok Agent'

log_rename = logging.getLogger('Suffix changes')
log_rename.setLevel(logging.WARNING)
log_delmat = logging.getLogger('Deleting material')
log_delmat.setLevel(logging.DEBUG)

def pick_blender_material(main_mat_name):
    # O(n)
    suffix = ''
    try:
        return bpy.data.materials[main_mat_name + suffix]
    except KeyError:
        mat = bpy.data.materials.new(main_mat_name + suffix)
        mat.use_nodes = True
        mat.sv_props.sv_created = True
        return mat


def update_material_list(parent_mat, length, suffix, to_update_children):
    # add or delete materials
    name = parent_mat.name
    children = parent_mat.sv_props.children_branch[suffix].children
    length -= 1
    if length == len(children):
        if not to_update_children:
            return
        for child in children:
            create_copy_shader_tree(parent_mat, child.mat)
    elif length > len(children):
        for i in range(length):
            try:
                create_copy_shader_tree(parent_mat, children[i].mat)
            except IndexError:
                full_name = name + suffix + '.{0:03}'.format(i + 1)
                child_mat = bpy.data.materials.new(full_name)
                item = children.add()
                item.mat = child_mat
                create_copy_shader_tree(parent_mat, child_mat)
    else:
        for i in range(length, len(children))[::-1]:
            bpy.data.materials.remove(children[i].mat)
            children.remove(i)


def set_values_to_agents(parent_mat, owner_id, suffix,  values):

    def set_values(agent, input_values):

        for sock, val in zip(agent.inputs, input_values):
            sock.default_value = val
        for sock, val in zip(agent.outputs, input_values):
            sock.default_value = val

    children = parent_mat.sv_props.children_branch[suffix].children
    print(owner_id)
    for node in parent_mat.node_tree.nodes:
        if del_suffix(node.name) == AGENT_NAME and node.owner == owner_id:
            print(True)
            set_values(node, values[0])
            break
    for child, val in zip(children, values[1:]):
        for node in child.mat.node_tree.nodes:
            if del_suffix(node.name) == AGENT_NAME and node.owner == owner_id:
                set_values(node, val)
                break


def create_copy_shader_node(node, tree):
    attrs = dir(node)
    new_node = tree.nodes.new(node.bl_idname)
    for attr in attrs:
        if attr[0] == '_':
            continue
        if hasattr(attr, '__call__'):
            continue
        try:
            setattr(new_node, attr, getattr(node, attr))
        except AttributeError:
            continue
    for i_in, input in enumerate(node.inputs):
        if hasattr(input, 'default_value'):
            if hasattr(input.default_value, '__iter__'):
                for i_val, val in enumerate(input.default_value):
                    new_node.inputs[i_in].default_value[i_val] = val
            else:
                new_node.inputs[i_in].default_value = input.default_value
    for i_out, output in enumerate(node.outputs):
        if hasattr(output, 'default_value'):
            if hasattr(output.default_value, '__iter__'):
                for i_val, val in enumerate(output.default_value):
                    new_node.outputs[i_out].default_value[i_val] = val
            else:
                new_node.outputs[i_out].default_value = output.default_value


def create_copy_shader_tree(from_mat, to_mat):

    def get_socket_index(sockets, socket):
        for i, sock in enumerate(sockets):
            if sock == socket:
                return i

    if not from_mat.use_nodes:
        return
    if not to_mat.use_nodes:
        to_mat.use_nodes = True

    from_tree = from_mat.node_tree
    to_tree = to_mat.node_tree

    for node in to_tree.nodes:
        to_tree.nodes.remove(node)
    for node in from_tree.nodes:
        create_copy_shader_node(node, to_tree)
    for link in from_tree.links:
        node_name_from = link.from_node.name
        node_name_to = link.to_node.name
        sock_i_from = get_socket_index(link.from_node.outputs, link.from_socket)
        sock_i_to = get_socket_index(link.to_node.inputs, link.to_socket)
        to_tree.links.new(to_tree.nodes[node_name_from].outputs[sock_i_from],
                          to_tree.nodes[node_name_to].inputs[sock_i_to])


def del_suffix(name):
    return name.rsplit('.')[0]


def match_input_lists(input, combine_object=False):
    # input [[[0], [1,2]], [[3,4], [5,6,7], [8]]]
    # output [[[0,0], [3,4]], [[1,2,2], [5,6,7]], [[1,2], [8,8]]]
    match_obj = zip(*match_long_repeat(input))
    output = []
    for obj in match_obj:
        output.append(match_long_repeat(obj))
    if combine_object:
        return output
    else:
        return [l for l in zip(*output)]


def is_material_viewport_shade_in_screen(context):
    spaces = [area.spaces[0] for area in context.screen.areas]
    view_3d_spaces = [space for space in spaces if space.type == 'VIEW_3D']
    for space in view_3d_spaces:
        if space.viewport_shade == 'MATERIAL':
            return True
    return False


class SvMaterialList(bpy.types.PropertyGroup):
    mat = PointerProperty(name='Material', type=bpy.types.Material)


class SvMaterialConnectorNodeData(bpy.types.PropertyGroup):
    required_number = IntProperty(name='Required number',
                                  description='required number of instance of main material '
                                              'for current Sverchok \"material connector\" node')


class SvMaterialChildrenBranches(bpy.types.PropertyGroup):
    nodes_data = bpy.props.CollectionProperty(name='Data of connector nodes',
                                             type=SvMaterialConnectorNodeData,
                                             description='Data related with current branches '
                                                         'per Sverchok material connector nodes')
    children = bpy.props.CollectionProperty(name='Children of main material',
                                            type=SvMaterialList,
                                            description='Different branches have different children')


class SvMaterialProps(bpy.types.PropertyGroup):
    sv_created = bpy.props.BoolProperty(name='SV created',
                                        default=False,
                                        description='Was material created by Sverchok')
    children_branch = bpy.props.CollectionProperty(name='Branch data', type=SvMaterialChildrenBranches)


class SvCreateAgent(bpy.types.Operator):

    bl_idname = "node.sv_create_agent"
    bl_label = "Create Agent"

    @staticmethod
    def zoom_to_shader_node(material, cycle_node):
        if TEMP_MESH_NAME not in bpy.data.meshes:
            empty_mesh = bpy.data.meshes.new(TEMP_MESH_NAME)
        else:
            empty_mesh = bpy.data.meshes[TEMP_MESH_NAME]
        if TEMP_OBJECT_NAME not in bpy.data.objects:
            temp_object = bpy.data.objects.new(TEMP_OBJECT_NAME, empty_mesh)
            bpy.context.scene.objects.link(temp_object)
        else:
            temp_object = bpy.data.objects[TEMP_OBJECT_NAME]
        bpy.context.scene.objects.active = temp_object
        temp_object.data.materials.clear()
        temp_object.data.materials.append(material)

        bpy.context.space_data.tree_type = 'ShaderNodeTree'
        cycle_node.select = True
        # node.select = True
        bpy.ops.node.view_selected()

    def execute(self, context):
        mat = context.node.main_material

        if not context.node.agent_node:
            cycle_node = mat.node_tree.nodes.new('SvMaterialAgent')
            cycle_node.owner = context.node.node_id
            context.node.agent_node = cycle_node

        context.node.agent_node.switch_lose_yourself(False)
        self.zoom_to_shader_node(mat, context.node.agent_node)

        return {'FINISHED'}


class SvJumpBackToNode(bpy.types.Operator):

    bl_idname = "node.sv_jump_back_to_node"
    bl_label = "Jump back to Sverchok cycle node"

    def execute(self, context):
        cycle_node = context.node
        if cycle_node.is_main_node_exist:
            bpy.context.space_data.tree_type = 'SverchCustomTreeType'
            sv, sv_tree_name, sv_node_name = cycle_node.owner.split('@')
            parent_tree = bpy.data.node_groups[sv_tree_name]
            bpy.context.space_data.node_tree = parent_tree
            parent_tree.nodes[sv_node_name].select = True
            bpy.ops.node.view_selected()

            bpy.data.objects.remove(bpy.data.objects[TEMP_OBJECT_NAME])
            parent_tree.nodes[sv_node_name].process(True)

        return {'FINISHED'}


class SvUpdateChildrenMaterials(bpy.types.Operator):

    bl_idname = "node.sv_update_children_materials"
    bl_label = "Update all materials which was copied from main material"

    def execute(self, context):
        agent = context.node
        if agent.is_main_node_exist:
            _, tree_name, node_name = agent.owner.split('@')
            sv_node = bpy.data.node_groups[tree_name].nodes[node_name]
            sv_node.process(True)
        return {'FINISHED'}


class SvMaterialAgent(bpy.types.NodeCustomGroup):

    bl_name = 'SvMaterialAgent'
    bl_label = AGENT_NAME

    owner = StringProperty(default='',
                           description="which node created agent")

    #custom_node_tree = bpy.props.PointerProperty(name='Sverchok shader node', type=bpy.types.NodeTree)

    to_update_children = bpy.props.BoolProperty(default=True, description='switch to real time updating of children')
    lose_yourself = bpy.props.BoolProperty(description='True if can not find owner node')

    def create_node_group(self):
        name = '.' + self.bl_name
        tree = bpy.data.node_groups.new(name, 'ShaderNodeTree')
        tree.outputs.new("NodeSocketColor", "Color")
        tree.outputs.new("NodeSocketFloat", "Value")
        tree.outputs.new("NodeSocketVector", "Vector")
        tree.inputs.new("NodeSocketColor", "Color")
        tree.inputs.new("NodeSocketFloat", "Value")
        tree.inputs.new("NodeSocketVector", "Vector")
        node_out = tree.nodes.new('NodeGroupOutput')
        node_in = tree.nodes.new('NodeGroupInput')
        tree.links.new(node_in.outputs[0], node_out.inputs[0])
        tree.links.new(node_in.outputs[1], node_out.inputs[1])
        tree.links.new(node_in.outputs[2], node_out.inputs[2])
        #self.custom_node_tree = tree
        return tree

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context):
        try:
            custom_node_group = bpy.data.node_groups['.' + self.bl_name]
        except KeyError:
            custom_node_group = self.create_node_group()
        self.node_tree = custom_node_group
        for sock in self.inputs:
            sock.hide = True

        #self.node_tree = bpy.data.node_groups['SvShaderNodeTree']
        #self.node_tree = bpy.data.node_groups.new('.' + self.bl_name, 'ShaderNodeTree')
        #self.create_sockets()
        #self.node_tree.nodes.new('NodeGroupOutput')

    # Draw the node components
    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        _, owner_tree_name, owner_node_name = self.owner.split('@')
        col.label(text=owner_tree_name, icon='NODETREE')
        col.label(text=owner_node_name, icon='RNA')
        col.operator('node.sv_jump_back_to_node', text='Edit in Sverchok', icon='FILE_PARENT')
        #if self.to_update_children:
        #    update_icon = 'OUTLINER_OB_LAMP'
        #else:
        #    update_icon = 'OUTLINER_DATA_LAMP'
        #col.prop(self, 'to_update_children', text='update changes', icon=update_icon)
        if not self.lose_yourself:
            row = layout.row()
            row.scale_y = 3
            row.operator('node.sv_update_children_materials', text='Update children', icon='FILE_REFRESH')

    def free(self):
        pass

    @property
    def is_main_node_exist(self):
        _, owner_tree_name, owner_node_name = self.owner.split('@')
        try:
            bpy.data.node_groups[owner_tree_name].nodes[owner_node_name]
            self.switch_lose_yourself(False)
            return True
        except KeyError:
            self.switch_lose_yourself(True)
            return False

    def switch_lose_yourself(self, is_lost):
        if is_lost:
            self.use_custom_color = True
            self.color = (1, 0, 0)
            self.lose_yourself = True
        else:
            self.use_custom_color = False
            self.lose_yourself = False


class SvMaterialConnector(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Something
    Well

    You can use number of points and lines as many as you wish
    """
    bl_idname = 'SvMaterialConnector'
    bl_label = 'Material connector'
    bl_icon = 'MATERIAL_DATA'

    """
    About renaming material:
    material - main material (parent)
    children - generated children of main material for current branch
    children_branch - groups of children
    nodes_data - data related with current branch per sv_node
    agent - material node of main material
    [i] - item in sequence related with current node
    
    There are 5 possible events during renaming:
    1. del material -> if there are no more owners of the material
                       and if material was created by Sverchok
        del children
        del material
    2. leave material -> remain 1 or more owners of the material
        del agent
        del nodes_data[i]
        if not nodes_data[current_branch]:
            del children
            del children_branch[i]
    3. rename material -> if there was only one owner
        rename children
    4. join to material -> if already there is material with such name
        if current not in children_branch
            new children_branch
        new nodes_data
    5. new material -> if there are not material with such name
        new children_branch
        new nodes_data
    
    there are no commands of creating of new agents and children
    because this part of work take place in process method
    in current implementation first two events were putted in deleter
    rest of them were putted in setter
    
    Something similar with renaming suffix (branch name)
    """

    def change_name_material(self, context):
        log_rename.debug('```___Start to handle material name changing___```')
        if not self.material:
            log_rename.debug('Material was not created yet - nothing to change')
            return
        if self.material.name == self.material_name:
            log_rename.debug('Name was not renamed - do nothing')
            self.process()
            return
        # try to connect to existen material
        try:
            log_rename.debug('try pick material from Blender with new name')
            existing_material = bpy.data.materials[self.material_name]
            log_rename.debug('material with such name already exists')
            del self.main_material
            log_rename.debug('last material was removed')
            self.main_material = existing_material
            log_rename.debug('memoriz new material')
        # create material if there is no with such name
        except KeyError:
            log_rename.debug('material with such name was not found in Blender db')
            if not self.get_number_material_users() and self.material.sv_props.sv_created:
                log_rename.debug('last material created by Sverchok and has no other users')
                self.main_material = self.material_name
                log_rename.debug('material was just renamed')
            else:
                log_rename.debug('last material was created by Blender UI or has other users')
                del self.main_material
                self.main_material = bpy.data.materials.new(self.material_name)
                log_rename.debug('new material was created')
                self.material.sv_props.sv_created = True
        log_rename.debug('Finish handle material name changing')
        self.process()

    def change_name_suffix(self, context):
        log_rename.debug('____````Starting change suffix````_____')
        if not self.material:
            log_rename.debug('Material was not created yet - cancel')
            return
        if self.previous_suffix == self.child_suffix:
            log_rename.debug('Suffix has the same name - cancel')
            return
        if self.child_suffix in self.material.sv_props.children_branch:
            log_rename.debug('Branch with new name already exist')
            log_rename.debug('Leave or del old branch')
            self.del_branch()
            log_rename.debug('Join to existing branch')
            self.join_branch()
        else:
            log_rename.debug('There is no branch with such name')
            if not self.get_number_branch_users():
                log_rename.debug('There is no other users of this branch')
                log_rename.debug('Rename branch')
                self.rename_branch()
            else:
                log_rename.debug('There is other users of this branch')
                log_rename.debug('Leave old branch')
                self.del_branch()
                log_rename.debug('Create new branch')
                self.new_branch()
        log_rename.debug('Finish suffix changing')
        self.previous_suffix = self.child_suffix
        self.process()

    def do_process(self, context):
        self.process()

    material_name = StringProperty(default='SvMaterial',
                                   update=change_name_material,
                                   description="sets which base name the object will use, "
                                   "use N-panel to pick alternative random names")

    child_suffix = StringProperty(default='_copy', update=change_name_suffix,
                                  description='Suffix of children materials')
    previous_suffix = StringProperty(default='_copy', description='For internal usage only')

    unit_color = FloatVectorProperty(update=do_process,
                                     name='Color',
                                     default=(.3, .3, .2, 1.0),
                                     size=4,
                                     min=0.0,
                                     max=1.0,
                                     subtype='COLOR')

    value = FloatProperty(update=do_process,
                          name='Value',
                          default=0.0)

    vector = FloatVectorProperty(size=3,
                                 default=(0, 0, 0),
                                 name='Vector',
                                 update=do_process)

    update_mode = BoolProperty(name='UPD', description='', default=True, update=do_process)
    update_opengl = BoolProperty(name='UPD', default=True, update=do_process,
                                 description='Does not update if there is screen in material shader node')

    material = PointerProperty(name='Material', type=bpy.types.Material)

    def init(self, context):
        super().init(context)
        try:
            self.main_material = bpy.data.materials[self.material_name]
        except KeyError:
            self.main_material = bpy.data.materials.new(self.material_name)
            self.material.sv_props.sv_created = True

    def copy(self, node):
        try:
            self.main_material = bpy.data.materials[self.material_name]
        except KeyError:
            self.main_material = bpy.data.materials.new(self.material_name)
            self.material.sv_props.sv_created = True

    def free(self):
        del self.main_material

    def sv_init(self, context):
        self.inputs.new('SvColorSocket', "Colors").prop_name = "unit_color"
        self.inputs.new('StringsSocket', 'Value').prop_name = "value"
        self.inputs.new('VerticesSocket', "Vector").prop_name = "vector"
        self.outputs.new('StringsSocket', 'Materials').prop_name = "update_mode"

    def draw_buttons(self, context, layout):
        view_icon = 'BLENDER' if self.update_mode else 'ERROR'
        upd_row = layout.row(align=True)
        upd_row.prop(self, 'update_mode', text='UPD', icon=view_icon, toggle=True)
        upd_row.prop(self, 'update_opengl', text='OpenGL', toggle=True)
        layout.row().prop(self, 'material_name', text="", icon='MATERIAL_DATA')
        if self.agent_node:
            button_name = 'Switch to material'
            button_icon = 'NODETREE'
        else:
            button_name = 'Create Agent'
            button_icon = 'ZOOMIN'
        layout.row().operator("node.sv_create_agent", text=button_name, icon=button_icon)

    def draw_buttons_ext(self, context, layout):
        view_icon = 'BLENDER' if self.update_mode else 'ERROR'
        upd_row = layout.row(align=True)
        upd_row.prop(self, 'update_mode', text='UPD', icon=view_icon, toggle=True)
        upd_row.prop(self, 'update_opengl', text='OpenGL', toggle=True)
        col_mat_name = layout.column()
        col_mat_name.label(text='Main material:', icon='MATERIAL_DATA')
        col_mat_name.prop(self, 'material_name', text="")
        col = layout.column(align=True)
        col.label(text='Suffix of child:', icon='COPY_ID')
        col.prop(self, 'child_suffix', text="")

    def process(self, upd_material_tree=False):
        if not self.material_name or not self.update_mode:
            return

        if any([sock.is_linked for sock in self.inputs]):
            matched_input = match_input_lists([socket_in.sv_get() for socket_in in self.inputs])
            flattened_input = [i for l in matched_input for i in l]
            total_material_number = len(flattened_input[0])
            rn_of_material = self.get_required_number(total_material_number)
            update_material_list(self.main_material, rn_of_material,
                                 self.child_suffix, upd_material_tree)
        else:
            flattened_input = [sock.sv_get()[0] for sock in self.inputs]

        if self.update_opengl:
            set_values_to_agents(self.main_material, self.node_id, self.child_suffix, list(zip(*flattened_input)))
        elif not is_material_viewport_shade_in_screen(bpy.context):
            set_values_to_agents(self.main_material, self.node_id, self.child_suffix, list(zip(*flattened_input)))

        self.outputs['Materials'].sv_set([[self.main_material] +
                        [child.mat for child in self.material.sv_props.children_branch[self.child_suffix].children]])

        #if self.agent_node:
        #    self.agent_node.node_tree.nodes['Group Output'].inputs[0].default_value = self.inputs[0].sv_get()[0][0]
        #    self.agent_node.node_tree.nodes['Group Output'].inputs[1].default_value = self.inputs[1].sv_get()[0][0]

        #    self.agent_node.outputs[0].default_value = self.inputs[0].sv_get()[0][0]
        #    self.agent_node.outputs[1].default_value = self.inputs[1].sv_get()[0][0]

    @property
    def node_id(self):
        return 'sv' + '@' + self.id_data.name + '@' + self.name

    @property
    def main_material(self):
        # returns material, creates if need
        # New instance of material
        if not self.material:
            self.material = pick_blender_material(self.material_name)
        return self.material

    @main_material.setter
    def main_material(self, new_material_or_name):
        # material was renamed
        if isinstance(new_material_or_name, str):
            new_name = new_material_or_name
            self.material.name = new_name
            # well it will be easier to regenerate children instead of renaming
            self.del_children()
        # new instance or existing material
        elif isinstance(new_material_or_name, bpy.types.Material):
            new_material = new_material_or_name
            self.material = new_material
            if self.child_suffix not in self.material.sv_props.children_branch:
                self.material.sv_props.children_branch.add().name = self.child_suffix
            self.material.sv_props.children_branch[self.child_suffix].nodes_data.add().name = self.node_id
        else:
            raise TypeError('This type: {} can not be assigned to material'.format(type(new_material_or_name)))

        self.material.use_nodes = True

    @main_material.deleter
    def main_material(self):
        log_delmat.debug('___```Start deleting material```___')
        i_nodes_data = self.material.sv_props.children_branch[self.child_suffix].nodes_data.find(self.node_id)
        self.material.sv_props.children_branch[self.child_suffix].nodes_data.remove(i_nodes_data)
        log_delmat.debug('Props node was removed from material db')
        # there are no other users of the material
        if not self.get_number_material_users() and self.material.sv_props.sv_created:
            log_delmat.debug('Material has "{}" users and '
                             'it was created by Sverchok'.format(self.get_number_material_users()))
            log_delmat.debug('Delete children')
            self.del_children()
            log_delmat.debug('Remove material')
            bpy.data.materials.remove(self.material)
            log_delmat.debug('Assign empty material to node')
            self.material = None
        # there are some users or material was not created by Sverchok
        else:
            log_delmat.debug('Material has "{}" users or'
                             ' was not created by Sverchok'.format(self.get_number_material_users()))
            log_delmat.debug('Delete Agent node')
            del self.agent_node
            if not self.get_number_branch_users():
                log_delmat.debug('Branch has no other users')
                log_delmat.debug('Delete children')
                self.del_children()
                i_branch = self.material.sv_props.children_branch.find(self.child_suffix)
                log_delmat.debug('Remove branch')
                self.material.sv_props.children_branch.remove(i_branch)

    def del_branch(self):
        i_node_props = self.material.sv_props.children_branch[self.previous_suffix].nodes_data.find(self.node_id)
        self.material.sv_props.children_branch[self.previous_suffix].nodes_data.remove(i_node_props)
        if not self.get_number_branch_users():
            self.del_children()
            i_branch = self.material.sv_props.children_branch.find(self.previous_suffix)
            self.material.sv_props.children_branch.remove(i_branch)

    def join_branch(self):
        self.material.sv_props.children_branch[self.child_suffix].nodes_data.add().name = self.node_id

    def rename_branch(self):
        self.del_children()
        self.material.sv_props.children_branch[self.previous_suffix].name = self.child_suffix

    def new_branch(self):
        branch = self.material.sv_props.children_branch.add()
        branch.name = self.child_suffix
        branch.nodes_data.add().name = self.node_id

    def get_number_material_users(self):
        # for current material
        correct = 0
        if self.material.name == self.material_name:
            correct = 1
        return len([node for node in self.get_all_connector_nodes()
                    if node.material_name == self.material.name]) - correct

    def get_number_branch_users(self):
        if self.previous_suffix not in self.main_material.sv_props.children_branch:
            return 0
        else:
            return len(self.main_material.sv_props.children_branch[self.previous_suffix].nodes_data)

    def del_children(self):
        for child in self.material.sv_props.children_branch[self.previous_suffix].children:
            bpy.data.materials.remove(child.mat)
        self.material.sv_props.children_branch[self.previous_suffix].children.clear()

    @property
    def agent_node(self):
        # Try find agent
        for node in self.main_material.node_tree.nodes:
            if node.bl_idname == 'SvMaterialAgent' and node.owner == self.node_id:
                return node
        return None

    @agent_node.setter
    def agent_node(self, agent):
        pass

    @agent_node.deleter
    def agent_node(self):
        agent = self.agent_node
        if agent:
            self.material.node_tree.nodes.remove(self.agent_node)

    def update_data_structure(self):
        connector_nodes = self.get_all_connector_nodes()
        for node in connector_nodes:
            if node.child_suffix not in node.main_material.sv_props.children_branch:
                node.main_material.sv_props.children_branch.add().name = node.child_suffix
            branch = node.main_material.sv_props.children_branch[node.child_suffix]
            if node.node_id not in branch.prop_nodes:
                branch.prop_nodes.add().name = node.node_id


        related_suffixes_with_current_mat = [node.child_suffix for node in connector_nodes if
                                             node.material_name == self.material_name]
        children_branch = self.main_material.sv_props.children_branch
        for suffix in related_suffixes_with_current_mat:
            if suffix not in children_branch:
                branch = children_branch.add()
                branch.name = suffix

        for i, branch in enumerate(children_branch):
            print(branch.name, '-', related_suffixes_with_current_mat)
            if branch.name not in related_suffixes_with_current_mat:
                children_branch.remove(i)

        if self.node_id not in children_branch[self.child_suffix].nodes_data:
            children_branch[self.child_suffix].nodes_data.add().name = self.node_id

    def get_required_number(self, current_request):
        mat_props = self.main_material.sv_props
        print('mat_props.children_branch[{}].nodes_data[{}].required_number'.format(self.child_suffix, self.node_id))
        mat_props.children_branch[self.child_suffix].nodes_data[self.node_id].required_number = current_request
        return max([nodes_data.required_number for
                    nodes_data in mat_props.children_branch[self.child_suffix].nodes_data])

    @staticmethod
    def get_all_connector_nodes():
        all_nodes = []
        for tree in bpy.data.node_groups:
            if tree.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
                for node in tree.nodes:
                    if node.bl_idname == 'SvMaterialConnector':
                        all_nodes.append(node)
        return all_nodes

    def has_material_other_agents(self):
        for node in self.main_material.node_tree.nodes:
            if node.bl_idname == 'SvMaterialAgent' and node.owner != self.node_id:
                return True
        return False

    def rename_children(self):
        self.main_material.sv_props.children_branch


classes = [SvMaterialList,
           SvMaterialConnectorNodeData,
           SvMaterialChildrenBranches,
           SvMaterialProps,
           SvCreateAgent,
           SvJumpBackToNode,
           SvUpdateChildrenMaterials,
           SvMaterialAgent,
           SvMaterialConnector]


def register():
    [bpy.utils.register_class(cl) for cl in classes]

    bpy.types.Material.sv_props = bpy.props.PointerProperty(type=SvMaterialProps)


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes]
