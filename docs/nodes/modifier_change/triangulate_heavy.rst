Triangulate Heavy
=================

This node tesselates all polygons that are not triangles, using this code::

            # for all objects/bm incomming:
            #
            for f in bm.faces:
                coords = [v.co for v in f.verts]
                indices = [v.index for v in f.verts]

                if len(coords) > 3:
                    for pol in tessellate([coords]):
                        new_faces.append([indices[i] for i in pol])
                else:
                    new_faces.append([v.index for v in f.verts])

which may not be super efficient.

   This node is a heavier implementation of Triangulate until someone finds time to figure
   out the bug in the original node.

