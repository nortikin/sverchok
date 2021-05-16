import numpy as np

def geometry_from_points(points, mode="python"):
    """
    using sdf module from:  https://github.com/fogleman/sdf

    f.ex:
        f = sdf.sphere()
        points = f.generate(samples=1200)   # higher is slower, but more precise.
        geom = geometry_from_points(points, mode="np")

        >>> geom.verts
        >>> geom.tris

    input:
        points: the direct output from `f.generate()`
        mode:   "np" (numpy), or "python"
    output:
        geom:   with a `.verts` atribute and `.tris`
                verts and tris are output in numpy arrays if the mode is "np",
                else standard python lists.
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