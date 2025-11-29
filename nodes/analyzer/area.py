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

import math

from mathutils import Vector, Matrix

import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from mathutils.geometry import area_tri as area
from mathutils.geometry import tessellate_polygon as tessellate
from sverchok.utils.modules.polygon_utils import areas_from_polygons

class SvAreaNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    ''' Area '''
    bl_idname = 'SvAreaNodeMK2'
    bl_label = 'Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'

    sum_faces: BoolProperty(name='sum faces', default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "vertices")
        self.inputs.new('SvStringsSocket', "polygons")
        self.inputs.new('SvStringsSocket', "groups_id")

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['polygons'].label = 'Polygons'
        self.inputs['groups_id'].label = 'Group By'

        self.outputs.new('SvStringsSocket', "area")
        self.outputs.new('SvStringsSocket', "groups_id")
        self.outputs['area'].label = 'Area'
        self.outputs['groups_id'].label = 'Group By'

    def draw_buttons(self, context, layout):
        layout.prop(self, "sum_faces", text="Sum Faces")

    def process(self):
        inputs = self.inputs
        objs_vertices = inputs["vertices"].sv_get(default=None)
        objs_polygons = inputs["polygons"].sv_get(default=None)

        outputs = self.outputs
        if not outputs['area'].is_linked or not all([objs_vertices, objs_polygons]):
            return
        
        if inputs['groups_id'].is_linked==False:
            objs_groups_id=[]
            for I, polygons in enumerate(objs_polygons):
                objs_groups_id.append([0]*len(polygons))

        else:
            objs_groups_id=inputs["groups_id"].sv_get()

        # no smart auto extending here.
        res_areas = []
        res_groups_id = []
        for vertices, polygons, groups_id in zip(objs_vertices, objs_polygons, objs_groups_id):
            obj1_areas = []
            obj1_groups_id = []
            if self.sum_faces==True:
                group_polygons=dict()
                len_polygons = len(polygons)
                for I, group_id in enumerate(groups_id):
                    if I<=len_polygons-1:
                        if group_id not in group_polygons:
                            group_polygons[group_id] = []
                        group_polygons[group_id].append( polygons[I])
                    else:
                        break
                    pass

                for k in sorted(group_polygons):
                    _polygons = group_polygons[k]
                    areas_of_group = areas_from_polygons(vertices, _polygons, sum_faces=self.sum_faces)
                    obj1_areas.extend(areas_of_group)
                    obj1_groups_id.extend([k]*len(areas_of_group))
            else:
                areas = areas_from_polygons(vertices, polygons, sum_faces=self.sum_faces)
                obj1_areas.extend(areas)
                obj1_groups_id.extend(groups_id)

            res_areas.append(obj1_areas)
            res_groups_id.append(obj1_groups_id)
        
        outputs['area'].sv_set(res_areas)
        outputs['groups_id'].sv_set(res_groups_id)

classes = [
    SvAreaNodeMK2
]
register, unregister = bpy.utils.register_classes_factory(classes)