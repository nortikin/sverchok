def sv_main(Points=[], SourceTri=[], TargetTri=[]):

    in_sockets = [
        ['v', 'Points', Points],
        ['v', 'SourceTri', SourceTri],
        ['v', 'TargetTri', TargetTri]

        ]

    import mathutils
    from mathutils import Vector

    out = []

    if SourceTri and TargetTri and Points:

        st = [Vector(x) for x in SourceTri[0][:3]]
        tt = [Vector(x) for x in TargetTri[0][:3]]
        Points = [Vector(x) for x in Points[0]]

        for i in Points:
            out.append(mathutils.geometry.barycentric_transform(i, st[0], st[1], st[2], tt[0], tt[1], tt[2])[:])

    out_sockets = [
        ['v', 'TransformedPoints', [out]]

    ]

    return in_sockets, out_sockets
    
