from mathutils import Vector
from collections import defaultdict


def sv_main(verts=[[]], nx=20, ny=20, nz=20):

    in_sockets = [
        ['v', 'verts', verts],
        ['s', 'nx', nx],
        ['s', 'ny', ny],
        ['s', 'nz', nz]]

    grid_3d = defaultdict(list)

    def downsample(verts, n=(20, 20, 20)):

        def getBBox(verts):
            rotated = list(zip(*verts[::-1]))
            return [[min(dim), max(dim)] for dim in rotated]

        def get_divs(bbox):
            # refactor later.
            x_span = bbox[0][1] - bbox[0][0]
            y_span = bbox[1][1] - bbox[1][0]
            z_span = bbox[2][1] - bbox[2][0]
            x_seg = x_span / n[0]
            y_seg = y_span / n[1]
            z_seg = z_span / n[2]
            xdiv = [bbox[0][0] + (x_seg * i) for i in range(n[0])]
            ydiv = [bbox[1][0] + (y_seg * i) for i in range(n[1])]
            zdiv = [bbox[2][0] + (z_seg * i) for i in range(n[2])]
            return xdiv, ydiv, zdiv

        def avg_vert(verts):
            n_verts = len(verts)
            s = verts[0]
            if n_verts == 1:
                return s
            else:
                for v in verts[1:]:
                    s = s + v
                return s * (1 / n_verts)

        def find_slot(dim, dimdivs):
            for idx, div in reversed(list(enumerate(dimdivs))):
                if not dim >= div:
                    continue
                else:
                    return idx
            return 0

        def get_bucket_tuple(vec):
            x_idx = find_slot(vec.x, xdiv)
            y_idx = find_slot(vec.y, ydiv)
            z_idx = find_slot(vec.z, zdiv)
            return x_idx, y_idx, z_idx

        bbox = getBBox(verts)
        xdiv, ydiv, zdiv = get_divs(bbox)

        for v in verts:
            vec = Vector(v)
            bucket = get_bucket_tuple(vec)
            grid_3d[bucket].append(vec)

        return [avg_vert(v)[:] for v in grid_3d.values()]

    # out boilerplate - set your own sockets packet
    # the same principle as in in_sockets
    verts_out = []
    out_sockets = [['v', 'Downsampled', verts_out]]

    if verts and verts[0]:
        good_verts = verts[0]
        out_sockets[0][2] = [downsample(good_verts, n=(nx, ny, nz))]

    return in_sockets, out_sockets
