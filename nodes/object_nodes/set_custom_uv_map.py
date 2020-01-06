# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import match_long_repeat, repeat_last, updateNode


def set_custom_map(obj, verts, faces, uv_name='SVMap', matrix=None):
    if uv_name in obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[uv_name])
    obj.data.uv_layers.new(name=uv_name)
    set_uv(verts, faces, obj, uv_name)


def set_uv(verts, faces, obj, uv_name, matrix=None):
    # for uv_obj, obj in zip(ver_uv, obj_in):
    #     pass
    #
    # len_loop = len(obj.data.loops)
    # len_uv_in = len(uv_obj)
    #
    # if len_loop < len_uv_in:
    #     uv_obj = uv_obj[0:len_loop]
    # elif len_loop > len_uv_in:
    #     _, uv_obj = match_long_repeat([list(range(len_loop)), uv_obj])
    #
    # xy_uv = [(u, v) for u, v, _ in uv_obj]
    #
    # per_loop_list = [uv for pair in xy_uv for uv in pair]
    if matrix:
        loop_points = [(mat @ Vector(co))[:2] for co, mat in zip((verts[i] for face in faces for i in face),
                                                                 cycle([matrix]))]
    else:
        loop_points = [Vector(co)[:2] for co in (verts[i] for face in faces for i in face)]
    obj.data.uv_layers[uv_name].data.foreach_set(
        "uv",
        [val for point in loop_points for val in point])


def deform_uv(obj, uv_name, matrix):

    uv_co = [l.uv for l in obj.data.uv_layers[uv_name].data]

    xy_uv = [(m @ l.to_3d())[:2] for l, m in zip(uv_co, repeat_last([matrix]))]
    per_loop_list = [uv for pair in xy_uv for uv in pair]

    obj.data.uv_layers[uv_name].data.foreach_set("uv", per_loop_list)


class SvSetCustomUVMap(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...

    ...
    ...
    """
    bl_idname = 'SvSetCustomUVMap'
    bl_label = 'Set custom UV map'
    bl_icon = 'GROUP_UVS'

    active: bpy.props.BoolProperty(name='Make active', default=True, update=updateNode)
    uv_name: bpy.props.StringProperty(name='Uv name', default='SVMap', description='Name of UV layer',
                                      update=updateNode)

    def draw_buttons(self, context, layout):
        row = layout.column(align=True)
        row.prop(self, 'uv_name', text='', icon='GROUP_UVS')
        row.prop(self, 'active', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvMatrixSocket', 'Matrix')
        self.outputs.new('SvObjectSocket', "Objects")

    def process(self):
        if not all([sock.is_linked for sock in list(self.inputs)[:-1]]):
            return

        for ob, v, f, m in zip(
                self.inputs['Objects'].sv_get(),
                self.inputs['Verts'].sv_get(deepcopy=False),
                self.inputs['Faces'].sv_get(deepcopy=False),
                self.inputs['Matrix'].sv_get(deepcopy=False) if self.inputs['Matrix'].is_linked else cycle([None])):

            set_custom_map(ob, v, f, self.uv_name, m)

        self.outputs['Objects'].sv_set(self.inputs['Objects'].sv_get())


def register():
    bpy.utils.register_class(SvSetCustomUVMap)


def unregister():
    bpy.utils.unregister_class(SvSetCustomUVMap)
