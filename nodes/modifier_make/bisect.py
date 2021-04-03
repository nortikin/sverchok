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
from bpy.props import BoolProperty, IntVectorProperty
import bmesh
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Matrix_generate, Vector_generate
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.mesh_functions import mesh_join
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

# based on CrossSectionNode
# but using python bmesh code for driving
# by Linus Yng / edits+upgrades Dealga McArdle and Victor Doval

def bisect_bmesh(bm, pp, pno, outer, inner, fill):


    geom_in = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(
        bm, geom=geom_in, dist=0.00001,
        plane_co=pp, plane_no=pno, use_snap_center=False,
        clear_outer=outer, clear_inner=inner)

    # this needs work function with solid geometry
    if fill:
        fres = bmesh.ops.edgenet_prepare(
            bm, edges=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        )
        bmesh.ops.edgeloop_fill(bm, edges=fres['edges'])

    edges = []
    faces = []
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    verts, edges, faces = pydata_from_bmesh(bm)

    bm.clear()
    bm.free()

    return (verts, edges, faces)

def bisect(cut_me_vertices, cut_me_edges, pp, pno, outer, inner, fill):

    if not cut_me_edges or not cut_me_vertices:
        return False

    if len(cut_me_edges[0]) > 2:
        bm = bmesh_from_pydata(cut_me_vertices, [], cut_me_edges)
    else:
        bm = bmesh_from_pydata(cut_me_vertices, cut_me_edges, [])

    return bisect_bmesh(bm, pp, pno, outer, inner, fill)



class SvBisectNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    ''' Matrix Cuts geometry'''
    bl_idname = 'SvBisectNode'
    bl_label = 'Bisect'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_BISECT'

    build_bmesh = True
    bmesh_inputs = [0, 1]

    inner: BoolProperty(
        name='inner', description='clear inner',
        default=False, update=updateNode)

    outer: BoolProperty(
        name='outer', description='clear outer',
        default=False, update=updateNode)

    fill: BoolProperty(
        name='fill', description='Fill cuts',
        default=False, update=updateNode)

    slice_mode: BoolProperty(
        name="Per Object", update=updateNode, default=False,
        description="slice each object with all matrices, or match object and matrices individually")

    slice_mode: BoolProperty(
        name="Per Object", update=updateNode, default=False,
        description="slice each object with all matrices, or match object and matrices individually")

    remove_empty: BoolProperty(
        name="Clean Output", update=updateNode, default=False,
        description="Remove empty objects from output")

    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('JOIN', 'Join', 'Join (mesh join) last level of objects', 1),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]
    correct_output: bpy.props.EnumProperty(
        name="Simplify Output",
        description="Behavior on different list lengths, object level",
        items=correct_output_modes, default="FLAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edg_pol')
        self.inputs.new('SvMatrixSocket', 'cut_matrix')

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket', 'edges')
        self.outputs.new('SvStringsSocket', 'polygons')

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.label(text='Remove:')
        row = col.row(align=True)
        row.prop(self, 'inner', text="Inner", toggle=True)
        row.prop(self, 'outer', text="Outer", toggle=True)
        row = layout.row(align=True)
        row.prop(self, 'fill', text="Fill", toggle=True)
        layout.prop(self, 'remove_empty')

        row.prop(self, 'slice_mode', toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'correct_output')
        layout.prop(self, 'list_match')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")
        if not self.slice_mode:
            layout.prop_menu_enum(self, 'correct_output')

    def pre_setup(self):
        self.inputs['vertices'].is_mandatory = True
        self.inputs['edg_pol'].is_mandatory = True

        if self.slice_mode:
            self.inputs['cut_matrix'].nesting_level = 1
        else:
            self.inputs['cut_matrix'].nesting_level = 2

        self.inputs['cut_matrix'].default_mode = 'MATRIX'


    def process_data(self, params):

        verts_out = []
        edges_out = []
        polys_out = []
        if self.slice_mode:
            bms, cut_mats = params
            for cut_mat, bm in zip(cut_mats, bms):
                pp = cut_mat.to_translation()
                pno = Vector((0.0, 0.0, 1.0)) @ cut_mat.to_3x3().transposed()

                res = bisect_bmesh(bm.copy(), pp, pno, self.outer, self.inner, self.fill)
                if not res:
                    return
                if self.remove_empty:
                    if not res[0]:
                        continue
                verts_out.append(res[0])
                edges_out.append(res[1])
                polys_out.append(res[2])
        else:
            bms, cut_mats_s = params
            for cut_mats, bm in zip(cut_mats_s, bms):
                vs, es, ps = [], [], []
                for cut_mat in cut_mats:
                    pp = cut_mat.to_translation()
                    pno = Vector((0.0, 0.0, 1.0)) @ cut_mat.to_3x3().transposed()
                    res = bisect_bmesh(bm.copy(), pp, pno, self.outer, self.inner, self.fill)
                    if not res:
                        return
                    if self.remove_empty:
                        if not res[0]:
                            continue
                    if self.correct_output == 'FLAT':
                        verts_out.append(res[0])
                        edges_out.append(res[1])
                        polys_out.append(res[2])
                    else:
                        vs.append(res[0])
                        es.append(res[1])
                        ps.append(res[2])

                if self.correct_output == 'NONE':
                    verts_out.append(vs)
                    edges_out.append(es)
                    polys_out.append(ps)
                elif self.correct_output == 'JOIN':
                    r = mesh_join(vs, es, ps)
                    verts_out.extend(r[0])
                    edges_out.extend(r[1])
                    polys_out.extend(r[2])



        return verts_out, edges_out, polys_out



def register():
    bpy.utils.register_class(SvBisectNode)


def unregister():
    bpy.utils.unregister_class(SvBisectNode)
