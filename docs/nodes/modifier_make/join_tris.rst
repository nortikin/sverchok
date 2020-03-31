join tris
=========

The workhorse code of this node is essentially a bmesh.operator (bmesh.ops)::

    def join_tris(verts, faces, self):
        if not verts:
            return False

        bm = bmesh_from_pydata(verts, [], faces)

        bmesh.ops.join_triangles(
            bm, faces=bm.faces,
            angle_face_threshold=self.face_threshold,
            angle_shape_threshold=self.shape_threshold
        )
        bm.verts.index_update()
        bm.faces.index_update()

        faces_out = []
        verts_out = [vert.co[:] for vert in bm.verts]
        _ = [faces_out.append([v.index for v in face.verts]) for face in bm.faces]

        bm.clear()
        bm.free()
        return (verts_out, faces_out)


params
------

Face Threshold.
Shape Threshold.

The inputs and outputs
----------------------

Verts and Polygons