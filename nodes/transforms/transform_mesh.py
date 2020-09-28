# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from contextlib import contextmanager
from functools import reduce, lru_cache
from collections import namedtuple
from itertools import chain, cycle

import bpy
import bmesh
from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


Transform_mode = namedtuple('Transform_mode', ('move', 'scale', 'rotate'))
Select_mode = namedtuple('Select_mode', ('vert', 'edge', 'face'))
Origin_mode = namedtuple('Origin_mode', ('individ', 'median', 'bound', 'cust'))
Space_mode = namedtuple('Space_mode', ('norm', 'glob', 'cust'))
Direction_mode = namedtuple('Direction_mode', ('x', 'y', 'z', 'cust'))
MaskMode = namedtuple('MaskMode', ('boolean', 'index'))
LayerNames = namedtuple('LayerNames', ['mask', 'index_prop'])

TR_MODE = Transform_mode('Move', 'Scale', 'Rotate')
SEL_MODE = Select_mode('Verts', 'Edges', 'Faces')
OR_MODE = Origin_mode('Individual', 'Median', 'Center_bound_box', 'Custom')
SP_MODE = Space_mode('Normal', 'Global', 'Custom')
DIR_MODE = Direction_mode('X', 'Y', 'Z', 'Custom')
DIR_VEC = Direction_mode(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), None)
MASK_MODE = MaskMode('Bool_mask', 'Index_mask')


def transform_mesh(verts, edges=None, faces=None, mask=None, custom_origins=None, space_directions=None, indexes=None,
                   directions=None, factors=None, transform_mode=TR_MODE.move, origin_mode=OR_MODE.individ,
                   direction_mode=DIR_MODE.x, selection_mode=SEL_MODE.vert, space_mode=SP_MODE.glob,
                   mask_mode=MASK_MODE.boolean):
    """
    The function takes mesh and transform it according parameters. It can move, scale and rotate parts of mesh.
    The logic is close how Blender manipulate with mesh itself.
    Distribution of parameters: with bool mask all parameters are setting to selected elements ony by one.
    With integer mask parameters are setting to a group of elements.
    For example: given indexes - [1, 3], given parameters - [param1, param2].
    To all parts of mesh masked by 1 will be assigned with param1.
    To all parts of mesh masked by 3 will be assigned param2. All other parts will be unchanged.
    :param verts: list of tuple(float, float, float)
    :param edges: list of tuple(int, int)
    :param faces: list of list of int
    :param mask: two types masks are supported. list of bool or list of int
    :param custom_origins: custom center of transformation - list of tuple(float, float, float)
    :param space_directions: custom normal to center of transformation - list of tuple(float, float, float)
    :param indexes: list of int, index of part of mesh to assign parameters
    :param directions: list of tuple(float, float, float), transformation vector
    :param factors: list of float, direction * factor
    :param transform_mode: str, 'Move', 'Scale', 'Rotate'
    :param origin_mode: str, 'Individual', 'Median', 'Center_bound_box', 'Custom'
    :param direction_mode: str, 'X', 'Y', 'Z', 'Custom'
    :param selection_mode: str, 'Verts', 'Edges', 'Faces'
    :param space_mode: str, 'Normal', 'Global', 'Custom'
    :param mask_mode: str, 'Bool mask', 'Index mask'
    :return: list of tuple(float, float, float)
    """
    if mask and selection_mode == SEL_MODE.face and not faces:
        raise LookupError("Faces should be connected")
    if mask and selection_mode == SEL_MODE.edge and not any([faces, edges]):
        raise LookupError("Faces or edges should be connected")
    if mask and selection_mode == SEL_MODE.edge and not edges:
        raise LookupError("Edges should be plugged")
    if mask is None:
        mask = [True]
    if not isinstance(mask[0], int):
        mask = list(map(int, mask))

    with get_bmesh(verts, edges, faces, space_mode == SP_MODE.norm) as bm:
        bm_components = {SEL_MODE.vert: bm.verts, SEL_MODE.edge: bm.edges, SEL_MODE.face: bm.faces}
        if mask and not any(mask[:len(bm_components[selection_mode])]):
            return verts

        layers = generate_layers(bm_components[selection_mode], indexes, mask)
        if mask_mode == MASK_MODE.index:
            selected = iter_bm_index_mask(bm_components[selection_mode], origin_mode, indexes, layers)
        elif origin_mode in [OR_MODE.individ, OR_MODE.cust]:
            selected = iter_bm_islands(bm_components[selection_mode], mask_mode, layers)
        else:
            selected = [[v for v, m in zip(bm_components[selection_mode], iter_last(mask)) if m]]

        for sel in selected:
            sel_verts = get_selected_verts(sel)
            space = get_space(sel, space_mode, origin_mode, layers, mask_mode, custom_origins, space_directions)

            if transform_mode == TR_MODE.move:
                # space matrix applies to bmesh vertices
                move_vec = space.to_quaternion() \
                           @ get_move_vector(sel, directions, factors, mask_mode, layers, direction_mode)
                bmesh.ops.translate(bm, vec=move_vec, space=Matrix(), verts=sel_verts)
            elif transform_mode == TR_MODE.rotate:
                rotation = Matrix.Rotation(
                    get_factor(factors, sel, mask_mode, layers), 3,
                    space.to_quaternion() @ get_move_axis(sel, directions, direction_mode, layers, mask_mode))
                bmesh.ops.rotate(bm, cent=space.to_translation(), matrix=rotation, verts=sel_verts, space=Matrix())
            elif transform_mode == TR_MODE.scale:
                scale_vec = get_scale_vector(sel, directions, factors, layers, mask_mode, direction_mode)
                bmesh.ops.scale(bm, vec=scale_vec, space=space.inverted_safe(), verts=sel_verts)

        return [v.co[:] for v in bm.verts]


