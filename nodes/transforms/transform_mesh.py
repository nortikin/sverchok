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

TR_MODE = Transform_mode('Move', 'Scale', 'Rotate')
SEL_MODE = Select_mode('Verts', 'Edges', 'Faces')
OR_MODE = Origin_mode('Individual', 'Median', 'Center bound box', 'Custom')
SP_MODE = Space_mode('Normal', 'Global', 'Custom')
DIR_MODE = Direction_mode('X', 'Y', 'Z', 'Custom')
DIR_VEC = Direction_mode(Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), None)


def transform_mesh(verts, edges=None, faces=None, mask=None, custom_origins=None, space_directions=None,
                   directions=None, factors=None, transform_mode=TR_MODE.move, origin_mode=OR_MODE.individ,
                   direction_mode=DIR_MODE.x, selection_mode=SEL_MODE.vert, space_mode=SP_MODE.glob):
    if mask and selection_mode == SEL_MODE.face and not faces:
        raise LookupError("Faces should be connected")
    if mask and selection_mode == SEL_MODE.edge and not any([faces, edges]):
        raise LookupError("Faces or edges should be connected")

    with get_bmesh(verts, edges, faces, space_mode == SP_MODE.norm) as bm:
        bm_components = {SEL_MODE.vert: bm.verts, SEL_MODE.edge: bm.edges, SEL_MODE.face: bm.faces}
        if mask and not any(mask[:len(bm_components[selection_mode])]):
            return verts

        if origin_mode in [OR_MODE.individ, OR_MODE.cust]:
            selected = iter_bm_islands(bm, selection_mode, mask)
        else:
            selected = [[v for v, m in zip(bm_components[selection_mode], mask or cycle([True])) if m]]

        for sel in selected:
            sel_verts = get_selected_verts(sel)
            space = get_space(sel, space_mode, origin_mode, custom_origins, space_directions)

            if transform_mode == TR_MODE.move:
                # space matrix applies to bmesh vertices
                bmesh.ops.translate(bm, vec=space.to_quaternion() @ get_move_vector(sel, directions, factors, direction_mode),
                                    space=Matrix(), verts=sel_verts)
            elif transform_mode == TR_MODE.rotate:
                bmesh.ops.rotate(bm, cent=space.to_translation(),
                                 matrix=Matrix.Rotation(calc_average_factor(factors, sel), 3, space.to_quaternion() @ get_move_axis(sel, directions, direction_mode)),
                                 verts=sel_verts, space=Matrix())
            elif transform_mode == TR_MODE.scale:
                bmesh.ops.scale(bm, vec=get_scale_vector(sel, directions, factors, direction_mode),
                                space=space.inverted(), verts=sel_verts)

        return [v.co[:] for v in bm.verts]


@contextmanager
def get_bmesh(verts, edges=None, faces=None, update_normals=False, use_operators=True):
    error = None
    bm = bmesh.new(use_operators=use_operators)
    try:
        bm_verts = [bm.verts.new(co) for co in verts]
        [bm.edges.new((bm_verts[i1], bm_verts[i2])) for i1, i2 in edges or []]
        [bm.faces.new([bm_verts[i] for i in face]) for face in faces or []]
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        if update_normals:
            bm.normal_update()
        yield bm
    except Exception as Ex:
        error = Ex
    finally:
        bm.free()
    if error:
        raise error


def iter_bm_islands(bm, sel_mode, mask=None):
    if sel_mode == SEL_MODE.face:
        # mark faces which are not selected at first
        used = {f for f, m in zip(bm.faces, iter_last(mask) if mask else cycle([True])) if not m}
        for face in bm.faces:
            if face in used:
                continue
            stack = {face, }
            island = []
            while stack:
                next_face = stack.pop()
                used.add(next_face)
                island.append(next_face)
                for edge in next_face.edges:
                    for f in edge.link_faces:
                        if f not in used:
                            stack.add(f)
            yield island

    if sel_mode == SEL_MODE.edge:
        used = {e for e, m in zip(bm.edges, iter_last(mask) if mask else cycle([True])) if not m}
        for edge in bm.edges:
            if edge in used:
                continue
            stack = {edge, }
            island = []
            while stack:
                next_edge = stack.pop()
                used.add(next_edge)
                island.append(next_edge)
                for vert in next_edge.verts:
                    for e in vert.link_edges:
                        if e not in used:
                            stack.add(e)
            yield island

    if sel_mode == SEL_MODE.vert:
        used = {v for v, m in zip(bm.verts, iter_last(mask) if mask else cycle([True])) if not m}
        for vert in bm.verts:
            if vert in used:
                continue
            stack = {vert, }
            island = []
            while stack:
                next_vert = stack.pop()
                used.add(next_vert)
                island.append(next_vert)
                for edge in next_vert.link_edges:
                    if edge.other_vert(next_vert) not in used:
                        stack.add(edge.other_vert(next_vert))
            yield island


