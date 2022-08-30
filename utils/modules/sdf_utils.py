import numpy as np

def geometry_from_points(points, mode="python"):
    """
    using sdf module from:  https://github.com/fogleman/sdf

    input:
        points: the direct output from `f.generate()`
        mode:   "np" (numpy), or "python"
    output:
        geom:   with a `.verts` attribute and `.tris`
                verts and tris are output in numpy arrays if the mode is "np",
                else standard python lists.

    usage in snlite:

        '''
        in scale v
        out verts v
        out faces s
        '''

        from sdf import *
        from sverchok.utils.modules.sdf_utils import geometry_from_points

        f = box(2) & slab(z0=-0.5, z1=0.5).k(0.1)
        f.scale((1, 0.5, 1))
        f -= cylinder(0.25).circular_array(6, 0.6).k(0.05)

        points = f.generate(samples=23200)

        geom = geometry_from_points(points, mode="np")
        verts.append(geom.verts)
        faces.append(geom.tris)

    """


    geom = lambda: None
    num_points = len(points)
    if mode == "python":
        geom.verts = [plist.tolist() for plist in points]
        geom.tris = np.arange(0, num_points, 1).reshape((-1, 3)).tolist()
    elif mode == "np":
        geom.verts = np.array(points)
        geom.tris = np.arange(0, num_points, 1).reshape((-1, 3))
    return geom
