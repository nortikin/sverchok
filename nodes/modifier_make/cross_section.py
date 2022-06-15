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
import mathutils

from bpy.props import BoolProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_generate, Vector_degenerate
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.nodes.modifier_change.mixn import ModifierLiteNode


def normal_consistent(bm, direction):
    flip_list = [face for face in bm.faces if not((face.normal - direction).length < 0.004)]
    bmesh.ops.reverse_faces(bm, faces=flip_list)


def section(cut_me_vertices, cut_me_edges, mx, pp, pno, FILL=False, TRI=True):
    """Finds the section mesh between a mesh and a plane
    cut_me: Blender Mesh - the mesh to be cut
    mx: Matrix - The matrix of object of the mesh for correct coordinates
    pp: Vector - A point on the plane
    pno: Vector - The cutting plane's normal
    Returns: Mesh - the resulting mesh of the section if any or
             Boolean - False if no section exists"""

    def equation_plane(point, normal_dest):
        # получаем коэффициенты уравнения плоскости по точке и нормали
        normal = normal_dest.normalized()
        A = normal.x
        B = normal.y
        C = normal.z
        D = (A*point.x+B*point.y+C*point.z)*-1

        if A < 0.0:
            A *= -1
            B *= -1
            C *= -1
            D *= -1

        return (A, B, C, D)

    def point_on_plane(v1, ep):
        formula = ep[0]*v1.x+ep[1]*v1.y+ep[2]*v1.z+ep[3]
        if formula == 0.0:
            return True
        else:
            return False

    if not cut_me_edges or not cut_me_vertices:
        return False

    verts = []
    ed_xsect = {}
    x_me = {}

    ep = equation_plane(pp, pno)
    cut_me_polygons = []
    if len(cut_me_edges[0]) > 2:
        cut_me_polygons = cut_me_edges.copy()
        cut_me_edges = []

    new_me = bpy.data.meshes.new('tempus')
    new_me.from_pydata(cut_me_vertices, cut_me_edges, cut_me_polygons)
    new_me.update(calc_edges=True)

    for ed_idx, ed in enumerate(new_me.edges):
        # getting a vector from each edge vertices to a point on the plane
        # first apply transformation matrix so we get the real section

        vert1 = ed.vertices[0]
        v1 = new_me.vertices[vert1].co @ mx.transposed()

        vert2 = ed.vertices[1]
        v2 = new_me.vertices[vert2].co @ mx.transposed()

        vec = v2-v1
        mul = vec @ pno
        if mul == 0.0:
            if not point_on_plane(v1, ep):
                # parallel and not on plane
                continue

        epv = ep[0]*vec.x + ep[1]*vec.y + ep[2]*vec.z
        if epv == 0:
            t0 = 0
        else:
            t0 = -(ep[0]*v1.x+ep[1]*v1.y+ep[2]*v1.z + ep[3]) / epv

        pq = vec*t0+v1
        if (pq-v1).length <= vec.length and (pq-v2).length <= vec.length:
            verts.append(pq)
            ed_xsect[ed.key] = len(ed_xsect)

    edges = []
    for f in new_me.polygons:
        # get the edges that the intersecting points form
        # to explain this better:
        # If a face has an edge that is proven to be crossed then use the
        # mapping we created earlier to connect the edges properly
        ps = [ed_xsect[key] for key in f.edge_keys if key in ed_xsect]

        if len(ps) == 2:
            edges.append(tuple(ps))

    x_me['Verts'] = verts
    x_me['Edges'] = edges
    bpy.data.meshes.remove(new_me)

    if x_me:
        if edges and FILL:

            bm = bmesh_from_pydata(verts, edges, [])
            bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.000002)
            fres = bmesh.ops.edgenet_prepare(bm, edges=bm.edges[:])

            if not TRI:
                # Alt + F
                bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=fres['edges'])
            else:
                # can generate N-Gons
                bmesh.ops.edgeloop_fill(bm, edges=fres['edges'])

            # in case there are islands generated by the above operations, and said islands have varying
            # normals (up/down flipped due to lack of surrounding information), then we force all faces
            # to conform to the normal as obtained by the Matrix that generates this cut.
            normal_consistent(bm, pno)

            bm.verts.index_update()
            bm.edges.index_update()
            bm.faces.index_update()

            verts, edges, faces = pydata_from_bmesh(bm)
            x_me['Verts'] = verts
            x_me['Edges'] = faces # edges   --  this was outputting faces into edges when fill was ticked?

            bm.clear()
            bm.free()


        return x_me
    else:
        return False


class CrossSectionNode(ModifierLiteNode, bpy.types.Node, SverchCustomTreeNode):
    '''Plane Intersection'''
    bl_idname = 'CrossSectionNode'
    bl_label = 'Cross Section'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CUT'

    fill_check: BoolProperty(
        name='fill', description='to fill section',
        default=False, update=updateNode)

    tri: BoolProperty(
        name='tri', description='triangle or polygon',
        default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edg_pol')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.inputs.new('SvMatrixSocket', 'cut_matrix')

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket', 'edges')

    def draw_buttons(self, context, layout):
        layout.prop(self, "fill_check", text="Fill section")
        layout.prop(self, "tri", text="alt+F / F")

    def process(self):
        mandatory_sockets = [self.inputs['vertices'], self.inputs['edg_pol'], self.inputs['cut_matrix']]
        if not all([s.is_linked for s in mandatory_sockets]):
            return

        verts_ob = Vector_generate(self.inputs['vertices'].sv_get())
        edg_pols_ob = self.inputs['edg_pol'].sv_get()

        if self.inputs['matrix'].is_linked:
            matrixs = self.inputs['matrix'].sv_get()
        else:
            matrixs = []
            for le in verts_ob:
                matrixs.append(Matrix())

        cut_mats = self.inputs['cut_matrix'].sv_get()

        verts_out = []
        edges_out = []
        for cut_mat in cut_mats:
            pp = Vector((0.0, 0.0, 0.0)) @ cut_mat.transposed()
            pno = Vector((0.0, 0.0, 1.0)) @ cut_mat.to_3x3().transposed()

            verts_pre_out = []
            edges_pre_out = []
            for idx_mob, matrix in enumerate(matrixs):
                idx_vob = min(idx_mob, len(verts_ob)-1)
                idx_epob = min(idx_mob, len(edg_pols_ob)-1)
                matrix = Matrix(matrix)

                x_me = section(verts_ob[idx_vob], edg_pols_ob[idx_epob], matrix, pp, pno, self.fill_check, self.tri)
                if x_me:
                    verts_pre_out.append(x_me['Verts'])
                    edges_pre_out.append(x_me['Edges'])

            if verts_pre_out:
                verts_out.extend(verts_pre_out)
                edges_out.extend(edges_pre_out)

        self.outputs['vertices'].sv_set(Vector_degenerate(verts_out))
        self.outputs['edges'].sv_set(edges_out)


def register():
    bpy.utils.register_class(CrossSectionNode)


def unregister():
    bpy.utils.unregister_class(CrossSectionNode)
