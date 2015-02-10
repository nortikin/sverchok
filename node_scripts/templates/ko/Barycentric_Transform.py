def sv_main(Points=[], SourceTri=[], TargetTri=[]):

    in_sockets = [
        ['v', 'Points', Points],
        ['v', 'SourceTri', SourceTri],
        ['v', 'TargetTri', TargetTri]

        ]

    import mathutils
    from sverchok.data_structure import (match_long_cycle)

    out = []
    if SourceTri and TargetTri and Points:

        Points, SourceTri, TargetTri = match_long_cycle([Points, SourceTri, TargetTri])

        g = 0
        while g < len(Points):

            st = SourceTri[g][:3]
            tt = TargetTri[g][:3]
            P = Points[g]

            out.append([mathutils.geometry.barycentric_transform(i, st[0], st[1], st[2], tt[0], tt[1], tt[2])[:] for i in P])

            g = g+1

    out_sockets = [
        ['v', 'TransformedPoints', out]
    ]

    return in_sockets, out_sockets
