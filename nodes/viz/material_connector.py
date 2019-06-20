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
from random import randint

import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, StringProperty, FloatVectorProperty, PointerProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat, updateNode
from sverchok.utils.sv_viewer_utils import greek_alphabet
from sverchok.utils.logging import debug


TEMP_MESH_NAME = 'SV_Temp_mesh'
TEMP_OBJECT_NAME = 'SV_Temp_object'
AGENT_NAME = 'Sverchok Agent'


def pick_blender_material(main_mat_name):
    """
    Get material from Blender if material with such name exists or create new material
    :param main_mat_name: required name of material - str
    :return: material - bpy.types.Material
    """
    suffix = ''
    try:
        return bpy.data.materials[main_mat_name + suffix]
    except KeyError:
        mat = bpy.data.materials.new(main_mat_name + suffix)
        mat.use_nodes = True
        mat['sv_created'] = True
        return mat


def update_material_list(parent_mat, children, length, suffix, to_update_children):
    """
    change dimension of list of copies of main material,
    new materials creates with node tree equal to main material,
    works with created data structure in material object
    :param parent_mat: main material from which creates copies - bpy.types.Material
    :param length: required dimension of list - int
    :param suffix: for copies - str
    :param to_update_children: replace node tree in created copies of material to node tree of main material - bool
    :return: None
    """
    name = parent_mat.name
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


def set_values_to_agents(parent_mat, children, owner_id, suffix, values):
    """
    apply input values to agent node
    :param parent_mat: main material - bpy.types.Material
    :param owner_id: id of current Sverchok node for searching appropriate agent node - str
    :param suffix: name of current branch - str
    :param values: for applying to agent nodes
    :return: None
    """

    def set_values(agent, input_values):

        for sock, val in zip(agent.inputs, input_values):
            sock.default_value = val
        for sock, val in zip(agent.outputs, input_values):
            sock.default_value = val

    for node in parent_mat.node_tree.nodes:
        if node.bl_idname == 'SvMaterialAgent' and node.owner_id == owner_id:
            set_values(node, values[0])
            break
    for child, val in zip(children, values[1:]):
        for node in child.mat.node_tree.nodes:
            if node.bl_idname == 'SvMaterialAgent' and node.owner_id == owner_id:
                set_values(node, val)
                break


def create_copy_shader_node(node, tree):
    """
    create copy of any node to required node tree
    :param node: node for copy - bpy.types.Node
    :param tree: node tree where node should be copied - bpy.types.NodeTree
    :return: None
    """
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
    if node.bl_idname == 'SvMaterialAgent':
        for sock in new_node.inputs:
            sock.hide = True


def create_copy_shader_tree(from_mat, to_mat):
    """
    create copy of node tree from one material to another
    :param from_mat: material from which make copy - bpy.types.Material
    :param to_mat: material for receiving copy - bpy.types.Material
    :return: None
    """

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


def match_input_lists(input, combine_object=False):
    """
    matching and transposition list of lists
    input [[[0], [1,2]], [[3,4], [5,6,7], [8]]]
    output [[[0,0], [3,4]], [[1,2,2], [5,6,7]], [[1,2], [8,8]]]
    :param input: list of lists - list
    :param combine_object: if transposition is required then True - bool
    :return: modified list
    """
    match_obj = zip(*match_long_repeat(input))
    output = []
    for obj in match_obj:
        output.append(match_long_repeat(obj))
    if combine_object:
        return output
    else:
        return [l for l in zip(*output)]


def is_material_viewport_shade_in_screen(context):
    """
    search areas on screen, if there is area with 3D viewport editor
     that has Material node of viewport shading returns True
    :param context: bpy.context
    :return: bool
    """
    spaces = [area.spaces[0] for area in context.screen.areas]
    view_3d_spaces = [space for space in spaces if space.type == 'VIEW_3D']
    for space in view_3d_spaces:
        if space.viewport_shade == 'MATERIAL':
            return True
    return False


