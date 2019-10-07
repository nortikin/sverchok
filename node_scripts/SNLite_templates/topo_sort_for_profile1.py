"""
in in_verts v
in in_edges s
out vout v
out eout s
"""


def dodo(verts, edges, verts_o,k):
    for i in edges:
        if k in i:
            # this is awesome !!
            k = i[int(not i.index(k))]
            verts_o.append(verts[k])
            return k, i
    return False, False

def sortof(edges,verts,edges_o,verts_o):
    ed = edges[0][1]
    k = edges[0][0]
    while True:
        k, ed = dodo(verts, edges, verts_o,k)
        if ed:
            edges.remove(ed)
        if not ed:
            break
    edges_o = [[k,k+1] for k in range(len(verts_o)-1)]
    edges_o.append([0, len(verts_o)-1])
    #print(edges,ed)
    if edges:
        return sortof(edges,verts,edges_o,verts_o)
    else:
        return [edges_o, verts_o]

if in_verts:
    for edges, verts in zip(in_edges, in_verts):
        #print(edges)
        edges_ = []
        verts_ = []
        edges_o,verts_o = sortof(edges,verts,edges_,verts_)
        print(edges_o,verts_o)
        eout.append(edges_o)
        vout.append(verts_o)