@contextmanager
def get_bmesh(verts, edges=None, faces=None, update_normals=False, update_indexes=True, use_operators=True):
    """
    It creates bmesh and delete it after usage
    :param verts: list of tuple(float, float, float)
    :param edges: list of tuple(int, int)
    :param faces: list of list of int
    :param update_normals: bool, it needs for some operators and for getting actual data of normals manually
    :param update_indexes: bool, for bm.verts[10]
    :param use_operators: bool, for using bmesh.ops
    :return: bmesh object
    """
    error = None
    bm = bmesh.new(use_operators=use_operators)
    try:
        # create mesh
        bm_verts = [bm.verts.new(co) for co in verts]
        [bm.edges.new((bm_verts[i1], bm_verts[i2])) for i1, i2 in edges or []]
        [bm.faces.new([bm_verts[i] for i in face]) for face in faces or []]

        # update mesh
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        if update_normals:
            bm.normal_update()
        if update_indexes:
            bm.verts.index_update()
            bm.edges.index_update()
            bm.faces.index_update()
        yield bm
    except Exception as Ex:
        error = Ex
    finally:
        bm.free()
    if error:
        raise error


def generate_layers(mesh_elements, indexes, mask):
    # generate required for the algorithm layers
    def gen_prop_index_data():
        # given indexes: [1, 3], index mask: [0, 0, 1, 2, 2, 3, 3, 4], returns: [-1, -1, 0, -1, -1, 1, 1, -1]
        element_prop_indexes_map = {el_i: prop_i for prop_i, el_i in enumerate(indexes)}
        return [element_prop_indexes_map[mi] if mi in element_prop_indexes_map else -1 for mi in mask]

    def create_layer(sequence, layer_name, layer_type, data):
        """
        generate layers of bmesh object
        :param sequence: bm.verts, bm.edges, bm.faces or bm.loops
        :param layer_name: str
        :param layer_type: str, according bmesh API, some of available variants: 'int', 'float', 'string'
        :param data: list of values with types according given layer type. Length of list == length of sequence
        :return: layer item
        """
        layer = getattr(sequence.layers, layer_type).new(layer_name)
        for element, val in zip(sequence, iter_last(data)):
            element[layer] = val
        return layer

    layer_settings = {'mask': ('int', mask),
                      'index_prop': ('int', gen_prop_index_data())}

    return LayerNames(*[create_layer(mesh_elements, layer_name, *layer_settings[layer_name])
                        for layer_name in layer_settings])


