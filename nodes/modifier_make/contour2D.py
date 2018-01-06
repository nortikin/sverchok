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
import itertools

from math import sin, cos, pi, degrees, radians, atan2, asin, ceil
from mathutils import Vector

import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    fullList, match_long_repeat,
    dataCorrect, repeat_last,
    updateNode, match_long_cycle)
from sverchok.utils.modules.geom_utils import pt_in_triangle
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.edges_intersect_mk2 import (
    remove_doubles_with_edges,
    intersect_edges)


modeItems = [
    ("Constant", "Constant", ""),
    ("Weighted", "Weighted", "")]

listMatchItems = [
    ("Long Repeat", "Long Repeat", ""),
    ("Long Cycle", "Long Cycle", "")]


def mask_by_distance(verts, parameters, modulo, edges, maskT, min_dist):

    mask = []
    for i in range(len(verts)):
        d = 0
        v = verts[i]
        vVec = Vector(v)
        for j in range(modulo):
            rad = parameters[2][j]
            if rad < min_dist:
                continue
            vo = parameters[0][j]
            vfx = v[0]-vo[0]
            vfy = v[1]-vo[1]
            dN = pow(pow(vfx, 2) + pow(vfy, 2), 0.5)
            verticesNum = parameters[1][j]

            dLim = (rad * abs(cos(pi/verticesNum))) * (1- maskT)

            if dN < dLim:
                d = 1
                break
        if d == 0:
            netOffCount = [0 for i in range(modulo)]
            for ed in edges:
                v1 = parameters[0][ed[0]]
                v2 = parameters[0][ed[1]]
                r1 = parameters[2][ed[0]]
                r2 = parameters[2][ed[1]]
                if v1 == v and r1 < min_dist or v2 == v and r2 < min_dist or r1 < min_dist and r2 < min_dist :
                    continue
                beta = parameters[3][ed[0]]

                dLim1 = (r1 * abs(cos(0.5 * pi / parameters[1][ed[0]]))) * (1- maskT)
                dLim2 = (r2 * abs(cos(0.5 * pi / parameters[1][ed[1]]))) * (1- maskT)

                netOff = netOffCount[ed[0]]
                netOffCount[ed[0]] += 3
                netOffCount[ed[1]] += 3
                vL1a = [v1[0] + dLim1 * cos(beta[1+netOff]), v1[1] + dLim1 * sin(beta[1+netOff]), v1[2]]
                vL1b = [v1[0] + dLim1 * cos(beta[2+netOff]), v1[1] + dLim1 * sin(beta[2+netOff]), v1[2]]
                vL2a = [v2[0] + dLim2 * cos(beta[1+netOff]), v2[1] + dLim2 * sin(beta[1+netOff]), v2[2]]
                vL2b = [v2[0] + dLim2 * cos(beta[2+netOff]), v2[1] + dLim2 * sin(beta[2+netOff]), v2[2]]
                A = pt_in_triangle(v, vL2a, vL1a, vL1b)
                B = pt_in_triangle(v, vL2a, vL1b, vL2b)

                if A or B:
                    d = 1
                    break

        mask.append(0 if d > 0 else 1)

    return mask


def mask_vertices(verts, edges, mask):
    # function taken from vertices_mask.py
    verts_outF = []
    edges_outF = []
    for ve, pe, ma in zip([verts], [edges], repeat_last([mask])):
        current_mask = itertools.islice(itertools.cycle(ma), len(ve))
        vert_index = [i for i, m in enumerate(current_mask) if m]
        if len(vert_index) < len(ve):
            index_set = set(vert_index)
            vert_dict = {j: i for i, j in enumerate(vert_index)}
            new_vert = [ve[i] for i in vert_index]
            is_ss = index_set.issuperset
            new_pe = [[vert_dict[n] for n in fe]
                      for fe in pe if is_ss(fe)]
            verts_outF.append(new_vert)
            edges_outF.append(new_pe)

        else:  # no reprocessing needed
            verts_outF.append(ve)
            edges_outF.append(pe)
    return verts_outF[0], edges_outF[0]


