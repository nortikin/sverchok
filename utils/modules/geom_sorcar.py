# import sverchok
from sverchok.nodes.modifier_make.solidify import solidify

def make_sorcar_logo():
    """ makes sorcar 3d - literal data"""
    a = 0.4233
    b = 0.7778
    c = 0.6878
    d = 0.3333
    e = 1.0
    f = 0.9100
    g = 0.8678
    h = 0.2433
    i = 0.6456
    j = 0.5556
    k = 0.4656
    l = 0.2011
    m = 0.1111
    n = 0.0211

    verts_2d = [
        (-a, -b), (-c, -b), (-b, -c), (-b, -d), (-e, -d), (-e, -f), (-f, -e), (-d, -e),
        (-d, -g), (-h, -b), (+h, -b), (+d, -g), (+d, -e), (+f, -e), (+e, -f), (+e, -d),
        (+b, -d), (+b, -c), (+c, -b), (+a, -b), (+d, -c), (+d, -i), (+a, -j), (+k, -j),
        (+j, -k), (+j, -l), (+k, -m), (+a, -m), (+d, -n), (+d, +n), (+h, +m), (-h, +m),
        (-d, +l), (-d, +k), (-h, +j), (+h, +j), (+d, +k), (+d, +a), (+a, +d), (+k, +d),
        (+j, +a), (+j, +k), (+k, +j), (+a, +j), (+d, +i), (+d, +c), (+a, +b), (+c, +b),
        (+b, +c), (+b, +d), (+e, +d), (+e, +f), (+f, +e), (+d, +e), (+d, +g), (+h, +b),
        (-h, +b), (-d, +g), (-d, +e), (-f, +e), (-e, +f), (-e, +d), (-b, +d), (-b, +c),
        (-c, +b), (-a, +b), (-d, +c), (-d, +i), (-a, +j), (-k, +j), (-j, +k), (-j, +l),
        (-k, +m), (-a, +m), (-d, +n), (-d, -n), (-h, -m), (+h, -m), (+d, -l), (+d, -k),
        (+h, -j), (-h, -j), (-d, -k), (-d, -a), (-a, -d), (-k, -d), (-j, -a), (-j, -k),
        (-k, -j), (-a, -j), (-d, -i), (-d, -c)
    ]

    verts_3d = [(v[0], v[1], 0.05) for v in verts_2d]
    face = list(range(len(verts_3d)))
    verts, edges, faces, _ = solidify(verts_3d, [face], [0.1])
    return verts, edges, faces