class SvMaterialList(bpy.types.PropertyGroup):
    # storage of child of main material
    mat = PointerProperty(name='Material', type=bpy.types.Material)


class SvCreateAgent(bpy.types.Operator):
    # initializing agent node and jump to it
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
        if bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.objects.active = temp_object
        temp_object.data.materials.clear()
        temp_object.data.materials.append(material)

        bpy.context.space_data.tree_type = 'ShaderNodeTree'
        cycle_node.select = True
        bpy.ops.node.view_selected()

    def execute(self, context):
        mat = context.node.main_material

        if not context.node.agent_node:
            cycle_node = mat.node_tree.nodes.new('SvMaterialAgent')
            cycle_node.owner_id = context.node.node_id
            cycle_node.owner_ng = context.node.id_data
            cycle_node.node_tree = context.node.shader_ng
            context.node.change_number_of_sockets(None)

        context.node.agent_node.switch_lose_yourself(False)
        self.zoom_to_shader_node(mat, context.node.agent_node)

        return {'FINISHED'}


class SvJumpBackToNode(bpy.types.Operator):
    # jump from shader editor to Sverhok editor
    bl_idname = "node.sv_jump_back_to_node"
    bl_label = "Jump back to Sverchok cycle node"

    def execute(self, context):
        cycle_node = context.node
        if cycle_node.is_main_node_exist:
            bpy.context.space_data.tree_type = 'SverchCustomTreeType'
            bpy.context.space_data.node_tree = cycle_node.owner_ng
            for node in cycle_node.owner_ng.nodes:
                if node.bl_idname == 'SvMaterialConnector' and node.node_id == cycle_node.owner_id:
                    node.select = True
                    sv_node = node
                else:
                    node.select = False
            bpy.ops.node.view_selected()

            bpy.data.objects.remove(bpy.data.objects[TEMP_OBJECT_NAME])
            if sv_node:
                sv_node.do_process_props(context, True)

        return {'FINISHED'}


class SvUpdateChildrenMaterials(bpy.types.Operator):
    # Apply changes in Shader editor to copies of main material
    bl_idname = "node.sv_update_children_materials"
    bl_label = "Update all materials which was copied from main material"

    def execute(self, context):
        agent = context.node
        if agent.is_main_node_exist:
            for node in agent.owner_ng.nodes:
                if node.bl_idname == 'SvMaterialConnector' and node.node_id == agent.owner_id:
                    node.do_process_props(context, True)
                    break
        return {'FINISHED'}


class SvCmNewMaterial(bpy.types.Operator):

    bl_idname = "node.sv_cm_new_material"
    bl_label = "Assign new material to node connector"

    def execute(self, context):
        context.node.material_name = context.node.get_next_name()
        return {'FINISHED'}


class SvCmPickMaterial(bpy.types.Operator):

    bl_idname = "node.sv_cm_pick_material"
    bl_label = "Pick existing materials"
    bl_property = "search_material"

    def get_available_materials(scene, context):
        occupied_names = set()
        for ng in bpy.data.node_groups:
            if ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
                for node in ng.nodes:
                    if node.bl_idname == 'SvMaterialConnector':
                        occupied_names.add(node.material_name)
                        occupied_names.add(node.material_name + node.child_suffix)
        unused_materials = []
        for mat in bpy.data.materials:
            if mat.name in occupied_names:
                continue
            try:
                name_without_suffix, _ = mat.name.rsplit('.', 1)
                if name_without_suffix in occupied_names:
                    continue
            except ValueError:
                pass
            unused_materials.append(mat)
        return [(mat.name, mat.name, '', "MATERIAL_DATA", i) for i, mat in enumerate(unused_materials)]

    search_material = bpy.props.EnumProperty(items=get_available_materials, name='search')
    node_path = StringProperty()

    def execute(self, context):
        tree_name, node_name = self.node_path.split('@')
        bpy.data.node_groups[tree_name].nodes[node_name].material_name = self.search_material
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


