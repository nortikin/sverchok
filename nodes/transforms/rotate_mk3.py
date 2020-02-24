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
from math import radians

from mathutils import Matrix, Vector, Euler, Quaternion

import bpy
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty, StringProperty
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control

def matrix_apply_np(verts, matrix):
    '''taken from https://blender.stackexchange.com/a/139517'''

    verts_co_4d = np.ones(shape=(verts.shape[0], 4), dtype=np.float)
    verts_co_4d[:, :-1] = verts  # cos v (x,y,z,1) - point,   v(x,y,z,0)- vector
    return np.einsum('ij,aj->ai', matrix, verts_co_4d)[:, :-1]

def np_rotate_many_centers(props, mat, np_local_match):
    verts, centers = np_local_match([np.array(p) for p in props[:2]])
    return matrix_apply_np(verts - centers, mat) + centers

def np_rotate_one_center(props, mat):
    center = np.array(props[1][0])[np.newaxis,:]
    verts = np.array(props[0])
    if np.linalg.norm(center[0]) > 0:
        return matrix_apply_np(verts - center, mat) + center

    return matrix_apply_np(verts, mat)

def rotate_one_center(props, mat):
    c = Vector(props[1][0])
    if c.magnitude > 0:
        return [(c + mat @ (Vector(ve) - c))[:] for ve in props[0]]
    return [(mat @ Vector(ve))[:] for ve in props[0]]

def rotate_vecs_constant_mat(props, mat, output_numpy, np_local_match, result):
    if len(props[1]) > 1:
        rotated = np_rotate_many_centers(props, mat, np_local_match)
        result.append(rotated if output_numpy else rotated.tolist())
    else:
        if output_numpy:
            result.append(np_rotate_one_center(props, mat))
        else:
            result.append(rotate_one_center(props, mat))

def axis_rotate_meshes(params, constant, matching_f):
    '''
    params are verts, centers, axis and angle
    - verts, centers and axis should be list as [[[float, float, float],],] (Level 3)
    - Angle should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    desired_levels = [3, 3, 3, 2]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    match_mode, output_numpy = constant
    params = matching_f(params)
    np_local_match = numpy_list_match_func[match_mode]
    local_match = list_match_func[match_mode]
    for props in zip(*params):
        rotated = []
        lens = map(len, props[2:])
        if any(l > 1 for l in lens):
            verts, centers, axis, angle = local_match(props)
            for ve, ce, ax, an in zip(verts, centers, axis, angle):
                mat = Matrix.Rotation(radians(an), 4, ax)
                c = Vector(ce)
                rotated.append((c + mat @ (Vector(ve) - c))[:])
            result.append(np.array(rotated) if output_numpy else rotated)
        else:
            ax = props[2][0]
            an = props[3][0]
            mat = Matrix.Rotation(radians(an), 4, ax)
            rotate_vecs_constant_mat(props, mat, output_numpy, np_local_match, result)

    return result

def euler_rotate_meshes(params, constant, matching_f):
    '''
    params are verts, centers, x, y and z
    - verts and centers should be list as [[[float, float, float],],] (Level 3)
    - x,y,z should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    desired_levels = [3, 3, 2, 2, 2]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    match_mode, output_numpy, order = constant
    params = matching_f(params)
    np_local_match = numpy_list_match_func[match_mode]
    local_match = list_match_func[match_mode]
    for props in zip(*params):
        lens = map(len, props[2:])
        if any(l > 1 for l in lens):
            verts, centers, x_ang, y_ang, z_ang = local_match(props)
            rotated = []
            for ve, cent, x, y, z in zip(verts, centers, x_ang, y_ang, z_ang):
                mat = Euler((radians(x), radians(y), radians(z)), order).to_matrix().to_4x4()
                cen_v = Vector(cent)
                rotated.append((mat @ (Vector(ve)- cen_v) + cen_v)[:])
            result.append(np.array(rotated) if output_numpy else rotated)
        else:
            x, y, z = props[2][0], props[3][0], props[4][0]
            mat = Euler((radians(x), radians(y), radians(z)), order).to_matrix().to_4x4()
            rotate_vecs_constant_mat(props, mat, output_numpy, np_local_match, result)

    return result

