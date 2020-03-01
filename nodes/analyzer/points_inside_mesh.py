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


from itertools import cycle
import bpy
from bpy.props import (IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty)
import bmesh
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.noise import seed_set, random_unit_vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


def generate_random_unitvectors():
    # may need many more directions to increase accuracy
    # generate up to 6 directions, filter later
    seed_set(140230)
    return [random_unit_vector() for i in range(6)]

directions = generate_random_unitvectors()


def get_points_in_mesh(verts, faces, points, eps=0.0, num_samples=3):
    mask_inside = []

    bvh = BVHTree.FromPolygons(verts, faces, all_triangles=False, epsilon=eps)

    for direction in directions[:num_samples]:
        samples = []
        mask = samples.append

        for point in points:
            hit = bvh.ray_cast(point, direction)
            if hit[0]:
                v = hit[1].dot(direction)
                mask(not v < 0.0)
            else:
                mask(False)

        mask_inside.append(samples)

    if len(mask_inside) == 1:
        return mask_inside[0]
    else:
        mask_totals = []
        oversample = mask_totals.append
        num_points = len(points)

        # exactly what the criteria should be here is not clear, this seems enough.
        for i in range(num_points):
            fsum = sum(mask_inside[j][i] for j in range(num_samples))

            if num_samples == 2:
                oversample(fsum >= 1)
            elif num_samples == 3:
                oversample(fsum >= 2)
            elif num_samples == 4:
                oversample(fsum >= 3)
            elif num_samples == 5:
                oversample(fsum >= 4)
            elif num_samples == 6:
                oversample(fsum >= 4)
        return mask_totals


def are_inside(verts, faces, points, eps):
    bm = bmesh_from_pydata(verts, [], faces, normal_update=True)
    mask_inside = []
    mask = mask_inside.append
    bvh = BVHTree.FromBMesh(bm, epsilon=eps)

    # return points on polygons
    for point in points:
        fco, normal, _, _ = bvh.find_nearest(point)
        p2 = fco - Vector(point)
        v = p2.dot(normal)
        mask(not v < 0.0)  # addp(v >= 0.0) ?

    return mask_inside


def get_points_in_mesh_2D(verts, faces, points, normal, eps=0.0):
    mask_totals = []
    bvh = BVHTree.FromPolygons(verts, faces, all_triangles=False, epsilon=eps)

    for point in points:
        inside = False
        for direction in normal:
            hit = bvh.ray_cast(point, Vector(direction))
            if hit[0]:
                inside = True
                break
            else:
                hit = bvh.ray_cast(point, -Vector(direction))
                if hit[0]:
                    inside = True
                    break
        mask_totals.append(inside)
    return mask_totals

def get_points_in_mesh_2D_clip(verts, faces, points, normal, clip_distance, eps=0.0, matchig_method='REPEAT'):
    mask_totals = []
    bvh = BVHTree.FromPolygons(verts, faces, all_triangles=False, epsilon=eps)

    normal, clip_distance = list_match_func[matchig_method]([normal, clip_distance])
    for point in points:
        inside = False
        for direction, dist in zip(normal, clip_distance):
            hit = bvh.ray_cast(point, Vector(direction))
            if hit[0] and hit[3] < dist:
                inside = True
                break
            else:
                hit = bvh.ray_cast(point, -Vector(direction))
                if hit[0] and hit[3] < dist:
                    inside = True
                    break
        mask_totals.append(inside)
    return mask_totals

