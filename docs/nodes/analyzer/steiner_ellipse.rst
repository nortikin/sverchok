Steiner Ellipse
===============

.. image:: https://user-images.githubusercontent.com/14288520/197339759-0adedfc5-3ff4-48c3-b1bc-0611f58d2547.png
  :target: https://user-images.githubusercontent.com/14288520/197339759-0adedfc5-3ff4-48c3-b1bc-0611f58d2547.png

Functionality
-------------

This node can generate either Steiner inellipse_ (inscribed ellipse) or Steiner
ellipse (circumellipse_) for each triangular face of the input mesh. For non-tri
faces, the node will either skip them or give an error, depending on a setting.

.. _inellipse: https://en.wikipedia.org/wiki/Steiner_inellipse
.. _circumellipse: https://en.wikipedia.org/wiki/Steiner_ellipse

Main properties of the Steiner inellipse are:

* It touches each side of the triangle in the midpoint of that side;
* The center of the ellipse is the centroid (barycenter) of the triangle.

Main properties of the Steiner circumellipse are:

* It touches the triangle in it's vertices;
* The center of the ellipse is the centroid (barycenter) of the triangle.

.. image:: https://user-images.githubusercontent.com/14288520/197340422-1ef4281c-720b-425c-83a3-f19839266f08.png
  :target: https://user-images.githubusercontent.com/14288520/197340422-1ef4281c-720b-425c-83a3-f19839266f08.png

Inputs
------

This node has the following inputs:

- **Vertices**. The vertices of the input mesh. This input is mandatory.
- **Faces**. The faces of the input mesh. This input is mandatory.

Parameters
-----------

This node has the following parameters:

- **Mode**. Defines which ellipses should be generated. The available modes are:

  - **Inellipse**. Generate Steiner inellipses (inscribed ellipses). This is the default mode.
  - **Circumellipse**. Generate Steiner circumellipses.

- **On non-tri faces**. Defines what the node should do if it encounters a
  non-triangular face. There are following options available:

   - **Skip**. Just skip such faces - do not generate inscribed circles for them.
   - **Error**. Stop processing and give an error (turn the node red).

   The default option is **Skip**. This parameter is available in the N panel only.

.. image:: https://user-images.githubusercontent.com/14288520/197340131-e740e76f-1123-4c49-9a57-afe51d68b8ec.png
  :target: https://user-images.githubusercontent.com/14288520/197340131-e740e76f-1123-4c49-9a57-afe51d68b8ec.png

Outputs
-------

This node has the following outputs:

- **Center**. Centers of the ellipses.
- **F1**, **F2**. Focal points of the ellipses.
- **SemiMajorAxis**. Lengths of semi-major axes of the ellipses.
- **SemiMinorAxis**. Lengths of semi-minor axes of the ellipses.
- **C**. Distances from the center of ellipse to it's focal points.
- **Eccentricity**. Eccentricity values of the ellipses.
- **Normal**. Normals of the planes where ellipses lie; i.e. face normals.
- **Matrix**. For each ellipse, this contains a matrix, Z axis of which points
  along face normal, and the translation component equals to the center of the
  ellipse. This output can be used to actually place ellipses at their places.


.. image:: https://user-images.githubusercontent.com/14288520/197339778-127d8e76-31b7-4106-82af-effedf52ffcb.png
  :target: https://user-images.githubusercontent.com/14288520/197339778-127d8e76-31b7-4106-82af-effedf52ffcb.png

See also
--------

* CAD-> :doc:`Offset </nodes/modifier_change/offset>`

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/197340888-f7efbd04-87d6-4c01-a894-5678ce6eb7ec.png
  :target: https://user-images.githubusercontent.com/14288520/197340888-f7efbd04-87d6-4c01-a894-5678ce6eb7ec.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Generator->Generator Extended-> :doc:`Ellipse </nodes/generators_extended/ellipse_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197341070-e2a795e9-5b68-419f-ba88-48d245836409.gif
  :target: https://user-images.githubusercontent.com/14288520/197341070-e2a795e9-5b68-419f-ba88-48d245836409.gif

---------

Inscribed ellipses for Delaunay triangulation of some random points:

.. image:: https://user-images.githubusercontent.com/14288520/197341404-3bc0e71f-6eac-4548-a772-ab56943483f2.png
  :target: https://user-images.githubusercontent.com/14288520/197341404-3bc0e71f-6eac-4548-a772-ab56943483f2.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator->Generator Extended-> :doc:`Ellipse </nodes/generators_extended/ellipse_mk3>`
* Spatial-> :doc:`Delaunay 2D </nodes/spatial/delaunay_2d>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Inscribed ellipses for triangulated Suzanne:

.. image:: https://user-images.githubusercontent.com/14288520/197342060-9ccf446e-4632-4956-9077-1656942e9177.png
  :target: https://user-images.githubusercontent.com/14288520/197342060-9ccf446e-4632-4956-9077-1656942e9177.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator->Generator Extended-> :doc:`Ellipse </nodes/generators_extended/ellipse_mk3>`
* Modifiers->Modifier Change-> :doc:`Triangulate Mesh </nodes/modifier_change/triangulate>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Circumellipse of some random triangle:

.. image:: https://user-images.githubusercontent.com/14288520/197342491-5d2ebc54-a92a-43c5-82bc-48f2553d843f.png
  :target: https://user-images.githubusercontent.com/14288520/197342491-5d2ebc54-a92a-43c5-82bc-48f2553d843f.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Generator->Generator Extended-> :doc:`Ellipse </nodes/generators_extended/ellipse_mk3>`
* Generator->Generators Extended-> :doc:`Triangle </nodes/generators_extended/triangle>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197342709-7520d927-0830-41b3-84d5-6c6f955427b4.gif
  :target: https://user-images.githubusercontent.com/14288520/197342709-7520d927-0830-41b3-84d5-6c6f955427b4.gif

