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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, match_long_cycle
import numpy as np


def edge_elongation(np_verts, np_verts_n, np_edges):
    '''Calculate edge length variation'''

    pairs_edges = np_verts[np_edges, :]
    vect_rest = (pairs_edges[:, 0, :] - pairs_edges[:, 1, :])
    dist_rest = np.linalg.norm(vect_rest, axis=1)
    pairs = np_verts_n[np_edges, :]
    dif_v = pairs[:, 0, :] - pairs[:, 1, :]
    dist = np.linalg.norm(dif_v, axis=1)
    elong = dist - dist_rest

    return elong


def vert_edge_defromation(elong, np_verts, np_edges):
    '''Redistribute edge length variation to vertices'''

    x = elong[:, np.newaxis] / 2
    v_len = len(np_verts)
    deformation = np.zeros((v_len, v_len, 1), dtype=np.float32)
    deformation[np_edges[:, 0], np_edges[:, 1], :] = x
    deformation[np_edges[:, 1], np_edges[:, 0], :] = x

    return np.sum(deformation, axis=1)[:, 0]


def area_calc_setup(pols):
    '''Analyze pols information'''

    np_pols = np.array(pols)
    p_len = len(pols)
    if np_pols.dtype == np.object:
        np_len = np.vectorize(len)
        pols_sides = np_len(np_pols)
        pols_sides_max = np.amax(pols_sides)
        pols = match_long_cycle(pols)
        np_pols = np.array(pols)
        p_non_regular = True
    else:
        p_non_regular = False
        pols_sides = np.array(p_len)
        pols_sides_max = len(pols[0])

    return [np_pols, pols_sides_max, pols_sides, p_len, p_non_regular]


def get_normals(v_pols):
    '''Calculate polygon normals'''

    v1 = v_pols[:, 1, :] - v_pols[:, 0, :]
    v2 = v_pols[:, 2, :] - v_pols[:, 0, :]
    pols_normal = np.cross(v1, v2)
    pols_normal_d = np.linalg.norm(pols_normal, axis=1)

    return pols_normal / pols_normal_d[:, np.newaxis]


def area_calc(np_verts, area_params):
    '''Calculate polygons area'''

    np_pols, pols_sides_max, pols_sides, p_len, p_non_regular = area_params

    v_pols = np_verts[np_pols, :]
    pols_normal = get_normals(v_pols)

    prod = np.zeros((pols_sides_max, p_len, 3), dtype=np.float32)
    if p_non_regular:

        for i in range(pols_sides_max):
            mask = pols_sides > i
            end_i = (i + 1) % pols_sides_max
            prod[i, mask, :] = np.cross(v_pols[mask, i, :], v_pols[mask, end_i, :])

        prod = np.sum(prod, axis=0)
        area = abs(np.sum(prod * pols_normal, axis=1) / 2)

    else:
        for i in range(pols_sides_max):
            end_i = (i + 1) % pols_sides_max
            prod[i, :, :] = np.cross(v_pols[:, i, :], v_pols[:, end_i, :])

        prod = np.sum(prod, axis=0)
        area = abs(np.sum(prod * pols_normal, axis=1) / 2)

    return area


def area_to_verts(np_verts, area_params, pols_deformation):
    '''Redistribute area variation to verts.'''

    np_pols, pols_sides_max, pols_sides, p_len, advance = area_params

    pol_id = np.arange(p_len)
    pol_def_to_vert = pols_deformation / pols_sides
    deformation = np.zeros((len(np_verts), p_len), dtype=np.float32)
    if advance:
        for i in range(pols_sides_max):
            mask = pols_sides > i
            deformation[np_pols[mask, i], pol_id[mask]] += pol_def_to_vert[mask]

    else:
        for i in range(pols_sides_max):
            deformation[np_pols[:, i], pol_id] += pol_def_to_vert

    return np.sum(deformation, axis=1)