def iter_bm_islands(mesh_elements, mask_mode, layers: LayerNames):
    # returns bounded set of elements. Set is bounded if its elements with each other and mak is true in bool mode
    # or have the same indexes in index mode,
    def vert_neighbours(vert):
        for edge in vert.link_edges:
            v = edge.other_vert(vert)
            if ensure_next(vert, v):
                yield v

    def edge_neighbours(edge):
        for vert in edge.verts:
            for e in vert.link_edges:
                if ensure_next(edge, e):
                    yield e

    def face_neighbours(face):
        for edge in face.edges:
            for f in edge.link_faces:
                if ensure_next(face, f):
                    yield f

    def ensure_next(start_elem, next_elem):
        if start_elem == next_elem:
            return False
        if mask_mode == MASK_MODE.boolean:
            if next_elem[layers.mask]:
                return True
        else:
            if start_elem[layers.index_prop] == next_elem[layers.index_prop]:
                return True
        return False

    def mesh_walk(elements, neighbours_walk):
        used = set()
        for element in elements:
            if element in used:
                continue
            if mask_mode == MASK_MODE.boolean:
                if not element[layers.mask]:
                    continue
            stack = {element, }
            island = []
            while stack:
                next_element = stack.pop()
                used.add(next_element)
                island.append(next_element)
                for el in neighbours_walk(next_element):
                    if el not in used:
                        stack.add(el)
            yield island

    walk_map = {bmesh.types.BMVert: vert_neighbours,
                bmesh.types.BMEdge: edge_neighbours,
                bmesh.types.BMFace: face_neighbours}
    return mesh_walk(mesh_elements, walk_map[type(mesh_elements[0])])


def iter_bm_index_mask(bm_component, origin_mode, indexes, layers: LayerNames):
    # returns set of elements bounded by a same index in order of given indexes
    mesh_index_parts = {}
    for elem in bm_component:
        if elem[layers.mask] not in mesh_index_parts:
            mesh_index_parts[elem[layers.mask]] = []
        mesh_index_parts[elem[layers.mask]].append(elem)
    for ind in indexes:
        if ind in mesh_index_parts:
            if origin_mode == OR_MODE.individ:
                yield from iter_bm_islands(mesh_index_parts[ind], MASK_MODE.index, layers)
            else:
                yield mesh_index_parts[ind]


def get_move_vector(selected, directions, factors, mask_mode, layers: LayerNames, direction_mode=DIR_MODE.x):
    # returns vector for translate operator
    factor = get_factor(factors, selected, mask_mode, layers)
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower()) * factor
    else:
        if mask_mode == MASK_MODE.boolean:
            direction = get_median_center([Vector(get_item_last(directions, sel.index)) for sel in selected])
        else:
            direction = Vector(get_item_last(directions, selected[0][layers.index_prop]))
        return direction * factor


def get_scale_vector(selected, directions, factors, layers: LayerNames, mask_mode, direction_mode=DIR_MODE.x):
    # returns vector for scale operator
    index = {'X': 0, 'Y': 1, 'Z': 2}
    factor = get_factor(factors, selected, mask_mode, layers)
    if direction_mode in DIR_MODE[:-1]:
        vec = [1, 1]
        vec.insert(index[direction_mode], 1 * factor)
        return Vector(vec)
    else:
        if mask_mode == MASK_MODE.index:
            return Vector(get_item_last(directions, selected[0][layers.index_prop])) * factor
        else:
            return get_median_center([Vector(get_item_last(directions, sel.index)) for sel in selected]) * factor


def get_move_axis(selected, directions, direction_mode, layers: LayerNames, mask_mode):
    # returns axis vector for rotation operator
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower())
    else:
        if mask_mode == MASK_MODE.index:
            return Vector(get_item_last(directions, selected[0][layers.index_prop]))
        else:
            return calc_average_normal([Vector(get_item_last(directions, sel.index)) for sel in selected])


def get_factor(factors, selected, mask_mode, layers: LayerNames):
    # returns factor for translate, scale and rotate operators
    if mask_mode == MASK_MODE.index:
        return get_item_last(factors, selected[0][layers.index_prop])
    else:
        if len(factors) == 1:
            return factors[0]
        else:
            return sum([get_item_last(factors, sel.index) for sel in selected]) / len(selected)


