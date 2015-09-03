from mathutils import Vector
import numpy as np

def sv_main(powers=[],pow_str=[],points=[],lent=0.1,subs=30):

    in_sockets = [
        ['v', 'powers', powers],
        ['s', 'pow_str', pow_str],
        ['v', 'points', points],
        ['s', 'lent', lent],
        ['s', 'subs', subs]]

    verts_out = []
    edges_out = []

    def out_sockets():
        return [
            ['v', 'verts_out', verts_out],
            ['s', 'faces_out', edges_out]]
    if not all([powers, pow_str, points]):
        return in_sockets, out_sockets()


    powers = [np.array(i) for i in powers[0]]
    points = [np.array(i) for i in points[0]]

    #points = Vector_generate(points)
    #powers = Vector_generate(powers)

    def nextpoint(poi,powers):
        verts = []
        for pow in powers:
            ve = poi-pow
            verts.append(ve.tolist())
        return np.array(verts)

    for poi in points:
        vers = []
        edgs = []
        for k in range(subs):
            if k > 0:
                edgs.append([k-1,k])
            else:
                vers.append(poi.tolist())
            verts = nextpoint(poi,powers)
            vect = verts.sum(axis=0)
            vect = vect/vect.max()
            vertnext = poi+(1/(vect*lent))
            vers.append(vertnext.tolist())
            poi = vertnext
        edges_out.append(edgs)
        verts_out.append(vers)
    

    return in_sockets, out_sockets()