def get_move_vector(selected, directions, factors, direction_mode=DIR_MODE.x):
    average_factor = calc_average_factor(factors, selected)
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower()) * average_factor
    else:
        average_direction = get_median_center(
            [Vector(directions[sel.index if len(directions) > sel.index else -1]) for sel in selected])
        return average_direction * average_factor


def get_scale_vector(selected, directions, factors, direction_mode=DIR_MODE.x):
    index = {'X': 0, 'Y': 1, 'Z': 2}
    average_factor = calc_average_factor(factors, selected)
    if direction_mode in DIR_MODE[:-1]:
        vec = [1, 1]
        vec.insert(index[direction_mode], 1 * average_factor)
        return Vector(vec)
    else:
        return get_median_center(
            [Vector(directions[sel.index if len(directions) > sel.index else -1]) for sel in selected]) * average_factor


def get_move_axis(selected, directions, direction_mode):
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower())
    else:
        return calc_average_normal(
            [Vector(directions[sel.index if len(directions) > sel.index else -1]) for sel in selected])


def calc_average_factor(factors, selected):
    if len(factors) == 1:
        return factors[0]
    else:
        return sum([factors[sel.index if len(factors) > sel.index else -1] for sel in selected]) / len(selected)


def get_selected_verts(selected):
    if type(selected[0]) == bmesh.types.BMVert:
        return selected
    elif type(selected[0]) == bmesh.types.BMEdge:
        return list({v for e in selected for v in e.verts})
    elif type(selected[0]) == bmesh.types.BMFace:
        return list({v for f in selected for v in f.verts})
    else:
        raise ValueError(f"Such type: {type(selected)} is not supported")


def get_space(selected, space_mode, origin_mode, custom_origins=None, space_directions=None):
    origin = get_origin(selected, origin_mode, custom_origins)
    if space_mode == SP_MODE.glob:
        return Matrix.Translation(origin)
    elif space_mode == SP_MODE.norm:
        normal = get_normals(selected)
        # average tangent can be not perpendicular to average normal
        _tangent = get_tangents(selected)
        tangent = normal.cross(_tangent.cross(normal))
        return build_matrix(origin, normal, tangent)
    elif space_mode == SP_MODE.cust:
        normal = calc_average_normal([Vector(space_directions[sel.index]) if len(space_directions) > sel.index else
                                      Vector(space_directions[-1]) for sel in selected])
        tangent = Vector((0, 1, 0)) if normal == Vector((0, 0, 1)) else normal.cross(Vector((0, 0, 1)))
        return build_matrix(origin, normal, tangent)
    else:
        raise ValueError(f"Such space mode: {space_mode} is not supported")


def get_origin(mesh_component, origin_mode, custom_origins=None):
    if origin_mode == OR_MODE.cust:
        return get_median_center([Vector(custom_origins[sel.index]) if len(custom_origins) > sel.index else
                                  Vector(custom_origins[-1]) for sel in mesh_component])
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
    if origin_mode == OR_MODE.bound:
        return get_bound_center([v.co for v in verts])
    if origin_mode in [OR_MODE.median, OR_MODE.individ]:
        return get_median_center([v.co for v in verts])


def get_edges_origin(edges, origin_mode):
    if origin_mode == OR_MODE.bound:
        return get_bound_center([e.verts[0].co.lerp(e.verts[1].co, 0.5) for e in edges])
    if origin_mode in [OR_MODE.median, OR_MODE.individ]:
        return get_median_center([v.co for v in{v for e in edges for v in e.verts}])


def get_faces_origin(faces, origin_mode):
    if origin_mode == OR_MODE.bound:
        return get_bound_center([f.calc_center_bounds() for f in faces])
    if origin_mode in [OR_MODE.median, OR_MODE.individ]:
        return get_median_center([v.co for v in {v for f in faces for v in f.verts}])


