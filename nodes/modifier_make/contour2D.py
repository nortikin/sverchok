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
from collections import defaultdict
from math import sin, cos, pi, degrees, radians, atan2, asin
from mathutils.geometry import intersect_line_line as LineIntersect
from mathutils import Vector

import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    fullList, match_long_repeat,
    dataCorrect, repeat_last,
    updateNode, match_long_cycle)
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.cad_module_class import CAD_ops
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

modeItems = [
    ("Constant", "Constant", ""),
    ("Weighted", "Weighted", "")]

listMatchItems = [
    ("Long Repeat", "Long Repeat", ""),
    ("Long Cycle", "Long Cycle", "")]

def order_points(edge, point_list):
    ''' order these edges from distance to v1, then
    sandwich the sorted list with v1, v2 '''
    v1, v2 = edge
    dist = lambda co: (v1-co).length
    point_list = sorted(point_list, key=dist)
    return [v1] + point_list + [v2]


def remove_permutations_that_share_a_vertex(cm, bm, permutations):
    ''' Get useful Permutations '''

    final_permutations = []
    for edges in permutations:
        raw_vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        if cm.duplicates(raw_vert_indices):
            continue

        # reaches this point if they do not share.
        final_permutations.append(edges)

    return final_permutations


def get_valid_permutations(cm, bm, edge_indices):
    raw_permutations = itertools.permutations(edge_indices, 2)
    permutations = [r for r in raw_permutations if r[0] < r[1]]
    return remove_permutations_that_share_a_vertex(cm, bm, permutations)


def can_skip(cm, closest_points, vert_vectors):
    '''this checks if the intersection lies on both edges, returns True
    when criteria are not met, and thus this point can be skipped'''
    if not closest_points:
        return True
    if not isinstance(closest_points[0].x, float):
        return True
    if cm.num_edges_point_lies_on(closest_points[0], vert_vectors) < 2:
        return True

    # if this distance is larger than than VTX_PRECISION, we can skip it.
    cpa, cpb = closest_points
    return (cpa-cpb).length > cm.VTX_PRECISION


def get_intersection_dictionary(cm, bm, edge_indices):

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    permutations = get_valid_permutations(cm, bm, edge_indices)

    k = defaultdict(list)
    d = defaultdict(list)

    for edges in permutations:
        raw_vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        vert_vectors = cm.vectors_from_indices(bm, raw_vert_indices)

        points = LineIntersect(*vert_vectors)

        # some can be skipped.    (NaN, None, not on both edges)
        if can_skip(cm, points, vert_vectors):
            continue

        # reaches this point only when an intersection happens on both edges.
        [k[edge].append(points[0]) for edge in edges]

    # k will contain a dict of edge indices and points found on those edges.
    for edge_idx, unordered_points in k.items():
        tv1, tv2 = bm.edges[edge_idx].verts
        v1 = bm.verts[tv1.index].co
        v2 = bm.verts[tv2.index].co
        ordered_points = order_points((v1, v2), unordered_points)
        d[edge_idx].extend(ordered_points)

    return d


def update_mesh(bm, d):
    ''' Make new geometry '''

    oe = bm.edges
    ov = bm.verts

    for old_edge, point_list in d.items():
        num_edges_to_add = len(point_list)-1
        for i in range(num_edges_to_add):
            a = ov.new(point_list[i])
            b = ov.new(point_list[i+1])
            oe.new((a, b))
            bm.normal_update()


def unselect_nonintersecting(bm, d_edges, edge_indices):
    # print(d_edges, edge_indices)
    if len(edge_indices) > len(d_edges):
        reserved_edges = set(edge_indices) - set(d_edges)
        for edge in reserved_edges:
            bm.edges[edge].select = False
        # print("unselected {}, non intersecting edges".format(reserved_edges))