class SvPointInside(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mask verts with geom
    Tooltip:  Mask points inside geometry in 2D or 3D

    """
    bl_idname = 'SvPointInside'
    bl_label = 'Points Inside Mesh'
    sv_icon = 'SV_POINTS_INSIDE_MESH'

    mode_options = [(k[0], k[1], '', i) for i, k in enumerate([("algo_1", "Regular"), ("algo_2", "Multisample")])]
    dimension_options = [(k, k, '', i) for i, k in enumerate(["2D", "3D"])]

    @throttled
    def update_sockets(self, context):
        if self.dimensions_mode == '2D' and len(self.inputs) < 4:
            self.inputs.new('SvVerticesSocket', 'Plane Normal').prop_name = 'normal'
        elif self.dimensions_mode == '3D' and len(self.inputs) > 3:
            self.inputs.remove(self.inputs['Plane Normal'])
        if self.dimensions_mode == '2D' and self.limit_max_dist and len(self.inputs) < 5:
            self.inputs.new('SvStringsSocket', 'Max Dist').prop_name = 'max_dist'
        elif self.dimensions_mode == '3D' or  not self.limit_max_dist:
            if 'Max Dist' in self.inputs:
                self.inputs.remove(self.inputs['Max Dist'])

    dimensions_mode: EnumProperty(
        items=dimension_options,
        description="offers different approaches to finding internal points",
        default="3D", update=update_sockets)

    normal: FloatVectorProperty(
        name='Normal', description='Plane Normal',
        size=3, default=(0, 0, 1),
        update=updateNode)
    max_dist: FloatProperty(
        name='Max Distance', description='Maximum valid distance',
        default=10.0, update=updateNode)
    limit_max_dist: BoolProperty(
        name='Limit Proyection', description='Limit projection distance',
        default=False, update=update_sockets)

    selected_algo: EnumProperty(
        items=mode_options,
        description="offers different approaches to finding internal points",
        default="algo_1", update=updateNode)

    epsilon_bvh: FloatProperty(
        name='Tolerance', description='fudge value',
        default=0.0, min=0.0, max=1.0,
        update=updateNode)

    num_samples: IntProperty(
        name='Samples Num',
        description='Number of rays to cast',
        min=1, max=6, default=3,
        update=updateNode)

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, between Normal and Max Distance",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'verts')
        self.inputs.new('SvStringsSocket', 'faces')
        self.inputs.new('SvVerticesSocket', 'points')
        self.outputs.new('SvStringsSocket', 'mask')
        self.outputs.new('SvVerticesSocket', 'verts')
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'dimensions_mode', expand=True)
        if self.dimensions_mode == '2D':
            layout.prop(self, 'limit_max_dist', expand=True)
        else:
            layout.prop(self, 'selected_algo', expand=True)
            if self.selected_algo == 'algo 2':
                layout.prop(self, 'epsilon_bvh', text='Epsilon')
                layout.prop(self, 'num_samples', text='Samples')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'list_match_global', text='Global Match')
        if self.dimensions_mode == '2D' and self.limit_max_dist:
            layout.prop(self, 'list_match_local', text='Local Match')

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        if self.dimensions_mode == '2D' and self.limit_max_dist:
            layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def get_data(self):
        # general parameters
        params = [s.sv_get() for s in self.inputs[:3]]
        # special parameters
        if self.dimensions_mode == '2D':
            params.append(self.inputs['Plane Normal'].sv_get(default=[[]]))
            if self.limit_max_dist:
                params.append(self.inputs['Max Dist'].sv_get(default=[[]]))

        match_func = list_match_func[self.list_match_global]
        params = match_func(params)
        # general options
        params.append(cycle([self.epsilon_bvh]))
        # special options and main_func
        if self.dimensions_mode == '3D':
            if self.selected_algo == 'algo_1':
                main_func = are_inside
            elif self.selected_algo == 'algo_2':
                params.append(cycle([self.num_samples]))
                main_func = get_points_in_mesh
        else:
            if self.limit_max_dist:
                params.append(cycle([self.list_match_local]))
                main_func = get_points_in_mesh_2D_clip
            else:
                main_func = get_points_in_mesh_2D

        return main_func, params

    def process(self):

        if not all(socket.is_linked for socket in self.inputs[:3]):
            return

        main_func, params = self.get_data()

        mask = []
        for par in zip(*params):
            mask.append(main_func(*par))

        self.outputs['mask'].sv_set(mask)

        if self.outputs['verts'].is_linked:
            out_verts = []
            for masked, pts_in in zip(mask, params[2]):
                out_verts.append([p for m, p in zip(masked, pts_in) if m])
            self.outputs['verts'].sv_set(out_verts)


def register():
    bpy.utils.register_class(SvPointInside)


def unregister():
    bpy.utils.unregister_class(SvPointInside)
