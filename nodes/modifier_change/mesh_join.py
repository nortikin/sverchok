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
from sverchok.utils.mesh_functions import meshes_py, meshes_np, to_elements
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from sverchok.data_structure import updateNode, ensure_nesting_level
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

def apply_matrix(objs, matrices):
    new_objects_vertices = []
    for object1_vertices, mat1 in zip(objs, matrices):
        if mat1==Matrix():
            # Для единичной матрицы не делать преобразований. Так будет быстрее
            object1_vertices_new = object1_vertices[:]
        else:
            object1_vertices_np = np.asarray(object1_vertices, dtype=np.float32)
            object1_vertices_np_converted = matrix_apply_np(object1_vertices_np, mat1)
            object1_vertices_new = object1_vertices_np_converted.tolist()
        new_objects_vertices.append(object1_vertices_new)

    return new_objects_vertices

def join_meshes(meshes):
    """
    meshes:
        iterable из троек:
        (vertices, edges, faces)
    """
    result_vertices = []
    result_edges = []
    result_faces = []

    vertex_offset = 0

    for vertices, edges, faces in meshes:
        result_vertices.extend(vertices)

        if edges:
            result_edges.extend(
                [ [index + vertex_offset for index in edge] for edge in edges if len(edge)>=2]
            )

        if faces:
            result_faces.extend(
                [ [index + vertex_offset for index in face] for face in faces if len(face) >= 3]
            )

        vertex_offset += len(vertices)

    return result_vertices, result_edges, result_faces

def clear_mesh(meshes):
    """
    remove invalid edges and faces (generally if some input lists of edges and faces has zero length list of indexes. ex. [[ [], [0,1,2,3], [],  ]] -> [[[0,1,2,3]]]  )
    meshes:
        iterable из троек:
        (vertices, edges, faces)
    """
    result_vertices = []
    result_edges = []
    result_faces = []

    for vertices, edges, faces in meshes:
        obj_vertices = vertices
        obj_edges = []
        obj_faces = []

        if edges:
            obj_edges.extend(
                [ edge for edge in edges if len(edge)>=2]
            )

        if faces:
            obj_faces.extend(
                [ face for face in faces if len(face) >= 3]
            )
        pass

        result_vertices.append( obj_vertices )
        result_edges.append( obj_edges )
        result_faces.append( obj_faces )


    return result_vertices, result_edges, result_faces

def resize_list(lst, length):
    if isinstance(lst, (list, tuple)):
        if len(lst) >= length:
            return lst[:length]

        if not lst:
            return lst

        return lst + [lst[-1]] * (length - len(lst))
    else:
        return lst

CONTAINER_TYPES = (list, tuple)

def flatten_atomic_groups(data):
    """
    Finds groups of atomic values at any nesting depth
    and returns them at the same level.

    list and tuple are treated as containers.
    Everything else is treated as an atomic value:
    int, float, str, Vector, Matrix, dict, None, custom objects, etc.

    Valid:
        [[[[1, 2.0], ["text", Vector(...)]]], [[Matrix(...), None]]]

    Result:
        [
            [1, 2.0],
            ["text", Vector(...)],
            [Matrix(...), None],
        ]

    Invalid:
        [[1, 2], 3]

    A level cannot contain both containers and atomic values.
    """

    if not isinstance(data, CONTAINER_TYPES):
        raise TypeError( f"Expected list or tuple, got {type(data).__name__}" )

    def _flatten_atomic_groups(items, path=()):
        # Empty containers produce no groups.
        if not items:
            return

        first_is_container = isinstance( items[0], CONTAINER_TYPES, )

        # Every element on this level must have the same role:
        # either all containers or all atomic values.
        for index, item in enumerate(items[1:], start=1):
            item_is_container = isinstance( item, CONTAINER_TYPES, )

            if item_is_container != first_is_container:
                location = ( "".join(f"[{i}]" for i in path) or "[root]" )
                expected = "container (list/tuple)" if first_is_container else "atomic value"
                raise ValueError(f"Mixed level at {location}: element {index} has type {type(item).__name__}; expected {expected}")

        if first_is_container:
            for index, item in enumerate(items):
                yield from _flatten_atomic_groups( item, path + (index,), )
        else:
            # Normalize tuple groups to lists.
            yield list(items)

    return list(_flatten_atomic_groups(data))


