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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.data_structure import updateNode


class SvVolumeNodeMK3(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: volume
    Tooltip: Calculate volume of an object
    """
    bl_idname = 'SvVolumeNodeMK3'
    bl_label = 'Volume'
    bl_icon = 'SNAP_VOLUME'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices' ).label = 'Vertices'
        self.inputs.new('SvStringsSocket' , 'polygons' ).label = 'Polygons'
        self.inputs.new('SvStringsSocket' , 'groups_id').label = 'Group By'

        self.outputs.new('SvStringsSocket', 'volumes'   ).label = 'Volumes'
        self.outputs.new('SvStringsSocket', 'groups_id').label = 'Group By'
        self.outputs.new('SvStringsSocket', 'grouped_volumes'   ).label = 'Grouped Volumes'
        self.outputs.new('SvStringsSocket', 'grouped_id').label = 'Grouped id'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices = self.inputs['vertices'].sv_get(deepcopy=False, default=[])
        faces = self.inputs['polygons'].sv_get(deepcopy=False, default=[])
        if self.inputs['groups_id'].is_linked:
            groups_id = self.inputs['groups_id'].sv_get(deepcopy=False, default=[])
        else:
            groups_id = [[0]]
        
        if len(groups_id)==0:
            groups_id.append([0])

        while( len(groups_id)<len(vertices)):
            groups_id.append(groups_id[-1])
        while( len(groups_id)>len(vertices)):
            groups_id.pop()

        volumes_out = []
        grouped_volumes = dict()
        out_groups_id = []
        out_grouped_volumes = []
        out_grouped_id = []
        for verts_obj, faces_obj, group_id in zip(vertices, faces, groups_id):
            group_id_0 = group_id[0]
            out_groups_id.append([group_id_0])
            bm = bmesh_from_pydata(verts_obj, [], faces_obj, normal_update=True)
            vol = bm.calc_volume()
            volumes_out.append([vol])
            if group_id_0 not in grouped_volumes:
                grouped_volumes[group_id_0] = []
            grouped_volumes[group_id_0].append(vol)
            bm.free()
            pass

        for key, value in grouped_volumes.items():
            summ_volumes = sum(value)
            out_grouped_volumes.append([summ_volumes])
            out_grouped_id.append([key])
            pass

        self.outputs['volumes'].sv_set(volumes_out)
        self.outputs['groups_id'].sv_set(out_groups_id)
        self.outputs['grouped_volumes'].sv_set(out_grouped_volumes)
        self.outputs['grouped_id'].sv_set(out_grouped_id)


classes = [SvVolumeNodeMK3]
register, unregister = bpy.utils.register_classes_factory(classes)