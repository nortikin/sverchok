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


def transform_mesh(verts, edges=None, faces=None, mask=None, custom_origin=None, custom_direction=None, factor=None, 
                   transform_mode=TR_MODE.move, origin_mode=OR_MODE.individ,
                   direction_mode=DIR_MODE.x, selection_mode=SEL_MODE.vert, space_mode=SP_MODE.glob):
    if mask and selection_mode == SEL_MODE.face and not faces:
        raise LookupError("Faces should be connected")
    if mask and selection_mode == SEL_MODE.edge and not any([faces, edges]):
        raise LookupError("Faces or edges should be connected")
    if not any(mask):
        return verts

    with get_bmesh(verts, edges, faces, space_mode == SP_MODE.norm) as bm:
        sel_verts = get_selected_verts(bm, mask, selection_mode)
        space = get_space(bm, mask, selection_mode, space_mode, origin_mode)

        if transform_mode == TR_MODE.move:
            # space matrix applies to bmesh vertices
            bmesh.ops.translate(bm, vec=space.to_quaternion() @ get_move_vector(custom_direction, factor, direction_mode),
                                space=Matrix(), verts=sel_verts)
        elif transform_mode == TR_MODE.rotate:
            bmesh.ops.rotate(bm, cent=space.to_translation(),
                             matrix=Matrix.Rotation(factor[0], 3, space.to_quaternion() @ get_move_axis(custom_direction, direction_mode)),
                             verts=sel_verts, space=Matrix())
        elif transform_mode == TR_MODE.scale:
            bmesh.ops.scale(bm, vec=get_scale_vector(custom_direction, factor, direction_mode),
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


def get_move_vector(direction, factor, direction_mode=DIR_MODE.x):
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower()) * factor[0]
    else:
        return Vector(direction[0]) * factor[0]


def get_scale_vector(direction, factor, direction_mode=DIR_MODE.x):
    index = {'X': 0, 'Y': 1, 'Z': 2}
    if direction_mode in DIR_MODE[:-1]:
        vec = [1, 1]
        vec.insert(index[direction_mode], 1 * factor[0])
        return Vector(vec)
    else:
        return Vector(direction[0]) * factor[0]


def get_move_axis(direction, direction_mode):
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower())
    else:
        return direction[0]


def get_selected_verts(bm, mask, sel_mode):
    if mask:
        if sel_mode == SEL_MODE.vert:
            return [vert for vert, select in zip(bm.verts, mask) if select]
        elif sel_mode == SEL_MODE.edge and bm.edges:
            return list({vert for edge, select in zip(bm.edges, mask) if select for vert in edge.verts})
        elif sel_mode == SEL_MODE.face and bm.faces:
            return list({vert for face, select in zip(bm.faces, mask) if select for vert in face.verts})
    else:
        return bm.verts


def get_space(bm, mask, sel_mode, space_mode, origin_mode):
    if sel_mode == SEL_MODE.vert:
        selected = [v for v, m in zip(bm.verts, mask or cycle([True])) if m]
    elif sel_mode == SEL_MODE.edge:
        selected = [e for e, m in zip(bm.edges, mask or cycle([True])) if m]
    elif sel_mode == SEL_MODE.face:
        selected = [f for f, m in zip(bm.faces, mask or cycle([True])) if m]
    else:
        raise ValueError(f"Given selection mode: {sel_mode} is unsupported")
    origin = get_origin(selected, origin_mode)
    if space_mode == SP_MODE.glob:
        return Matrix.Translation(origin)
    elif space_mode == SP_MODE.norm:
        normal = get_normals(selected)
        tangent = get_tangents(selected)
        return build_matrix(origin, normal, tangent)


def get_origin(mesh_component, origin_mode):
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


def get_edges_origin(edges, origin_mode):
    if origin_mode == OR_MODE.bound:
        return get_bound_center([e.verts[0].co.lerp(e.verts[1].co, 0.5) for e in edges])


def get_faces_origin(faces, origin_mode):
    if origin_mode == OR_MODE.bound:
        return get_bound_center([f.calc_center_bounds() for f in faces])


def get_bound_center(verts):
    x_min = min(v.x for v in verts)
    y_min = min(v.y for v in verts)
    z_min = min(v.z for v in verts)
    x_max = max(v.x for v in verts)
    y_max = max(v.y for v in verts)
    z_max = max(v.z for v in verts)
    return Vector(((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2))


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
    # n1 = normals.pop()
    # for n2 in normals:
    #     n1 = (n1 + n2).normalized()
    # return n1


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
    # x_axis = normal.cross(tangent)
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
        if self.origin_mode != OR_MODE.cust:
            self.inputs['Origin'].hide = True
        else:
            self.inputs['Origin'].hide = False
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
    origin_mode: bpy.props.EnumProperty(items=origin_mode_items, name='Origin', default='Custom', update=update_sockets)
    space_mode: bpy.props.EnumProperty(items=space_mode_items, name='Space', update=updateNode)
    direction_mode: bpy.props.EnumProperty(items=direction_mode_items, name='Direction', update=updateNode)
    origin: bpy.props.FloatVectorProperty(name='Origin', update=updateNode)
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
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
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
        edges = self.inputs['Edges'].sv_get(deepcopy=False) if self.inputs['Edges'].is_linked else cycle([None])
        faces = self.inputs['Faces'].sv_get(deepcopy=False) if self.inputs['Faces'].is_linked else cycle([None])
        mask = iter_last(self.inputs['Mask'].sv_get(deepcopy=False)) if self.inputs['Mask'].is_linked else cycle([None])
        origin = iter_last(self.inputs['Origin'].sv_get(deepcopy=False))
        direction = iter_last(self.inputs['Direction'].sv_get(deepcopy=False))
        factor = iter_last(self.inputs['Factor'].sv_get(deepcopy=False))
        out = []
        for v, e, f, m, o, d, fac in zip(verts, edges, faces, mask, origin, direction, factor):
            out.append(transform_mesh(v, e, f, m, o, d, fac, self.transform_mode, self.origin_mode,
                                      self.direction_mode, self.select_mode, self.space_mode))
        self.outputs['Verts'].sv_set(out)


def register():
    bpy.utils.register_class(SvTransformMesh)


def unregister():
    bpy.utils.unregister_class(SvTransformMesh)
