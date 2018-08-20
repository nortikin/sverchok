"""
in verts_A v
in verts_B v
out verts v
out faces s
""" 

from mathutils import Vector
# for sure this can be made in two lines of code

if verts_A and verts_B:
    for va, vb in zip(verts_A,verts_B):
        # first define closest points to connect
        length_short = 1000
        ik_shortest = []
        i = 0
        la = len(va)
        lb = len(vb)
        for a in va:
            k = 0
            for b in vb:
                vabl = (Vector(a)-Vector(b)).length
                if length_short > vabl:
                    length_short = vabl
                    ik_shortest = [i,k]
                k+=1
            i+=1
        # connection
        i,k = ik_shortest
        va_ = va.copy()
        va_.extend(vb)
        va_.append(va[i])
        va_.append(vb[k])
        verts.append(va_)

        fap = [k+la,i]
        # from i to la
        for t in (range(i+1, la)):
            fap.append(t)
        # from la to i-1
        for p in (range(i)):
            fap.append(p)
        # join both
        fap.extend([la+lb,la+lb+1])
        # if equal direction (silently): from k reversed to 0
        for n in reversed(range(la,k+la)):
            fap.append(n)
        # continue from lb to k.... not gives 26 somehow
        for d in reversed(range(k+la+1, lb+la)): # 24+3=27
            fap.append(d)
        faces.append([fap])