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
from bpy.props import EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e)


class SvBMOpsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' BMesh Ops '''
    bl_idname = 'SvBMOpsNode'
    bl_label = 'bmesh_ops'
    bl_icon = 'OUTLINER_OB_EMPTY'

    PV = ['remove_doubles(bm,verts=Vidx,dist=v[0])',
          'collapse(bm,edges=Eidx)',
          'unsubdivide(bm,verts=Vidx,iterations=v[0])',
          'holes_fill(bm,edges=Eidx,sides=v[0])',
          'bridge_loops(bm,edges=Eidx,use_pairs=b[0],use_cyclic=b[1],use_merge=b[2],merge_factor=v[0],twist_offset=v[1])',
          'smooth_vert(bm,verts=Vidx,factor=v[0],mirror_clip_x=b[0],mirror_clip_y=b[1],mirror_clip_z=b[2],clip_dist=v[1],use_axis_x=b[3],use_axis_y=b[4],use_axis_z=b[5])',
          'dissolve_verts(bm,verts=Vidx,use_face_split=b[0],use_boundary_tear=b[1])',
          'dissolve_edges(bm,edges=Eidx,use_verts=b[0],use_face_split=b[1])',
          'dissolve_faces(bm,faces=Pidx,use_verts=b[0])',
          'triangulate(bm,faces=Pidx,quad_method=v[0],ngon_method=v[1])',
          'join_triangles(bm,faces=Pidx,cmp_sharp=b[0],cmp_uvs=b[1],cmp_vcols=b[2],cmp_materials=b[3],limit=v[0])',
          'connect_verts_concave(bm,faces=Pidx)',
          'connect_verts_nonplanar(bm,angle_limit=v[0],faces=Pidx)',
          'subdivide_edgering(bm,edges=Eidx,interp_mode=v[0],smooth=v[1],cuts=v[2],profile_shape=v[3],profile_shape_factor=v[4])',
          'inset_individual(bm,faces=Pidx,thickness=v[0],depth=v[1],use_even_offset=b[0],use_interpolate=b[1],use_relative_offset=b[2])',
          'grid_fill(bm,edges=Eidx,mat_nr=v[0],use_smooth=b[0],use_interp_simple=b[1])',
          'edgenet_fill(bm, edges=Eidx, mat_nr=v[0], use_smooth=b[0], sides=v[1])',
          'rotate_edges(bm, edges=Eidx, use_ccw=b[0])'
          ]

    oper = EnumProperty(name="BMop", default=PV[0], items=e(PV), update=updateNode)

    def sv_init(self, context):
        si = self.inputs.new
        si('StringsSocket', 'Objects')
        si('StringsSocket', 'Value(v)')
        si('StringsSocket', 'Bool(b)')
        si('StringsSocket', 'idx')
        self.outputs.new('VerticesSocket', 'Verts')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Polys')

    def draw_buttons(self, context, layout):
        layout.prop(self, "oper", "Get")

    def process(self):
        if not self.outputs['Verts'].is_linked:
            return
        si = self.inputs
        obj = si['Objects'].sv_get()
        obl = len(obj)
        if obl>1:
            b = (si['Bool(b)'].sv_get([[0,0,0,0,0,0]])*obl)[:obl]
            v = (si['Value(v)'].sv_get([[1,1,1,1,1]])*obl)[:obl]
            idx = (si['idx'].sv_get([[0]])*obl)[:obl]
        else:
            b = si['Bool(b)'].sv_get([[0,0,0,0,0,0]])
            v = si['Value(v)'].sv_get([[1,1,1,1,1]])
            idx = si['idx'].sv_get([[0]])
        Sidx = si['idx'].is_linked
        outv = []
        oute = []
        outp = []
        op = "bmesh.ops."+self.oper
        if "verts=Vidx" in op:
            cur = 1
        elif "edges=Eidx" in op:
            cur = 2
        elif "faces=Pidx" in op:
            cur = 3
        for ob, b, v, idx in zip(obj,b,v,idx):
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            if Sidx:
                if cur == 1:
                    bm.verts.ensure_lookup_table()
                    Vidx = [bm.verts[i] for i in idx]
                elif cur == 2:
                    bm.edges.ensure_lookup_table()
                    Eidx = [bm.edges[i] for i in idx]
                elif cur == 3:
                    bm.faces.ensure_lookup_table()
                    Pidx = [bm.faces[i] for i in idx]
            else:
                Vidx,Eidx,Pidx=bm.verts,bm.edges,bm.faces
            exec(op)
            outv.append([i.co[:] for i in bm.verts])
            oute.append([[i.index for i in e.verts] for e in bm.edges])
            outp.append([[i.index for i in p.verts] for p in bm.faces])
            bm.free()
        self.outputs['Verts'].sv_set(outv)
        self.outputs['Edges'].sv_set(oute)
        self.outputs['Polys'].sv_set(outp)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvBMOpsNode)


def unregister():
    bpy.utils.unregister_class(SvBMOpsNode)
