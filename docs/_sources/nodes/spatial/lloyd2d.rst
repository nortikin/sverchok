Lloyd 2D
========

.. image:: https://user-images.githubusercontent.com/14288520/202758803-abfc383d-8feb-4ef7-8159-4ca7545fa1f3.png
  :target: https://user-images.githubusercontent.com/14288520/202758803-abfc383d-8feb-4ef7-8159-4ca7545fa1f3.png

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points in 2D space
(XOY plane) uniformly inside bounding box or bounding circle.

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

.. image:: https://user-images.githubusercontent.com/14288520/202763588-bc4d27ec-87fc-4a75-849e-9cee13db7a14.png
  :target: https://user-images.githubusercontent.com/14288520/202763588-bc4d27ec-87fc-4a75-849e-9cee13db7a14.png

Inputs
------

This node has the following inputs:

* **Vertices**. Points to be redistributed. Only X and Y coordinates of these
  points will be used. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202764057-d3496a5d-21dc-4ebb-b7da-690c0fdfe416.png
  :target: https://user-images.githubusercontent.com/14288520/202764057-d3496a5d-21dc-4ebb-b7da-690c0fdfe416.png

* **Iterations**. Number of Lloyd's algorithm iterations. The default value is 3.
* **Weights**. Scalar Field object used to assign different weights for
  different places on XOY plane. More points will be put in places which have
  bigger weight. This input is optional. If not connected, uniform Lloyd
  algorithm will be used.

Parameters
----------

This node has the following parameters:

* **Bounds mode**. This defines bounding shape of generated points. The available options are:

  * **Bounding box**
  * **Bounding circle**.

  The default value is **Bounding box**.

.. image:: https://user-images.githubusercontent.com/14288520/202764601-be65e31c-b467-4937-8584-9ac48b7b6e67.png
  :target: https://user-images.githubusercontent.com/14288520/202764601-be65e31c-b467-4937-8584-9ac48b7b6e67.png

* **Clipping**. This parameter is available in the N panel only. Clipping
  distance for Voronoi diagrams used in the process of Lloyd algorithm. In most
  cases, this parameter has very slight effect on the result, so you do not
  have to change it. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/202764959-b6f2acd9-964d-4ef3-a114-e4983b396c2e.png
  :target: https://user-images.githubusercontent.com/14288520/202764959-b6f2acd9-964d-4ef3-a114-e4983b396c2e.png

Outputs
-------

This node has the following output:

* **Vertices**. Redistributed points.

Examples of Usage
-----------------

Redistribution within bounding box:

.. image:: https://user-images.githubusercontent.com/14288520/202765810-9c1f77e7-7d90-412e-9850-0eb447cc3940.png
  :target: https://user-images.githubusercontent.com/14288520/202765810-9c1f77e7-7d90-412e-9850-0eb447cc3940.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The same setup, but in "bounding circle" mode:

.. image:: https://user-images.githubusercontent.com/14288520/202766150-cddbf502-9043-4bfc-8990-3ce4d73e49c2.png
  :target: https://user-images.githubusercontent.com/14288520/202766150-cddbf502-9043-4bfc-8990-3ce4d73e49c2.png

---------

The same setup, but with distance from origin used as weight:

.. image:: https://user-images.githubusercontent.com/14288520/202766665-5c6d1029-4b3b-40b4-974b-257027197199.png
  :target: https://user-images.githubusercontent.com/14288520/202766665-5c6d1029-4b3b-40b4-974b-257027197199.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Weighted Lloyd distribution used to create Voronoi diagram:

.. image:: https://user-images.githubusercontent.com/14288520/202767953-6726827d-c1cf-4713-b39c-d35dd4335d30.png
  :target: https://user-images.githubusercontent.com/14288520/202767953-6726827d-c1cf-4713-b39c-d35dd4335d30.png