def get_bound_center(verts):
    x_min = min(v.x for v in verts)
    y_min = min(v.y for v in verts)
    z_min = min(v.z for v in verts)
    x_max = max(v.x for v in verts)
    y_max = max(v.y for v in verts)
    z_max = max(v.z for v in verts)
    return Vector(((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2))


def get_median_center(verts):
    return reduce(lambda v1, v2: v1 + v2, verts) / len(verts)


def get_normals(mesh_component):
    if type(mesh_component[0]) == bmesh.types.BMVert:
        return calc_average_normal([v.normal for v in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMEdge:
        return calc_average_normal([get_edge_normal_tangent(e)[0] for e in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMFace:
        return calc_average_normal([f.normal for f in mesh_component])
    else:
        raise ValueError(f"Such type: {type(mesh_component)} is not supported")


def get_tangents(mesh_component):
    if type(mesh_component[0]) == bmesh.types.BMVert:
        return calc_average_normal([get_vert_tang(v) for v in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMEdge:
        return calc_average_normal([get_edge_normal_tangent(e)[1] for e in mesh_component])
    elif type(mesh_component[0]) == bmesh.types.BMFace:
        return calc_average_normal([get_face_tangent(f) for f in mesh_component])
    else:
        raise ValueError(f"Such type: {type(mesh_component)} is not supported")


def calc_average_normal(normals):
    return reduce(lambda v1, v2: v1 + v2, normals).normalized()


@lru_cache(maxsize=None)
def get_edge_normal_tangent(edge):
    direct = (edge.verts[1].co - edge.verts[0].co).normalized()
    _normal = (edge.verts[0].normal + edge.verts[1].normal).normalized()
    tang = direct.cross(_normal)
    return tang.cross(direct), tang


def get_vert_tang(vert):
    # returns tangent close to Blender logic in normal mode
    # vert - bmesh vertex
    if len(vert.link_edges) == 2:
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
    return chain(l, cycle([l[-1]]))


class SvTransformMesh(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    ...
    """
    bl_idname = 'SvTransformMesh'
    bl_label = 'Transform Mesh'
    bl_icon = 'MOD_BOOLEAN'

    def update_sockets(self, context):
        def hide(socket, statement):
            if socket.hide != statement:
                socket.hide_safe = statement

        hide(self.inputs['Origin'], True if self.origin_mode != OR_MODE.cust else False)
        hide(self.inputs['Space direction'], True if self.space_mode != SP_MODE.cust else False)
        updateNode(self, context)

    transform_mode_items = [(i, i, '') for i in ('Move', 'Scale', 'Rotate')]
    select_mode_items = [(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Verts', 'Edges', 'Faces'), ('VERTEXSEL', 'EDGESEL', 'FACESEL')))]
    origin_mode_items = [(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Individual', 'Median', 'Center bound box', 'Custom'),
        ('PIVOT_INDIVIDUAL', 'PIVOT_MEDIAN', 'PIVOT_BOUNDBOX', 'PIVOT_CURSOR')))]
    space_mode_items = [(n, n, '', ic, i) for i, (n, ic) in enumerate(zip(
        ('Normal', 'Global', 'Custom'), ('ORIENTATION_NORMAL', 'ORIENTATION_GLOBAL', 'ORIENTATION_CURSOR')))]
    direction_mode_items = [(n, n, '') for n in DIR_MODE]

    transform_mode: bpy.props.EnumProperty(items=transform_mode_items, update=updateNode)
    select_mode: bpy.props.EnumProperty(items=select_mode_items, update=updateNode)
    origin_mode: bpy.props.EnumProperty(items=origin_mode_items, name='Origin', default=OR_MODE.bound,
                                        update=update_sockets)
    space_mode: bpy.props.EnumProperty(items=space_mode_items, name='Space', update=update_sockets)
    direction_mode: bpy.props.EnumProperty(items=direction_mode_items, name='Direction', update=updateNode)
    origin: bpy.props.FloatVectorProperty(name='Origin', update=updateNode)
    space_direction: bpy.props.FloatVectorProperty(name="Space direction", default=(0, 0, 1), update=updateNode)
    direction: bpy.props.FloatVectorProperty(name='Direction', update=updateNode)
    factor: bpy.props.FloatProperty(name='Factor', default=1.0, update=updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.scale_y = 1.5
        row.prop(self, 'transform_mode', expand=True)
        layout.prop(self, 'origin_mode')
        layout.prop(self, 'space_mode')

    def draw_buttons_ext(self, context, layout):
        pass

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
                socket.draw_expander_template(context, col, self, 'direction')

    def process(self):
        if not self.inputs['Verts'].is_linked:
            return

        verts = self.inputs['Verts'].sv_get(deepcopy=False)
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=cycle([None]))
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=cycle([None]))
        mask = iter_last(self.inputs['Mask'].sv_get(deepcopy=False, default=[None]))
        origin = iter_last(self.inputs['Origin'].sv_get(deepcopy=False))
        space_direction = iter_last(self.inputs['Space direction'].sv_get(deepcopy=False))
        direction = iter_last(self.inputs['Direction'].sv_get(deepcopy=False))
        factor = iter_last(self.inputs['Factor'].sv_get(deepcopy=False))
        out = []
        for v, e, f, m, o, sd, d, fac in zip(verts, edges, faces, mask, origin, space_direction, direction, factor):
            out.append(transform_mesh(v, e, f, m, o, sd, d, fac, self.transform_mode, self.origin_mode,
                                      DIR_MODE.cust if self.inputs['Direction'].is_linked else self.direction_mode,
                                      self.select_mode, self.space_mode))
        self.outputs['Verts'].sv_set(out)


def register():
    bpy.utils.register_class(SvTransformMesh)


def unregister():
    bpy.utils.unregister_class(SvTransformMesh)
