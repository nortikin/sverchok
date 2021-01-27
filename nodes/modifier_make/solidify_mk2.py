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
from mathutils import Vector
import bpy
from bmesh.types import BMVert, BMEdge, BMFace
from bpy.props import FloatProperty, BoolProperty
import bmesh
from itertools import cycle
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, get_partial_result_pydata
# by Linus Yng

def create_edges(bm, v_len):
    edges =[]
    for edge in bm.edges[:]:
        edges.append([v.index for v in edge.verts[:]])

    edges_new = [[e[0]+v_len, e[1]+v_len] for e in edges]
    side_edges = [[v.index, v.index+v_len] for v in bm.verts if v.is_boundary]
    return edges + edges_new +side_edges

def solidify(vertices, faces, thickness, offset=None, even=True):

    if not faces or not vertices:
        return False

    if len(faces[0]) == 2:
        return False
    if offset is None:
        offset = [-1]
    verlen = set(range(len(vertices)))

    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    geom_in = bm.verts[:] + bm.edges[:] + bm.faces[:]

    if len(offset) == 1 and offset == -1:
        if even:
            new_verts = [(v.co+ v.normal * t * v.calc_shell_factor())[:] for v, t in zip(bm.verts, cycle(thickness))]
        else:
            new_verts = [(v.co+ v.normal*t)[:] for v, t in zip(bm.verts, cycle(thickness))]

        vertices_out = vertices +  new_verts
    else:
        if even:
            new_verts=[(v.co + v.normal * t * v.calc_shell_factor() *((-o/2)+0.5))[:] for v, t, o in zip(bm.verts, cycle(thickness), cycle(offset))]
            old_verts=[(v.co - v.normal * t * v.calc_shell_factor() * ((o/2)+0.5))[:] for v, t, o in zip(bm.verts, cycle(thickness), cycle(offset))]

        else:
            new_verts=[(v.co + v.normal * t * ((-o/2) + 0.5))[:] for v, t, o in zip(bm.verts, cycle(thickness), cycle(offset))]
            old_verts=[(v.co - v.normal * t * ((o/2) + 0.5))[:] for v, t, o in zip(bm.verts, cycle(thickness), cycle(offset))]

        vertices_out = old_verts +  new_verts

    v_len = len(vertices)
    new_pols = [[c+v_len for c in p] for p in faces]
    rim_pols = []
    for e in bm.edges:
        if e.is_boundary:
            rim_pols.append([
                e.verts[0].index,
                e.verts[1].index,
                e.verts[1].index + v_len,
                e.verts[0].index + v_len])

    faces_out = [f[::-1] for f in faces] + new_pols + rim_pols
    pol_group = [0]*len(faces) + [1]*len(new_pols) + [2]*len(rim_pols)
    new_verts_mask = [0]*len(vertices)+ [1]*len(new_verts)

    edges_out = create_edges(bm, v_len)
    return (vertices_out, edges_out, faces_out, new_pols, rim_pols, pol_group, new_verts_mask)

class SvSolidifyNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude/Thicken Mesh
    Tooltip: Extrude along normal the mesh surface.

    """
    bl_idname = 'SvSolidifyNodeMk2'
    bl_label = 'Solidify'
    bl_icon = 'MOD_SOLIDIFY'

    thickness: FloatProperty(
        name='Thickness', description='Shell thickness',
        default=0.1, update=updateNode)
    offset: FloatProperty(
        name='Offset', description='Offset Thickness from center',
        default=1, soft_min=-1, soft_max=1, update=updateNode)
    even: BoolProperty(
        name='Even Thickness', description='Mantain Thinkness by adjusting sharp corners',
        default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', 'Offset').prop_name = 'offset'

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Polygons')
        self.outputs.new('SvStringsSocket', 'New Pols')
        self.outputs.new('SvStringsSocket', 'Rim Pols')
        self.outputs.new('SvStringsSocket', 'Pols Group')
        self.outputs.new('SvStringsSocket', 'New Verts Mask')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'even')
    def process(self):
        if not any((s.is_linked for s in self.outputs)):
            return

        if not (self.inputs['Vertices'].is_linked and self.inputs['Polygons'].is_linked):
            return

        verts = self.inputs['Vertices'].sv_get(deepcopy=False)
        polys = self.inputs['Polygons'].sv_get(deepcopy=False)
        thickness = self.inputs['Thickness'].sv_get(deepcopy=False)
        offset = self.inputs['Offset'].sv_get(deepcopy=False)

        verts_out = []
        edges_out = []
        polys_out = []
        new_pols = []
        rim_pols = []
        pols_groups = []
        new_verts_mask = []

        for v, p, t, o in zip_long_repeat(verts, polys, thickness, offset):
            res = solidify(v, p, t, o, self.even)

            if not res:
                return
            verts_out.append(res[0])
            edges_out.append(res[1])
            polys_out.append(res[2])
            new_pols.append(res[3])
            rim_pols.append(res[4])
            pols_groups.append(res[5])
            new_verts_mask.append(res[6])

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Polygons'].sv_set(polys_out)
        self.outputs['New Pols'].sv_set(new_pols)
        self.outputs['Rim Pols'].sv_set(rim_pols)
        self.outputs['Pols Group'].sv_set(pols_groups)
        self.outputs['New Verts Mask'].sv_set(new_verts_mask)


def register():
    bpy.utils.register_class(SvSolidifyNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvSolidifyNodeMk2)
