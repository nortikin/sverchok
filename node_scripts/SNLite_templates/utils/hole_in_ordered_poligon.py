"""
in verts_A v
in edges_A s
in verts_B v
in edges_B s
out verts v
out faces s
""" 

from mathutils import Vector
from sverchok.utils.sv_mesh_utils import polygons_to_edges
# for sure this can be made in two lines of code
# i.e. a - circle 24 verts, b - triangle 3 verts (27 length)


def order(verts, edges, verts_o,k):
    for i in edges:
        if k in i:
            # this is awesome !!
            k = i[int(not i.index(k))]
            verts_o.append(verts[k])
            return k, i
    return False, False

if verts_A and verts_B and edges_A and edges_B:


    # pols2edges
    if len(edges_A[0][0]) > 2:
        edges_A = polygons_to_edges(edges_A, unique_edges=True)
    if len(edges_B[0][0]) > 2:
        edges_B = polygons_to_edges(edges_B, unique_edges=True)


    # ordering sort edges chain
    def ordering(in_verts, in_edges):
        ed = 1
        vout = []
        for edges, verts in zip(in_edges, in_verts):
            verts_o = []
            k = 0
            while True:
                k, ed = order(verts, edges, verts_o,k)
                if ed:
                    edges.remove(ed)
                if not ed:
                    break
            vout.append(verts_o)
        return vout

    verts_A = ordering(verts_A,edges_A)
    verts_B = ordering(verts_B,edges_B)
    # print('>>>>>',verts_A)


    # main part

    for va, vb in zip(verts_A,verts_B):
        # first define closest points to connect
        length_short = 1000
        ik_shortest = []
        i = 0
        la = len(va) # 24
        lb = len(vb) # 3
        for a in va:
            k = 0
            for b in vb:
                vabl = (Vector(a)-Vector(b)).length
                if length_short > vabl:
                    length_short = vabl
                    ik_shortest = [i,k]
                k+=1
            i+=1
        # connection / i.e. k=1 i=12
        i,k = ik_shortest
        va_ = va.copy()
        va_.extend(vb)
        va_.append(va[i])
        va_.append(vb[k])
        verts.append(va_)

        # 25,12
        fap = [k+la,i]
        # from i to la / 13...23
        for t in (range(i+1, la)):
            fap.append(t)
        # from 0 to i-1 / 0 to 11
        for p in (range(i)):
            fap.append(p)
        # join both with copy vertices at end / 27 to 28
        fap.extend([la+lb,la+lb+1])
        # if equal direction (silently): from k reversed to 0 / 24 only
        for n in reversed(range(la,k+la)):
            fap.append(n)
        # continue from lb to k / only 26
        for d in reversed(range(k+la+1, lb+la)):
            fap.append(d)
        faces.append([fap])