def intersectEdges(verts, edges, epsi):
    bm = bmesh_from_pydata(verts, edges, [])

    edge_indices = [e.index for e in bm.edges]
    trim_indices = len(edge_indices)
    for edge in bm.edges:
        edge.select = True

    cm = CAD_ops(epsilon=epsi)
    d = get_intersection_dictionary(cm, bm, edge_indices)
    unselect_nonintersecting(bm, d.keys(), edge_indices)
    # store non_intersecting edge sequencer
    add_back = [[i.index for i in edge.verts] for edge in bm.edges if not edge.select]

    update_mesh(bm, d)
    verts_out = [v.co.to_tuple() for v in bm.verts]
    edges_out = [[j.index for j in i.verts] for i in bm.edges]

    # optional correction, remove originals, add back those that are not intersecting.
    edges_out = edges_out[trim_indices:]
    edges_out.extend(add_back)
    bm.free()
    return verts_out, edges_out


def ptInTriang(p_test, p0, p1, p2):
    # Function taken from Ramiro R.C https://stackoverflow.com/a/46409704
    dX = p_test[0] - p0[0]
    dY = p_test[1] - p0[1]
    dX20 = p2[0] - p0[0]
    dY20 = p2[1] - p0[1]
    dX10 = p1[0] - p0[0]
    dY10 = p1[1] - p0[1]

    s_p = (dY20*dX) - (dX20*dY)
    t_p = (dX10*dY) - (dY10*dX)
    D = (dX10*dY20) - (dY10*dX20)

    if D > 0:
        return (  (s_p >= 0) and (t_p >= 0) and (s_p + t_p) <= D  )
    else:
        return (  (s_p <= 0) and (t_p <= 0) and (s_p + t_p) >= D  )


def maskByDistance(verts, parameters, modulo, edges, maskT):

    mask = []
    for i in range(len(verts)):
        d = 0
        v = verts[i]
        vVec = Vector(v)
        for j in range(modulo):
            vo = parameters[0][j]
            vfx = v[0]-vo[0]
            vfy = v[1]-vo[1]
            dN = pow(pow(vfx, 2) + pow(vfy, 2), 0.5)
            verticesNum = parameters[1][j]
            dLim = parameters[2][j]*abs(cos(pi/verticesNum))- maskT
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
                beta = parameters[3][ed[0]]

                dLim1 = r1 * abs(cos(0.5 * pi / parameters[1][ed[0]]))- maskT
                dLim2 = r2 * abs(cos(0.5 * pi / parameters[1][ed[1]]))- maskT

                netOff = netOffCount[ed[0]]
                netOffCount[ed[0]] += 3
                netOffCount[ed[1]] += 3
                vL1a = [v1[0] + dLim1 * cos(beta[1+netOff]), v1[1] + dLim1 * sin(beta[1+netOff]), v1[2]]
                vL1b = [v1[0] + dLim1 * cos(beta[2+netOff]), v1[1] + dLim1 * sin(beta[2+netOff]), v1[2]]
                vL2a = [v2[0] + dLim2 * cos(beta[1+netOff]), v2[1] + dLim2 * sin(beta[1+netOff]), v2[2]]
                vL2b = [v2[0] + dLim2 * cos(beta[2+netOff]), v2[1] + dLim2 * sin(beta[2+netOff]), v2[2]]
                A = ptInTriang(v, vL2a, vL1a, vL1b)
                B = ptInTriang(v, vL2a, vL1b, vL2b)

                if A or B:
                    d = 1
                    break
        if d > 0:
            mask.append(0)
        else:
            mask.append(1)

    return mask


def maskVertices(verts, edges, mask):
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


def CalcMidPoints(verts, edges):
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


def maskEdges(edges, mask):
    edges_out = []
    for m, ed in zip(mask, edges):
        if m == True:
                edges_out.append(ed)
    return edges_out


def distanceEdges(v1, v2, p):
    a = abs((v2[1]-v1[1]) * p[0] - (v2[0]-v1[0]) * p[1] + (v2[0]*v1[1]) - (v2[1]*v1[0]))
    b = pow(pow(v2[1]-v1[1], 2) + pow(v2[0]-v1[0], 2), 0.5)
    return a / b


