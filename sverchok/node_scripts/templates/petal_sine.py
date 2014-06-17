from math import sin, cos, radians, pi
from mathutils import Vector, Euler


def sv_main(n_petals=8, vp_petal=20, profile_radius=1.3, amp=1.0):

    in_sockets = [
        ['s', 'Num Petals',  n_petals],
        ['s', 'Verts per Petal',  vp_petal],
        ['s', 'Profile Radius', profile_radius],
        ['s', 'Amp',  amp],
    ]

    # variables
    z_float = 0.0
    n_verts = n_petals * vp_petal
    section_angle = 360.0 / n_verts
    position = (2 * (pi / (n_verts / n_petals)))

    # consumables
    Verts = []

    # makes vertex coordinates
    for i in range(n_verts):
        # difference is a function of the position on the circumference
        difference = amp * cos(i * position)
        arm = profile_radius + difference
        ampline = Vector((arm, 0.0, 0.0))

        rad_angle = radians(section_angle * i)
        myEuler = Euler((0.0, 0.0, rad_angle), 'XYZ')

        # changes the vector in place, successive calls are accumulative
        # we reset at the start of the loop.
        ampline.rotate(myEuler)
        x_float = ampline.x
        y_float = ampline.y
        Verts.append((x_float, y_float, z_float))

    # makes edge keys, ensure cyclic
    Edges = [[i, i + 1] for i in range(n_verts - 1)]
    Edges.append([i, 0])

    out_sockets = [
        ['v', 'Verts', [Verts]],
        ['s', 'Edges', [Edges]],
    ]

    return in_sockets, out_sockets
