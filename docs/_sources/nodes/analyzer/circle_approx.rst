Circle Fit
==========

.. image:: https://user-images.githubusercontent.com/14288520/197307332-2aaaa061-fe0b-4a35-b688-0f3896c7790e.png
  :target: https://user-images.githubusercontent.com/14288520/197307332-2aaaa061-fe0b-4a35-b688-0f3896c7790e.png

Functionality
-------------

This node tries to approximate the provided set of vertices by a circle (i.e.,
fit a circle through given set of vertices). It searches for such a circle, that
all provided vertices have minimum distance to it.

The circle is represented by it's center, it's radius, and a normal of a plane
it is lying in.

For this node to work correctly, it needs at least 3 vertices on the input.

Inputs
------

This node has the following input:

* **Vertices** - the vertices to be approximated with a circle.

Outputs
-------

This node has the following outputs:

* **Center** - the center of the circle.
* **Radius** - the radius of the circle.
* **Normal** - normal of the plane to which the circle belongs.
* **Matrix** - matrix mapping to the circle local coordinates; Z axis of this
  matrix is parallel to the normal vector of the plane.
* **Projections** - projections of the input vertices to the circle.
* **Diffs** - difference vectors, i.e. vectors pointing from original vertices
  to their projections to the circle.
* **Distances** - distances from the original vertices to the circle.

.. image:: https://user-images.githubusercontent.com/14288520/197329926-ad9e3c06-1832-4f66-a5c6-ca8cd38c24c5.png
  :target: https://user-images.githubusercontent.com/14288520/197329926-ad9e3c06-1832-4f66-a5c6-ca8cd38c24c5.png

Examples of usage
-----------------

Fit a circle for vertices from arbitrary mesh object:

.. image:: https://user-images.githubusercontent.com/14288520/197330263-3f960a21-daa0-4c87-a3b5-5eb66b95e7d9.png
  :target: https://user-images.githubusercontent.com/14288520/197330263-3f960a21-daa0-4c87-a3b5-5eb66b95e7d9.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197330493-8f7d7422-2213-46bc-9d41-6fdd109f8524.gif
  :target: https://user-images.githubusercontent.com/14288520/197330493-8f7d7422-2213-46bc-9d41-6fdd109f8524.gif