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

from typing import List, Tuple
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.mesh_functions import meshes_py, join_meshes, meshes_np, to_elements
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from sverchok.data_structure import updateNode
from sverchok.utils.vectorize import vectorize, devectorize, SvVerts, SvEdges, SvPolys
from sverchok.utils.mesh_functions import apply_matrix_to_vertices_py
from sverchok.utils.modules.matrix_utils import matrix_apply_np
from mathutils import Matrix
import numpy as np

class SocketInfo:
    def __init__(self, socket_type, sverchok_socket_type, socket_name, pos, valid, is_linked, socket_links, ):
        self.socket_type = socket_type
        self.sverchok_socket_type = sverchok_socket_type
        self.socket_name = socket_name
        self.pos = pos
        self.valid = valid
        self.is_linked = is_linked
        self.links = socket_links[:]
        pass
    
class SocketsGroup:
    def __init__(self, group_idx, names, default=None):
        # Чтобы получать доступ через квадратные скобки
        self.attr_by_index = names
        self.group_idx = group_idx
        for name in names:
            setattr(self, name, SocketInfo(name, None, None, None, False, False, []) )
        return
    
    def __getitem__(self, index):
        attr_name = self.attr_by_index[index]
        return getattr(self, attr_name)
    
    def __setitem__(self, index, value):
        attr_name = self.attr_by_index[index]
        setattr(self, attr_name, value)

def mesh_join(vertices, edges, polygons):
    is_py_input = isinstance(vertices[0], (list, tuple))
    meshes = (meshes_py if is_py_input else meshes_np)(vertices, edges, polygons)
    meshes = join_meshes(meshes)
    out_vertices, out_edges, out_polygons = to_elements(meshes)

    return out_vertices, out_edges, out_polygons


def apply_matrices(
        *,
        vertices: SvVerts,
        edges: SvEdges,
        polygons: SvPolys,
        matrices: List[Matrix],
        implementation_mode: str = 'Python') -> Tuple[SvVerts, SvEdges, SvPolys]:
    """several matrices can be applied to a mesh
    in this case each matrix will populate geometry inside object"""

    if not matrices or (vertices is None or not len(vertices)):
        return vertices, edges, polygons

    if implementation_mode == 'NumPy':
        vertices = np.asarray(vertices, dtype=np.float32)

    _apply_matrices = matrix_apply_np if isinstance(vertices, np.ndarray) else apply_matrix_to_vertices_py

    sub_vertices = []
    sub_edges = [edges] * len(matrices) if edges else None
    sub_polygons = [polygons] * len(matrices) if polygons else None
    for matrix in matrices:
        sub_vertices.append(_apply_matrices(vertices, matrix))

    out_vertices, out_edges, out_polygons = join_meshes(vertices=sub_vertices, edges=sub_edges, polygons=sub_polygons)
    return out_vertices, out_edges, out_polygons


def apply_matrix(
        *,
        vertices: SvVerts,
        edges: SvEdges,
        polygons: SvPolys,
        matrix: Matrix,
        implementation_mode: str = 'Python') -> Tuple[SvVerts, SvEdges, SvPolys]:
    """several matrices can be applied to a mesh
    in this case each matrix will populate geometry inside object"""

    if not matrix or (vertices is None or not len(vertices)):
        return vertices, edges, polygons

    if implementation_mode == 'NumPy':
        vertices = np.asarray(vertices, dtype=np.float32)

    _apply_matrices = matrix_apply_np if isinstance(vertices, np.ndarray) else apply_matrix_to_vertices_py

    new_vertices = _apply_matrices(vertices, matrix)

    return new_vertices, edges, polygons