def calculate_mid_points(verts, edges):
    midPoints = []
    for ed in edges:
        vm = [0, 0, 0]
        for s in ed:
            v1 = verts[s]
            vm[0] += v1[0] * 0.5
            vm[1] += v1[1] * 0.5
            vm[2] += v1[2] * 0.5
        midPoints.append(vm)
    return midPoints


def mask_edges(edges, mask):
    edges_out = []
    for m, ed in zip(mask, edges):
        if m:
            edges_out.append(ed)
    return edges_out


def sort_verts_by_connexions(verts_in, edges_in):
    vertsOut = []
    edgesOut = []

    edges_length = len(edges_in)
    edgesIndex = [j for j in range(edges_length)]
    edges0 = [j[0] for j in edges_in]
    edges1 = [j[1] for j in edges_in]
    edIndex = 0
    orSide = 0
    edgesCopy = [edges0, edges1, edgesIndex]

    for co in edgesCopy:
        co.pop(0)

    for j in range(edges_length):
        e = edges_in[edIndex]
        ed = []
        if orSide == 1:
            e = [e[1], e[0]]

        for side in e:
            if verts_in[side] in vertsOut:
                ed.append(vertsOut.index(verts_in[side]))
            else:
                vertsOut.append(verts_in[side])
                ed.append(vertsOut.index(verts_in[side]))

        edgesOut.append(ed)

        edIndexOld = edIndex
        vIndex = e[1]
        if vIndex in edgesCopy[0]:
            k = edgesCopy[0].index(vIndex)
            edIndex = edgesCopy[2][k]
            orSide = 0

            for co in edgesCopy:
                co.pop(k)

        elif vIndex in edgesCopy[1]:
            k = edgesCopy[1].index(vIndex)
            edIndex = edgesCopy[2][k]
            orSide = 1
            for co in edgesCopy:
                co.pop(k)

        if edIndex == edIndexOld and len(edgesCopy[0]) > 0:
            edIndex = edgesCopy[2][0]
            orSide = 0
            for co in edgesCopy:
                co.pop(0)

    # add unconnected vertices
    if len(vertsOut) != len(verts_in):
        for verts, i in zip(verts_in, range(len(verts_in))):
            if verts not in vertsOut:
                vertsOut.append(verts)

    return vertsOut, edgesOut


def build_net(verts_in, edges_in, vLen, Radius):
    net = []
    for j in range(vLen):
        connect = []
        net.append(connect)
    for ed in edges_in:
        s0 = ed[0]
        s1 = ed[1]
        if s0 > len(verts_in) - 1 or s1 > len(verts_in) - 1:
            break
        v0 = verts_in[s0]
        v1 = verts_in[s1]
        an = atan2(v1[1] - v0[1], v1[0] - v0[0]) + pi
        an2 = atan2(v0[1]-v1[1], v0[0] - v1[0]) + pi
        r1 = Radius[s0 % len(Radius)]
        r2 = Radius[s1 % len(Radius)]
        dist = pow(pow(v1[0] - v0[0], 2) + pow(v1[1] - v0[1], 2), 0.5)
        beta = asin(min(max((r1-r2)/dist, -1), 1))
        net[s0].append((an + 0.5*pi) % (2*pi))
        net[s0].append((an + 0.5*pi + beta) % (2*pi))
        net[s0].append((an + 1.5*pi - beta) % (2*pi))
        net[s1].append((an2 + 0.5*pi) % (2*pi))
        net[s1].append((an2 + 0.5*pi - beta) % (2*pi))
        net[s1].append((an2 + 1.5*pi + beta) % (2*pi))

    return net


def list_matcher(a, listMatch):

    if listMatch == "Long Cycle":
        return match_long_cycle(a)
    else:
        return match_long_repeat(a)