def get_selected_verts(selected):
    # convert any sequence of elements to sequence vector elements
    if type(selected[0]) == bmesh.types.BMVert:
        return selected
    elif type(selected[0]) == bmesh.types.BMEdge:
        return list({v for e in selected for v in e.verts})
    elif type(selected[0]) == bmesh.types.BMFace:
        return list({v for f in selected for v in f.verts})
    else:
        raise ValueError(f"Such type: {type(selected)} is not supported")


def get_space(selected, space_mode, origin_mode, layers: LayerNames, mask_mode, custom_origins=None,
              space_directions=None):
    # returns space matrix for selected elements according given options
    origin = get_origin(selected, origin_mode, mask_mode, layers, custom_origins)
    if space_mode == SP_MODE.glob:
        return Matrix.Translation(origin)
    elif space_mode == SP_MODE.norm:
        normal = get_normals(selected)
        # average tangent can be not perpendicular to average normal
        _tangent = get_tangents(selected)
        tangent = normal.cross(_tangent.cross(normal))
        return build_matrix(origin, normal, tangent)
    elif space_mode == SP_MODE.cust:
        if mask_mode == MASK_MODE.index:
            normal = Vector(get_item_last(space_directions, selected[0][layers.index_prop]))
        else:
            normal = calc_average_normal([Vector(get_item_last(space_directions, sel.index)) for sel in selected])
        tangent = Vector((0, 1, 0)) if normal == Vector((0, 0, 1)) else normal.cross(Vector((0, 0, 1)))
        return build_matrix(origin, normal, tangent)
    else:
        raise ValueError(f"Such space mode: {space_mode} is not supported")


def get_origin(mesh_component, origin_mode, mask_mode, layers: LayerNames, custom_origins=None):
    # get origin of selected elements
    if origin_mode == OR_MODE.cust:
        if mask_mode == MASK_MODE.index:
            return Vector(get_item_last(custom_origins, mesh_component[0][layers.index_prop]))
        else:
            return get_median_center([Vector(get_item_last(custom_origins, sel.index)) for sel in mesh_component])
    else:
        if type(mesh_component[0]) == bmesh.types.BMVert:
            return get_verts_origin(mesh_component, origin_mode)
        elif type(mesh_component[0]) == bmesh.types.BMEdge:
            return get_edges_origin(mesh_component, origin_mode)
        elif type(mesh_component[0]) == bmesh.types.BMFace:
            return get_faces_origin(mesh_component, origin_mode)
        else:
            raise ValueError(f"Such type: {type(mesh_component)} is not supported")


def get_verts_origin(verts, origin_mode):
    # returns origin of selected vertices
    if origin_mode == OR_MODE.bound:
        return get_bound_center([v.co for v in verts])
    if origin_mode in [OR_MODE.median, OR_MODE.individ]:
        return get_median_center([v.co for v in verts])


def get_edges_origin(edges, origin_mode):
    # returns origin of selected edges
    if origin_mode == OR_MODE.bound:
        return get_bound_center([e.verts[0].co.lerp(e.verts[1].co, 0.5) for e in edges])
    if origin_mode in [OR_MODE.median, OR_MODE.individ]:
        return get_median_center([v.co for v in{v for e in edges for v in e.verts}])


def get_faces_origin(faces, origin_mode):
    # returns origin of selected faces
    if origin_mode == OR_MODE.bound:
        return get_bound_center([f.calc_center_bounds() for f in faces])
    if origin_mode in [OR_MODE.median, OR_MODE.individ]:
        return get_median_center([v.co for v in {v for f in faces for v in f.verts}])