class SvMeshJoinNodeMK3( ModifierNode, SverchCustomTreeNode, bpy.types.Node, 
                        #SvRecursiveNode,
                        ):
    '''
    Triggers: Join Meshes
    Tooltip: Join many mesh into on mesh object
    '''

    bl_idname = 'SvMeshJoinNodeMK3'
    bl_label = 'Mesh Join'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MESH_JOIN'

    groups_offset = 1 # Количество обязательных сокетов. Их надо пропустить
    group_struct = {'vertices':{'sverchok_socket_type': 'SvVerticesSocket'}, 'edges':{'sverchok_socket_type':'SvStringsSocket'}, 'polygons':{'sverchok_socket_type':'SvStringsSocket',}, 'matrices': {'sverchok_socket_type': 'SvMatrixSocket', }} # список имён сокетов в группе. Последовательность важна. Если сокеты встретятся в другой последовательности, то это будет считаться ошибкой

    mesh_join: bpy.props.BoolProperty(name='Join', default=True, update=updateNode, description="If set, then this node will join output meshes into one mesh")

    def update_do_last_group_empty(self, context):
        self.sv_update()
        updateNode(self, context)
        return

    do_last_group_empty: bpy.props.BoolProperty(
        name='Last Group Empty',
        default=True,
        update=update_do_last_group_empty,
        description="If set then add empty group after last element"
    )

    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    implementation_mode: bpy.props.EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method (See Documentation)',
        default="Python", update=updateNode)

    def draw_vertices_in_socket(self, socket, context, layout):
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}")
        else:
            layout.label(text=f'{socket.label}')
        pass

    def draw_buttons(self, context, layout):
        root = layout.box().column(align=True)
        # root.use_property_split = True
        # root.use_property_decorate = False
        root.prop(self, 'mesh_join')
        root.prop(self, 'do_last_group_empty')
        root.label(text='Implementation:')
        root.row(align=True).prop(self, 'implementation_mode', expand=True)

    def sv_init(self, context):
        groups = self.inputs.new('SvStringsSocket', 'groups')
        groups.label = 'Groups'
        verts1 = self.inputs.new('SvVerticesSocket', 'vertices1')
        verts1.is_mandatory = True
        verts1.nesting_level = 3
        verts1.default_mode = 'NONE'
        verts1.label = 'Vertices 1'
        verts1.custom_draw = 'draw_vertices_in_socket'

        pols1 = self.inputs.new('SvStringsSocket', 'polygons1')
        pols1.nesting_level = 3
        pols1.default_mode = 'EMPTY_LIST'
        pols1.label = 'Polygons'

        # TODO: позже вернуь перед polygons
        edges1 = self.inputs.new('SvStringsSocket', 'edges1')
        edges1.nesting_level = 3
        edges1.default_mode = 'EMPTY_LIST'
        edges1.label = 'Edges'

        edges2 = self.inputs.new('SvStringsSocket', 'wrong_socket2')
        edges2.nesting_level = 3
        edges2.default_mode = 'EMPTY_LIST'
        edges2.label = 'Wrong Socket2'

        edges2 = self.inputs.new('SvStringsSocket', 'edges2')
        edges2.nesting_level = 3
        edges2.default_mode = 'EMPTY_LIST'
        edges2.label = 'Edges [2]'

        edges5 = self.inputs.new('SvStringsSocket', 'edges5')
        edges5.nesting_level = 3
        edges5.default_mode = 'EMPTY_LIST'
        edges5.label = 'Edges [5]'

        edges2 = self.inputs.new('SvStringsSocket', 'wrong_socket')
        edges2.nesting_level = 3
        edges2.default_mode = 'EMPTY_LIST'
        edges2.label = 'Wrong Socket'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs['vertices'].label = 'Vertices'
        self.outputs.new('SvStringsSocket', 'edges')
        self.outputs['edges'].label = 'Edges'
        self.outputs.new('SvStringsSocket', 'polygons')
        self.outputs['polygons'].label = 'Polygons'
        self.outputs.new('SvMatrixSocket', 'matrices')
        self.outputs['matrices'].label = 'Matrices'

        return

    def reload_sockets_data(self, groups_offset, self_inputs, group_names):
        # Загрузить структуру сокетов
        elems = dict()
        invalid_elems = []
        valid_pos = groups_offset
        for I in range(groups_offset, len(self_inputs)):
            socket_I = self_inputs[I]
            socket_group_name = None
            for group_name in group_names:
                if socket_I.name.startswith(group_name):
                    socket_group_name = group_name
                    break
            # Если имя сокета не начинается с имени группы, то такой сокет не валиден:
            if socket_group_name is None:
                invalid_elems.append(socket_I.name)
                continue
            
            group_idx = socket_I.name.replace(socket_group_name, "")
            # Если имя сокета не заканчивается числом (это должен быть индекс), то такой сокет не валиден:
            if group_idx.isnumeric()==False:
                invalid_elems.append(socket_I.name)
                continue
            else:
                group_idx = int(group_idx)
                if group_idx not in elems:
                    elems[group_idx] = SocketsGroup(group_idx, group_names)
                valid_pos = (group_idx*len(group_names)+group_names.index(socket_group_name)+groups_offset)==I
                # Проверить, что текущий сокет находится в нужной позиции (с учётом отступа обязательного сокета)
                # Чисто теоретически может случиться так, что среди мешанины неправильных сокетов встретится сокет
                # на корректной позиции, то перед его позицией должна встретиться неправильная позиция.
                # В дальнейшем такая первая неправильная позиция должна будет считаться исходной для удаления
                # следующих сокетов и их пересоздания
                socket_links = []
                for link in socket_I.links:
                    socket_links.append(dict(from_node_name=link.from_node.name, from_socket_name=link.from_socket.name))
                socketInfo = SocketInfo(socket_group_name, self.group_struct[socket_group_name]['sverchok_socket_type'], socket_I.name, I, valid_pos, socket_I.is_linked, socket_links)
                setattr(elems[group_idx], socket_group_name, socketInfo)
                continue
        return elems, invalid_elems

    def sv_update(self):
        # adjust_sockets

        group_names = tuple(self.group_struct)
        len_group_names = len(group_names)
        elems, invalid_elems = self.reload_sockets_data(self.groups_offset, self.inputs, group_names)

        if invalid_elems:
            while(invalid_elems):
                socket_name = invalid_elems.pop()
                socket_to_remove = self.inputs[socket_name]
                for link in list(socket_to_remove.links):
                    self.id_data.links.remove(link)
                self.inputs.remove( socket_to_remove )
            
            # Ещё раз проверить корректность сокетов после удаления невалидных сокетов:
            elems, invalid_elems = self.reload_sockets_data(self.groups_offset, self.inputs, group_names)
            if invalid_elems:
                raise RuntimeError(f"Wrong sockets: {invalid_elems}")
        
        # Отсортировать группы сокетов и упаковать их индексы:
        elems = {
            new_index: elems[old_key]
            for new_index, old_key in enumerate(sorted(elems))
        }

        # Проверить, если последния группа, с индексом больше 0, не подключена, то отметить её для удаления
        for I in range(len(elems)-1, 0, -1):
            elems_I = elems[I]
            elems_I1 = elems[I-1]
            
            if (all( [getattr(elems_I, name).is_linked==False for name in group_names]) and
                all( [getattr(elems_I1, name).is_linked==False for name in group_names])):
                del elems[I]
                continue
            else:
                break
            pass

        # Проверить, если к последней группе подключен хоть один link, то добавить после последней группы ещё одну группу
        if elems:
            elems_last = elems[len(elems)-1]
            if self.do_last_group_empty==True and any( [getattr(elems_last, name).is_linked==True for name in group_names])==True:
                max_idx = len(elems)
                elems[max_idx] = SocketsGroup(max_idx, group_names)
                elems[max_idx].vertices.valid = True
                elems[max_idx].edges.valid = True
                elems[max_idx].polygons.valid = True
            elif self.do_last_group_empty==False and any( [getattr(elems_last, name).is_linked==True for name in group_names])==False and len(elems)>1:
                del elems[len(elems)-1]
            pass


        # Просканировать сокеты на предмет корректности позиций и удалить всех, кто ниже первой некорректной позиции:
        min_invalid_pos = None
        for I in range(self.groups_offset, len(self.inputs)):
            group_idx, elem_idx = divmod(I-self.groups_offset, len_group_names)
            group_name = group_names[elem_idx]
            if group_idx not in elems:
                break
            elem_I = elems[group_idx][elem_idx]
            if elem_I is None or elem_I.valid==False:
                min_invalid_pos = I
                break
            pass

        # Если минмальный индекс некорректной позиции не найден (все сокеты корректно находятся на своих местах), 
        # то определить максимальный индекс входных сокетов, чтобы стереть лишние группы.
        if min_invalid_pos is None:
            min_invalid_pos = self.groups_offset + len(elems)*len_group_names

        # Удалить все входящие сокеты включая эту позицию
        if min_invalid_pos<=0:
            pass
        else:
            while(len(self.inputs)>=min_invalid_pos+1):
                socket_to_remove = self.inputs[-1]
                for link in list(socket_to_remove.links):
                    self.id_data.links.remove(link)
                self.inputs.remove( socket_to_remove )
                pass

            # тут создать недостающие сокеты и восстановить соединения для перемещаемых сокетов:
            for I in range(len(elems)*len_group_names):
                group_idx, elem_idx = divmod(I, len_group_names)
                elem_I = elems[group_idx][elem_idx]
                
                sverchok_socket_type = self.group_struct[elem_I.socket_type]['sverchok_socket_type']
                if elem_I.socket_type=='vertices':
                    socket_label = f'{elem_I.socket_type.capitalize()}[{group_idx}]'
                else:
                    socket_label = f'{elem_I.socket_type.capitalize()}'
                socket_name = f'{elem_I.socket_type}{group_idx}'
                if socket_name in self.inputs:
                    socket = self.inputs[socket_name]
                else:
                    socket = self.inputs.new(sverchok_socket_type, socket_name)
                
                if elem_I.socket_type=='vertices':
                    socket.custom_draw = 'draw_vertices_in_socket'
                else:
                    socket.custom_draw = ''
                socket.label = socket_label

                # Восстановить сокеты
                if socket.is_linked==False:
                    tree = self.id_data
                    for link in elem_I.links:
                        from_node_name = link['from_node_name']
                        from_socket_name = link['from_socket_name']
                        if from_node_name in tree.nodes and from_socket_name in tree.nodes[ from_node_name ].outputs:
                            from_socket = tree.nodes[ from_node_name ].outputs[ from_socket_name ]
                            new_link = tree.links.new(socket, from_socket)
                        pass
                pass
            pass
        # 1. Прочитать сокеты и запомнить какие 
        return

    def migrate_from(self, old_node):
        verts = self.inputs['vertices1']
        verts.is_mandatory = True
        verts.default_mode = 'NONE'

        edges = self.inputs['edges1']
        edges.nesting_level = 3
        edges.default_mode = 'EMPTY_LIST'

        pols = self.inputs['polygons1']
        pols.nesting_level = 3
        pols.default_mode = 'EMPTY_LIST'

    # def process_data(self, params):
    #     #return mesh_join(*params)
    #     return [[],[],[],[]]

    def process(self):
        
        group_names = tuple(self.group_struct)
        elems, invalid_elems = self.reload_sockets_data(self.groups_offset, self.inputs, group_names)
        len_group_names = len(group_names)
        
        if invalid_elems:
            pass
        else:
            out_vertices, out_edges, out_polygons = [], [], []
            for I, elem_I in elems.items():
                verts_I = elem_I.vertices
                edges_I = elem_I.edges
                polygons_I = elem_I.polygons
                matrices_I = elem_I.matrices
                
                if verts_I.is_linked==False:
                    # Пропустить
                    pass
                else:
                    group_vertices  = self.inputs[verts_I.socket_name   ].sv_get(default=[], deepcopy=False)
                    group_edges     = self.inputs[edges_I.socket_name   ].sv_get(default=[], deepcopy=False)
                    group_polygons  = self.inputs[polygons_I.socket_name].sv_get(default=[], deepcopy=False)
                    group_matrices  = self.inputs[matrices_I.socket_name].sv_get(default=[], deepcopy=False)

                    # fixing matrices nesting level if necessary, this is for back capability, can be removed later on
                    if group_matrices:
                        is_flat_list = not isinstance(group_matrices[0], (list, tuple))
                        if is_flat_list:
                            _apply_matrix = vectorize(apply_matrix, match_mode='REPEAT')
                            group_out_vertices, group_out_edges, group_out_polygons = _apply_matrix(
                                vertices=group_vertices, edges=group_edges, polygons=group_polygons, matrix=group_matrices, implementation_mode=self.implementation_mode)
                        else:
                            _apply_matrix = vectorize(apply_matrices, match_mode="REPEAT")
                            group_out_vertices, group_out_edges, group_out_polygons = _apply_matrix(
                                vertices=group_vertices or None, edges=group_edges or None, polygons=group_polygons or None, matrices=group_matrices or None,
                                implementation_mode=self.implementation_mode)
                    else:
                        group_out_vertices, group_out_edges, group_out_polygons = group_vertices, group_edges, group_polygons

                    if self.mesh_join:
                        _join_mesh = devectorize(join_meshes, match_mode="REPEAT")
                        group_out_vertices, group_out_edges, group_out_polygons = _join_mesh(
                            vertices=group_out_vertices, edges=group_out_edges, polygons=group_out_polygons)
                        group_out_vertices, group_out_edges, group_out_polygons = (
                            group_out_vertices if group_out_vertices is not None and len(group_out_vertices) else group_out_vertices,
                            group_out_edges    if group_out_edges    is not None and len(group_out_edges   ) else group_out_edges,
                            group_out_polygons if group_out_polygons is not None and len(group_out_polygons) else group_out_polygons)
                        pass
                    pass
                    out_vertices.extend(group_out_vertices)
                    out_edges   .extend(group_out_edges)
                    out_polygons.extend(group_out_polygons)
                pass

        self.outputs['vertices'].sv_set(out_vertices)
        self.outputs['edges'   ].sv_set(out_edges)
        self.outputs['polygons'].sv_set(out_polygons)


classes = [SvMeshJoinNodeMK3,]
register, unregister = bpy.utils.register_classes_factory(classes)