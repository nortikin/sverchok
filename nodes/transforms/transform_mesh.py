# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


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
    bm = bmesh.new()
    bm_verts = [bm.verts.new(co) for co in verts]
    bm_edges = [bm.edges.new((bm_verts[i1], bm_verts[i2])) for i1, i2 in edges] if edges else []
    bm_faces = [bm.faces.new([bm_verts[i] for i in face]) for face in faces] if faces else []
    sel_verts = get_selected_verts(bm_verts, bm_edges, bm_faces, mask, selection_mode)
    if space_mode == SP_MODE.norm:
        bm.normal_update()
        space = Matrix.Rotation(factor)

    if transform_mode == TR_MODE.move:
        bmesh.ops.translate(bm, vec=get_move_vector(custom_direction, factor, direction_mode),
                            space=Matrix(), verts=sel_verts)
    elif transform_mode == TR_MODE.rotate:
        bmesh.ops.rotate(bm, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(factor[0], 3, get_move_axis(custom_direction, direction_mode)),
                         verts=sel_verts, space=Matrix())
    elif transform_mode == TR_MODE.scale:
        bmesh.ops.scale(bm, vec=custom_direction[0], space=Matrix.Translation(custom_origin[0]), verts=sel_verts)

    return [v.co[:] for v in bm_verts]


def get_move_vector(direction, factor, direction_mode=DIR_MODE.x):
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower()) * factor[0]
    else:
        return Vector(direction[0]) * factor[0]


def get_move_axis(direction, direction_mode):
    if direction_mode in DIR_MODE[:-1]:
        return getattr(DIR_VEC, direction_mode.lower())
    else:
        return direction[0]


def get_selected_verts(bm_verts, bm_edges, bm_faces, mask, sel_mode):
    if mask:
        if sel_mode == SEL_MODE.vert:
            return [vert for vert, select in zip(bm_verts, mask) if select]
        elif sel_mode == SEL_MODE.edge and bm_edges:
            return list({vert for edge, select in zip(bm_edges, mask) if select for vert in edge.verts})
        elif sel_mode == SEL_MODE.face and bm_faces:
            return list({vert for face, select in zip(bm_faces, mask) if select for vert in face.verts})
    else:
        return bm_verts


def get_normal_tangent(bm_verts, bm_edges, bm_faces, mask, sel_mode):
    if sel_mode == SEL_MODE.vert:
        return calc_average_normal([vert.noraml for vert, sel in zip(bm_verts, mask) if mask])
    elif sel_mode == SEL_MODE.edge:
        return calc_average_normal(
            [v.normal for v in {vert for edge, sel in zip(bm_edges, mask) if edge for vert in edge.verts}])
    elif sel_mode == SEL_MODE.face:
        return calc_average_normal([face.normal for face, sel in zip(bm_faces, mask) if sel])


def calc_average_normal(normals):
    n1 = normals.pop()
    for n2 in normals:
        n1 = (n1 + n2).normalized()
    return n1


def calc_edge_normal(edge):
    direct = (edge.verts[1].co - edge.verts[0].co).normalized()
    _normal = (edge.verts[0].normal + edge.verts[1].normal).normalized()
    tang = direct.cross(_normal)
    return tang.cross(direct)


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