def get_bound_center(verts):
    # returns center of bounding box of given vertices
    x_min = min(v.x for v in verts)
    y_min = min(v.y for v in verts)
    z_min = min(v.z for v in verts)
    x_max = max(v.x for v in verts)
    y_max = max(v.y for v in verts)
    z_max = max(v.z for v in verts)
    return Vector(((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2))


def get_median_center(verts):
    # returns median center of given vertices
    return reduce(lambda v1, v2: v1 + v2, verts) / len(verts)


def get_normals(mesh_component):
    # returns normals of any selected elements
    if type(mesh_component[0]) == bmesh.types.BMVert:
        return calc_average_normal([v.normal for v in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMEdge:
        return calc_average_normal([get_edge_normal_tangent(e)[0] for e in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMFace:
        return calc_average_normal([f.normal for f in mesh_component])
    else:
        raise ValueError(f"Such type: {type(mesh_component)} is not supported")


def get_tangents(mesh_component):
    # returns tangent of any selected elements
    if type(mesh_component[0]) == bmesh.types.BMVert:
        return calc_average_normal([get_vert_tang(v) for v in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMEdge:
        return calc_average_normal([get_edge_normal_tangent(e)[1] for e in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMFace:
        return calc_average_normal([get_face_tangent(f) for f in mesh_component])
    else:
        raise ValueError(f"Such type: {type(mesh_component)} is not supported")


def calc_average_normal(normals):
    # calculates average normal of give normals, given normals should be normalized
    return reduce(lambda v1, v2: v1 + v2, normals).normalized()


@lru_cache(maxsize=None)
def get_edge_normal_tangent(edge):
    # returns tangent of given edge close to Blender logic
    direct = (edge.verts[1].co - edge.verts[0].co).normalized()
    _normal = (edge.verts[0].normal + edge.verts[1].normal).normalized()
    tang = direct.cross(_normal)
    return tang.cross(direct), tang


def get_vert_tang(vert):
    # returns tangent close to Blender logic in normal mode
    # vert - bmesh vertex
    if len(vert.link_edges) == 2 and vert.link_loops:
        return vert.link_loops[0].calc_tangent().cross(vert.normal)
    elif vert.normal == Vector((0, 0, 1)):
        return Vector((-1, 0, 0))
    elif vert.normal == Vector((0, 0, -1)):
        return Vector((1, 0, 0))
    else:
        return vert.normal.cross(vert.normal.cross(Vector((0, 0, 1)))).normalized()


def get_face_tangent(face):
    # returns tangent close to Blender logic in normal mode
    # face - bmesh face
    if len(face.edges) > 3:
        return face.calc_tangent_edge_pair().normalized() * -1
    else:
        return face.calc_tangent_edge_diagonal()


def build_matrix(center, normal, tangent):
    # build matrix from 3 vectors (center, normal(z), tangent(y))
    x_axis = tangent.cross(normal)
    return Matrix(list(zip(x_axis.resized(4), tangent.resized(4), normal.resized(4), center.to_4d())))


def iter_last(l):
    # returns generator which repeat last element of given sequence infinitely
    return chain(l, cycle([l[-1]]))


def get_item_last(seq, ind):
    # return item of sequence, if index is out of range returns last item
    try:
        return seq[ind]
    except IndexError:
        return seq[-1]


class SvTransformMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: move rotate scale

    Transform mesh on mesh level
    Similar how Blender do transformations
    """
    bl_idname = 'SvTransformMesh'
    bl_label = 'Transform Mesh'
    bl_icon = 'MOD_BOOLEAN'
    sv_icon = 'SV_TRANSFORM_SELECT'

    def update_sockets(self, context):
        def hide(socket, statement):
            if socket.hide != statement:
                socket.hide_safe = statement

        hide(self.inputs['Origin'], True if self.origin_mode != OR_MODE.cust else False)
        hide(self.inputs['Space direction'], True if self.space_mode != SP_MODE.cust else False)
        hide(self.inputs['Mask index'], True if self.mask_mode == MASK_MODE.boolean else False)
        updateNode(self, context)

    transform_mode_items = [(i, i, '') for i in TR_MODE]
    mask_mode_items = [(i, i.replace("_", " "), '') for i in MASK_MODE]
    select_mode_items = [(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]
    origin_mode_items = [(n, n.replace("_", " "), '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Individual', 'Median', 'Center_bound_box', 'Custom'),
        ('PIVOT_INDIVIDUAL', 'PIVOT_MEDIAN', 'PIVOT_BOUNDBOX', 'PIVOT_CURSOR')))]
    space_mode_items = [(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Normal', 'Global', 'Custom'), ('ORIENTATION_NORMAL', 'ORIENTATION_GLOBAL', 'ORIENTATION_CURSOR')))]
    direction_mode_items = [(n, n, '') for n in DIR_MODE]

    transform_mode: bpy.props.EnumProperty(items=transform_mode_items, update=updateNode)
    mask_mode: bpy.props.EnumProperty(items=mask_mode_items, update=update_sockets)
    select_mode: bpy.props.EnumProperty(items=select_mode_items, update=updateNode)
    origin_mode: bpy.props.EnumProperty(items=origin_mode_items, name='Origin', default=OR_MODE.bound,
                                        update=update_sockets)
    space_mode: bpy.props.EnumProperty(items=space_mode_items, name='Space', update=update_sockets)
    direction_mode: bpy.props.EnumProperty(items=direction_mode_items, name='Direction', update=updateNode)
    origin: bpy.props.FloatVectorProperty(name='Origin', update=updateNode)
    space_direction: bpy.props.FloatVectorProperty(name="Space direction", default=(0, 0, 1), update=updateNode)
    active_index: bpy.props.IntProperty(name="Mask index", update=updateNode)
    direction: bpy.props.FloatVectorProperty(name='Direction', update=updateNode)
    factor: bpy.props.FloatProperty(name='Factor', default=1.0, update=updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.scale_y = 1.5
        row.prop(self, 'transform_mode', expand=True)
        layout.prop(self, 'mask_mode', expand=True)
        layout.prop(self, 'origin_mode')
        layout.prop(self, 'space_mode')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', "Mask").custom_draw = 'draw_mask_socket'
        or_socket = self.inputs.new('SvVerticesSocket', "Origin")
        or_socket.prop_name = 'origin'
        or_socket.hide = True
        sp_dir_socket = self.inputs.new('SvVerticesSocket', "Space direction")
        sp_dir_socket.prop_name = 'space_direction'
        sp_dir_socket.hide = True
        ind_socket = self.inputs.new('SvStringsSocket', 'Mask index')
        ind_socket.prop_name = 'active_index'
        ind_socket.hide = True
        dir_sock = self.inputs.new('SvVerticesSocket', "Direction")
        dir_sock.custom_draw = 'draw_direction_socket'
        dir_sock.prop_name = 'direction'
        self.inputs.new('SvStringsSocket', "Factor").prop_name = 'factor'
        self.outputs.new('SvVerticesSocket', 'Verts')

    def draw_mask_socket(self, socket, context, layout):
        layout.label(text='Mask')
        layout.prop(self, 'select_mode', expand=True, icon_only=True)

    def draw_direction_socket(self, socket, context, layout):
        if socket.is_linked:
            layout.label(text='Direction')
        else:
            col = layout.column()
            row = col.row()
            row.prop(self, 'direction_mode', expand=True)
            if self.direction_mode == DIR_MODE.cust:
                socket.draw_property(col, self, 'direction')

    def process(self):
        if not self.inputs['Verts'].is_linked:
            return

        verts = self.inputs['Verts'].sv_get(deepcopy=False)
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=cycle([None]))
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=cycle([None]))
        mask = iter_last(self.inputs['Mask'].sv_get(deepcopy=False, default=[None]))
        origin = iter_last(self.inputs['Origin'].sv_get(deepcopy=False))
        space_direction = iter_last(self.inputs['Space direction'].sv_get(deepcopy=False))
        active_index = iter_last(self.inputs['Mask index'].sv_get(deepcopy=False))
        direction = iter_last(self.inputs['Direction'].sv_get(deepcopy=False))
        factor = iter_last(self.inputs['Factor'].sv_get(deepcopy=False))
        out = []

        dir_mode = DIR_MODE.cust if self.inputs['Direction'].is_linked else self.direction_mode

        for v, e, f, m, o, sd, ai, d, fac in zip(verts, edges, faces, mask, origin, space_direction, active_index, direction, factor):
            out.append(transform_mesh(v, e, f, m, o, sd, ai, d, fac, self.transform_mode, self.origin_mode,
                                      dir_mode, self.select_mode, self.space_mode, self.mask_mode))

        self.outputs['Verts'].sv_set(out)


def register():
    bpy.utils.register_class(SvTransformMesh)


def unregister():
    bpy.utils.unregister_class(SvTransformMesh)
