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
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e, second_as_first_cycle as safc)


class SvBMOpsNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    ''' BMesh Ops '''
    bl_idname = 'SvBMOpsNodeMK2'
    bl_label = 'BMesh Ops 2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_BMESH_OPS'

    PV = ['remove_doubles(bm,verts=e,dist=v[0])',
                #'remove_doubles distance'],
          'collapse(bm,edges=e,uvs=bool(int(v[0])))',
                #'collapse uvs'],
          'unsubdivide(bm,verts=e,iterations=int(v[0]))',
                #'unsubdivide iterations'],
          'holes_fill(bm,edges=e,sides=int(v[0]))',
                #'joles_fill sides'],
          'dissolve_faces(bm,faces=e,use_verts=bool(int(v[0])))',
                #'dissolve_faces use_verts'],
          'dissolve_edges(bm,edges=e,use_verts=bool(int(v[0])),use_face_split=bool(int(v[1])))',
                #'dissolve_edges use_verts, use_fill_split'],
          'dissolve_verts(bm,verts=e,use_face_split=bool(int(v[0])),use_boundary_tear=bool(int(v[1])))',
                #'dissolve_verts face_split, boundary_tear'],
          'connect_verts_concave(bm,faces=e)',
                #'connect_verts_concave'],
          'recalc_face_normals(bm,faces=e)',
                #'recals_face_normals'],
          'rotate_edges(bm,edges=e,use_ccw=bool(int(v[0])))',
                #'rotate_edges use_ccv'],
          'connect_verts_nonplanar(bm,angle_limit=v[0],faces=e)',
                #'connect_verts_nonplanar angle_limit'],
          'triangulate(bm,faces=e,quad_method=int(v[0]),ngon_method=int(v[1]))',
                #'triangulate quad_method, ngon_method'],
          'grid_fill(bm,edges=e,mat_nr=int(v[0]),use_smooth=bool(int(v[1])),use_interp_simple=bool(int(v[2])))',
                #'grid_fill material, use_smooth, use_smooth'],
          'poke(bm,faces=e,offset=v[0],center_mode=int(v[1]),use_relative_offset=bool(int(v[2])))',
                #'poke offset, mode, relative'],
          'bridge_loops(bm,edges=e,use_pairs=bool(int(v[0])),use_cyclic=bool(int(v[1])),use_merge=bool(int(v[2])),merge_factor=v[3],twist_offset=v[4])',
                #'bridge_loops use_pairs, use_cyclic, use_merge, merge_factor, twist_offset'],
          'beautify_fill(bm,faces=e,edges=[],use_restrict_tag=bool(int(v[0])),method=int(v[1]))',
                #'beautify_fill use_restrict, method'],
          'smooth_vert(bm,verts=e,factor=v[0],mirror_clip_x=bool(int(v[1])),mirror_clip_y=bool(int(v[2])),mirror_clip_z=bool(int(v[3])),clip_dist=v[4],use_axis_x=bool(int(v[5])),use_axis_y=bool(int(v[6])),use_axis_z=bool(int(v[7])))',
                #'smooth_verts,factor,clipx,clipy,clipz,clipdist,useX,useY,useZ'],
          'join_triangles(bm,faces=e,cmp_seam=bool(int(v[0])),cmp_sharp=bool(int(v[1])),cmp_uvs=bool(int(v[2])),cmp_vcols=bool(int(v[3])),cmp_materials=bool(int(v[4])),angle_face_threshold=v[5],angle_shape_threshold=v[6])',
                #'join_triangles seam, sharp, uvs, vcols, mats, angleface, anglethreshold'],
          'subdivide_edgering(bm,edges=e,interp_mode=int(v[0]),smooth=v[1],cuts=int(v[2]),profile_shape=int(v[3]),profile_shape_factor=v[4])',
                #'subdiv_edgering mode, smooth, cuts, shape, factor'],
          'inset_individual(bm,faces=e,thickness=v[0],depth=v[1],use_even_offset=bool(int(v[2])),use_interpolate=bool(int(v[3])),use_relative_offset=bool(int(v[4])))',
                #'inset_individual, thkns,depth,use_offset, use_inerpol,use_relative'],
          'inset_region(bm,faces=e,use_boundary=bool(int(v[0])),use_even_offset=bool(int(v[1])),use_interpolate=bool(int(v[2])),use_relative_offset=bool(int(v[3])),use_edge_rail=bool(int(v[4])),thickness=v[5],depth=v[6],use_outset=bool(int(v[7])))',
                #'inset_region, use_bondary, use_even_offset, use_interpolate, use_rel_offset, use_edge_rail, thickns, depth, use_outset'],
          ]

    oper: EnumProperty(name="BMop", default=PV[0], items=e(PV), update=updateNode)

    V0: FloatProperty(name='V0', default=0, update=updateNode)
    V1: FloatProperty(name='V1', default=0, update=updateNode)
    V2: FloatProperty(name='V2', default=0, update=updateNode)
    V3: FloatProperty(name='V3', default=0, update=updateNode)
    V4: FloatProperty(name='V4', default=0, update=updateNode)
    V5: FloatProperty(name='V5', default=0, update=updateNode)
    V6: FloatProperty(name='V6', default=0, update=updateNode)
    V7: FloatProperty(name='V7', default=0, update=updateNode)

    def sv_init(self, context):
        si = self.inputs.new
        si('SvStringsSocket', 'bmesh_list')
        si('SvStringsSocket', 'BM_element(e)')
        self.outputs.new('SvStringsSocket', 'bmesh_list')

    def draw_buttons(self, context, layout):
        layout.prop(self, "oper", text="Get")
        for i in range(self.oper.count("=v[")):
            layout.prop(self, "V"+str(i), text="v"+str(i))
        for i in range(self.oper.count("=int(v[")):
            layout.prop(self, "V"+str(i), text="v"+str(i))

    def process(self):
        if not self.outputs['bmesh_list'].is_linked:
            return
        bml, e = self.inputs
        obj = bml.sv_get()
        v = [self.V0,self.V1,self.V2,self.V3,self.V4,self.V5,self.V6,self.V7]
        outp = []
        op = "bmesh.ops."+self.oper
        print(op)
        if e.is_linked:
            element = e.sv_get()
            for bm, e in zip(obj, element):
                exec(op)
                outp.append(bm.copy())
                bm.free()
        else:
            if "verts=e" in op:
                cur = "verts"
            elif "edges=e" in op:
                cur = "edges"
            elif "faces=e" in op:
                cur = "faces"
            for bm in obj:
                e = getattr(bm, cur)
                exec(op)
                outp.append(bm.copy())
                bm.free()
        self.outputs['bmesh_list'].sv_set(outp)


def register():
    bpy.utils.register_class(SvBMOpsNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvBMOpsNodeMK2)

if __name__ == '__main__':
    register()