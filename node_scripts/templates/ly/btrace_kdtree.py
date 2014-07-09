import mathutils
import random
import collections
from itertools import islice

def sv_main(objs=[], seed=1, start=-1):

    # in boilerplate, could be less verbose
    in_sockets = [
        ['v', 'verts', objs],
        ['s', 'seed', seed],
        ['s', 'start', start]
    ]
    
    random.seed(seed)
    edge_out = []
    
    for verts in objs:
        if not verts:
            break
    
        size = len(verts)
        kd = mathutils.kdtree.KDTree(size)

        for i, v in enumerate(verts):
            kd.insert(v, i)
        kd.balance()
        if 0 < start and start < size:
            index = start
        else:
            index = random.randrange(size)
            
        out = collections.OrderedDict({index:0})
        while len(out) < size:
            found_next = False
            n = 0
            step = 5
            while not found_next:
                count = min(size, n+step)
                for pt, n_i, dist in islice(kd.find_n(verts[index], count), n, count):
                    if not n_i in out:
                        out[n_i] = index
                        index = n_i
                        found_next = True
                        break

                if n > size:
                    break
                n += 5
        out.popitem(last=False)
        edge_out.append([(j,k) for j,k in out.items()])

    out_sockets = [
        ['s', 'Edges', edge_out]
    ]

    return in_sockets, out_sockets
