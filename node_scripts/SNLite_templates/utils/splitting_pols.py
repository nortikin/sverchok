"""
in vers_in v d=[[]] n=0
in pols_in s d=[[]] n=0
in value s d=0.5 n=2
in direction s d=0 n=2
in shift s d=0 n=2
in ignoresecond s d=0 n=2
out vers_out v
out pols_out s
"""


from mathutils import Vector as V

pols_out, vers_out = [], []
sh = True
igs = ignoresecond
for ver, pol in zip(vers_in,pols_in):
    nex = len(ver)
    np,nv = [],ver
    for p in pol:
        igs = not igs
        if ignoresecond and igs:
            np.append(p)
            continue
        nex += 2
        sh = not sh
        if not direction:
            if shift and not sh:
                np.append([p[0],nex-2,nex-1,p[3]])
            else:
                np.append([p[3],nex-1,nex-2,p[0]])
            if shift and sh:
                np.append([nex-1,p[2],p[1],nex-2])
            else:
                np.append([nex-2,p[1],p[2],nex-1])
            nv.append(list((V(ver[p[1]])+value*(V(ver[p[0]])-V(ver[p[1]]))).to_tuple()))
            nv.append(list((V(ver[p[2]])+value*(V(ver[p[3]])-V(ver[p[2]]))).to_tuple()))
        else:
            if shift and not sh:
                np.append([nex-1,p[3],p[2],nex-2])
            else:
                np.append([nex-2,p[2],p[3],nex-1])
            if shift and sh:
                np.append([nex-2,p[1],p[0],nex-1])
            else:
                np.append([nex-1,p[0],p[1],nex-2])
            nv.append(list((V(ver[p[2]])+value*(V(ver[p[1]])-V(ver[p[2]]))).to_tuple()))
            nv.append(list((V(ver[p[3]])+value*(V(ver[p[0]])-V(ver[p[3]]))).to_tuple()))
    pols_out.append(np)
    vers_out.append(nv)