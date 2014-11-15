import mathutils
from mathutils import *


def sv_main(normals=[]):

    in_sockets = [
        ['v', 'normal', normals]]

    out = []

    if normals:
        for i in normals[0]:
            out.append(Vector(i).to_track_quat("Z", "X").to_euler()[:])

    out_sockets = [
        ['v', 'rotation_euler', [out]]
    ]

    return in_sockets, out_sockets