def quat_rotate_meshes(params, constant, matching_f):
    '''
    params are verts, centers, x, y, z and w
    - verts and centers should be list as [[[float, float, float],],] (Level 3)
    - x, y, z and w should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    desired_levels = [3, 3, 2, 2, 2, 2]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    match_mode, output_numpy = constant
    params = matching_f(params)
    np_local_match = numpy_list_match_func[match_mode]
    local_match = list_match_func[match_mode]
    for props in zip(*params):
        lens = map(len, props[2:])
        if any(l > 1 for l in lens):
            verts, centers, x_ang, y_ang, z_ang, w_ang = local_match(props)
            rotated = []
            for ve, ce, x, y, z, w in zip(verts, centers, x_ang, y_ang, z_ang, w_ang):
                quat = Quaternion((w, x, y, z)).normalized()
                ce_v = Vector(ce)
                rotated.append(((quat @ (Vector(ve) - ce_v) + ce_v))[:])

            result.append(np.array(rotated) if output_numpy else rotated)
        else:
            x, y, z, w = props[2][0], props[3][0], props[4][0], props[5][0]
            mat = Quaternion((w, x, y, z)).normalized().to_matrix().to_4x4()
            rotate_vecs_constant_mat(props, mat, output_numpy, np_local_match, result)
    return result

class SvRotationNodeMk3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Rotate vertices
    Tooltip: Rotate input vertices using Axis/Angle, Euler or Quaternion

    """

    bl_idname = 'SvRotationNodeMk3'
    bl_label = 'Rotation_mk3'
    bl_icon = 'NONE'
    sv_icon = 'SV_ROTATE'


    centers_: FloatVectorProperty(
        name='Centers', description='Center of the scaling transform',
        size=3, default=(0, 0, 0),
        update=updateNode)
    axis_: FloatVectorProperty(
        name='Axis', description='Rotation Axis',
        size=3, default=(0, 0, 1),
        update=updateNode)
    angle_: FloatProperty(
        name='Angle', description='rotation angle', default=0.0, update=updateNode)
    x_: FloatProperty(
        name='X', description='X angle', default=0.0, update=updateNode)
    y_: FloatProperty(
        name='Y', description='Y angle', default=0.0, update=updateNode)
    z_: FloatProperty(
        name='Z', description='Z angle', default=0.0, update=updateNode)
    w_: FloatProperty(
        name='W', description='W', default=1.0, update=updateNode)

    actual_mode: StringProperty(default="")

    def update_sockets(self):
        print(1,'updating sockets', self.mode, self.actual_mode)
        mode = self.mode
        if mode == self.actual_mode:
            return

        print(2, 'updating sockets', self.mode, self.actual_mode,  len(self.inputs))
        while len(self.inputs) > 2:
            print(3, 'updating sockets', self.mode, self.actual_mode)
            self.inputs.remove(self.inputs[-1])

        if mode == 'AXIS':
            # self.inputs.new('SvVerticesSocket', "center").prop_name = "centers"
            self.inputs.new('SvVerticesSocket', "Axis").prop_name = "axis_"
            self.inputs.new('SvStringsSocket', "Angle").prop_name = "angle_"
        elif mode in ('EULER', 'QUAT'):
            self.inputs.new('SvStringsSocket', "X").prop_name = "x_"
            self.inputs.new('SvStringsSocket', "Y").prop_name = "y_"
            self.inputs.new('SvStringsSocket', "Z").prop_name = "z_"
            if mode == 'QUAT':
                self.inputs.new('SvStringsSocket', "W").prop_name = "w_"

        self.actual_mode = mode
    @throttled
    def mode_change(self, context):
        print('changing')
        self.update_sockets()
        # just because click doesn't mean we need to change mode
        # mode = self.mode
        # if mode == self.actual_mode:
        #     return
        #
        # while len(self.inputs) > 2:
        #     self.inputs.remove(self.inputs[-1])
        #
        # if mode == 'AXIS':
        #     # self.inputs.new('SvVerticesSocket', "center").prop_name = "centers"
        #     self.inputs.new('SvVerticesSocket', "Axis").prop_name = "axis_"
        #     self.inputs.new('SvStringsSocket', "Angle").prop_name = "angle_"
        # elif mode in ('EULER', 'QUAT'):
        #     self.inputs.new('SvStringsSocket', "X").prop_name = "x_"
        #     self.inputs.new('SvStringsSocket', "Y").prop_name = "y_"
        #     self.inputs.new('SvStringsSocket', "Z").prop_name = "z_"
        #     if mode == 'QUAT':
        #         self.inputs.new('SvStringsSocket', "W").prop_name = "w_"
        #
        # self.actual_mode = mode

    modes = [
        ("AXIS", "Axis", "Axis and angle rotation", 1),
        ("EULER", "Euler", "Euler Rotation", 2),
        ("QUAT", "Quat", "Quaternion Rotation", 3),
    ]

    mode: EnumProperty(
        name="mode", description="mode", default='AXIS', items=modes, update=mode_change)

    orders = [
        ('XYZ', "XYZ",        "", 0),
        ('XZY', 'XZY',        "", 1),
        ('YXZ', 'YXZ',        "", 2),
        ('YZX', 'YZX',        "", 3),
        ('ZXY', 'ZXY',        "", 4),
        ('ZYX', 'ZYX',        "", 5),
    ]
    order: EnumProperty(
        name="Order", description="Order", default="XYZ", items=orders, update=updateNode)

    multiplier: FloatProperty(
        name='Scale', description='Multiplying  factor',
        default=1.0, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):

        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvVerticesSocket', "Centers").prop_name = "centers_"
        self.inputs.new('SvVerticesSocket', "Axis").prop_name = "axis_"
        self.inputs.new('SvStringsSocket', "Angle").prop_name = "angle_"
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.update_sockets()
        # self.mode_change(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        if self.mode == 'EULER':
            layout.prop(self, "order", text="Order:")


    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, 'output_numpy')
        layout.prop(self, 'list_match', expand=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, 'output_numpy')
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def migrate_from(self, old_node):
        # self.mode = old_node.mode
        #
        if old_node.mode == 'AXIS':
            return True
        self.location.y -= 250
        print(self.mode, self.actual_mode)
        # self.update_sockets()
        print(self.mode, self.actual_mode)
        # while len(self.inputs) > 2:
        #     self.inputs.remove(self.inputs[-1])
        #
        # if self.mode in ('EULER', 'QUAT'):
        #     self.inputs.new('SvStringsSocket', "X").prop_name = "x_"
        #     self.inputs.new('SvStringsSocket', "Y").prop_name = "y_"
        #     self.inputs.new('SvStringsSocket', "Z").prop_name = "z_"
        #     if self.mode == 'QUAT':
        #         self.inputs.new('SvStringsSocket', "W").prop_name = "w_"
        return False

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        result = []

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs]

        matching_f = list_match_func[self.list_match]
        ops = [self.list_match, self.output_numpy]
        if self.mode == 'AXIS':
            desired_levels = [3, 3, 3, 2]
            rotate_func = axis_rotate_meshes
        elif self.mode == 'EULER':
            desired_levels = [3, 3, 2, 2, 2]
            rotate_func = euler_rotate_meshes
            ops.append(self.order)
        else:
            desired_levels = [3, 3, 2, 2, 2, 2]
            rotate_func = quat_rotate_meshes

        result = recurse_f_level_control(params, ops, rotate_func, matching_f, desired_levels)

        self.outputs[0].sv_set(result)

classes = [SvRotationNodeMk3]
register, unregister = bpy.utils.register_classes_factory(classes)
