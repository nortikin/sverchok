Lloyd 2D
========

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points in 2D space
(XOY plane) uniformly inside bounding box or bounding circle.

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

Inputs
------

This node has the following inputs:

* **Vertices**. Points to be redistributed. Only X and Y coordinates of these
  points will be used. This input is mandatory.
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

* **Clipping**. This parameter is available in the N panel only. Clipping
  distance for Voronoi diagrams used in the process of Lloyd algorithm. In most
  cases, this parameter has very slight effect on the result, so you do not
  have to change it. The default value is 1.0.

Outputs
-------

This node has the following output:

* **Vertices**. Redistributed points.

Examples of Usage
-----------------

Redistribution within bounding box:

.. image:: https://user-images.githubusercontent.com/284644/100523403-1b8c3a00-31d2-11eb-8d7f-26e0fc93ccd1.png

The same setup, but in "bounding circle" mode:

.. image:: https://user-images.githubusercontent.com/284644/100523404-1c24d080-31d2-11eb-9cf1-1ebe3d5447ad.png

The same setup, but with distance from origin used as weight:

.. image:: https://user-images.githubusercontent.com/284644/100523405-1cbd6700-31d2-11eb-84c5-ed21fdee7437.png

Weighted Lloyd distribution used to create Voronoi diagram:

.. image:: https://user-images.githubusercontent.com/284644/100244260-8af6f500-2f58-11eb-8805-7ebd9cf61423.png