def area_variation(np_verts, np_verts_n, area_params):
    '''get areas and subtract relaxed area to deformed area'''

    relax_area = area_calc(np_verts, area_params)
    defromation_area = area_calc(np_verts_n, area_params)

    return defromation_area - relax_area


def calc_deformations(meshes, gates, result):
    '''calculate edge elong and polygon area variation'''

    for vertices, vertices_n, edges, pols in zip(*meshes):
        np_verts = np.array(vertices)
        np_verts_n = np.array(vertices_n)
        if len(edges) > 0 and (gates[0] or gates[1]):
            np_edges = np.array(edges)
            elong = edge_elongation(np_verts, np_verts_n, np_edges)
            result[0].append(elong if gates[4] else elong.tolist())
            if gates[1]:
                elong_v = vert_edge_defromation(elong, np_verts, np_edges)
                result[1].append(elong_v if gates[4] else elong_v.tolist())

        if len(pols) > 0 and (gates[2] or gates[3]):
            area_params = area_calc_setup(pols)
            area_var = area_variation(np_verts, np_verts_n, area_params)
            result[2].append(area_var if gates[4] else area_var.tolist())
            if gates[3]:
                area_var_v = area_to_verts(np_verts, area_params, area_var)
                result[3].append(area_var_v if gates[4] else area_var_v.tolist())

    return result


class SvDeformationNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Measure deformation
    Tooltip: Deformation between to states, edge elong a area variation
    '''
    bl_idname = 'SvDeformationNode'
    bl_label = 'Deformation'
    bl_icon = 'MOD_SIMPLEDEFORM'
    sv_icon = 'SV_DEFORMATION'

    output_numpy : BoolProperty(
        name='Output NumPy', description='output NumPy arrays',
        default=False, update=updateNode)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "output_numpy", toggle=False)

    def sv_init(self, context):
        '''create sockets'''
        sinw = self.inputs.new
        sonw = self.outputs.new
        sinw('SvVerticesSocket', "Rest Verts")
        sinw('SvVerticesSocket', "Distort Verts")
        sinw('SvStringsSocket', "Edges")
        sinw('SvStringsSocket', "Pols")

        sonw('SvStringsSocket', "Edges Def")
        sonw('SvStringsSocket', "Pols Def")
        sonw('SvStringsSocket', "Vert Edge Def")
        sonw('SvStringsSocket', "Vert Pol Def")

    def get_data(self):
        '''get all data from sockets'''
        si = self.inputs
        vertices_s = si['Rest Verts'].sv_get(default=[[]])
        vertices_n = si['Distort Verts'].sv_get(default=[[]])
        edges_in = si['Edges'].sv_get(default=[[]])
        pols_in = si['Pols'].sv_get(default=[[]])

        return match_long_repeat([vertices_s, vertices_n, edges_in, pols_in])

    def ready(self):
        '''check if there are the needed links'''
        si = self.inputs
        so = self.outputs
        ready = any(s.is_linked for s in so)
        ready = ready and si[0].is_linked and si[1].is_linked
        ready = ready and (si[2].is_linked or si[3].is_linked)
        return ready

    def process(self):
        '''main node function called every update'''
        so = self.outputs
        if not self.ready():
            return

        result = [[], [], [], []]
        gates = []
        gates.append(so['Edges Def'].is_linked)
        gates.append(so['Vert Edge Def'].is_linked)
        gates.append(so['Pols Def'].is_linked)
        gates.append(so['Vert Pol Def'].is_linked)
        gates.append(self.output_numpy)
        meshes = self.get_data()

        result = calc_deformations(meshes, gates, result)

        if gates[0]:
            so['Edges Def'].sv_set(result[0])
        if gates[1]:
            so['Vert Edge Def'].sv_set(result[1])
        if gates[2]:
            so['Pols Def'].sv_set(result[2])
        if gates[3]:
            so['Vert Pol Def'].sv_set(result[3])


def register():
    '''register class in Blender'''
    bpy.utils.register_class(SvDeformationNode)


def unregister():
    '''unregister class in Blender'''
    bpy.utils.unregister_class(SvDeformationNode)
