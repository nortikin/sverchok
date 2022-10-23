Sphere Fit
==========

.. image:: https://user-images.githubusercontent.com/14288520/197330854-5d86a738-29b0-452d-b388-45c363214c9d.png
  :target: https://user-images.githubusercontent.com/14288520/197330854-5d86a738-29b0-452d-b388-45c363214c9d.png

Functionality
-------------

This node tries to approximate the provided set of vertices by a sphere (in
other words, fit a sphere through given set of vertices). It searches for such
a sphere, that all provided vertices have the minimum distance to it.

The sphere is represented by it's center point and radius.

For this node to work correctly, it needs at least 4 vertices on the input.

Inputs
------

This node has the following input:

* **Vertices** - the vertices to be approximated with a sphere.

Outputs
-------

This node has the following outputs:

* **Center** - the center of the sphere.
* **Radius** - the radius of the sphere.
* **Projections** - projections of the input vertices to the sphere surface.
* **Diffs** - difference vectors, i.e. vectors pointing from original vertices
  to their projections to the sphere.
* **Distances** - distances from the original vertices to the sphere surface.

.. image:: https://user-images.githubusercontent.com/14288520/197332199-46278505-49d1-4a10-8cf8-6974723e2a23.png
  :target: https://user-images.githubusercontent.com/14288520/197332199-46278505-49d1-4a10-8cf8-6974723e2a23.png

.. image:: https://user-images.githubusercontent.com/14288520/197332488-92afed3f-9592-4c81-abe8-98502f8aaf81.gif
  :target: https://user-images.githubusercontent.com/14288520/197332488-92afed3f-9592-4c81-abe8-98502f8aaf81.gif

Examples of usage
-----------------

Fit a sphere for vertices from arbitrary mesh:

.. image:: https://user-images.githubusercontent.com/284644/74602397-d925c080-50c9-11ea-8981-9278eb618539.png
  :target: https://user-images.githubusercontent.com/284644/74602397-d925c080-50c9-11ea-8981-9278eb618539.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Fit a sphere for vertices from random vectors:

.. image:: https://user-images.githubusercontent.com/14288520/197332683-d83e1de6-0e8c-4ce2-b22e-607f94b50127.png
  :target: https://user-images.githubusercontent.com/14288520/197332683-d83e1de6-0e8c-4ce2-b22e-607f94b50127.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197332786-e33d48ec-955d-4555-9222-88c2d73a4786.gif
  :target: https://user-images.githubusercontent.com/14288520/197332786-e33d48ec-955d-4555-9222-88c2d73a4786.gif