def flatten_atomic(data):
    """
    Flattens nested lists/tuples into one list.

    Each individual nesting level must contain either:
    - only containers: list / tuple;
    - only atomic values: anything except list / tuple.

    Mixed levels raise ValueError.

    Valid:
        [[[[1, 2], [3, 4]]], [[5, 6]]]
        -> [1, 2, 3, 4, 5, 6]

    Invalid:
        [[1, 2], 3]
    """

    if not isinstance(data, CONTAINER_TYPES):
        raise TypeError( f"Expected list or tuple, got {type(data).__name__}" )

    def _flatten(items, path=()):
        if not items:
            return

        first_is_container = isinstance(items[0], CONTAINER_TYPES)

        # Check that the current level is homogeneous.
        for index, item in enumerate(items[1:], start=1):
            item_is_container = isinstance(item, CONTAINER_TYPES)

            if item_is_container != first_is_container:
                location = "".join(f"[{i}]" for i in path) or "[root]"
                expected = "list/tuple" if first_is_container else "non-container value"

                raise ValueError( f"Mixed types at {location}: element {index} is {type(item).__name__}, expected {expected}" )

        if first_is_container:
            for index, item in enumerate(items):
                yield from _flatten(item, path + (index,))
        else:
            yield from items

    return list(_flatten(data))