class SvContourNode(bpy.types.Node, SverchCustomTreeNode):
    ''' 2D Path with offset '''
    bl_idname = 'SvContourNode'
    bl_label = 'Contour 2D'
    bl_icon = 'MESH_CIRCLE'

    modeI = EnumProperty(
        name="modeI",
        description="Constant or weigted distance when multiple radius are given",
        items=modeItems, default="Constant",
        update=updateNode)

    listMatch = EnumProperty(
        name="listMatch",
        description="Behaviour on diffent list lengths",
        items=listMatchItems, default="Long Cycle",
        update=updateNode)

    rm_doubles = FloatProperty(
        name='R. Doubles',
        description="Remove Doubles Distance",
        min=0.0, default=0.0001,
        step=0.1, update=updateNode)

    epsilon = FloatProperty(
        name='Int. Tolerance',
        description="Intersection tolerance",
        min=1.0e-5, default=1.0e-5,
        step=0.02, update=updateNode)

    maskT = FloatProperty(
        name='Mask tolerance',
        description="Mask tolerance",
        min=-1.0, default=1.0e-5,
        step=0.02, update=updateNode)

    rad_ = FloatProperty(
        name='Distance', description='Contour distance',
        default=1.0, min=1.0e-5, update=updateNode)

    vert_ = IntProperty(
        name='N Vertices', description='Nº of Vertices per input vector',
        default=24, min=4, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Distance").prop_name = 'rad_'
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'vert_'
        self.inputs.new('VerticesSocket', "Verts_in")
        self.inputs.new('StringsSocket', "Edges_in")

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, "modeI", expand=True)
        layout.prop(self, 'rm_doubles')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "modeI", expand=True)
        layout.prop(self, 'rm_doubles')
        layout.prop(self, 'epsilon')
        layout.prop(self, 'maskT')
        layout.prop(self, "listMatch", expand=True)

    def make_verts(self, verts_in, Vertices, Radius, net):
        listVertX = []
        listVertY = []
        listVertZ = []
        x = verts_in[0]
        y = verts_in[1]
        z = verts_in[2]
        vAngle = 0


        connex = len(net)/3
        if connex > 0:
            for i in range(0, int(len(net)), 3):
                vAngle += (net[i])/(connex)

        theta = 360/Vertices
        vert = Vertices
        if connex > 1:
            netAll = []
            for j in range(0, len(net)):
                ind = j % 3
                if ind != 0:
                    beta = net[j]
                    netAll.append(beta)

            newAngs = [(radians(theta * i) + vAngle) % (2*pi) for i in range(vert)]
            newAngs = sorted(newAngs + netAll)

            for angL in newAngs:
                listVertX.append(x + Radius*cos(angL))
                listVertY.append(y + Radius*sin(angL))
                listVertZ.append(z)

        elif connex == 1:

            beta = (net[1] - net[2])
            if beta <= 0:
                beta = (net[1] - net[2] + 2*pi)
            vAngle += net[0] - net[1] - pi
            vert = int((degrees(beta)) / theta) + 1

            for i in range(vert):
                localAngle = (radians(theta*i) + vAngle + 4*pi) % (2*pi)
                listVertX.append(x + Radius * cos(localAngle))
                listVertY.append(y + Radius * sin(localAngle))
                listVertZ.append(z)

            listVertX.append(x + Radius * cos(net[1]))
            listVertY.append(y + Radius * sin(net[1]))
            listVertZ.append(z)

        else:
            for i in range(vert):
                localAngle = (radians(theta*i) + vAngle + 4*pi) % (2*pi)

                listVertX.append(x + Radius * cos(localAngle))
                listVertY.append(y + Radius * sin(localAngle))
                listVertZ.append(z)
        points = list((x, y, z) for x, y, z in zip(listVertX, listVertY, listVertZ))
        return points

    def side_edges(self, v, edges, radius, net):
        Verts = []
        Edges = []
        n = 0
        netOffset = [0 for i in range(len(net))]

        for ed in edges:
            for s in ed:
                netOf = netOffset[s]
                netOffset[s] += 3
                x1 = v[s][0] + radius[s] * cos(net[s][1 + netOf])
                y1 = v[s][1] + radius[s] * sin(net[s][1 + netOf])
                x2 = v[s][0] + radius[s] * cos(net[s][2 + netOf])
                y2 = v[s][1] + radius[s] * sin(net[s][2 + netOf])

                Verts.append((x1, y1, v[s][2]))
                Verts.append((x2, y2, v[s][2]))

            Edges.append((n, n+3))
            Edges.append((n+1, n+2))
            n += 4
        return Verts, Edges

    def make_edges(self, Vertices, net, pointsL):
        listEdg = [(i, i + 1) for i in range(pointsL - 1)]
        if len(net) != 1:
            listEdg.append((pointsL-1, 0))
        return listEdg

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        # inputs
        vertsAll = inputs['Verts_in'].sv_get(deepcopy=False, default=[[(0.0, 0.0, 0.0)]])

        radiusAll = inputs['Distance'].sv_get(deepcopy=False, default=[[abs(self.rad_)]])
        radiusAll = [list(map(lambda x: abs(x), radius)) for radius in radiusAll]

        verticesAll = inputs['Nº Vertices'].sv_get(deepcopy=False, default=[[self.vert_]])
        verticesAll = [list(map(lambda x: max(2, int(x)), Vertices)) for Vertices in verticesAll]

        edgesAll = inputs['Edges_in'].sv_get(deepcopy=False, default=[[]])

        # outputs
        if not outputs['Vertices'].is_linked:
            return

        family = list_matcher([vertsAll, radiusAll, verticesAll, edgesAll], self.listMatch)
        vertices_outX = []
        edges_outX = []
        for verts_in, Radius, Vertices, edges_in in zip(*family):
            vLen = len(verts_in)
            edges_in = [i for i in edges_in if i[0] < vLen and i[1] < vLen]

            if self.modeI == "Weighted":
                perimeter_number = ceil(len(Radius) / vLen)
                print(perimeter_number)
                actualRadius = []
                for i in range(perimeter_number):
                    if self.listMatch == "Long Repeat":
                        actualRadius.append([Radius[min((i*vLen + j), len(Radius) - 1)] for j in range(vLen)])
                    else:
                        actualRadius.append([Radius[(i*vLen + j) % len(Radius) ] for j in range(vLen)])

            else:
                perimeter_number = len(Radius)
                actualRadius = []
                for i in range(perimeter_number):
                    actualRadius.append([Radius[i % len(Radius)] for j in range(vLen)])

            for i in range(perimeter_number):

                net = build_net(verts_in, edges_in, vLen, actualRadius[i])
                parameters = list_matcher([verts_in, Vertices, actualRadius[i], net], self.listMatch)
                parameters = [data[0:vLen] for data in parameters]

                points = [self.make_verts(vi, v, r, n) for vi, v, r, n in zip(*parameters)]
                totalPoints = sum(len(p) for p in points)
                parameters.append(points)

                edg = [self.make_edges(v, n, len(p)) for vi, v, r, n, p in zip(*parameters)]

                if inputs['Edges_in'].is_linked:
                    verts_Sides_out, edge_Side_out = self.side_edges(parameters[0], edges_in, parameters[2], parameters[3])
                    points.append(verts_Sides_out)
                    edg.append(edge_Side_out)

                verts_out, _, edges_out = mesh_join(points, [], edg)

                mask = mask_by_distance(verts_out, parameters, vLen, edges_in, self.maskT, self.epsilon)
                checker = [ [e[0], e[1]] for e in edges_out if (mask[e[0]] != mask[e[1]]) or (mask[e[0]] and mask[e[1]])]
                checker = list(set([element for tupl in checker for element in tupl]))
                smartMask = [i in checker or i >= totalPoints for i in range(len(verts_out))]
                verts_out, edges_out = mask_vertices(verts_out, edges_out, smartMask)

                verts_out, edges_out = intersect_edges(verts_out, edges_out, self.epsilon)

                mask = mask_by_distance(verts_out, parameters, vLen, edges_in, self.maskT, self.epsilon)

                verts_out, edges_out = mask_vertices(verts_out, edges_out, mask)

                verts_out, edges_out = remove_doubles_with_edges(verts_out, edges_out, self.rm_doubles)

                if inputs['Edges_in'].is_linked:
                    mid_points = calculate_mid_points(verts_out, edges_out)
                    maskEd = mask_by_distance(mid_points, parameters, vLen, edges_in, self.maskT, self.epsilon)
                    edges_out = mask_edges(edges_out, maskEd)

                verts_out, edges_out = sort_verts_by_connexions(verts_out, edges_out)
                vertices_outX.append(verts_out)
                edges_outX.append(edges_out)

        outputs['Vertices'].sv_set(vertices_outX)

        if outputs['Edges'].is_linked:
            outputs['Edges'].sv_set(edges_outX)


def register():
    bpy.utils.register_class(SvContourNode)


def unregister():
    bpy.utils.unregister_class(SvContourNode)
