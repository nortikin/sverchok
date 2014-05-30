from math import sin, cos, pi
import mathutils
from mathutils import Vector

def sv_main(verts=[[]]):

    in_sockets = [
        ['v', 'verts', verts]]

    verts = verts[0]
    print('now;', verts)
    size = len(verts)
    kd = mathutils.kdtree.KDTree(size)

    for i, vtx in enumerate(verts):
        kd.insert(Vector(vtx), i)
    kd.balance()

    e = []
    e_set = set()
    for i, vtx in enumerate(verts):
        
        # 2, because the first closest vertex to each
        # vertex is that vertex.
        for (co, index, dist) in kd.find_n(vtx, 2)[1:]:
            edge = tuple(sorted([i, index]))
            if not edge in e_set:
                e_set.add(edge)
                e.append(edge)

    # out boilerplate
    print(e)
    out_sockets = [
        ['s', 'Edges', [e]]
    ]

    return in_sockets, out_sockets
