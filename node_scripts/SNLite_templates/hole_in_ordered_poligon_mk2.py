"""
in verts_A v
in verts_B v
out verts v
out faces s
""" 

from mathutils import Vector
# for sure this can be made in two lines of code
# i.e. a - circle 24 verts, b - triangle 3 verts (27 length)

if verts_A and verts_B:
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
        va_.append(va[i_])
        va_.append(vb[k_])
        va_.append(va[i])
        va_.append(vb[k])
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
        fap.extend([la+lb,la+lb+1])

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
        fap_.extend([la+lb+2,la+lb+3])

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