class SvMaterialAgent(bpy.types.NodeCustomGroup):
    # Node for shader editor which has connection with Sverchok node
    bl_name = 'SvMaterialAgent'
    bl_label = AGENT_NAME

    owner_id = StringProperty(default='', description="which node created agent")
    owner_ng = bpy.props.PointerProperty(name='Sverchok shader node', type=bpy.types.NodeTree)
    lose_yourself = bpy.props.BoolProperty(description='True if can not find owner node')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.operator('node.sv_jump_back_to_node', text='Edit in Sverchok', icon='FILE_PARENT')
        if not self.lose_yourself:
            row = layout.row()
            row.scale_y = 3
            row.operator('node.sv_update_children_materials', text='Update children', icon='FILE_REFRESH')

    @property
    def is_main_node_exist(self):
        # Check whether Sverchok node was lost
        # Should be rewritten after name independent approach
        for node in self.owner_ng.nodes:
            if node.bl_idname == 'SvMaterialConnector' and node.node_id == self.owner_id:
                self.switch_lose_yourself(False)
                return True
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
    agent - material node of main material

    There are 5 possible events during renaming:
    1. del material -> if there are no more owners of the material
                       and if material was created by Sverchok
        del children
        del material
    2. leave material -> remain 1 owner of the material (copy)
        del agent
    3. rename material -> if there was only one owner
        rename children
    4. join to material -> if already there is material with such name
    5. new material -> if there are not material with such name

    there are no commands of creating of new agents and children
    because this part of work take place in process method
    in current implementation first two events were putted in deleter
    rest of them were putted in setter
    """

    @staticmethod
    def draw_message(wm, context):
        wm.layout.label('Node has to have unique material name')
        wm.layout.label('Node with such material name already exists.')

    def change_name_material(self, context):
        # Logic of changing name of material
        debug('```___Start to handle material name changing___```')
        if not self.material_name:
            return
        if self.material and self.material.name == self.material_name:
            debug('Name was not renamed - do nothing')
            self.do_process(context)
            return
        if not self.is_valid_name:
            context.window_manager.popup_menu(self.draw_message, title="Repeated name", icon='INFO')
            debug('Name is node valid - auto renaming')
            self.material_name = ''
            del self.main_material
            return
        # try to connect to existen material
        try:
            debug('try pick material from Blender with new name')
            existing_material = bpy.data.materials[self.material_name]
            debug('material with such name already exists')
            if self.material:
                del self.main_material
            debug('last material was removed')
            self.main_material = existing_material
            debug('memoriz new material')
        # create material if there is no with such name
        except KeyError:
            debug('material with such name was not found in Blender db')
            if not self.material:
                debug('material was not created yet')
                self.main_material = bpy.data.materials.new(self.material_name)
                debug('new material was created')
                self.material['sv_created'] = True
            elif not self.get_number_material_users() and 'sv_created' in self.material.keys():
                debug('last material created by Sverchok and has not other users')
                self.main_material = self.material_name
                debug('material was just renamed')
            else:
                debug('last material was created by Blender UI or has other users')
                del self.main_material
                self.main_material = bpy.data.materials.new(self.material_name)
                debug('new material was created')
                self.material['sv_created'] = True
        debug('Finish handle material name changing')
        self.do_process(context)

    def change_name_suffix(self, context):
        # Logic of changing name of suffix
        debug('____````Starting change suffix````_____')
        if not self.material:
            debug('Material was not created yet - cancel')
            return
        self.del_children()
        debug('Finish suffix changing')
        self.do_process(context)

    def change_number_of_sockets(self, context):
        links = [(link.from_socket, link.to_socket.name) for sock in self.inputs for link in sock.links]
        self.inputs.clear()
        for i in range(self.number_color_parameters):
            self.inputs.new('SvColorSocket', "Color{}".format(i)).prop_name = "color{}".format(i)
        for i in range(self.number_value_parameters):
            self.inputs.new('StringsSocket', "Value{}".format(i)).prop_name = "value{}".format(i)
        for i in range(self.number_vector_parameters):
            self.inputs.new('VerticesSocket', "Vector".format(i)).prop_name = "vector{}".format(i)
        for sock1, sock_name2 in links:
            if sock_name2 in self.inputs:
                self.id_data.links.new(sock1, self.inputs[sock_name2])

        agent = self.agent_node
        if agent:
            links = [(link.from_socket.name, link.to_socket) for sock in agent.outputs for link in sock.links]
            # agent.outputs.clear()

            self.shader_ng.outputs.clear()
            self.shader_ng.inputs.clear()
            for i in range(self.number_color_parameters):
                self.shader_ng.outputs.new("NodeSocketColor", "Color{}".format(i))
                self.shader_ng.inputs.new("NodeSocketColor", "Color{}".format(i))
            for i in range(self.number_value_parameters):
                self.shader_ng.outputs.new("NodeSocketFloat", "Value{}".format(i))
                self.shader_ng.inputs.new("NodeSocketFloat", "Value{}".format(i))
            for i in range(self.number_vector_parameters):
                self.shader_ng.outputs.new("NodeSocketVector", "Vector{}".format(i))
                self.shader_ng.inputs.new("NodeSocketVector", "Vector{}".format(i))
            for sock1, sock2 in zip(self.shader_ng.nodes['Group Input'].outputs,
                                    self.shader_ng.nodes['Group Output'].inputs):
                self.shader_ng.links.new(sock1, sock2)

            for input_sock in agent.inputs:
                input_sock.hide = True
            for sock1_name, sock2 in links:
                if sock1_name in agent.outputs:
                    agent.id_data.links.new(agent.outputs[sock1_name], sock2)
            self.do_process_props(context, upd_material_tree=True)

    def do_process_props(self, context, upd_material_tree=False):
        """
        Calling process method with parameters.
        :param upd_material_tree: Should be switched on when main shader was changed nad updating children
        """
        self.update_materials_tree = upd_material_tree
        self.do_process(context)
        self.update_materials_tree = False

    def do_process(self, context):
        # Unfortunately current update system does not update node if there are no any links to it.
        # It is not good approach of making update of node in bypass of update system but
        # I don't see now another solution.
        if True not in [link.is_linked for link in list(self.inputs) + list(self.outputs)]:
            self.process()
        else:
            updateNode(self, context)

    material_name = StringProperty(default='', update=change_name_material, description="sets which base name the object will use, "
                                               "use N-panel to pick alternative random names")
    child_suffix = StringProperty(default='_copy', update=change_name_suffix,
                                  description='Suffix of children materials')
    n_id = StringProperty()

    for i in range(5):
        color_name = 'color{}'.format(i)
        value_name = 'value{}'.format(i)
        vector_name = 'vector{}'.format(i)
        locals()[color_name] = FloatVectorProperty(update=do_process, name='Color', default=(.3, .3, .2, 1.0),
                                                   size=4, min=0.0, max=1.0, subtype='COLOR')
        locals()[value_name] = FloatProperty(update=do_process, name='Value', default=0.0)
        locals()[vector_name] = FloatVectorProperty(size=3, default=(0, 0, 0), name='Vector', update=do_process)

    update_materials_tree = BoolProperty(name='Update shader node tree',
                                         description="Should be switched on when main shader was changed")
    update_mode = BoolProperty(name='UPD', description='', default=True, update=do_process)
    update_opengl = BoolProperty(name='UPD', default=True, update=do_process,
                                 description='Does not update if there is screen in material shader node')

    material = PointerProperty(name='Material', type=bpy.types.Material)
    shader_node_group = PointerProperty(name='Shader node group', type=bpy.types.NodeTree)
    children = bpy.props.CollectionProperty(type=SvMaterialList)

    number_color_parameters = IntProperty(name='Color', default=1, min=0, max=5, update=change_number_of_sockets)
    number_value_parameters = IntProperty(name='Value', default=1, min=0, max=5, update=change_number_of_sockets)
    number_vector_parameters = IntProperty(name='Vector', default=1, min=0, max=5, update=change_number_of_sockets)

    def copy(self, node):
        self.material_name = ''
        self.n_id = ''
        self.material = None
        self.shader_node_group = None
        self.children.clear()

    def free(self):
        # We have to call this method for keeping Blender database in actual condition
        del self.main_material

    def sv_init(self, context):
        self.use_custom_color = True
        self.inputs.new('SvColorSocket', "Colors").prop_name = "color0"
        self.inputs.new('StringsSocket', 'Value').prop_name = "value0"
        self.inputs.new('VerticesSocket', "Vector").prop_name = "vector0"
        self.outputs.new('StringsSocket', 'Materials').prop_name = "update_mode"

    def draw_buttons(self, context, layout):
        view_icon = 'BLENDER' if self.update_mode else 'ERROR'
        upd_row = layout.row(align=True)
        upd_row.prop(self, 'update_mode', text='UPD', icon=view_icon, toggle=True)
        upd_row.prop(self, 'update_opengl', text='OpenGL', toggle=True)
        if self.material_name:
            row_name = layout.row(align=True)
            row_name.prop(self, 'material_name', text="", icon='MATERIAL_DATA')
            search = row_name.operator('node.sv_cm_pick_material', text='', icon='COLLAPSEMENU')
            search.node_path = self.id_data.name + '@' + self.name
            if self.agent_node:
                button_name = 'Switch to material'
                button_icon = 'NODETREE'
            else:
                button_name = 'Create Agent'
                button_icon = 'ZOOMIN'
            layout.row().operator("node.sv_create_agent", text=button_name, icon=button_icon)
        else:
            row = layout.row(align=True)
            row.operator('node.sv_cm_new_material', text='New', icon='ZOOMIN')
            search = row.operator('node.sv_cm_pick_material', text='Pick', icon='COLLAPSEMENU')
            search.node_path = self.id_data.name + '@' + self.name

    def draw_buttons_ext(self, context, layout):
        view_icon = 'BLENDER' if self.update_mode else 'ERROR'
        upd_row = layout.row(align=True)
        upd_row.prop(self, 'update_mode', text='UPD', icon=view_icon, toggle=True)
        upd_row.prop(self, 'update_opengl', text='OpenGL', toggle=True)
        if self.material_name:
            col_mat_name = layout.column()
            col_mat_name.label(text='Main material:', icon='MATERIAL_DATA')
            col_mat_name.prop(self, 'material_name', text="")
            col = layout.column(align=True)
            col.label(text='Suffix of child:', icon='COPY_ID')
            col.prop(self, 'child_suffix', text="")

        col_num = layout.column(align=True)
        col_num.label(text='add/remove sockets', icon='SCULPTMODE_HLT')
        row_num = col_num.row(align=True)
        row_num.prop(self, 'number_color_parameters')
        row_num.prop(self, 'number_value_parameters')
        row_num.prop(self, 'number_vector_parameters')

    def process(self):
        if not self.material_name or not self.update_mode:
            return

        if any([sock.is_linked for sock in self.inputs]):
            matched_input = match_input_lists([socket_in.sv_get() for socket_in in self.inputs])
            flattened_input = [i for l in matched_input for i in l]
            total_material_number = len(flattened_input[0])
            update_material_list(self.main_material, self.children, total_material_number,
                                 self.child_suffix, self.update_materials_tree)
        else:
            flattened_input = [sock.sv_get()[0] for sock in self.inputs]

        if self.inputs:
            if self.update_opengl:
                set_values_to_agents(self.main_material, self.children, self.node_id,
                                     self.child_suffix, list(zip(*flattened_input)))
            elif not is_material_viewport_shade_in_screen(bpy.context):
                set_values_to_agents(self.main_material, self.children, self.node_id,
                                     self.child_suffix, list(zip(*flattened_input)))

        self.outputs['Materials'].sv_set([[self.main_material] + [child.mat for child in self.children]])

    @staticmethod
    def get_next_name():
        gai = bpy.context.scene.SvGreekAlphabet_index
        name = greek_alphabet[gai]
        bpy.context.scene.SvGreekAlphabet_index += 1
        if name == 'Omega':
            return 'Sv{0:05}'.format(randint(0, 99999))
        else:
            return 'Sv' + name

    @property
    def is_valid_name(self):
        names = [node.material_name for node in self.get_all_connector_nodes(include_current=False)]
        return False if self.material_name in names else True

    @property
    def shader_ng(self):
        if not self.shader_node_group:
            tree = bpy.data.node_groups.new('.' + 'SvShaderGroup', 'ShaderNodeTree')
            tree.nodes.new('NodeGroupOutput')
            tree.nodes.new('NodeGroupInput')
            self.shader_node_group = tree
        return self.shader_node_group

    @property
    def main_material(self):
        # Returns material, creates or pick material from Blender db if it was not attached to the node before
        if not self.material:
            self.material = pick_blender_material(self.material_name)
        return self.material

    @main_material.setter
    def main_material(self, new_material_or_name):
        """
        join new material to node or rename existing material, update db of Blender
        :param new_material_or_name: if input is string the name material will be renamed only
                                    (bpy.types.Material or str)
        :return: None
        """
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
        else:
            raise TypeError('This type: {} can not be assigned to material'.format(type(new_material_or_name)))

        self.material.use_nodes = True

    @main_material.deleter
    def main_material(self):
        # Delete attached material or leave it, update db of Blender
        debug('___```Start deleting material```___')
        debug('Remove children')
        self.del_children()
        del self.agent_node
        if self.material and 'sv_created' in self.material.keys() and not self.get_number_material_users():
            debug('Material was created by Sverchok and has not another user')
            debug('Remove material')
            bpy.data.materials.remove(self.material)
            self.material = None

    def get_number_material_users(self):
        """
        Search other connector nodes and check if they have the same name of main material
        :return: number of connector nodes with the same name of main material of current node
        """
        if not self.material:
            return 0
        correct = 0
        if self.material.name == self.material_name:
            correct = 1
        return len([node for node in self.get_all_connector_nodes()
                    if node.material_name == self.material.name]) - correct

    def del_children(self):
        # Delete all children of current node
        for child in self.children:
            bpy.data.materials.remove(child.mat)
        self.children.clear()

    @property
    def agent_node(self):
        # Return agent node or None if agent node was not created yet
        if self.material:
            for node in self.material.node_tree.nodes:
                if node.bl_idname == 'SvMaterialAgent' and node.owner_id == self.node_id:
                    return node
        return None

    @agent_node.deleter
    def agent_node(self):
        # Delete agent node, in instance if sv node is deleting
        agent = self.agent_node
        if agent:
            self.material.node_tree.nodes.remove(self.agent_node)

    def get_all_connector_nodes(self, include_current=True):
        # Get all connector nodes from all layouts of Sverchok
        all_nodes = []
        for tree in bpy.data.node_groups:
            if tree.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
                for node in tree.nodes:
                    if node.bl_idname == 'SvMaterialConnector':
                        if include_current:
                            all_nodes.append(node)
                        else:
                            if node.node_id != self.node_id:
                                all_nodes.append(node)
        return all_nodes


classes = [SvMaterialList,
           SvCreateAgent,
           SvJumpBackToNode,
           SvUpdateChildrenMaterials,
           SvCmNewMaterial,
           SvCmPickMaterial,
           SvMaterialAgent,
           SvMaterialConnector]


def register():
    [bpy.utils.register_class(cl) for cl in classes]


def unregister():
    [bpy.utils.unregister_class(cl) for cl in classes]
