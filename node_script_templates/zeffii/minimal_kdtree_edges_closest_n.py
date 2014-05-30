from math import sin, cos, pi
import mathutils
from mathutils import Vector

def sv_main(verts=[[]]):

    in_sockets = [
        ['v', 'verts', verts]]

    verts = verts[0]
    size = len(verts)
    kd = mathutils.kdtree.KDTree(size)

    for i, vtx in enumerate(verts):
        kd.insert(Vector(vtx), i)
    kd.balance()

    e = []
    e_set = set()
    for i, vtx in enumerate(verts):
        
        # 2, because the first closest vertex to each
        # vertex is that vertex. [1:] to skip the first
        for (co, index, dist) in kd.find_n(vtx, 2)[1:]:
            edge = tuple(sorted([i, index]))
            
            # checking if edge tuple is in a set is faster on larger
            # sets.
            if not edge in e_set:
                e_set.add(edge)
                e.append(edge)

    out_sockets = [
        ['s', 'Edges', [e]]
    ]

    return in_sockets, out_sockets
