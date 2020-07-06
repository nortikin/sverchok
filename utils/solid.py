# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from sverchok.dependencies import FreeCAD
if FreeCAD is  not None:
    import math
    from sverchok.data_structure import match_long_repeat as mlr
    import MeshPart
    
    def basic_mesher(solids, precisions):
        verts = []
        faces = []
        for solid, precision in zip(*mlr([solids, precisions])):
            rawdata = solid.tessellate(precision)
            b_verts = []
            b_faces = []
            for v in rawdata[0]:
                b_verts.append((v.x, v.y, v.z))
            for f in rawdata[1]:
                b_faces.append(f)
            verts.append(b_verts)
            faces.append(b_faces)

        return verts, faces

    def standard_mesher(solids, surface_deviation, angle_deviation, relative_surface_deviation):
        verts = []
        faces = []
        for solid, s_dev, ang_dev in zip(*mlr([solids, surface_deviation, angle_deviation])):
            mesh = MeshPart.meshFromShape(
                Shape=solid,
                LinearDeflection=s_dev,
                AngularDeflection=math.radians(ang_dev),
                Relative=relative_surface_deviation)

            verts.append([v[:] for v in mesh.Topology[0]])
            faces.append(mesh.Topology[1])

        return verts, faces

    def mefisto_mesher(solids, max_edge_length):

        verts = []
        faces = []
        for solid, max_edge in zip(*mlr([solids, max_edge_length])):
            mesh = MeshPart.meshFromShape(
                Shape=solid,
                MaxLength=max_edge
                )

            verts.append([v[:] for v in mesh.Topology[0]])
            faces.append(mesh.Topology[1])

        return verts, faces