def removeDoubles(verts_in, edges_in, distance):
    bm = bmesh_from_pydata(verts_in[0], edges_in[0], [])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=distance)
    verts_out = [v.co.to_tuple() for v in bm.verts]
    edges_out = [[j.index for j in i.verts] for i in bm.edges]

    return verts_out, edges_out


def sortVerticesByConnexions(verts_in, edges_in):
    vertsOut = []
    edgesOut = []

    edgeLegth = len(edges_in)
    edgesIndex = [j for j in range(edgeLegth)]
    edges0 = [j[0] for j in edges_in]
    edges1 = [j[1] for j in edges_in]
    edIndex = 0
    orSide = 0
    edgesCopy = [edges0, edges1, edgesIndex]

    for co in edgesCopy:
        co.pop(0)

    for j in range(edgeLegth):
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


def buildNet(verts_in, edges_in, vLen, Radius):
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


def listMatcher(a, listMatch):
    if listMatch == "Long Cycle":
        return match_long_cycle(a)
    else:
        return match_long_repeat(a)


class SvContourNode(bpy.types.Node, SverchCustomTreeNode):
    ''' 2D Path with offset '''
    bl_idname = 'SvContourNode'
    bl_label = 'Contour 2D'
    bl_icon = 'MESH_CIRCLE'

    modeI = EnumProperty(name="modeI",
                         description="Constant or weigted distance when multiple radius are given",
                         items=modeItems, default="Constant",
                         update=updateNode)
    listMatch = EnumProperty(name="listMatch",
                             description="Behaviour on diffent list lengths",
                             items=listMatchItems, default="Long Cycle",
                             update=updateNode)

    rm_doubles = FloatProperty(name='R. Doubles',
                               description="Remove Doubles Distance",
                               min=0.0, default=0.0001,
                               step=0.1, update=updateNode)
    epsilon = FloatProperty(name='Int. Tolerance',
                            description="Intersection tolerance",
                            min=1.0e-5, default=1.0e-5,
                            step=0.02, update=updateNode)
    maskT = FloatProperty(name='Mask tolerance',
                          description="Mask tolerance",
                          min=-1.0, default=1.0e-5,
                          step=0.02, update=updateNode)
    rad_ = FloatProperty(name='Distance', description='Contour distance',
                         default=1.0, min=1.0e-5,
                         update=updateNode)
    vert_ = IntProperty(name='N Vertices', description='Nº of Vertices per input vector',
                        default=24, min=4,
                        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'vert_'
        self.inputs.new('VerticesSocket', "Verts_in")
        self.inputs.new('StringsSocket', "Edges_in")

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, "modeI", expand=True)
        r = layout.row(align=True)
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
            netC = []
            for j in range(0, len(net)):
                netP = []
                ind = j % 3
                if ind != 0:
                    netP.append(net[j])
                    angSide = net[3*int(j/3)] - pi/2
                    offAng = pi/2
                    if ind == 2:
                        offAng = pi/2
                    beta = net[j]
                    angTan = (angSide+offAng-beta)
                    if angTan < 0:
                        angTan += 2 * pi
                    netP.append(beta)
                    netP.append(int(j/3))
                    netP.append(angSide)
                    netP.append(j)
                    netP.append(angTan)
                    netC.append(netP)
            netC.sort()
            lastAng = netC[-1][1]
            lastIndex = netC[-1][2]
            lastAngSide = netC[-1][3]
            lastAngTan = netC[0][5]
            for k in range(len(netC)):
                ang = netC[k]
                difAng = (ang[1]-lastAng)
                if lastAng > ang[1]:
                    difAng += 2 * pi
                angSide = ang[3]
                offAng = 3*pi/2

                if ((ang[2] != lastIndex)):
                    vert = int((degrees(difAng)) / theta) + 1
                    for i in range(vert):
                        angL = lastAng + difAng / vert * i
                        listVertX.append(x+Radius*cos(angL))
                        listVertY.append(y+Radius*sin(angL))
                        listVertZ.append(z)

                lastIndex = ang[2]
                lastAng = ang[1]
                lastAngSide = ang[3]
                lastAngTan = ang[5]
                listVertX.append(x + Radius * cos(ang[0]))
                listVertY.append(y + Radius * sin(ang[0]))
                listVertZ.append(z)
        elif connex == 1:
            beta = (net[1] - net[2])
            if beta < 0:
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

    def sideEdges(self, v, edges, radius, net):
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
        if len(net) == 0:
            listEdg.append((pointsL-1, 0))
        return listEdg

    def make_faces(self, Vertices):
        listPlg = list(range(Vertices))

        return [listPlg]

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        # inputs

        if inputs['Verts_in'].is_linked:

            VertsAll = inputs['Verts_in'].sv_get(deepcopy=False)
        else:
            VertsAll = [[(0.0, 0.0, 0.0)]]

        if inputs['Radius'].is_linked:

            RadiusAll = inputs['Radius'].sv_get(deepcopy=False)
        else:
            RadiusAll = [[self.rad_]]

        if inputs['Nº Vertices'].is_linked:
            VerticesAll = inputs['Nº Vertices'].sv_get(deepcopy=False)
            VerticesAll = [list(map(lambda x: max(2, int(x)), Vertices)) for Vertices in VerticesAll]
        else:
            VerticesAll = [[self.vert_]]

        if inputs['Edges_in'].is_linked:
            edgesAll = inputs['Edges_in'].sv_get(deepcopy=False)
        else:
            edgesAll = [[]]

        # outputs
        if outputs['Vertices'].is_linked:
            family = listMatcher([VertsAll, RadiusAll, VerticesAll, edgesAll], self.listMatch)
            vertices_outX = []
            edges_outX = []
            for verts_in, Radius, Vertices, edges_in in zip(*family):
                vLen = len(verts_in)
                edges_in = [i for i in edges_in if i[0] < vLen and i[1] < vLen]

                if self.modeI == "Weighted":
                    perimeterNumber = 1
                    actualRadius = [Radius for i in range(vLen)]
                else:
                    perimeterNumber = len(Radius)
                    actualRadius = []
                    for i in range(perimeterNumber):
                            actualRadius.append([Radius[i % len(Radius)] for j in range(vLen)])

                for i in range(perimeterNumber):

                    net = buildNet(verts_in, edges_in, vLen, actualRadius[i])
                    parameters = listMatcher([verts_in, Vertices, actualRadius[i], net], self.listMatch)
                    parameters = [data[0:vLen] for data in parameters]

                    points = [self.make_verts(vi, v, r, n) for vi, v, r, n in zip(*parameters)]
                    parameters.append(points)

                    edg = [self.make_edges(v, n, len(p)) for vi, v, r, n, p in zip(*parameters)]

                    if inputs['Edges_in'].is_linked:
                        verts_Sides_out, edge_Side_out = self.sideEdges(parameters[0], edges_in, parameters[2], parameters[3])
                        points.append(verts_Sides_out)
                        edg.append(edge_Side_out)

                    verts_out, _, edges_out = mesh_join(points, [], edg)

                    verts_out, edges_out = intersectEdges(verts_out, edges_out, self.epsilon)

                    mask = maskByDistance(verts_out, parameters, vLen, edges_in, self.maskT)

                    verts_out, edges_out = maskVertices(verts_out, edges_out, mask)

                    verts_out, edges_out = removeDoubles([verts_out], [edges_out], self.rm_doubles)

                    if inputs['Edges_in'].is_linked:
                        midPoints = CalcMidPoints(verts_out, edges_out)
                        maskEd = maskByDistance(midPoints, parameters, vLen, edges_in, self.maskT)
                        edges_out = maskEdges(edges_out, maskEd)

                    verts_outFX, edges_outFX = sortVerticesByConnexions(verts_out, edges_out)
                    vertices_outX.append(verts_outFX)
                    edges_outX.append(edges_outFX)

            outputs['Vertices'].sv_set(vertices_outX)

            if outputs['Edges'].is_linked:
                outputs['Edges'].sv_set(edges_outX)


def register():
    bpy.utils.register_class(SvContourNode)


def unregister():
    bpy.utils.unregister_class(SvContourNode)
