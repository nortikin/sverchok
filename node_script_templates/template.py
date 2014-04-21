def sv_main(data=23, step=1):

    # in boilerplate - make your own sockets
    in_sockets = [
        ['s', 'Vertices',  data],
        ['s', 'Step', step],
    ]

    # import libraries if you need.
    from util import sv_zip
    from math import sin

    # your code here
    out_x = [i for i in range(int(data))]
    out_y = [0 for i in range(int(data))]
    out_z = [sin(i*step) for i in range(int(data))]
    out = [list(sv_zip(out_x, out_y, out_z))]
    edg = [[i, i-1] for i, ed in enumerate(out_x) if i > 0]

    # out boilerplate - set your own sockets packet
    out_sockets = [
        ['v', 'Out', out],
        ['s', 'edg', [edg]],
    ]

    return in_sockets, out_sockets

if __name__ == "__main__":
    # here your script's name must be the same as in blender's text datablock
    # no special characters (must be a valid variable name too, no dots)
    template = sv_main({0}, {1})