class SvMeshJoinNodeMK3( SverchCustomTreeNode, bpy.types.Node, ):
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
    matrixes_apply: bpy.props.BoolProperty(name='Apply Matrixes', default=False, update=updateNode, description="If set, then this node will apply matrices to output meshes")

    def update_do_last_group_empty(self, context):
        self.sv_update()
        updateNode(self, context)
        return

    do_last_group_empty: bpy.props.BoolProperty(
        name='Last Group Empty',
        default=False,
        update=update_do_last_group_empty,
        description="If set, an empty group is added after the last element."
    )

    # implementation_modes = [
    #     ("NumPy", "NumPy", "NumPy", 0),
    #     ("Python", "Python", "Python", 1)]

    # implementation_mode: bpy.props.EnumProperty(
    #     name='Implementation', items=implementation_modes,
    #     description='Choose calculation method (See Documentation)',
    #     default="Python", update=updateNode)

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
        row = root.row(align=True)
        row.prop(self, 'matrixes_apply')
        
    def draw_buttons_ext(self, context, layout):
        root = layout
        root.label(text='Implementation:')
        row = root.row(align=True)
        row.enabled = self.mesh_join
        #row.prop(self, 'implementation_mode', expand=True)

        root.prop(self, 'do_last_group_empty')
        return

    def sv_init(self, context):
        join_groups = self.inputs.new('SvStringsSocket', 'join_groups')
        join_groups.label = 'Join Groups'
        verts0 = self.inputs.new('SvVerticesSocket', 'vertices0')
        verts0.is_mandatory = True
        verts0.nesting_level = 3
        verts0.default_mode = 'NONE'
        verts0.label = 'Vertices 1'
        verts0.custom_draw = 'draw_vertices_in_socket'

        edges0 = self.inputs.new('SvStringsSocket', 'edges0')
        edges0.nesting_level = 3
        edges0.default_mode = 'EMPTY_LIST'
        edges0.label = 'Edges'

        polygons0 = self.inputs.new('SvStringsSocket', 'polygons0')
        polygons0.nesting_level = 3
        polygons0.default_mode = 'EMPTY_LIST'
        polygons0.label = 'Polygons'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs['vertices'].label = 'Vertices'
        self.outputs.new('SvStringsSocket', 'edges')
        self.outputs['edges'].label = 'Edges'
        self.outputs.new('SvStringsSocket', 'polygons')
        self.outputs['polygons'].label = 'Polygons'
        self.outputs.new('SvMatrixSocket', 'matrices')
        self.outputs['matrices'].label = 'Matrices'
        self.outputs.new('SvStringsSocket', 'original_ids')
        self.outputs['original_ids'].label = 'Original Ids'
        self.outputs.new('SvStringsSocket', 'ids')
        self.outputs['ids'].label = 'Ids'

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

        # Если минимальный индекс некорректной позиции не найден (все сокеты корректно находятся на своих местах), 
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
        return

    # def migrate_from(self, old_node):
    #     verts = self.inputs['vertices1']
    #     verts.is_mandatory = True
    #     verts.default_mode = 'NONE'

    #     edges = self.inputs['edges1']
    #     edges.nesting_level = 3
    #     edges.default_mode = 'EMPTY_LIST'

    #     pols = self.inputs['polygons1']
    #     pols.nesting_level = 3
    #     pols.default_mode = 'EMPTY_LIST'

    def migrate_links_from(self, old_node, operator):
        # Temporary enable last empty socket on migrate links and resore them after
        do_last_group_empty = self.do_last_group_empty
        if self.do_last_group_empty==False:
            self.do_last_group_empty = True
        super().migrate_links_from(old_node, operator)
        if do_last_group_empty==False:
            self.do_last_group_empty = False
        return

    def process(self):
        
        group_names = tuple(self.group_struct)
        elems, invalid_elems = self.reload_sockets_data(self.groups_offset, self.inputs, group_names)
        len_group_names = len(group_names)
        
        if invalid_elems:
            pass
        else:
            out_vertices, out_edges, out_polygons, out_matrices, out_original_ids = [], [], [], [], []

            join_groups_in = self.inputs['join_groups']
            join_groups = []

            if join_groups_in.is_linked:
                _join_groups = join_groups_in.sv_get(default=[], deepcopy=False)
            else:
                _join_groups = []

            if _join_groups:
                # Если join_groups
                if self.mesh_join==True:
                    join_groups = flatten_atomic_groups(_join_groups)
                else:
                    join_groups = [flatten_atomic(_join_groups)]
                #join_groups = flatten_integer_groups(_join_groups)
            else:
                #if not join_groups or self.mesh_join==False:
                join_groups = [list(range(0, len(elems)))]

            for join_group in join_groups:
                out_vertices_IJ, out_edges_IJ, out_polygons_IJ, out_matrices_IJ, out_original_ids_IJ = [], [], [], [], []

                # collect  group data
                #for IJ, elem_IJ in join_group_elems.items():
                for group_id in join_group:
                    if group_id not in elems:
                        continue
                    elem_IJ = elems[group_id]
                    verts_IJ = elem_IJ.vertices
                    edges_IJ = elem_IJ.edges
                    polygons_IJ = elem_IJ.polygons
                    matrices_IJ = elem_IJ.matrices
                    

                    if verts_IJ.is_linked==False:
                        # Skip
                        continue
                    else:
                        group_vertices_IJ  = self.inputs[verts_IJ.socket_name   ].sv_get(default=[], deepcopy=False)
                        group_edges_IJ     = self.inputs[edges_IJ.socket_name   ].sv_get(default=[], deepcopy=False)
                        group_polygons_IJ  = self.inputs[polygons_IJ.socket_name].sv_get(default=[], deepcopy=False)
                        group_matrices_IJ  = self.inputs[matrices_IJ.socket_name].sv_get(default=[], deepcopy=False)
                        if not group_matrices_IJ:
                            group_matrices_IJ = [Matrix()]

                        _group_matrices = ensure_nesting_level(group_matrices_IJ, 2)
                        group_matrices_IJ = _group_matrices[0]

                        # fixing matrices nesting level if necessary, this is for back capability, can be removed later on
                        max_length = max([len(elem) for elem in [group_vertices_IJ, group_edges_IJ, group_polygons_IJ, group_matrices_IJ if group_matrices_IJ else [Matrix()] ] ])
                        group_out_vertices_IJ, group_out_edges_IJ, group_out_polygons_IJ, group_out_matrices_IJ = resize_list(group_vertices_IJ, max_length), resize_list(group_edges_IJ if group_edges_IJ else [[]], max_length), resize_list(group_polygons_IJ if group_polygons_IJ else [[]], max_length), resize_list(group_matrices_IJ, max_length)

                        out_vertices_IJ  .extend(group_out_vertices_IJ)
                        out_edges_IJ     .extend(group_out_edges_IJ)
                        out_polygons_IJ  .extend(group_out_polygons_IJ)
                        out_matrices_IJ  .extend(group_out_matrices_IJ)
                        if group_out_vertices_IJ:
                            out_original_ids_IJ.extend([group_id]*max_length)
                    pass

                if len(out_vertices_IJ)==0:
                    # Skip if no vertices
                    continue

                out_original_ids.append(out_original_ids_IJ)

                if self.matrixes_apply==False and self.mesh_join==False:
                    # Combine all input sockets and pass data to output
                    out_original_ids = [[i] for elem in out_original_ids for i in elem]
                    out_vertices_IJ, out_edges_IJ, out_polygons_IJ = clear_mesh(list(zip(out_vertices_IJ, out_edges_IJ, out_polygons_IJ)))
                    pass
                elif self.matrixes_apply==False and self.mesh_join==True:
                    # Only join meshes into the first object's space.
                    m0 = out_matrices_IJ[0]
                    m0_inverted = m0.inverted()
                    out_matrices_IJ = [m0_inverted @ mat for mat in out_matrices_IJ]
                    out_vertices_IJ = apply_matrix(out_vertices_IJ, out_matrices_IJ)
                    out_vertices_IJ, out_edges_IJ, out_polygons_IJ = join_meshes(list(zip(out_vertices_IJ, out_edges_IJ, out_polygons_IJ)))
                    out_vertices_IJ, out_edges_IJ, out_polygons_IJ = [out_vertices_IJ], [out_edges_IJ], [out_polygons_IJ]
                    out_matrices_IJ = [m0]
                    pass
                elif self.matrixes_apply==True and self.mesh_join==False:
                    # Only Apply matrices and transfer results to outputs. Do not join meshes.
                    out_original_ids = [[i] for elem in out_original_ids for i in elem]
                    out_vertices_IJ = apply_matrix(out_vertices_IJ, out_matrices_IJ)
                    out_matrices_IJ = [Matrix() for mat in out_matrices_IJ]
                    pass
                elif self.matrixes_apply==True and self.mesh_join==True:
                    # Apply all matrixes and merge meshes into the first object. Set output matrix as Identity.
                    out_vertices_IJ = apply_matrix(out_vertices_IJ, out_matrices_IJ)
                    out_vertices_IJ, out_edges_IJ, out_polygons_IJ = join_meshes(list(zip(out_vertices_IJ, out_edges_IJ, out_polygons_IJ)))
                    out_vertices_IJ, out_edges_IJ, out_polygons_IJ = [out_vertices_IJ], [out_edges_IJ], [out_polygons_IJ]
                    out_matrices_IJ = [Matrix()]

                out_vertices.extend(out_vertices_IJ)
                out_edges   .extend(out_edges_IJ   )
                out_polygons.extend(out_polygons_IJ)
                out_matrices.extend(out_matrices_IJ)
                pass

        out_ids = [[I] for I in range(0, len(out_original_ids))]
        self.outputs['vertices'     ].sv_set(out_vertices)
        self.outputs['edges'        ].sv_set(out_edges)
        self.outputs['polygons'     ].sv_set(out_polygons)
        self.outputs['matrices'     ].sv_set(out_matrices)
        if 'original_ids' in self.outputs: self.outputs['original_ids' ].sv_set(out_original_ids)
        if          'ids' in self.outputs: self.outputs['ids'          ].sv_set(out_ids)

        return


classes = [SvMeshJoinNodeMK3,]
register, unregister = bpy.utils.register_classes_factory(classes)