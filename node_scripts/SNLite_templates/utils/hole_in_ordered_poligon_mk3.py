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
        i_do, k_do = False,False
        i_ = i-la//2
        if i_ < 0: 
            i_ += la
            i_do = True
        k_ = k-lb//2
        if k_ < 0: 
            k_ += lb
            k_do = True
        va_ = va.copy()
        va_.extend(vb)
        #va_.append(va[i_])
        #va_.append(vb[k_])
        #va_.append(va[i])
        #va_.append(vb[k])
        verts.append(va_)

        ##### one poligon
        # 25,12
        fap = [k+la,i]
        if not i_do:
            # from i to la / 13...23
            for t in (range(i+1, la)):
                fap.append(t)
            # from 0 to i-1 / 0 to 11
            for p in (range(i_)):
                fap.append(p)
        else:
            # from i to la / 13...23
            for t in (range(i+1,i_)):
                fap.append(t)

        # join both with copy vertices at end / 27 to 28
        fap.extend([i_,la+k_])
        #fap.extend([la+lb,la+lb+1])

        if not k_do:
            # if equal direction (silently): from k reversed to 0 / 24 only
            for n in reversed(range(la,k_+la)):
                fap.append(n)
            # continue from lb to k / only 26
            for d in reversed(range(k+la+1, lb+la)):
                fap.append(d)
        else:
            # if equal direction (silently): from k reversed to 0 / 24 only
            for n in reversed(range(la+k,la+k_)):
                fap.append(n)


        ##### two poligon
        # 25,12
        fap_ = [k_+la,i_]
        if i_do:
            # from i to la / 13...23
            for t in (range(i_+1, la)):
                fap_.append(t)
            # from 0 to i-1 / 0 to 11
            for p in (range(i)):
                fap_.append(p)
        else:
            # from i to la / 13...23
            for t in (range(i_+1,i)):
                fap_.append(t)

        # join both with copy vertices at end / 29 to 30
        fap_.extend([i,k+la])

        if k_do:
            # if equal direction (silently): from k reversed to 0 / 24 only
            for n in reversed(range(la,la+k)):
                fap_.append(n)
            # continue from lb to k / only 26
            for d in reversed(range(la+k_+1, la+lb)):
                fap_.append(d)
        else:
            # if equal direction (silently): from k reversed to 0 / 24 only
            for n in reversed(range(la+k_+1,k+la)):
                fap_.append(n)

        faces.append([fap,fap_])
