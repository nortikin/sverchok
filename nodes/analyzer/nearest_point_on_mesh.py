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
from bpy.props import EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.bvh_tree import bvh_tree_from_polygons
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

def take_third(elem):
    return elem[2]

def append_multiple(container, data):
    for r, rl in zip(container, data):
        r.append(rl)

def translate_data(data):
    try:
        return data[0][:], data[1][:], data[2], data[3]
    except TypeError:
        return [], [], -1, -1


def svmesh_to_bvh_lists(vsock, fsock, safe_check):
    for vertices, polygons in zip(vsock, fsock):
        yield bvh_tree_from_polygons(vertices, polygons, all_triangles=False, epsilon=0.0, safe_check=safe_check)

def nearest_point_in_mesh(verts, faces, points, safe_check=True):
    '''Expects multiple objects lists (level of nesting 3)'''
    output = [[] for i in range(4)]
    for bvh, pts in zip(svmesh_to_bvh_lists(verts, faces, safe_check), points):
        res_local = list(zip(*[translate_data(bvh.find_nearest(P)) for P in pts]))
        append_multiple(output, res_local)

    return output

def nearest_in_range(verts, faces, points, distance, safe_check=True, flat_output=True):
    '''
    verts, faces and points: Expects multiple objects lists (level of nesting 3)
    distace: expects a list with level of nesting of 2
    '''
    output = [[] for i in range(4)]
    for bvh, pts, dist in zip(svmesh_to_bvh_lists(verts, faces, safe_check), points, distance):

        res_local = [[] for i in range(4)]

        for pt, d in zip(pts, cycle(dist)):
            res = bvh.find_nearest_range(pt, d)
            #claning results:
            res = sorted(res, key=take_third)
            unique = []
            if flat_output:
                for r in res:
                    if not r[2] in unique:
                        unique.append(r[2])
                        append_multiple(res_local, translate_data(r))

            else:
                sub_res_local = [[] for i in range(4)]
                for r in res:
                    if not r[2] in unique:
                        unique.append(r[2])
                        append_multiple(sub_res_local, translate_data(r))

                append_multiple(res_local, sub_res_local)

        append_multiple(output, res_local)

    return output


class SvNearestPointOnMeshNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    """
    Triggers: BVH Closest Point
    Tooltip: Find nearest point on mesh surfaces
    """
    bl_idname = 'SvNearestPointOnMeshNode'
    bl_label = 'Nearest Point on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POINT_ON_MESH'

    modes = [
            ("find_nearest", "Nearest", "", 0),
            ("find_nearest_range", "Nearest in range", "", 1),
        ]

    def update_sockets(self, context):
        self.inputs['Distance'].hide_safe = self.mode == 'find_nearest'
        updateNode(self, context)

    mode: EnumProperty(
        name="Mode", items=modes,
        default='find_nearest',
        update=update_sockets)

    safe_check: BoolProperty(
        name='Safe Check',
        description='When disabled polygon indices referring to unexisting points will crash Blender but makes node faster',
        default=True)

    flat_output: BoolProperty(
        name='Flat Output',
        description='Output a single list for every list in stead of a list of lists',
        default=True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')
        if self.mode == 'find_nearest_range':
            layout.prop(self, 'flat_output')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')
        layout.prop(self, 'mode')
        layout.prop(self, 'safe_check')

    def sv_init(self, context):
        si = self.inputs.new
        so = self.outputs.new
        si('SvVerticesSocket', 'Verts')
        si('SvStringsSocket', 'Faces').nesting_level = 3
        for s in self.inputs[:2]:
            s.is_mandatory = True
        si('SvVerticesSocket', 'Points').use_prop = True
        d = si('SvStringsSocket', 'Distance')
        d.use_prop = True
        d.default_property = 10.0
        d.hide_safe = True

        so('SvVerticesSocket', 'Location')
        so('SvVerticesSocket', 'Normal')
        so('SvStringsSocket', 'Index')
        so('SvStringsSocket', 'Distance')


    def process_data(self, params):
        verts, faces, points, distance = params
        if self.mode == 'find_nearest':
            return nearest_point_in_mesh(verts, faces, points,
                                         safe_check=self.safe_check)
        else:
            return nearest_in_range(verts, faces, points, distance,
                                    safe_check=self.safe_check,
                                    flat_output=self.flat_output)

def register():
    bpy.utils.register_class(SvNearestPointOnMeshNode)


def unregister():
    bpy.utils.unregister_class(SvNearestPointOnMeshNode)
