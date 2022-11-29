Join Triangles
==============

.. image:: https://user-images.githubusercontent.com/14288520/199761921-6f72a310-a42d-4d5b-afb1-cde493ecd9d6.png
  :target: https://user-images.githubusercontent.com/14288520/199761921-6f72a310-a42d-4d5b-afb1-cde493ecd9d6.png


params
------

Face Threshold.
Shape Threshold.

The inputs and outputs
----------------------

Verts and Polygons

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

Examples
--------

.. image:: https://user-images.githubusercontent.com/619340/78026930-bccda280-735c-11ea-809e-b60a51b9938d.png
  :target: https://user-images.githubusercontent.com/619340/78026930-bccda280-735c-11ea-809e-b60a51b9938d.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Spatial-> :doc:`Delaunay 2D </nodes/spatial/delaunay_2d>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199772606-ca5afd88-096d-430b-a4a7-4e1e812c5280.png
  :target: https://user-images.githubusercontent.com/14288520/199772606-ca5afd88-096d-430b-a4a7-4e1e812c5280.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Modifiers->Modifier Change-> :doc:`Triangulate Mesh </nodes/modifier_change/triangulate>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
