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
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
import numpy as np
from bpy.props import BoolProperty, StringProperty, FloatVectorProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode

from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level


def UV(self, bm, uv_layer):
    # makes UV from layout texture area to sverchok vertices and polygons.
    vertices_dict = {}
    polygons_new = []
    polygons_new_append = polygons_new.append
    for fi in bm.faces:
        polygons_new_pol = []
        polygons_new_pol_append = polygons_new_pol.append
        for loop in fi.loops:
            li = loop.index
            polygons_new_pol_append(li)
            uv = loop[uv_layer].uv
            vertices_dict[li] = [ uv.x, uv.y, 0.0]

        polygons_new_append(polygons_new_pol)

    vertices_new = list( vertices_dict.values() )
    return [vertices_new, polygons_new]


class SvUVPointonMeshNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    ''' Transform vectors from UV space to Object space '''
    bl_idname = 'SvUVPointonMeshNodeMK2'
    bl_label = 'Find UV Coord on Surface'
    bl_icon = 'GROUP_UVS'
    is_scene_dependent = True
    is_animation_dependent = True

    object_ref: StringProperty(default='', update=updateNode)

    apply_modifiers: BoolProperty(
        name="Apply Modifiers", description="Off: use original object from scene\nOn: Apply modifiers before select UV Map",
        default=False, update=updateNode)

    uv_select_modes = [
            ('active_item', "Active Selected", "UV Map selected by an active elem in the list of UV Maps of object data", 0),
            ('active_render', "Active Render", "UV Map selected by property active_render in the list of UV Maps of object data (actived photo icon)", 1)
        ]

    uv_select_mode : EnumProperty(
            name = "Select UV Map by",
            description = "UV Map select from object data property by",
            items = uv_select_modes,
            default = 'active_item',
            update = updateNode)

    def sv_draw_buttons(self, context, layout):
        row = layout.row()
        col = row.column()
        col.label(text='Apply midifiers:')
        col = row.column()
        col.alignment = 'LEFT'
        col.prop(self, 'apply_modifiers', expand=True, text='')
        row = layout.row()
        row.column().label(text="Select UV Map by:")
        row.column().prop(self, 'uv_select_mode', expand=True ) #, text='')


    def sv_init(self, context):
        self.width = 250
        si, so = self.inputs.new, self.outputs.new
        si('SvMatrixSocket', 'Object Matrix')
        si('SvObjectSocket', 'Object Mesh')
        si('SvVerticesSocket', 'Point on UV')
        so('SvVerticesSocket', 'Point on mesh')
        so('SvVerticesSocket', 'UVMapVert')
        so('SvStringsSocket', 'UVMapPoly')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        
        iObjectMatrixes, iObjects, iPointsUV = self.inputs
        Matrixes = iObjectMatrixes.sv_get(default = [Matrix()])
        Objects = iObjects.sv_get(default=[])
        if len(Objects)==0:
            raise Exception(f'socket "Object Mesh" has to be connected or object has to be selected')
        Pom, uvV, uvP = self.outputs
        PointsUV = iPointsUV.sv_get(default=[])

        Matrixes = ensure_nesting_level(Matrixes, 1)
        Objects = ensure_nesting_level(Objects, 1)
        if iPointsUV.is_linked:
            PointsUV = ensure_nesting_level(PointsUV, 3)
        else:
            PointsUV = [[]]        

        POMs, UVMAPPs, UVMAPVs = [], [], []
        for i, (obj_matrix, obj, PointUV) in enumerate(zip_long_repeat(Matrixes, Objects,PointsUV) ):
            if not obj.data.uv_layers:
                raise Exception(f"Object '{obj.data.name}'[{i}] has no UV Maps. Open Properties->Data->UV Maps and check list of UV Maps.")
            
            # get all UV Maps name in object UV Maps list
            uv_layer_active_render_name = obj.data.uv_layers[0].name
            for uv in obj.data.uv_layers:
                if uv.active_render==True:
                    uv_layer_active_render_name = uv.name  # get UV Map name active render (photo mark)
                    break

            bm = bmesh.new()
            if self.apply_modifiers:
                # apply modifiers and build mesh after it
                sv_depsgraph = bpy.context.evaluated_depsgraph_get()
                scene_object = sv_depsgraph.objects[ obj.name ]
                object_to_mesh = scene_object.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                bm.from_mesh(object_to_mesh)
                scene_object.to_mesh_clear()
            else:
                # get mesh of original object from scene
                bm.from_mesh(obj.data)

            uv_layer_active = bm.loops.layers.uv.active
            uv_layer_active_render = obj.data.uv_layers[0]
            for uv in bm.loops.layers.uv:
                if uv.name==uv_layer_active_render_name:
                    uv_layer_active_render = uv
                    break

            if self.uv_select_mode=='active_item':
                uv_layer = uv_layer_active
            else: #if self.uv_select_mode=='active_render':
                uv_layer = uv_layer_active_render

            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            UVMAPV, UVMAPP = UV(self, bm, uv_layer)
            if Pom.is_linked:
                # resore UV to 3D
                bvh = BVHTree.FromPolygons(UVMAPV, UVMAPP, all_triangles=False, epsilon=0.0)
                lpom = [] # result in 3D
                for Puv in PointUV:
                    loc, norm, ind, dist = bvh.find_nearest(Puv)
                    _found_poly = bm.faces[ind]
                    _p1, _p2, _p3 = [v.co for v in bm.faces[ind].verts[0:3] ]
                    _uv1, _uv2, _uv3 = [l[uv_layer].uv.to_3d() for l in _found_poly.loops[0:3] ]
                    _V = barycentric_transform(Puv, _uv1, _uv2, _uv3, _p1, _p2, _p3)
                    pom = obj_matrix @ Vector(_V[:])
                    lpom.append( list( pom ) )
                
                POMs.append(lpom)
            bm.clear()
            UVMAPVs.append(UVMAPV)
            UVMAPPs.append(UVMAPP)

        if Pom.is_linked:
            Pom.sv_set(POMs)

        if uvV.is_linked:
            uvV.sv_set(UVMAPVs)
            uvP.sv_set(UVMAPPs)


def register():
    bpy.utils.register_class(SvUVPointonMeshNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvUVPointonMeshNodeMK2)
